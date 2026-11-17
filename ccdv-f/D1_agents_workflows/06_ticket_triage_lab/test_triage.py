import unittest

from triage import (
    FORMAT_ERROR,
    StubActionModel,
    Ticket,
    check_draft,
    classify_ambiguous,
    run_agent,
    run_workflow,
    write_stub_draft,
)


class WorkflowTests(unittest.TestCase):
    def test_clear_ticket_follows_fixed_steps(self):
        result = run_workflow(Ticket("TEST", "Please send my invoice."))
        self.assertEqual(result.trace, ("classify", "route", "draft (accepted)"))
        self.assertEqual(result.state.classification.category, "billing")
        self.assertEqual(result.state.queue, "Billing Support")
        self.assertIsNone(check_draft(result.state.accepted_draft))

    def test_ambiguous_ticket_uses_fixed_priority(self):
        ticket = Ticket("TEST", "The payment went through. The invoice is fine but I see an error.")
        result = run_workflow(ticket)
        self.assertEqual(result.state.classification.candidates, ("billing", "technical"))
        self.assertEqual(result.state.queue, "Billing Support")
        self.assertEqual(result.trace, ("classify", "route", "draft (accepted)"))

    def test_malformed_draft_is_rejected(self):
        result = run_workflow(Ticket("TEST", "The app shows an error.", simulate_bad_draft=True))
        self.assertIsNone(result.state.accepted_draft)
        self.assertEqual(result.state.draft_feedback, FORMAT_ERROR)
        self.assertEqual(result.trace[-1], "draft (rejected)")


class GuardrailTests(unittest.TestCase):
    def test_requires_one_nonempty_next_step_line(self):
        self.assertIsNone(check_draft("Thanks for the details.\nNext step: Send the invoice."))
        for draft in (
            "Please send the invoice.",
            "Next step:  ",
            "Thanks. Next step: Send the invoice.",
            "Next step: Send the invoice.\nNext step:",
        ):
            with self.subTest(draft=draft):
                self.assertEqual(check_draft(draft), FORMAT_ERROR)


class AgentTests(unittest.TestCase):
    def test_clear_ticket_skips_delegation(self):
        def unexpected_specialist(text, candidates):
            self.fail("The specialist should only receive ambiguous tickets.")

        result = run_agent(
            Ticket("TEST", "My password expired."),
            StubActionModel(),
            specialist=unexpected_specialist,
        )
        self.assertEqual(result.trace, ("classify", "route", "draft (accepted)", "finish"))
        self.assertEqual(result.state.queue, "Account Support")

    def test_ambiguous_ticket_delegates_once_and_routes_from_result(self):
        ticket = Ticket("TEST", "The payment went through. The invoice is fine but I see an error.")
        calls = []

        def specialist(text, candidates):
            calls.append((text, candidates))
            return classify_ambiguous(text, candidates)

        result = run_agent(ticket, StubActionModel(), specialist=specialist)
        self.assertEqual(calls, [(ticket.text, ("billing", "technical"))])
        self.assertEqual(result.trace, ("classify", "delegate", "route", "draft (accepted)", "finish"))
        self.assertEqual(result.state.classification.category, "technical")
        self.assertEqual(result.state.queue, "Technical Support")

    def test_specialist_can_return_manual_triage_when_evidence_is_inconclusive(self):
        result = run_agent(Ticket("TEST", "I have an invoice and a login question."), StubActionModel())
        self.assertEqual(result.state.classification.category, "general")
        self.assertEqual(result.state.queue, "Manual Triage")

    def test_agent_retries_with_feedback(self):
        feedback_seen = []

        def writer(ticket, category, feedback):
            feedback_seen.append(feedback)
            return write_stub_draft(ticket, category, feedback)

        result = run_agent(
            Ticket("TEST", "The app shows an error.", simulate_bad_draft=True),
            StubActionModel(),
            writer=writer,
        )
        self.assertEqual(feedback_seen, [None, FORMAT_ERROR])
        self.assertEqual(result.trace[-3:], ("draft (rejected)", "draft (accepted)", "finish"))
        self.assertIsNone(check_draft(result.state.accepted_draft))

    def test_agent_cannot_finish_before_a_draft_is_accepted(self):
        class FinishImmediately:
            def choose_action(self, ticket, state):
                return "finish"

        with self.assertRaisesRegex(ValueError, "'finish' is unavailable"):
            run_agent(Ticket("TEST", "My password expired."), FinishImmediately())

    def test_agent_stops_retrying_at_turn_limit(self):
        def broken_writer(ticket, category, feedback):
            return "Always missing the required line."

        with self.assertRaisesRegex(RuntimeError, "exhausted its 8-turn budget"):
            run_agent(Ticket("TEST", "My password expired."), StubActionModel(), writer=broken_writer)


if __name__ == "__main__":
    unittest.main()
