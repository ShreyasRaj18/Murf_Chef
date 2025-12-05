## Murf Chef - made by B. Shree Shreyas Raj , Rishi Mittal , Dhruv Mittal

---
Demo Video
---
[![Watch the Demo](https://img.shields.io/badge/Watch-Demo%20Video-blue?style=for-the-badge)](./TestVideo.mp4)

---
Introduction
---
Our aim was to provide guidance to people who are beginners in cooking. So we use Murf Falcon for TTS, Deepgram for ASR and Gemini for intelligence. It provides step by step guidance for any recipe in visual slide decks with voice assistants. So while cooking they do not need to touch their phone or laptop.

---
How It Works
---
Murf Chef is a voice-interactive cooking assistant that guides users through recipes hands-free. The application workflow consists of:

1. **User Input**: The user speaks a recipe name or cooking query
2. **Speech Recognition (ASR)**: Deepgram's live speech-to-text service captures and transcribes the user's voice in real-time
3. **AI Processing**: Google Gemini LLM processes the transcribed text and generates intelligent, contextual cooking guidance with step-by-step instructions
4. **Text-to-Speech (TTS)**: Murf Falcon converts the AI-generated guidance into natural, expressive audio output
5. **Visual + Audio Feedback**: The frontend displays recipe steps as visual slide decks while the voice assistant simultaneously narrates instructions

This seamless integration enables users to follow recipes completely hands-free while cooking, without needing to interact with their device.

---
Technical Stack
---
**Backend (Python)**
- **Framework**: Python server handling core logic
- **ASR Service**: Deepgram Live API for real-time speech-to-text transcription
- **LLM Service**: Google Gemini API for intelligent recipe guidance and step generation
- **TTS Service**: Murf Falcon API for high-quality natural voice synthesis
- **Session Management**: In-memory session store for managing user conversations and recipe state

**Frontend (React)**
- **UI Framework**: React.js for interactive user interface
- **Communication**: WebSocket/HTTP for real-time communication with backend
- **Display**: Visual slide deck rendering for step-by-step recipe presentation

**Key Components**:
- `asr_deepgram_live.py`: Handles live audio stream processing and speech-to-text conversion
- `llm_gemini.py`: Interfaces with Google Gemini for recipe guidance generation
- `tts_murf_falcon.py`: Converts text responses to natural voice output using Murf's API
- `session_store.py`: Maintains user session data and conversation history
- `pipeline.py`: Orchestrates the complete flow from audio input to voice output
- `server.py`: Main Flask application serving API endpoints

---
API Keys & Configuration
---
Murf Chef requires the following API keys and environment variables to function. Create a `.env` file in the `backend/` directory with the following:

**Required API Keys:**
1. **DEEPGRAM_API_KEY** - API key for Deepgram speech-to-text service
   - Service: Speech Recognition (ASR)
   - Get it from: https://console.deepgram.com

2. **GEMINI_API_KEY** - API key for Google Gemini LLM
   - Service: AI-powered recipe guidance generation
   - Get it from: https://aistudio.google.com/app/apikey

3. **MURF_API_KEY** - API key for Murf Falcon text-to-speech service
   - Service: Natural voice synthesis
   - Get it from: https://app.murf.ai/account/settings

**Optional Configuration Variables:**
- `VOICE_SERVER_HOST` (default: "0.0.0.0") - Server host address
- `VOICE_SERVER_PORT` (default: "8080") - Server port
- `DEEPGRAM_MODEL` (default: "nova-2-general") - Deepgram ASR model
- `GEMINI_MODEL` (default: "gemini-1.5-flash") - Gemini LLM model
- `MURF_VOICE_ID` (default: "en-US-natalie") - Murf voice character
- `MURF_BASE_URL` (default: "https://global.api.murf.ai") - Murf API endpoint
- `DEFAULT_LANGUAGE` (default: "en-US") - Default language for the application
- `TTS_SAMPLE_RATE` (default: "24000") - Audio sample rate in Hz
- `MAX_HISTORY_TURNS` (default: "10") - Maximum conversation history turns
- `REQUEST_TIMEOUT_SECONDS` (default: "20") - API request timeout

**Example .env file:**
```
DEEPGRAM_API_KEY=your_deepgram_key_here
GEMINI_API_KEY=your_gemini_key_here
MURF_API_KEY=your_murf_key_here
VOICE_SERVER_PORT=8080
GEMINI_MODEL=gemini-1.5-flash
MURF_VOICE_ID=en-US-natalie
```