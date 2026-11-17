"""Rebuild the fixed workflow's orchestration with LangGraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from triage import (
    QUEUES, Classification, Classifier, DraftWriter, Result, State, Ticket,
    attempt_draft, classify, write_stub_draft,
)


class GraphState(TypedDict, total=False):
    ticket: Ticket
    classification: Classification
    triage: State


def build_graph(classifier: Classifier = classify, writer: DraftWriter = write_stub_draft):
    def classify_node(state: GraphState):
        return {"classification": classifier(state["ticket"])}

    def route_node(state: GraphState):
        classification = state["classification"]
        return {"triage": State(classification=classification, queue=QUEUES[classification.category])}

    def draft_node(state: GraphState):
        return {"triage": attempt_draft(state["triage"], state["ticket"], writer)}

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify_node)
    graph.add_node("route", route_node)
    graph.add_node("draft", draft_node)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "route")
    graph.add_edge("route", "draft")
    graph.add_edge("draft", END)
    return graph.compile()


def run_graph(graph, ticket: Ticket) -> Result:
    state = graph.invoke({"ticket": ticket})["triage"]
    outcome = "rejected" if state.draft_feedback else "accepted"
    return Result(state, ("classify", "route", f"draft ({outcome})"))
