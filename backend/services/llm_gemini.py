import asyncio
import re
import numpy as np
from google import genai
from google.genai import types
from config import settings


class GeminiClient:
    def __init__(self, session):
        self.session = session
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.docs = []
        self.vecs = None

        self.sys_prompt = (
            "ROLE: You are an AI 911 Emergency Dispatcher. "
            "OBJECTIVE: Efficiently gather information, calm the caller, and simulate unit deployment. "
            "PROTOCOL:"
            "1. FIRST RESPONSE: Immediately ask '911, what is the location of your emergency?' "
            "2. GATHER INFO: Ask for the nature of the emergency (Police, Fire, Medical). "
            "3. CALM THE CALLER: Use phrases like 'Stay calm', 'Help is on the way', 'Stay on the line'. "
            "4. ACTION: Explicitly state you are dispatching units. E.g., 'I have dispatched Unit 4-Alpha to [Location].' "
            "5. DELEGATION: If the user asks complex questions, say 'I am connecting you to [Department Name] for further instruction.' "
            "CONSTRAINTS: "
            "Keep responses short (under 20 words) for speed. "
            "Speak with urgent, calm authority. "
            "Do NOT use markdown. Write strictly for Text-to-Speech audio."
        )

    async def generate_reply(self, history):
        if not history:

            query = "Hello"
        else:
            query = history[-1]["text"]

        context = ""

        prompt = f"Caller Input:\n{query}"

        try:
            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                config=types.GenerateContentConfig(
                    system_instruction=self.sys_prompt, temperature=0.4
                ),
                contents=prompt,
            )
            text = response.text if response.text else ""
            return self._clean_for_tts(text)
        except Exception as e:
            print(f"LLM Error: {e}")
            return "911 here. Please state your emergency."

    def _clean_for_tts(self, text):
        text = re.sub(r"[*_#`]", "", text)
        text = re.sub(r"\[.*?\]", "", text)
        return text.strip()
