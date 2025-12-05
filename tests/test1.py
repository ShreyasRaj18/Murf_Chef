import os
from deepgram import DeepgramClient
import asyncio

DEEPGRAM_SECRET = os.getenv("DEEPGRAM_API_SECRET")
dg = DeepgramClient(DEEPGRAM_SECRET)


async def run():
    res = await dg.transcription.prerecorded(
        {
            "url": "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
        },
        {"punctuate": True},
    )
    print(res)


asyncio.run(run())
