# CCDV-F Domain 1 · Ticket Triage Lab

Practice building a support-ticket triage system as a fixed workflow and as a model-directed tool loop. The core exercises take about 70 minutes and run offline with Python 3.10+ and the standard library. The full lab adds the Claude Messages API, Claude Agent SDK, and a LangGraph implementation. All 16 tickets are synthetic.

## Run the lab

Open a terminal in this folder and run these commands.

```powershell
python -B compare.py
python -B compare.py --ticket T04
python -B compare.py --ticket T06
python -B compare.py --ablation
python -B -m unittest discover -v
```

`compare.py` prints both traces and shows any changes in category, queue, or accepted draft. The summary reports category matches by case type, specialist calls, and draft retries. Use `--ablation` to run the same agent with delegation disabled. You can save the report with `python -B compare.py --ablation > comparison.txt`.

## Run the full implementation

Install the optional packages in a virtual environment. The plain offline command remains available before installation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B -m unittest discover -v
.\.venv\Scripts\python.exe -B compare.py --graph --ablation
```

For live mode, set `ANTHROPIC_API_KEY` in your shell and set `CLAUDE_MODEL` to a model ID available to that key and supporting structured outputs. The lab reads the same key for the Messages API and SDK. Live runs make billable requests. Start with T06 to check setup before running all 16 tickets.

```powershell
.\.venv\Scripts\python.exe -B compare.py --live --ticket T06 --ablation
.\.venv\Scripts\python.exe -B compare.py --live --ablation > comparison-live.txt
```

- **Workflow.** The application fixes the classify → route → draft order. The Messages API classifies and writes the response. Python maps the result to a queue and validates the draft.
- **Agent.** The SDK streams a session with allowlisted triage tools. Claude chooses whether to call the specialist and whether to revise a rejected draft. A `PreToolUse` hook blocks a malformed `accept_draft` call, and the handler also validates before saving. The session has an eight-turn budget. Only a successful SDK result with an accepted draft completes the ticket.
- **Subagent.** The delegate tool starts a separate Claude Agent SDK session. It receives the ticket and candidate categories, uses a dedicated classification prompt, and returns a validated category. This keeps the specialist focused on resolving the primary issue and lets the comparison disable delegation while preserving the main prompt and the other tools.
- **LangGraph.** `graph_workflow.py` rebuilds the workflow orchestration as three connected nodes using the same classifier, draft writer, and acceptance rule. It makes the state and edges explicit, with graph APIs available if the flow later needs branches or checkpoints. The fixed three-step version takes less plumbing in plain Python. The parity test runs every fixture through both implementations.

The live report logs elapsed wall-clock time per run and the median for ambiguous tickets, including session startup and tool calls. Compare the delegated agent with the same agent without delegation to estimate the extra time and any accuracy change. The local report below uses deterministic fixtures. A credentialed live run is needed for Claude measurements. See the [Messages API](https://platform.claude.com/docs/en/api/python/messages/create), [Agent SDK tools](https://code.claude.com/docs/en/agent-sdk/custom-tools), [hook reference](https://code.claude.com/docs/en/agent-sdk/hooks), and [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).

## Learning goals

1. Trace which decisions the application owns and which decisions it gives the model.
2. Enforce a response-format rule at the point where a draft is accepted.
3. Delegate a narrow classification decision using only the ticket text and candidate categories.
4. Measure the effect of delegation and retry on the same set of tickets.

## Hands-on practice

| Time | Exercise |
| --- | --- |
| 10 min | Read T01, T04, T06, T07, and T09 in `tickets.json`. Cover the expected categories and predict each version's route, whether it will delegate, and whether a draft will be accepted. Run the comparison and check your predictions. |
| 15 min | Rebuild `run_workflow()` from its three steps in `triage.py`, then run `python -B -m unittest -v test_triage.WorkflowTests`. Trace T06 through the keyword classifier and explain how it picks a route when two categories match. |
| 20 min | Trace how `run_agent()` passes the updated state back to `StubActionModel.choose_action()`. Run the full comparison with `--ablation` and record which tickets change category with delegation. |
| 15 min | Try to get the guardrail to accept a malformed draft. Run `python -B -m unittest -v test_triage.GuardrailTests test_triage.AgentTests`. Add one format edge case to `GuardrailTests` and rerun it. For a budget experiment, change the default `max_turns` to 4, run only T04, and explain the outcome before restoring 8. |
| 10 min | Answer the reflection questions and run the full comparison and test suite again. |

## What to observe

- The workflow calls classify → route → draft once per ticket. Its category follows the order in `KEYWORDS` when several categories match. Both versions share this classifier, the queue map, the draft writer, and the acceptance guardrail.
- T04 deliberately produces a draft with the wrong label. The guardrail accepts a draft only if it contains exactly one line beginning with `Next step:` and that line contains text after the label. The workflow ends with a rejected draft. The agent sees the feedback and attempts another draft before choosing `finish`.
- T06, T08, and T09 change routes after the specialist checks the ticket text. T07 delegates and keeps the original route. The specialist can return `general` for manual triage if the ticket gives too little evidence about the primary issue.
- The offline reference run has seven tickets with output differences. T06, T08, T09, T14, T15, and T16 change category, route, and draft. T04 changes draft acceptance only. The workflow and both agent variants match 8 of 8 clear labels. The delegated agent matches 7 of 8 ambiguous labels and the workflow and agent without delegation each match 2 of 8. T15 shows a specialist miss. These fixture scores describe the local rules.
- The offline loop's `ActionModel`, `DraftWriter`, and `Specialist` are injectable, so you can replace one collaborator at a time. The full live agent exercises the SDK's own tool loop and hook.

## Exam-style reflection

1. Every request follows classify → route → draft, and an LLM picks one of four queues. Is the system a workflow or an agent? Which part of the scenario determines your answer?
2. A support system must decide after classifying whether to delegate, route immediately, or request more information. Which architecture fits, and what intermediate result should drive the decision?
3. An outgoing response must contain exactly one nonempty `Next step:` line. Where would you enforce it, and what should happen when the check fails?
4. The loop reaches its turn budget after rejecting two drafts. What condition would signal successful completion, and what should the caller get when the budget runs out?
5. An ambiguous ticket mentions both a billing error and a login problem. What information should you send to a classification specialist, and what should it return if the primary issue remains unclear?
6. The specialist runs on four tickets and changes three routes. Which measurements from a fresh labeled dataset would tell you whether delegation is worth keeping?
