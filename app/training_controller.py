import random
import time

from app.gameplay_engine import GameplayEngine
from app.round_models import GameSessionReport, RoundPhase, SessionState
from domain.note_engine import normalize_note_name
from domain.models import AttemptFeedback, Prompt, SessionSummary
from domain.progress_service import ProgressService
from domain.session_service import SessionService
from domain.tetris_rules import create_empty_board
from infra.audio.player import AudioPlayer
from infra.audio.tone_generator import ToneGenerator


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
        auto_drop_step_seconds: float = 0.0,
        rng: random.Random | None = None,
    ) -> None:
        self._session_service = session_service
        self._progress_service = progress_service
        self._tone_generator = tone_generator
        self._audio_player = audio_player
        self._tone_seconds = tone_seconds
        self._timbre = timbre
        self._default_octave = default_octave
        self._rng = rng or random.Random()
        self._state: SessionState | None = None
        self._gameplay = GameplayEngine(
            session_service=session_service,
            timbre=timbre,
            auto_drop_step_seconds=max(0.0, auto_drop_step_seconds),
            rng=self._rng,
        )

    def start_session(self, attempts: int) -> SessionState:
        session_id = self._session_service.start_session()
        self._state = SessionState(
            session_id=session_id,
            remaining_attempts=attempts,
            board=create_empty_board(),
            started_monotonic=time.monotonic(),
        )
        return self._state

    def prepare_prompt(self) -> Prompt:
        if self._state is None:
            raise RuntimeError("Session has not started")
        if self._state.game_over:
            raise RuntimeError("Game is over")
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
        if self._state.round_phase == RoundPhase.PROMPT_NOTE:
            self._state.prompt_start_monotonic = time.monotonic()
            self._state.round_phase = RoundPhase.AWAIT_ANSWER

    def replay_current_prompt(self) -> None:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        if self._state.round_phase != RoundPhase.AWAIT_ANSWER:
            raise RuntimeError(f"Cannot replay prompt during phase {self._state.round_phase}")
        self.play_current_prompt()

    def submit_answer(self, guessed_note: str) -> AttemptFeedback:
        if self._state is None or self._state.current_prompt is None:
            raise RuntimeError("Prompt has not been prepared")
        if self._state.round_phase != RoundPhase.AWAIT_ANSWER:
            raise RuntimeError(f"Cannot submit answer during phase {self._state.round_phase}")
        prompt = self._state.current_prompt
        self._state.round_phase = RoundPhase.RESOLVE_ANSWER
        response_ms = int((time.monotonic() - self._state.prompt_start_monotonic) * 1000)
        normalized_guess = normalize_note_name(guessed_note)
        correct = normalized_guess == prompt.target_note
        feedback = AttemptFeedback(
            correct=correct,
            target_note=prompt.target_note,
            guessed_note=normalized_guess,
            response_ms=max(response_ms, 0),
        )
        if correct:
            self._state.round_phase = RoundPhase.DROP_PHASE
            auto_result = self._gameplay.run_correct_answer_auto_drop(self._state, prompt.target_note)
            self._gameplay.apply_pitch_scoring(self._state, correct=True, response_ms=response_ms)
            self._session_service.record_attempt(
                session_id=self._state.session_id,
                target_note=prompt.target_note,
                guessed_note=normalized_guess,
                octave=prompt.octave,
                response_ms=response_ms,
                timbre=self._timbre,
                selected_note=normalized_guess,
                selected_family=auto_result.selected_family,
                generated_piece=auto_result.generated_piece,
                placement_outcome=auto_result.placement_outcome,
                board_height_after=auto_result.board_height_after,
                lines_cleared_after=auto_result.lines_cleared_after,
            )
            self._finish_drop_phase()
            self._decrement_round_budget()
            self._state.current_prompt = None
            return feedback

        self._state.round_phase = RoundPhase.DROP_PHASE
        self._gameplay.apply_pitch_scoring(self._state, correct=False, response_ms=response_ms)
        self._gameplay.begin_incorrect_drop(self._state, prompt, normalized_guess, response_ms)
        return feedback

    def has_active_manual_piece(self) -> bool:
        return self._gameplay.has_active_manual_piece(self._state)

    def move_manual_left(self) -> bool:
        return self._gameplay.move_manual_left(self._state)

    def move_manual_right(self) -> bool:
        return self._gameplay.move_manual_right(self._state)

    def rotate_manual(self, clockwise: bool = True) -> bool:
        return self._gameplay.rotate_manual(self._state, clockwise=clockwise)

    def soft_drop_manual(self) -> bool:
        locked = self._gameplay.soft_drop_manual(self._state)
        if locked:
            self._finish_drop_phase()
            self._decrement_round_budget()
            if self._state is not None:
                self._state.current_prompt = None
        return locked

    def hard_drop_manual(self) -> None:
        self._gameplay.hard_drop_manual(self._state)
        if self._state is not None and self._state.pending_attempt is None:
            self._finish_drop_phase()
            self._decrement_round_budget()
            self._state.current_prompt = None

    def active_piece_snapshot(self) -> tuple[str, int, int, int] | None:
        return self._gameplay.active_piece_snapshot(self._state)

    def finish_session(self) -> SessionSummary:
        if self._state is None:
            raise RuntimeError("Session has not started")
        return self._session_service.finalize_session_metrics(
            session_id=self._state.session_id,
            mode="game",
            total_lines=self._state.total_lines_cleared,
            max_streak=self._state.max_streak,
            survival_seconds=self.survival_seconds(),
        )

    def recent_accuracy_by_note(self, limit: int = 500) -> dict[str, float]:
        attempts = self._session_service.list_recent_attempts(limit=limit)
        return self._progress_service.accuracy_by_note(attempts)

    def game_scores(self) -> tuple[int, int, int]:
        if self._state is None:
            return 0, 0, 0
        total = self._state.pitch_score + self._state.board_score
        return self._state.pitch_score, self._state.board_score, total

    def is_game_over(self) -> bool:
        return self._state.game_over if self._state is not None else False

    def survival_seconds(self) -> int:
        if self._state is None or self._state.started_monotonic <= 0:
            return 0
        return max(0, int(time.monotonic() - self._state.started_monotonic))

    def build_game_report(self) -> GameSessionReport:
        if self._state is None:
            raise RuntimeError("Session has not started")
        attempts = self._session_service.list_attempts_for_session(self._state.session_id)
        pitch_score, board_score, total_score = self.game_scores()
        return GameSessionReport(
            accuracy_by_note=self._progress_service.accuracy_by_note(attempts),
            confusion_pairs=self._progress_service.confusion_matrix(attempts),
            total_lines=self._state.total_lines_cleared,
            pitch_score=pitch_score,
            board_score=board_score,
            total_score=total_score,
            survival_seconds=self.survival_seconds(),
        )

    def _finish_drop_phase(self) -> None:
        if self._state is None:
            raise RuntimeError("Session has not started")
        if self._state.round_phase != RoundPhase.DROP_PHASE:
            raise RuntimeError(f"Cannot finish drop phase during {self._state.round_phase}")
        self._state.round_phase = RoundPhase.LOCK_AND_CLEAR
        self._state.round_phase = RoundPhase.NEXT_ROUND
        self._gameplay.check_for_game_over(self._state)

    def _decrement_round_budget(self) -> None:
        if self._state is None or self._state.game_over:
            return
        self._state.remaining_attempts -= 1
