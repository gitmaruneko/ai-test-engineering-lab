"""Shared answer schema and streaming providers."""

import asyncio
import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol

from anthropic import AsyncAnthropic
from pydantic import BaseModel, ConfigDict
from pydantic_core import from_json

from session_store import Session


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    answer: str
    citations: list[int]
    evidence: Literal["grounded", "insufficient"]

    def verify(self, sections: list[str]) -> None:
        if not self.answer.strip():
            raise ValueError("Answer is empty.")
        if bool(self.citations) != (self.evidence == "grounded"):
            raise ValueError("Citation list conflicts with evidence status.")
        if len(set(self.citations)) != len(self.citations):
            raise ValueError("Duplicate citations.")
        if any(section < 1 or section > len(sections) for section in self.citations):
            raise ValueError("Citation outside the document.")


class Usage(BaseModel):
    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class Completion:
    answer: Answer
    usage: Usage | None = None


class Provider(Protocol):
    mode: str

    def respond(self, session: Session, question: str) -> AsyncIterator[str | Completion]: ...


def request_messages(session: Session, question: str) -> list[dict]:
    document = [{"section": number, "text": text} for number, text in enumerate(session.sections, 1)]
    recent = [
        {
            "question": turn["question"], "answer": turn["answer"],
            "citations": [citation["section"] for citation in turn["citations"]],
        }
        for turn in session.recent
    ]
    return [{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": json.dumps({"report": document}, ensure_ascii=False),
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": json.dumps({
                    "older_context": session.summary, "recent_turns": recent, "question": question,
                }, ensure_ascii=False),
            },
        ],
    }]


def streamed_answer(raw: str) -> str:
    """Extract just the answer text from a possibly incomplete JSON prefix."""
    try:
        partial = from_json(raw, allow_partial="trailing-strings")
    except ValueError:
        return ""
    if isinstance(partial, dict) and isinstance(partial.get("answer"), str):
        return partial["answer"]
    return ""


class ClaudeProvider:
    mode = "claude"

    def __init__(self, model: str, prompt: str, max_output_tokens: int):
        self.model = model
        self.prompt = prompt
        self.max_output_tokens = max_output_tokens
        self.client = AsyncAnthropic(timeout=60, max_retries=1)

    async def respond(self, session: Session, question: str) -> AsyncIterator[str | Completion]:
        async with self.client.messages.stream(
            model=self.model,
            system=self.prompt,
            max_tokens=self.max_output_tokens,
            messages=request_messages(session, question),
            output_config={"format": {"type": "json_schema", "schema": Answer.model_json_schema()}},
        ) as stream:
            raw = ""
            sent = ""
            async for delta in stream.text_stream:
                raw += delta
                preview = streamed_answer(raw)
                if preview.startswith(sent) and len(preview) > len(sent):
                    yield preview[len(sent):]
                    sent = preview
            message = await stream.get_final_message()
        if message.stop_reason != "end_turn":
            raise ValueError(f"Claude stopped with {message.stop_reason}.")
        result = Answer.model_validate_json(raw)
        usage = message.usage
        yield Completion(result, Usage(
            input_tokens=usage.input_tokens,
            cache_creation_input_tokens=usage.cache_creation_input_tokens or 0,
            cache_read_input_tokens=usage.cache_read_input_tokens or 0,
            output_tokens=usage.output_tokens,
        ))


STOP_WORDS = {
    "a", "an", "and", "are", "did", "do", "for", "how", "in", "is", "it", "its",
    "of", "on", "that", "the", "their", "to", "was", "what", "when", "where", "who", "with",
}


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP_WORDS


class OfflineProvider:
    mode = "offline"

    async def respond(self, session: Session, question: str) -> AsyncIterator[str | Completion]:
        words = terms(question)
        context = set()
        if session.recent and re.search(r"\b(it|its|that|their)\b", question.lower()):
            context = terms(session.recent[-1]["question"])

        def relevance(pair: tuple[int, str]) -> tuple[int, int, bool]:
            paragraph = pair[1]
            paragraph_terms = terms(paragraph)
            has_body = "\n" in paragraph or not paragraph.startswith("#")
            return len(words & paragraph_terms), len(context & paragraph_terms), has_body

        section, paragraph = max(
            enumerate(session.sections, 1), key=relevance,
        )
        if words & terms(paragraph):
            excerpt = paragraph[:640]
            if len(paragraph) > len(excerpt):
                excerpt += "…"
            result = Answer(answer=excerpt, citations=[section], evidence="grounded")
        else:
            result = Answer(
                answer="文件中找不到可用關鍵字定位的答案。請改用文件中的詞彙或段落名稱提問。",
                citations=[], evidence="insufficient",
            )
        for start in range(0, len(result.answer), 32):
            yield result.answer[start:start + 32]
            await asyncio.sleep(0.015)
        yield Completion(result)
