import random
import time

from app.round_models import AutoDropResult, PendingAttempt, SessionState
from domain.game_constants import visual_mapping_for_note
from domain.models import Prompt
from domain.session_service import SessionService
from domain.tetris_rules import (
    AutoPlacementPlan,
    SPAWN_ROW,
    aggregate_column_heights,
    apply_auto_placement,
    can_spawn_any,
    clear_full_lines,
    collides,
    default_spawn,
    drop_until_collision,
    is_game_over,
    lock_piece,
    move,
    plan_best_auto_placement,
    rotate,
)


class GameplayEngine:
    def __init__(
        self,
        session_service: SessionService,
        timbre: str,
        auto_drop_step_seconds: float,
        rng: random.Random,
    ) -> None:
        self._session_service = session_service
        self._timbre = timbre
        self._auto_drop_step_seconds = auto_drop_step_seconds
        self._rng = rng
        self._piece_bag: list[str] = []

    def run_correct_answer_auto_drop(self, state: SessionState, note: str) -> AutoDropResult:
        if state.board is None:
            raise RuntimeError("Session has not started")
        mapping = visual_mapping_for_note(note)
        plan = plan_best_auto_placement(state.board, mapping.tetromino_family)
        state.last_auto_plan = plan
        if plan is None:
            return AutoDropResult(
                placement_outcome="auto_drop_no_valid_target",
                selected_family=mapping.tetromino_family,
                generated_piece=mapping.tetromino_family,
                board_height_after=aggregate_column_heights(state.board),
                lines_cleared_after=state.total_lines_cleared,
            )
        if self._auto_drop_step_seconds > 0.0:
            self._sleep_for_auto_drop(plan)
        updated_board, cleared_lines = apply_auto_placement(state.board, plan)
        state.board = updated_board
        state.total_lines_cleared += cleared_lines
        self.apply_board_scoring(state, cleared_lines)
        return AutoDropResult(
            placement_outcome="auto_drop_applied",
            selected_family=mapping.tetromino_family,
            generated_piece=mapping.tetromino_family,
            board_height_after=aggregate_column_heights(state.board),
            lines_cleared_after=state.total_lines_cleared,
        )

    def begin_incorrect_drop(
        self,
        state: SessionState,
        prompt: Prompt,
        normalized_guess: str,
        response_ms: int,
    ) -> None:
        if state.board is None:
            raise RuntimeError("Session has not started")
        generated_piece = self._next_piece_from_bag()
        state.pending_attempt = PendingAttempt(
            target_note=prompt.target_note,
            guessed_note=normalized_guess,
            octave=prompt.octave,
            response_ms=max(response_ms, 0),
            generated_piece=generated_piece,
        )
        state.active_piece = default_spawn(generated_piece)
        if is_game_over(state.board, generated_piece):
            self.lock_manual_piece(state, spawn_blocked=True)

    def has_active_manual_piece(self, state: SessionState | None) -> bool:
        return state is not None and state.active_piece is not None

    def move_manual_left(self, state: SessionState | None) -> bool:
        return self._try_move_manual_piece(state, dx=-1, dy=0)

    def move_manual_right(self, state: SessionState | None) -> bool:
        return self._try_move_manual_piece(state, dx=1, dy=0)

    def rotate_manual(self, state: SessionState | None, clockwise: bool = True) -> bool:
        if state is None or state.board is None or state.active_piece is None:
            return False
        candidate = rotate(state.active_piece, clockwise=clockwise)
        if collides(state.board, candidate):
            return False
        state.active_piece = candidate
        return True

    def soft_drop_manual(self, state: SessionState | None) -> bool:
        if state is None or state.board is None or state.active_piece is None:
            return False
        candidate = move(state.active_piece, dx=0, dy=1)
        if collides(state.board, candidate):
            self.lock_manual_piece(state)
            return True
        state.active_piece = candidate
        return False

    def hard_drop_manual(self, state: SessionState | None) -> None:
        if state is None or state.board is None or state.active_piece is None:
            return
        resting = drop_until_collision(state.board, state.active_piece)
        state.active_piece = resting
        self.lock_manual_piece(state)

    def active_piece_snapshot(self, state: SessionState | None) -> tuple[str, int, int, int] | None:
        if state is None or state.active_piece is None:
            return None
        piece = state.active_piece
        return piece.kind, piece.x, piece.y, piece.rotation

    def lock_manual_piece(self, state: SessionState | None, spawn_blocked: bool = False) -> None:
        if state is None or state.board is None or state.pending_attempt is None:
            raise RuntimeError("No manual drop to lock")
        pending = state.pending_attempt
        if not spawn_blocked:
            if state.active_piece is None:
                raise RuntimeError("No active piece to lock")
            locked = lock_piece(state.board, state.active_piece)
            state.board, lines = clear_full_lines(locked)
            state.total_lines_cleared += lines
            self.apply_board_scoring(state, lines)
            outcome = "incorrect_manual_locked"
        else:
            outcome = "incorrect_spawn_blocked"
        self._session_service.record_attempt(
            session_id=state.session_id,
            target_note=pending.target_note,
            guessed_note=pending.guessed_note,
            octave=pending.octave,
            response_ms=pending.response_ms,
            timbre=self._timbre,
            selected_note=pending.guessed_note,
            selected_family=visual_mapping_for_note(pending.guessed_note).tetromino_family,
            generated_piece=pending.generated_piece,
            placement_outcome=outcome,
            board_height_after=aggregate_column_heights(state.board),
            lines_cleared_after=state.total_lines_cleared,
        )
        state.active_piece = None
        state.pending_attempt = None
        self.check_for_game_over(state)

    @staticmethod
    def check_for_game_over(state: SessionState | None) -> None:
        if state is None or state.board is None:
            return
        state.game_over = not can_spawn_any(state.board, ("I", "O", "T", "S", "Z", "J", "L"))
        if state.game_over:
            state.remaining_attempts = 0

    @staticmethod
    def apply_pitch_scoring(state: SessionState | None, correct: bool, response_ms: int) -> None:
        if state is None:
            return
        if not correct:
            state.current_streak = 0
            return
        points = 100
        if response_ms <= 2000:
            points += 50
        state.current_streak += 1
        if state.current_streak % 5 == 0:
            points += 100
        if state.current_streak > state.max_streak:
            state.max_streak = state.current_streak
        state.pitch_score += points

    @staticmethod
    def apply_board_scoring(state: SessionState | None, lines_cleared: int) -> None:
        if state is None or lines_cleared <= 0:
            return
        state.board_score += 100 if lines_cleared == 1 else 250

    def _next_piece_from_bag(self) -> str:
        if not self._piece_bag:
            self._piece_bag = ["I", "O", "T", "S", "Z", "J", "L"]
            self._rng.shuffle(self._piece_bag)
        return self._piece_bag.pop()

    def _sleep_for_auto_drop(self, plan: AutoPlacementPlan) -> None:
        drop_distance = max(0, plan.piece.y - SPAWN_ROW)
        for _ in range(drop_distance):
            time.sleep(self._auto_drop_step_seconds)

    @staticmethod
    def _try_move_manual_piece(state: SessionState | None, dx: int, dy: int) -> bool:
        if state is None or state.board is None or state.active_piece is None:
            return False
        candidate = move(state.active_piece, dx=dx, dy=dy)
        if collides(state.board, candidate):
            return False
        state.active_piece = candidate
        return True
