from google import genai
from config import settings
import requests

text = "This is a test voice output."

payload = {"voiceId": settings.murf_voice_id, "text": text, "format": "mp3"}

headers = {"apikey": settings.murf_api_key, "Content-Type": "application/json"}

r = requests.post(
    f"{settings.murf_base_url}/v1/speech/generate", json=payload, headers=headers
)
print(r.status_code)
print(r.text)
