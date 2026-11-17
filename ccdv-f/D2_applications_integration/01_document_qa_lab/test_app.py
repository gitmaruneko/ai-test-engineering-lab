import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from app import ROOT, Settings, create_app
from model import Answer, ClaudeProvider, Completion, OfflineProvider, request_messages, streamed_answer
from session_store import Session, SessionChanged, SessionStore


def upload(client, name="report.md", data=b"Backup coordinator: Kai.\n\nRollback coordinator: June."):
    return client.post(
        "/api/sessions", content=data,
        headers={"Content-Type": "text/plain", "X-Document-Name": quote(name)},
    )


def ask(client, session_id, question):
    response = client.post(f"/api/sessions/{session_id}/questions", json={"question": question})
    return response, [json.loads(line) for line in response.iter_lines()]


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "sessions.sqlite3"
        self.settings = Settings.model_validate_json((ROOT / "config.json").read_bytes())
        self.client = TestClient(create_app(self.db, OfflineProvider(), self.settings))
        self.addCleanup(self.client.close)

    def test_streams_answers_with_citations_for_all_sample_reports(self):
        prompts = {
            "checkout-incident.md": ("What triggered the rollback?", "5%"),
            "backup-drill.md": ("How long did the restore take?", "seventy-four minutes"),
            "search-maintenance.md": ("When is index maintenance scheduled?", "02:00 UTC"),
        }
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/static/app.js").status_code, 200)
        for name, (question, expected) in prompts.items():
            with self.subTest(name=name):
                session = upload(self.client, name, (ROOT / "samples" / name).read_bytes())
                self.assertEqual(session.status_code, 201)
                response, events = ask(self.client, session.json()["id"], question)
                self.assertIn("application/x-ndjson", response.headers["content-type"])
                self.assertGreater(len(events), 2)
                answer = events[-1]["turn"]
                self.assertEqual(events[-1]["event"], "done")
                self.assertIn(expected, answer["answer"])
                self.assertIn(expected, answer["citations"][0]["excerpt"])
                self.assertEqual(
                    "".join(event["text"] for event in events[:-1]), answer["answer"]
                )
                self.assertIsNone(answer["usage"])

    def test_reopens_context_from_sqlite_and_restart_removes_followup_context(self):
        original = upload(self.client, "維運報告.md").json()
        path = f"/api/sessions/{original['id']}"
        ask(self.client, original["id"], "Who is the rollback coordinator?")

        with TestClient(create_app(self.db, OfflineProvider(), self.settings)) as reopened:
            restored = reopened.get(path).json()
            self.assertEqual(restored["name"], "維運報告.md")
            self.assertEqual(restored["total_turns"], 1)
            _, events = ask(reopened, original["id"], "Who is its coordinator?")
            self.assertIn("June", events[-1]["turn"]["answer"])
            fresh = reopened.post(f"{path}/restart").json()
            self.assertNotEqual(fresh["id"], original["id"])
            self.assertEqual(fresh["total_turns"], 0)
            self.assertEqual(fresh["section_count"], 2)
            _, events = ask(reopened, fresh["id"], "Who is its coordinator?")
            self.assertIn("Kai", events[-1]["turn"]["answer"])
            self.assertEqual(reopened.get(path).json()["total_turns"], 2)

    def test_summarizes_only_older_turns_and_bounds_saved_context(self):
        settings = self.settings.model_copy(update={"recent_turns": 2, "summary_entries": 1})
        with TestClient(create_app(self.db, OfflineProvider(), settings)) as client:
            session_id = upload(client).json()["id"]
            for index in range(1, 5):
                _, events = ask(client, session_id, f"Rollback question {index}")
            self.assertEqual(events[-1]["summarized_turns"], 2)
            self.assertEqual(events[-1]["retained_turns"], 2)

        session = SessionStore(self.db, 2, 1).get(session_id)
        self.assertEqual([turn["question"] for turn in session.recent],
                         ["Rollback question 3", "Rollback question 4"])
        self.assertEqual([entry["question"] for entry in session.summary], ["Rollback question 2"])
        self.assertEqual(session.summary[0]["citations"], [2])

    def test_invalid_citation_is_rejected_and_never_saved(self):
        class BrokenProvider:
            mode = "offline"

            async def respond(self, session, question):
                yield "Preview"
                yield Completion(Answer(answer="Preview", evidence="grounded", citations=[7]))

        with TestClient(create_app(self.db, BrokenProvider(), self.settings)) as client:
            session_id = upload(client).json()["id"]
            _, events = ask(client, session_id, "What happened?")
            self.assertEqual([event["event"] for event in events], ["delta", "error"])
            self.assertEqual(client.get(f"/api/sessions/{session_id}").json()["recent"], [])

    def test_rejects_invalid_uploads_and_missing_question(self):
        self.assertEqual(upload(self.client, "report.pdf").status_code, 400)
        self.assertEqual(upload(self.client, data=b"\xff").status_code, 400)
        self.assertEqual(upload(self.client, data=b"  ").status_code, 400)
        oversized = b"a" * (self.settings.max_document_bytes + 1)
        self.assertEqual(upload(self.client, data=oversized).status_code, 413)
        session_id = upload(self.client).json()["id"]
        response, _ = ask(self.client, session_id, "   ")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/sessions/missing").status_code, 404)

    def test_database_prevents_stale_request_overwriting_a_saved_turn(self):
        store = SessionStore(self.db, 4, 6)
        session = store.create("report.txt", ["Report excerpt"])
        store.append(session, {"question": "First", "answer": "A", "citations": []})
        with self.assertRaises(SessionChanged):
            store.append(session, {"question": "Stale", "answer": "B", "citations": []})
        self.assertEqual(store.get(session.id).recent[0]["question"], "First")


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def test_document_prefix_is_stable_across_questions_and_restarts(self):
        empty = Session("a", "first.md", ["Policy text"], [], [], 0)
        saved = Session("b", "renamed.md", ["Policy text"], [], [{"question": "First"}], 1)
        first, first_context = request_messages(empty, "First")[0]["content"]
        second, second_context = request_messages(saved, "Second")[0]["content"]
        self.assertEqual(first, second)
        self.assertEqual(second["cache_control"], {"type": "ephemeral"})
        self.assertNotEqual(first_context, second_context)

    def test_does_not_preview_json_metadata_or_unfinished_unicode(self):
        self.assertEqual(streamed_answer('{"answer":"first\\u'), "first")
        self.assertEqual(streamed_answer('{"answer":"first","citations":[1'), "first")
        self.assertEqual(streamed_answer('{"answer"'), "")

    async def test_live_adapter_converts_sdk_text_and_usage_to_stream_events(self):
        class FakeStream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *error):
                return None

            @property
            async def text_stream(self):
                yield '{"answer":"Hel'
                yield 'lo","citations":[1],"evidence":"grounded"}'

            async def get_final_message(self):
                return SimpleNamespace(
                    stop_reason="end_turn",
                    usage=SimpleNamespace(input_tokens=17, cache_creation_input_tokens=0,
                                          cache_read_input_tokens=1000, output_tokens=8),
                )

        with patch("model.AsyncAnthropic") as client:
            client.return_value.messages.stream.return_value = FakeStream()
            provider = ClaudeProvider("pinned-test-model", "Support prompt", 200)
            session = Session("a", "first.md", ["Hello"], [], [], 0)
            events = [event async for event in provider.respond(session, "What does it say?")]
        self.assertEqual(events[:-1], ["Hel", "lo"])
        self.assertEqual(events[-1].answer.citations, [1])
        self.assertEqual(events[-1].usage.cache_read_input_tokens, 1000)
        kwargs = client.return_value.messages.stream.call_args.kwargs
        self.assertEqual(kwargs["model"], "pinned-test-model")
        self.assertEqual(kwargs["output_config"]["format"]["schema"]["required"][0], "answer")


if __name__ == "__main__":
    unittest.main()
