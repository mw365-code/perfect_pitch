from typing import Protocol

from domain.models import NoteAttempt, SessionSummary


class AttemptStore(Protocol):
    def add_attempt(self, attempt: NoteAttempt) -> None: ...

    def list_recent_attempts(self, limit: int = 500) -> list[NoteAttempt]: ...

    def list_attempts_for_session(self, session_id: str) -> list[NoteAttempt]: ...


class SessionStore(Protocol):
    def start_session(self, session_id: str, started_at: str) -> None: ...

    def finish_session(self, summary: SessionSummary, ended_at: str) -> None: ...
