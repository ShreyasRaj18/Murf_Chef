import json
import base64
import websockets
from config import settings


class MurfFalconClient:
    def __init__(self):
        self.url = (
            f"wss://global.api.murf.ai/v1/speech/stream-input"
            f"?api-key={settings.murf_api_key}"
            f"&model=FALCON"
            f"&sample_rate={settings.tts_sample_rate}"
            f"&channel_type=MONO"
            f"&format=PCM"
        )

    async def stream_tts(self, text: str):
        async with websockets.connect(self.url) as ws:
            voice_config = {
                "voice_config": {
                    "voiceId": settings.murf_voice_id,
                    "multiNativeLocale": "hi-IN",
                    "style": "Conversation",
                    "rate": 0,
                    "pitch": 0,
                    "variation": 0.25,
                    "model": "FALCON",
                }
            }

            await ws.send(json.dumps(voice_config))
            await ws.send(json.dumps({"text": text, "end": True}))

            while True:
                resp = await ws.recv()
                data = json.loads(resp)

                if "audio" in data:
                    audio_bytes = base64.b64decode(data["audio"])
                    # RAW 16-bit PCM now, no header to strip
                    yield audio_bytes

                if data.get("final"):
                    break
