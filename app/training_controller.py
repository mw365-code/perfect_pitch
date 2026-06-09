import time
from dataclasses import dataclass
from enum import Enum

from domain.models import AttemptFeedback, Prompt, SessionSummary
from domain.progress_service import ProgressService
from domain.session_service import SessionService
from infra.audio.player import AudioPlayer
from infra.audio.tone_generator import ToneGenerator


class RoundPhase(str, Enum):
    PROMPT_NOTE = "PROMPT_NOTE"
    AWAIT_ANSWER = "AWAIT_ANSWER"
    RESOLVE_ANSWER = "RESOLVE_ANSWER"
    DROP_PHASE = "DROP_PHASE"
    LOCK_AND_CLEAR = "LOCK_AND_CLEAR"
    NEXT_ROUND = "NEXT_ROUND"


@dataclass
class SessionState:
    session_id: str
    remaining_attempts: int
    current_prompt: Prompt | None = None
    prompt_start_monotonic: float = 0.0
    round_phase: RoundPhase = RoundPhase.NEXT_ROUND


class TrainingController:
    def __init__(
        self,
        session_service: SessionService,
        progress_service: ProgressService,
        tone_generator: ToneGenerator,
        audio_player: AudioPlayer,
        tone_seconds: float,
        timbre: str,
        default_octave: int = 4,
    ) -> None:
        self._session_service = session_service
        self._progress_service = progress_service
        self._tone_generator = tone_generator
        self._audio_player = audio_player
        self._tone_seconds = tone_seconds
        self._timbre = timbre
        self._default_octave = default_octave
        self._state: SessionState | None = None

    def start_session(self, attempts: int) -> SessionState:
        session_id = self._session_service.start_session()
        self._state = SessionState(session_id=session_id, remaining_attempts=attempts)
        return self._state

    def prepare_prompt(self) -> Prompt:
        if self._state is None:
            raise RuntimeError("Session has not started")
        if self._state.remaining_attempts <= 0:
            raise RuntimeError("No attempts remaining")
        if self._state.round_phase != RoundPhase.NEXT_ROUND:
            raise RuntimeError(f"Cannot prepare prompt during phase {self._state.round_phase}")
        prompt = self._session_service.next_prompt(octave=self._default_octave)
        self._state.current_prompt = prompt
        self._state.round_phase = RoundPhase.PROMPT_NOTE
        return prompt

    def play_current_prompt(self) -> None:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        if self._state.round_phase not in (RoundPhase.PROMPT_NOTE, RoundPhase.AWAIT_ANSWER):
            raise RuntimeError(f"Cannot play prompt during phase {self._state.round_phase}")
        self._play_current_prompt_audio()
        if self._state.round_phase == RoundPhase.PROMPT_NOTE:
            self._state.prompt_start_monotonic = time.monotonic()
            self._state.round_phase = RoundPhase.AWAIT_ANSWER

    def replay_current_prompt(self) -> None:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        if self._state.round_phase != RoundPhase.AWAIT_ANSWER:
            raise RuntimeError(f"Cannot replay prompt during phase {self._state.round_phase}")
        self._play_current_prompt_audio()

    def _play_current_prompt_audio(self) -> None:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        prompt = self._state.current_prompt
        tone_file = self._tone_generator.generate_note_file(
            prompt.target_note,
            prompt.octave,
            duration_seconds=self._tone_seconds,
        )
        try:
            self._audio_player.play(tone_file)
        finally:
            self._audio_player.cleanup(tone_file)

    def submit_answer(self, guessed_note: str) -> AttemptFeedback:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        if self._state.round_phase != RoundPhase.AWAIT_ANSWER:
            raise RuntimeError(f"Cannot submit answer during phase {self._state.round_phase}")
        prompt = self._state.current_prompt
        self._state.round_phase = RoundPhase.RESOLVE_ANSWER
        response_ms = int((time.monotonic() - self._state.prompt_start_monotonic) * 1000)
        feedback = self._session_service.record_attempt(
            session_id=self._state.session_id,
            target_note=prompt.target_note,
            guessed_note=guessed_note,
            octave=prompt.octave,
            response_ms=response_ms,
            timbre=self._timbre,
        )
        self._state.round_phase = RoundPhase.DROP_PHASE
        self._finish_drop_phase()
        self._state.remaining_attempts -= 1
        self._state.current_prompt = None
        return feedback

    def finish_session(self) -> SessionSummary:
        if self._state is None:
            raise RuntimeError("Session has not started")
        summary = self._session_service.finish_session(self._state.session_id)
        return summary

    def recent_accuracy_by_note(self, limit: int = 500) -> dict[str, float]:
        attempts = self._session_service.list_recent_attempts(limit=limit)
        return self._progress_service.accuracy_by_note(attempts)

    def _finish_drop_phase(self) -> None:
        if self._state is None:
            raise RuntimeError("Session has not started")
        if self._state.round_phase != RoundPhase.DROP_PHASE:
            raise RuntimeError(f"Cannot finish drop phase during {self._state.round_phase}")
        self._state.round_phase = RoundPhase.LOCK_AND_CLEAR
        self._state.round_phase = RoundPhase.NEXT_ROUND
