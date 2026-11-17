"""SQLite-backed document sessions and bounded conversation context."""

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


class SessionChanged(Exception):
    """Another request saved a turn against the same session revision."""


@dataclass(frozen=True)
class Session:
    id: str
    name: str
    sections: list[str]
    recent: list[dict]
    summary: list[dict]
    revision: int

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "section_count": len(self.sections),
            "total_turns": self.revision,
            "summarized_turns": self.revision - len(self.recent),
            "recent": self.recent,
        }


class SessionStore:
    def __init__(self, path: Path, recent_turns: int, summary_entries: int):
        self.path = path
        self.recent_turns = recent_turns
        self.summary_entries = summary_entries
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sections TEXT NOT NULL,
                    recent TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    revision INTEGER NOT NULL
                )
            """)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def create(self, name: str, sections: list[str]) -> Session:
        session = Session(uuid4().hex, name, sections, [], [], 0)
        with closing(self.connect()) as db, db:
            db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, '[]', '[]', 0)",
                (session.id, name, json.dumps(sections)),
            )
        return session

    def get(self, session_id: str) -> Session | None:
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT name, sections, recent, summary, revision FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        name, sections, recent, summary, revision = row
        return Session(
            session_id, name, json.loads(sections), json.loads(recent), json.loads(summary), revision,
        )

    def append(self, session: Session, turn: dict) -> None:
        recent = [*session.recent, turn]
        summary = list(session.summary)
        for older_turn in recent[:-self.recent_turns]:
            answer = older_turn["answer"]
            summary.append({
                "question": older_turn["question"][:160],
                "answer_excerpt": answer[:220],
                "citations": [citation["section"] for citation in older_turn["citations"]],
            })
        recent = recent[-self.recent_turns:]
        summary = summary[-self.summary_entries:]
        with closing(self.connect()) as db, db:
            updated = db.execute(
                """UPDATE sessions SET recent = ?, summary = ?, revision = revision + 1
                   WHERE id = ? AND revision = ?""",
                (json.dumps(recent), json.dumps(summary), session.id, session.revision),
            )
            if updated.rowcount != 1:
                raise SessionChanged("Session advanced during this answer.")
