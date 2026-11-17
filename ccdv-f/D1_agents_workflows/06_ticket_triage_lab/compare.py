"""Run both designs on the same tickets and report their differences."""

import argparse
import asyncio
import json
import os
from collections import Counter
from pathlib import Path
from statistics import median
from time import perf_counter

from triage import Result, StubActionModel, Ticket, run_agent, run_workflow


def show_result(label: str, result: Result) -> None:
    print(f"  {label}: {' -> '.join(result.trace)}")
    if result.state.draft_feedback:
        print(f"    Guardrail: {result.state.draft_feedback}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticket", metavar="ID", help="run only the ticket with this ID")
    parser.add_argument("--live", action="store_true", help="use the Claude API and Agent SDK")
    parser.add_argument("--model", default=os.getenv("CLAUDE_MODEL"), help="Claude model ID")
    parser.add_argument("--graph", action="store_true", help="run the workflow using LangGraph")
    parser.add_argument("--ablation", action="store_true", help="also run the agent without delegation")
    args = parser.parse_args()

    dataset = json.loads(Path(__file__).with_name("tickets.json").read_text(encoding="utf-8"))
    rows = [row for row in dataset if args.ticket is None or row["id"] == args.ticket]
    if not rows:
        parser.error(f"unknown ticket ID: {args.ticket}")

    workflow_runner = run_workflow
    if args.live:
        if not os.getenv("ANTHROPIC_API_KEY") or not args.model:
            parser.error("--live requires ANTHROPIC_API_KEY and --model or CLAUDE_MODEL")
        from claude_triage import ClaudeWorkflow, run_claude_agent

        live_workflow = ClaudeWorkflow(args.model)
        workflow_runner = live_workflow.run
        agent_runner = lambda ticket: asyncio.run(run_claude_agent(ticket, live_workflow))
        without_delegate = lambda ticket: asyncio.run(
            run_claude_agent(ticket, live_workflow, delegate=False)
        )
    else:
        model = StubActionModel()
        model_without_delegate = StubActionModel(delegate=False)
        agent_runner = lambda ticket: run_agent(ticket, model)
        without_delegate = lambda ticket: run_agent(ticket, model_without_delegate)
    if args.graph:
        from graph_workflow import build_graph, run_graph

        graph = build_graph(live_workflow.classify, live_workflow.draft) if args.live else build_graph()
        workflow_runner = lambda ticket: run_graph(graph, ticket)

    runners = {"Workflow": workflow_runner, "Agent": agent_runner}
    if args.ablation:
        runners["Agent without delegation"] = without_delegate
    totals = Counter(row["case"] for row in rows)
    scores: dict[str, Counter[str]] = {label: Counter() for label in runners}
    ambiguous_times: dict[str, list[float]] = {label: [] for label in runners}
    differences: Counter[str] = Counter()
    mode = f"live Claude ({args.model})" if args.live else "offline stubs"
    print(f"Mode: {mode}"
          f" | workflow: {'LangGraph' if args.graph else 'Python'}")
    for row in rows:
        ticket = Ticket(row["id"], row["text"], row.get("simulate_bad_draft", False))
        expected = row["expected_category"]
        print(f"{ticket.id} [{row['case']}] expected={expected} | {ticket.text}")
        results = {}
        for label, runner in runners.items():
            started = perf_counter()
            result = runner(ticket)
            elapsed = perf_counter() - started
            results[label] = result
            show_result(label, result)
            if args.live:
                print(f"    Elapsed: {elapsed:.2f}s")
            if row["case"] == "ambiguous":
                ambiguous_times[label].append(elapsed)
            if result.state.classification.category == expected:
                scores[label][row["case"]] += 1

        workflow = results["Workflow"].state
        agent = results["Agent"].state
        fields = {
            "category": (workflow.classification.category, agent.classification.category),
            "queue": (workflow.queue, agent.queue),
            "accepted draft": (workflow.accepted_draft, agent.accepted_draft),
        }
        changed = [field for field, (before, after) in fields.items() if before != after]
        if not changed:
            print("  Outputs match.")
        for field in changed:
            before, after = fields[field]
            differences[field] += 1
            print(f"  {field}: workflow={before!r} | agent={after!r}")
        if changed:
            differences["tickets"] += 1
        differences["delegations"] += int(agent.delegated)
        if args.ablation:
            without_category = results["Agent without delegation"].state.classification.category
            if agent.classification.category != without_category:
                differences["ablation category"] += 1
                print(f"  Delegation: without={without_category} | with={agent.classification.category}")
        differences["agent retries"] += results["Agent"].trace.count("draft (rejected)")
        print()

    print("Category matches against sample labels")
    for label, score in scores.items():
        breakdown = ", ".join(f"{case} {score[case]}/{total}" for case, total in totals.items())
        print(f"  {label}: {breakdown}")
    print(
        f"Divergences: {differences['tickets']}/{len(rows)} tickets "
        f"(category {differences['category']}, queue {differences['queue']}, "
        f"accepted draft {differences['accepted draft']})"
    )
    print(
        f"Agent: {differences['delegations']} delegations, "
        f"{differences['agent retries']} draft retries"
    )
    if args.ablation:
        print(f"With/without delegation: {differences['ablation category']} category changes")
    if args.live and totals["ambiguous"]:
        print("Median end-to-end time on ambiguous tickets")
        for label, times in ambiguous_times.items():
            print(f"  {label}: {median(times):.2f}s")


if __name__ == "__main__":
    main()
