"""FastAPI entrypoint for integrated clinical trial optimization system."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from Agents.agent_loop import run_agent_loop
from Pipeline.main_pipeline import MainPipeline, PipelineResult
from Utils.model_registry import get_model_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "Frontend"
# Support both "Dashboard/dist" and "dashboard/dist" naming.
DASHBOARD_DIST = BASE_DIR / "Dashboard" / "dist"
if not DASHBOARD_DIST.is_dir():
    DASHBOARD_DIST = BASE_DIR / "dashboard" / "dist"

app = FastAPI(title="Clinical Trial Intelligence Layer", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline: Optional[MainPipeline] = None


def get_pipeline() -> MainPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MainPipeline(models_dir="/models")
        logger.info("Main pipeline initialized with /models")
    return _pipeline


@app.on_event("startup")
async def on_startup() -> None:
    get_model_registry("/models")
    get_pipeline()


class AnalyzeBody(BaseModel):
    text: Optional[str] = Field(None, description="Clinical text for NER + LSTM path")
    image: Optional[list[Any]] = Field(None, description="Nested image array")


def _resolve_input(body: AnalyzeBody) -> Any:
    if body.image is not None:
        return body.image
    if body.text and body.text.strip():
        return body.text
    raise HTTPException(status_code=400, detail="Provide non-empty `text` or `image`.")


def _format_sse(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, default=str)}\n\n"


def _enhance_ws_event(ev: dict[str, Any]) -> dict[str, Any]:
    out = dict(ev)
    agent = str(ev.get("agent") or "")
    msg = str(ev.get("message") or "")
    if agent == "Architect":
        out["effect"] = "architect_pulse"
    elif agent == "Critic":
        out["effect"] = "critic_glitch" if "Missing" in msg else "critic_ok"
        out["feedback"] = msg[:280]
    return out


def _ner_graph_payload(pr: PipelineResult) -> dict[str, Any]:
    return {"type": "ner_graph", "route": pr.route, "entities": pr.ner_entities}


def _run_pipeline_with_logging(body: AnalyzeBody, log_cb: Optional[Any]) -> dict[str, Any]:
    user_input = _resolve_input(body)
    pipeline_result = get_pipeline().run(user_input, log_callback=log_cb)
    return run_agent_loop(pipeline_result, log_cb=log_cb, max_iterations=3)


@app.post("/analyze")
async def analyze(body: AnalyzeBody) -> JSONResponse:
    try:
        result = await asyncio.to_thread(_run_pipeline_with_logging, body, None)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("analyze failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return JSONResponse(content=result)


@app.get("/health")
async def health() -> JSONResponse:
    reg = get_model_registry("/models")
    return JSONResponse({"status": "ok", "models_loaded": reg.any_loaded()})


@app.post("/analyze/stream")
async def analyze_stream(body: AnalyzeBody) -> StreamingResponse:
    loop = asyncio.get_running_loop()
    out_q: asyncio.Queue = asyncio.Queue()

    def log_cb(ev: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(out_q.put_nowait, ev)

    async def event_generator():
        worker_exc: list[Optional[BaseException]] = [None]
        final_result: list[Optional[dict[str, Any]]] = [None]

        def worker() -> None:
            try:
                final_result[0] = _run_pipeline_with_logging(body, log_cb=log_cb)
            except Exception as e:
                worker_exc[0] = e
            finally:
                loop.call_soon_threadsafe(
                    out_q.put_nowait,
                    {"type": "__worker_done__"},
                )

        task = asyncio.create_task(asyncio.to_thread(worker))
        try:
            while True:
                item = await out_q.get()
                if item.get("type") == "__worker_done__":
                    break
                yield _format_sse(item)
        finally:
            await task
        err = worker_exc[0]
        if err is not None:
            if isinstance(err, HTTPException):
                yield _format_sse(
                    {
                        "type": "error",
                        "status": err.status_code,
                        "detail": err.detail,
                    }
                )
            else:
                yield _format_sse({"type": "error", "message": str(err)})
            return
        if final_result[0] is not None:
            yield _format_sse({"type": "result", "data": final_result[0]})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.websocket("/ws/agents")
async def ws_agents(websocket: WebSocket) -> None:
    """
    Stream agent reasoning + NER graph for the immersive dashboard.
    First client message: JSON {\"action\":\"analyze\",\"text\":\"...\"} (optional \"image\").
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": f"Invalid JSON: {e}"})
        except Exception:
            pass
        return

    if data.get("action") != "analyze":
        await websocket.send_json({"type": "error", "detail": "action must be 'analyze'"})
        return

    try:
        body = AnalyzeBody.model_validate(
            {"text": data.get("text"), "image": data.get("image")}
        )
    except Exception as e:
        await websocket.send_json({"type": "error", "detail": str(e)})
        return

    loop = asyncio.get_running_loop()
    out_q: asyncio.Queue = asyncio.Queue()
    final_holder: dict[str, Any] = {}
    worker_exc: list[Optional[BaseException]] = [None]

    def log_cb(ev: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(out_q.put_nowait, _enhance_ws_event(ev))

    def worker() -> None:
        try:
            user_input = _resolve_input(body)
            pr = get_pipeline().run(user_input, log_callback=log_cb)
            loop.call_soon_threadsafe(out_q.put_nowait, _ner_graph_payload(pr))
            final_holder["result"] = run_agent_loop(pr, log_cb=log_cb, max_iterations=3)
        except Exception as e:
            worker_exc[0] = e
        finally:
            loop.call_soon_threadsafe(
                out_q.put_nowait,
                {"type": "__worker_done__"},
            )

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        while True:
            item = await out_q.get()
            if item.get("type") == "__worker_done__":
                break
            try:
                await websocket.send_json(item)
            except WebSocketDisconnect:
                task.cancel()
                return
    finally:
        await task

    err = worker_exc[0]
    if err is not None:
        if isinstance(err, HTTPException):
            try:
                await websocket.send_json(
                    {"type": "error", "status": err.status_code, "detail": err.detail}
                )
            except WebSocketDisconnect:
                pass
        else:
            try:
                await websocket.send_json({"type": "error", "message": str(err)})
            except WebSocketDisconnect:
                pass
        return

    res = final_holder.get("result")
    if res is None:
        return
    try:
        await websocket.send_json({"type": "result", "data": res})
        await websocket.send_json({"type": "final_output", "data": res})
    except WebSocketDisconnect:
        pass


@app.get("/")
async def root() -> RedirectResponse:
    if DASHBOARD_DIST.is_dir():
        return RedirectResponse(url="/dashboard/", status_code=307)
    return RedirectResponse(url="/ui/index.html", status_code=307)


if DASHBOARD_DIST.is_dir():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(DASHBOARD_DIST), html=True),
        name="dashboard",
    )

if FRONTEND_DIR.is_dir():
    app.mount(
        "/ui",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="ui",
    )
