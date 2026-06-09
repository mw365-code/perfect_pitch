from datetime import datetime, timezone
from uuid import uuid4

from domain.adaptation_service import AdaptationService
from domain.models import AttemptFeedback, NoteAttempt, Prompt, SessionSummary
from domain.ports import AttemptStore, SessionStore


class SessionService:
    def __init__(
        self,
        attempt_store: AttemptStore,
        session_store: SessionStore,
        adaptation_service: AdaptationService,
        notes: list[str],
    ) -> None:
        self._attempt_store = attempt_store
        self._session_store = session_store
        self._adaptation_service = adaptation_service
        self._notes = notes

    def start_session(self) -> str:
        session_id = str(uuid4())
        self._session_store.start_session(session_id, _utc_now_iso())
        return session_id

    def next_prompt(self, octave: int = 4) -> Prompt:
        recent = self._attempt_store.list_recent_attempts()
        note = self._adaptation_service.choose_next_note(self._notes, recent)
        return Prompt(target_note=note, octave=octave)

    def record_attempt(
        self,
        session_id: str,
        target_note: str,
        guessed_note: str,
        octave: int,
        response_ms: int,
        timbre: str,
    ) -> AttemptFeedback:
        normalized_guess = guessed_note.upper().strip()
        correct = normalized_guess == target_note
        attempt = NoteAttempt(
            session_id=session_id,
            target_note=target_note,
            guessed_note=normalized_guess,
            octave=octave,
            correct=correct,
            response_ms=max(response_ms, 0),
            timbre=timbre,
            created_at=_utc_now_iso(),
        )
        self._attempt_store.add_attempt(attempt)
        return AttemptFeedback(
            correct=correct,
            target_note=target_note,
            guessed_note=normalized_guess,
            response_ms=max(response_ms, 0),
        )

    def finish_session(self, session_id: str) -> SessionSummary:
        attempts = self._attempt_store.list_attempts_for_session(session_id)
        total = len(attempts)
        correct = sum(1 for item in attempts if item.correct)
        accuracy = (correct / total) if total else 0.0
        summary = SessionSummary(
            session_id=session_id,
            total_attempts=total,
            correct_attempts=correct,
            accuracy=accuracy,
        )
        self._session_store.finish_session(summary, _utc_now_iso())
        return summary

    def list_recent_attempts(self, limit: int = 500) -> list[NoteAttempt]:
        return self._attempt_store.list_recent_attempts(limit=limit)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
