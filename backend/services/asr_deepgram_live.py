import json
import websockets
import logging
from config import settings

logger = logging.getLogger("asr-deepgram-live")


class DeepgramLiveClient:
    def __init__(self) -> None:
        self.base_url = "wss://api.deepgram.com/v1/listen"

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Sends audio bytes to Deepgram over WebSocket and waits for the final transcript.
        This reduces HTTP overhead compared to the REST API.
        """
        if not audio_bytes:
            return ""

        url = (
            f"{self.base_url}"
            f"?model={settings.deepgram_model}"
            f"&smart_format=true"
            f"&encoding=linear16"
            f"&sample_rate=48000"
            f"&channels=1"
        )

        headers = {"Authorization": f"Token {settings.deepgram_api_key}"}

        try:
            async with websockets.connect(url, extra_headers=headers) as ws:

                await ws.send(audio_bytes)

                await ws.send(b"")

                final_transcript = ""

                async for message in ws:
                    data = json.loads(message)

                    if "channel" in data:
                        alts = data["channel"]["alternatives"]
                        if alts:
                            transcript = alts[0].get("transcript", "")
                            if transcript:
                                final_transcript += transcript + " "

                    if data.get("type") == "Metadata":
                        break

                return final_transcript.strip()

        except Exception as e:
            logger.error(f"Deepgram Live Error: {e}")
            return ""
