from dataclasses import dataclass
from enum import Enum

from domain.models import Prompt
from domain.tetris_rules import AutoPlacementPlan, FallingPiece


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
    board: list[list[int]] | None = None
    total_lines_cleared: int = 0
    pitch_score: int = 0
    board_score: int = 0
    current_streak: int = 0
    max_streak: int = 0
    started_monotonic: float = 0.0
    game_over: bool = False
    last_auto_plan: AutoPlacementPlan | None = None
    active_piece: FallingPiece | None = None
    pending_attempt: "PendingAttempt | None" = None
    recent_prompt_families: list[str] | None = None


@dataclass(frozen=True)
class AutoDropResult:
    placement_outcome: str
    selected_family: str
    generated_piece: str
    board_height_after: int
    lines_cleared_after: int


@dataclass(frozen=True)
class PendingAttempt:
    target_note: str
    guessed_note: str
    octave: int
    response_ms: int
    generated_piece: str
    selected_family: str
    placement_outcome: str
    controllable: bool
    display_note: str | None = None
    auto_plan: AutoPlacementPlan | None = None


@dataclass(frozen=True)
class GameSessionReport:
    accuracy_by_note: dict[str, float]
    confusion_pairs: dict[tuple[str, str], int]
    total_lines: int
    pitch_score: int
    board_score: int
    total_score: int
    survival_seconds: int
