"""Local document Q&A app with a streamed HTTP API."""

import json
import logging
import os
import re
from contextlib import aclosing, asynccontextmanager
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from model import ClaudeProvider, Completion, OfflineProvider, Provider
from session_store import Session, SessionChanged, SessionStore


ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger(__name__)


class Settings(BaseModel):
    model: str
    prompt_version: str = Field(pattern=r"^v[1-9][0-9]*$")
    max_output_tokens: int = Field(gt=0)
    recent_turns: int = Field(gt=0)
    summary_entries: int = Field(gt=0)
    max_document_bytes: int = Field(gt=0)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=800)


def packet(event: str, **data) -> bytes:
    return (json.dumps({"event": event, **data}, ensure_ascii=False) + "\n").encode("utf-8")


async def read_document(request: Request, limit: int) -> tuple[str, list[str]]:
    name = PureWindowsPath(unquote(request.headers.get("x-document-name", ""))).name
    if Path(name).suffix.lower() not in {".md", ".txt"} or len(name) > 150:
        raise HTTPException(400, "請上傳檔名在 150 字元以內的 .txt 或 .md 文件。")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise HTTPException(413, f"文件大小須在 {limit // 1024} KiB 以內。")
        body.extend(chunk)
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(400, "文件須為 UTF-8 文字。") from error
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        raise HTTPException(400, "文件包含不支援的控制字元。")
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    sections = [section.strip() for section in re.split(r"\n[ \t]*\n", text) if section.strip()]
    if not sections:
        raise HTTPException(400, "文件沒有可讀內容。")
    if len(sections) > 512:
        raise HTTPException(400, "文件最多可包含 512 個段落。")
    return name, sections


def create_app(
    db_path: Path | None = None,
    provider: Provider | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings.model_validate_json((ROOT / "config.json").read_bytes())
    if provider is None:
        mode = os.getenv("D2_PROVIDER", "offline")
        if mode == "claude":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise RuntimeError("Set ANTHROPIC_API_KEY before starting in Claude mode.")
            prompt = (ROOT / "prompts" / f"{settings.prompt_version}.txt").read_text(encoding="utf-8")
            provider = ClaudeProvider(settings.model, prompt, settings.max_output_tokens)
        elif mode == "offline":
            provider = OfflineProvider()
        else:
            raise RuntimeError("D2_PROVIDER must be offline or claude.")
    store = SessionStore(
        db_path or ROOT / ".local" / "sessions.sqlite3",
        settings.recent_turns,
        settings.summary_entries,
    )
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            if isinstance(provider, ClaudeProvider):
                await provider.client.close()

    app = FastAPI(title="D2 文件問答", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    def load_session(session_id: str) -> Session:
        session = store.get(session_id)
        if session is None:
            raise HTTPException(404, "找不到這個對話。")
        return session

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/config")
    def config():
        return {
            "mode": provider.mode, "model": settings.model,
            "prompt_version": settings.prompt_version,
            "max_document_bytes": settings.max_document_bytes,
        }

    @app.post("/api/sessions", status_code=201)
    async def upload(request: Request):
        name, sections = await read_document(request, settings.max_document_bytes)
        session = await run_in_threadpool(store.create, name, sections)
        return session.public()

    @app.get("/api/sessions/{session_id}")
    def session_details(session_id: str):
        return load_session(session_id).public()

    @app.post("/api/sessions/{session_id}/restart", status_code=201)
    def restart(session_id: str):
        current = load_session(session_id)
        return store.create(current.name, current.sections).public()

    @app.post("/api/sessions/{session_id}/questions")
    async def ask(session_id: str, body: Question):
        question = body.question.strip()
        if not question:
            raise HTTPException(400, "請輸入問題。")
        session = await run_in_threadpool(load_session, session_id)

        async def events():
            try:
                async with aclosing(provider.respond(session, question)) as stream:
                    async for part in stream:
                        if isinstance(part, str):
                            yield packet("delta", text=part)
                            continue
                        if isinstance(part, Completion):
                            completed = part
                            break
                    else:
                        raise ValueError("Stream ended without a final answer.")
                answer = completed.answer
                answer.verify(session.sections)
                turn = {
                    "question": question,
                    "answer": answer.answer,
                    "citations": [
                        {"section": number, "excerpt": session.sections[number - 1][:280]}
                        for number in answer.citations
                    ],
                    "evidence": answer.evidence,
                    "usage": completed.usage.model_dump() if completed.usage else None,
                }
                await run_in_threadpool(store.append, session, turn)
                total = session.revision + 1
                retained = min(total, settings.recent_turns)
                yield packet(
                    "done", turn=turn, total_turns=total, summarized_turns=total - retained,
                    retained_turns=retained,
                )
            except SessionChanged:
                yield packet("error", message="這個對話已有新答案。重新整理後再提問。")
            except (ValidationError, ValueError):
                yield packet("error", message="回答未通過驗證。已保留原本的對話，請再試一次。")
            except Exception as error:
                LOG.warning("Question stream failed: %s", type(error).__name__)
                yield packet("error", message="回答暫時無法完成。請稍後再試。")

        return StreamingResponse(
            events(), media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    return app
