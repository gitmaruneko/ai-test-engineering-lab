import json
import unittest
from importlib.util import find_spec
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from triage import Ticket, classify, run_workflow


@unittest.skipUnless(find_spec("langgraph"), "install requirements.txt for LangGraph tests")
class LangGraphTests(unittest.TestCase):
    def test_graph_matches_python_workflow_for_all_fixtures(self):
        from graph_workflow import build_graph, run_graph

        graph = build_graph()
        rows = json.loads(Path(__file__).with_name("tickets.json").read_text(encoding="utf-8"))
        for row in rows:
            with self.subTest(ticket=row["id"]):
                ticket = Ticket(row["id"], row["text"], row.get("simulate_bad_draft", False))
                self.assertEqual(run_graph(graph, ticket), run_workflow(ticket))


@unittest.skipUnless(
    find_spec("anthropic") and find_spec("claude_agent_sdk"),
    "install requirements.txt for Claude adapter tests",
)
class ClaudeTests(unittest.IsolatedAsyncioTestCase):
    def test_messages_workflow_passes_classification_to_drafting(self):
        from claude_triage import ClaudeWorkflow

        def response(text):
            return SimpleNamespace(
                stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)],
            )

        with patch("claude_triage.Anthropic") as anthropic:
            create = anthropic.return_value.messages.create
            create.side_effect = [
                response('{"category":"technical","candidates":["billing","technical"]}'),
                response("Thanks for reporting the issue.\nNext step: Share the error message."),
            ]
            result = ClaudeWorkflow("test-model").run(
                Ticket("TEST", "The invoice is correct, but there is an error.")
            )
        self.assertEqual(result.state.queue, "Technical Support")
        self.assertEqual(result.trace, ("classify", "route", "draft (accepted)"))
        self.assertIn("output_config", create.call_args_list[0].kwargs)
        draft_input = json.loads(create.call_args_list[1].kwargs["messages"][0]["content"])
        self.assertEqual(draft_input["category"], "technical")

    async def test_sdk_hook_blocks_bad_draft_and_specialist_gets_isolated_context(self):
        from claude_triage import SUBMIT_TOOL, ResultMessage, create_sdk_mcp_server, run_claude_agent

        ticket = Ticket("TEST", "The invoice is correct, but opening the paid page shows an error.")
        workflow = SimpleNamespace(model="test-model", classify=classify)
        registered = {}

        def capture_server(name, *, tools):
            registered.update({tool.name: tool.handler for tool in tools})
            return create_sdk_mcp_server(name, tools=tools)

        def success(**fields):
            return ResultMessage(
                subtype="success", duration_ms=0, duration_api_ms=0,
                is_error=False, num_turns=1, session_id="fake-session", **fields,
            )

        async def fake_query(*, prompt, options):
            message = await anext(prompt)
            payload = json.loads(message["message"]["content"])
            if options.output_format:
                self.assertEqual(payload, {"ticket": ticket.text, "candidates": ["billing", "technical"]})
                self.assertEqual(options.tools, [])
                self.assertFalse(options.mcp_servers)
                yield success(structured_output={"category": "technical"})
                return

            self.assertEqual(payload, {"ticket": ticket.text})
            await registered["classify"]({})
            await registered["delegate"]({})
            routed = await registered["route"]({})
            self.assertEqual(json.loads(routed["content"][0]["text"])["queue"], "Technical Support")

            matcher, = options.hooks["PreToolUse"]
            self.assertEqual(matcher.matcher, SUBMIT_TOOL)
            hook, = matcher.hooks
            bad_draft = {"draft": "Share the error message."}
            rejected = await hook({"tool_input": bad_draft}, "bad-call", {})
            self.assertEqual(rejected["hookSpecificOutput"]["permissionDecision"], "deny")
            good_draft = {"draft": "Next step: Share the error message."}
            self.assertEqual(await hook({"tool_input": good_draft}, "good-call", {}), {})
            self.assertFalse((await registered["accept_draft"](good_draft))["is_error"])
            yield success()

        with (
            patch("claude_triage.create_sdk_mcp_server", side_effect=capture_server),
            patch("claude_triage.query", side_effect=fake_query),
        ):
            result = await run_claude_agent(ticket, workflow)
        self.assertTrue(result.state.delegated)
        self.assertEqual(result.state.classification.category, "technical")
        self.assertEqual(result.trace[-3:], ("draft (rejected)", "draft (accepted)", "finish"))

    async def test_sdk_ablation_does_not_register_specialist_tool(self):
        from claude_triage import run_claude_agent

        async def fake_result(prompt, options):
            self.assertNotIn("mcp__triage__delegate", options.allowed_tools)
            self.assertEqual(len(options.allowed_tools), 3)

        with (
            patch("claude_triage.sdk_result", side_effect=fake_result),
            self.assertRaisesRegex(RuntimeError, "without an accepted draft"),
        ):
            await run_claude_agent(
                Ticket("TEST", "My invoice and login are broken."),
                SimpleNamespace(model="test-model", classify=classify),
                delegate=False,
            )
