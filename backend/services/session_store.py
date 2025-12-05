import asyncio
from dataclasses import dataclass, field
from typing import Dict, List
from config import settings


@dataclass
class Turn:
    user_text: str
    ai_text: str


@dataclass
class SessionData:
    session_id: str
    turns: List[Turn] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: str) -> SessionData:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionData(session_id=session_id)
                self._sessions[session_id] = session
            return session

    async def append_turn(
        self, session_id: str, user_text: str, ai_text: str
    ) -> SessionData:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionData(session_id=session_id)
                self._sessions[session_id] = session
            session.turns.append(Turn(user_text=user_text, ai_text=ai_text))
            if len(session.turns) > settings.max_history_turns:
                session.turns = session.turns[-settings.max_history_turns :]
            return session

    async def get_history_for_llm(self, session_id: str) -> list:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []
            history = []
            for turn in session.turns:
                history.append({"role": "user", "text": turn.user_text})
                history.append({"role": "model", "text": turn.ai_text})
            return history
