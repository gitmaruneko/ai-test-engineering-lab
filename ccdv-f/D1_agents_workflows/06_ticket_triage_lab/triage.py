"""Shared triage tools, a fixed workflow, and a model-directed loop."""

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal, Protocol


Category = Literal["billing", "technical", "account", "general"]
Action = Literal["classify", "delegate", "route", "draft", "finish"]

KEYWORDS: dict[Category, set[str]] = {
    "billing": {"charge", "charged", "invoice", "refund"},
    "technical": {"checkout", "crash", "error", "loading"},
    "account": {"email", "locked", "login", "password"},
}
QUEUES = {
    "billing": "Billing Support",
    "technical": "Technical Support",
    "account": "Account Support",
    "general": "Manual Triage",
}
NEXT_STEPS = {
    "billing": "Share the relevant invoice number so we can review it.",
    "technical": "Share the exact error message and when it appears.",
    "account": "Tell us which account access step is failing.",
    "general": "Tell us which issue you would like us to address first.",
}
NEXT_STEP_PREFIX = "Next step:"
FORMAT_ERROR = "Use exactly one line beginning with 'Next step:' and add text on that line."


@dataclass(frozen=True)
class Ticket:
    id: str
    text: str
    simulate_bad_draft: bool = False


@dataclass(frozen=True)
class Classification:
    category: Category
    candidates: tuple[Category, ...]

    @property
    def ambiguous(self) -> bool:
        return len(self.candidates) > 1


@dataclass(frozen=True)
class State:
    classification: Classification | None = None
    queue: str | None = None
    delegated: bool = False
    accepted_draft: str | None = None
    draft_feedback: str | None = None


@dataclass(frozen=True)
class Result:
    state: State
    trace: tuple[str, ...]


class ActionModel(Protocol):
    def choose_action(self, ticket: Ticket, state: State) -> Action: ...


DraftWriter = Callable[[Ticket, Category, str | None], str]
Specialist = Callable[[str, tuple[Category, ...]], Category]
Classifier = Callable[[Ticket], Classification]


def classify(ticket: Ticket) -> Classification:
    words = set(re.findall(r"\b[a-z]+\b", ticket.text.casefold()))
    candidates = tuple(
        category for category, keywords in KEYWORDS.items() if words & keywords
    )
    # The fixed baseline uses priority order when several categories match.
    return Classification(candidates[0] if candidates else "general", candidates)


def classify_ambiguous(text: str, candidates: tuple[Category, ...]) -> Category:
    """Stub for a specialist whose task is to identify the primary issue."""
    evidence: tuple[tuple[str, Category], ...] = (
        ("payment went through", "technical"),
        ("main issue is the duplicate charge", "billing"),
        ("main issue is unlocking", "account"),
    )
    text = text.casefold()
    matches = {
        category
        for phrase, category in evidence
        if phrase in text and category in candidates
    }
    if len(matches) == 1:
        return matches.pop()
    return "general"


def write_stub_draft(ticket: Ticket, category: Category, feedback: str | None) -> str:
    heading = f"Thanks for contacting {QUEUES[category]}."
    label = NEXT_STEP_PREFIX
    if ticket.simulate_bad_draft and feedback is None:
        label = "What to do:"
    return f"{heading}\n{label} {NEXT_STEPS[category]}"


def check_draft(draft: str) -> str | None:
    """Return feedback when the required line is absent, empty, or repeated."""
    lines = [line for line in draft.splitlines() if line.startswith(NEXT_STEP_PREFIX)]
    if len(lines) == 1 and lines[0][len(NEXT_STEP_PREFIX):].strip():
        return None
    return FORMAT_ERROR


def attempt_draft(state: State, ticket: Ticket, writer: DraftWriter) -> State:
    if state.classification is None or state.queue is None:
        raise ValueError("Route the classified ticket before drafting.")
    draft = writer(ticket, state.classification.category, state.draft_feedback)
    return accept_draft(state, draft)


def accept_draft(state: State, draft: str) -> State:
    feedback = check_draft(draft)
    return replace(
        state,
        accepted_draft=draft if feedback is None else None,
        draft_feedback=feedback,
    )


def run_workflow(
    ticket: Ticket,
    writer: DraftWriter = write_stub_draft,
    classifier: Classifier = classify,
) -> Result:
    classification = classifier(ticket)
    state = State(classification=classification, queue=QUEUES[classification.category])
    state = attempt_draft(state, ticket, writer)
    outcome = "rejected" if state.draft_feedback else "accepted"
    return Result(state, ("classify", "route", f"draft ({outcome})"))


class StubActionModel:
    """Choose one action from the current tool results on each turn."""

    def __init__(self, delegate: bool = True):
        self.delegate = delegate

    def choose_action(self, ticket: Ticket, state: State) -> Action:
        if state.classification is None:
            return "classify"
        if self.delegate and state.classification.ambiguous and not state.delegated:
            return "delegate"
        if state.queue is None:
            return "route"
        if state.accepted_draft is None:
            return "draft"
        return "finish"


def run_agent(
    ticket: Ticket,
    model: ActionModel,
    writer: DraftWriter = write_stub_draft,
    specialist: Specialist = classify_ambiguous,
    max_turns: int = 8,
) -> Result:
    state = State()
    trace: list[str] = []
    for _ in range(max_turns):
        action = model.choose_action(ticket, state)
        classification = state.classification
        match action:
            case "classify" if classification is None:
                state = replace(state, classification=classify(ticket))
            case "delegate" if classification and classification.ambiguous and not state.delegated:
                state = apply_specialist(
                    classification, specialist(ticket.text, classification.candidates)
                )
            case "route" if classification and state.queue is None:
                state = replace(state, queue=QUEUES[classification.category])
            case "draft" if state.queue is not None and state.accepted_draft is None:
                state = attempt_draft(state, ticket, writer)
                outcome = "rejected" if state.draft_feedback else "accepted"
                trace.append(f"draft ({outcome})")
                continue
            case "finish" if state.accepted_draft is not None:
                return Result(state, (*trace, "finish"))
            case _:
                raise ValueError(f"Action {action!r} is unavailable in the current state.")
        trace.append(action)
    raise RuntimeError(f"{ticket.id}: agent exhausted its {max_turns}-turn budget.")


def apply_specialist(classification: Classification, category: Category) -> State:
    if category not in (*classification.candidates, "general"):
        raise ValueError(f"Invalid specialist category: {category}")
    # A new classification invalidates any earlier route or draft.
    return State(classification=replace(classification, category=category), delegated=True)
