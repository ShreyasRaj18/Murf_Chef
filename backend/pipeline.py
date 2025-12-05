import logging
from aiohttp import web
from services.llm_gemini import GeminiClient
from services.tts_murf_falcon import MurfFalconClient
from services.session_store import SessionStore

from services.asr_deepgram_live import DeepgramLiveClient
from config import settings

logger = logging.getLogger("911-pipeline")


class VoicePipeline:
    def __init__(
        self,
        asr: DeepgramLiveClient,
        llm: GeminiClient,
        tts: MurfFalconClient,
        store: SessionStore,
    ) -> None:
        self.asr = asr
        self.llm = llm
        self.tts = tts
        self.store = store

    async def handle_audio_utterance(
        self, session_id: str, audio_bytes: bytes, ws: web.WebSocketResponse
    ) -> None:
        try:

            transcript = await self.asr.transcribe(audio_bytes)
        except Exception as e:
            logger.exception("ASR Critical Failure")

            await self._safe_send_json(
                ws,
                {
                    "type": "error",
                    "component": "asr",
                    "sessionId": session_id,
                    "detail": "Line interference, could not hear.",
                },
            )
            return

        if not transcript:

            return

        await self._safe_send_json(
            ws, {"type": "user_transcript", "sessionId": session_id, "text": transcript}
        )

        reply_text = ""
        try:
            history = await self.store.get_history_for_llm(session_id)
            history.append({"role": "user", "text": transcript})

            reply_text = await self.llm.generate_reply(history)

        except Exception as e:
            logger.exception("LLM Critical Failure")

            reply_text = "I am experiencing a system delay. Units are being notified. Please stay on the line."

        if not reply_text:
            reply_text = "911. I am here."

        await self.store.append_turn(session_id, transcript, reply_text)

        await self._safe_send_json(
            ws, {"type": "ai_text", "sessionId": session_id, "text": reply_text}
        )

        await self._safe_send_json(
            ws,
            {
                "type": "audio_start",
                "sessionId": session_id,
                "sampleRate": settings.tts_sample_rate,
            },
        )

        try:

            async for chunk in self.tts.stream_tts(reply_text):
                try:
                    if ws.closed:
                        break
                    await ws.send_bytes(chunk)
                except Exception as e:
                    logger.exception("Socket Send Error during TTS")
                    break
        except Exception as e:
            logger.exception("TTS Generation Failure")

        await self._safe_send_json(ws, {"type": "audio_end", "sessionId": session_id})

    async def _safe_send_json(self, ws: web.WebSocketResponse, payload: dict) -> None:
        try:
            if not ws.closed:
                await ws.send_json(payload)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
