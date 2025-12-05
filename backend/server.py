import asyncio
import json
import logging
import uuid
from typing import Dict
from aiohttp import web, ClientSession, WSMsgType
from config import settings
from services.llm_gemini import GeminiClient
from services.tts_murf_falcon import MurfFalconClient
from services.session_store import SessionStore
from pipeline import VoicePipeline
from backend.services.asr_deepgram_live import DeepgramLiveClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-backend")


class AppState:
    def __init__(self) -> None:
        self.http_session: ClientSession | None = None
        self.pipeline: VoicePipeline | None = None
        self.session_store = SessionStore()
        self.active_connections: Dict[str, web.WebSocketResponse] = {}


state = AppState()


async def on_startup(app: web.Application) -> None:
    session = ClientSession()

    asr = DeepgramLiveClient(session)
    llm = GeminiClient(session=session)
    tts = MurfFalconClient()

    state.http_session = session
    state.pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts, store=state.session_store)

    app["http_session"] = session
    logger.info("Pipeline initialized")


async def on_cleanup(app: web.Application) -> None:
    await app["http_session"].close()
    if state.http_session is not None:
        await state.http_session.close()
    logger.info("Cleanup complete")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(max_msg_size=10 * 1024 * 1024)
    await ws.prepare(request)
    session_id = request.query.get("sessionId") or str(uuid.uuid4())
    state.active_connections[session_id] = ws
    await ws.send_json({"type": "session_welcome", "sessionId": session_id})
    logger.info("WebSocket connected %s", session_id)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await handle_text_message(session_id, ws, msg.data)
            elif msg.type == WSMsgType.BINARY:
                await handle_audio_message(session_id, ws, msg.data)
            elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                break
    finally:
        state.active_connections.pop(session_id, None)
        logger.info("WebSocket closed %s", session_id)
        await ws.close()
    return ws


async def handle_text_message(
    session_id: str, ws: web.WebSocketResponse, data: str
) -> None:
    try:
        obj = json.loads(data)
    except Exception:
        await ws.send_json(
            {"type": "error", "sessionId": session_id, "reason": "invalid_json"}
        )
        return
    kind = obj.get("type")
    if kind == "ping":
        await ws.send_json({"type": "pong", "sessionId": session_id})
    elif kind == "reset_session":
        await state.session_store.append_turn(session_id, "", "")
        await ws.send_json({"type": "session_reset", "sessionId": session_id})
    else:
        await ws.send_json(
            {
                "type": "unknown_message_type",
                "sessionId": session_id,
                "receivedType": kind,
            }
        )


async def handle_audio_message(
    session_id: str, ws: web.WebSocketResponse, audio_bytes: bytes
) -> None:
    if not audio_bytes:
        return
    if state.pipeline is None:
        await ws.send_json(
            {"type": "error", "sessionId": session_id, "reason": "pipeline_unavailable"}
        )
        return
    asyncio.create_task(
        state.pipeline.handle_audio_utterance(session_id, audio_bytes, ws)
    )


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ws/voice", websocket_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


async def main() -> None:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.host, settings.port)
    await site.start()
    logger.info("Server running on %s:%s", settings.host, settings.port)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
