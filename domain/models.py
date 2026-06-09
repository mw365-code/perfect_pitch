from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    target_note: str
    octave: int


@dataclass(frozen=True)
class AttemptFeedback:
    correct: bool
    target_note: str
    guessed_note: str
    response_ms: int


@dataclass(frozen=True)
class NoteAttempt:
    session_id: str
    target_note: str
    guessed_note: str
    octave: int
    correct: bool
    response_ms: int
    timbre: str
    created_at: str
    selected_note: str | None = None
    selected_family: str | None = None
    generated_piece: str | None = None
    placement_outcome: str | None = None
    board_height_after: int | None = None
    lines_cleared_after: int | None = None

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "session_id": self.session_id,
            "target_note": self.target_note,
            "guessed_note": self.guessed_note,
            "octave": self.octave,
            "correct": self.correct,
            "response_ms": self.response_ms,
            "timbre": self.timbre,
            "created_at": self.created_at,
            "selected_note": self.selected_note,
            "selected_family": self.selected_family,
            "generated_piece": self.generated_piece,
            "placement_outcome": self.placement_outcome,
            "board_height_after": self.board_height_after,
            "lines_cleared_after": self.lines_cleared_after,
        }

    @classmethod
    def from_dict(cls, value: dict[str, str | int | bool | None]) -> "NoteAttempt":
        return cls(
            session_id=str(value["session_id"]),
            target_note=str(value["target_note"]),
            guessed_note=str(value["guessed_note"]),
            octave=int(value["octave"]),
            correct=bool(value["correct"]),
            response_ms=int(value["response_ms"]),
            timbre=str(value["timbre"]),
            created_at=str(value["created_at"]),
            selected_note=_to_optional_str(value.get("selected_note")),
            selected_family=_to_optional_str(value.get("selected_family")),
            generated_piece=_to_optional_str(value.get("generated_piece")),
            placement_outcome=_to_optional_str(value.get("placement_outcome")),
            board_height_after=_to_optional_int(value.get("board_height_after")),
            lines_cleared_after=_to_optional_int(value.get("lines_cleared_after")),
        )


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    total_attempts: int
    correct_attempts: int
    accuracy: float
    mode: str = "training"
    total_lines: int = 0
    max_streak: int = 0
    survival_seconds: int = 0

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "session_id": self.session_id,
            "total_attempts": self.total_attempts,
            "correct_attempts": self.correct_attempts,
            "accuracy": self.accuracy,
            "mode": self.mode,
            "total_lines": self.total_lines,
            "max_streak": self.max_streak,
            "survival_seconds": self.survival_seconds,
        }

    @classmethod
    def from_dict(cls, value: dict[str, str | int | float]) -> "SessionSummary":
        return cls(
            session_id=str(value["session_id"]),
            total_attempts=int(value["total_attempts"]),
            correct_attempts=int(value["correct_attempts"]),
            accuracy=float(value["accuracy"]),
            mode=str(value.get("mode", "training")),
            total_lines=int(value.get("total_lines", 0)),
            max_streak=int(value.get("max_streak", 0)),
            survival_seconds=int(value.get("survival_seconds", 0)),
        )


def _to_optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_optional_int(value: object | None) -> int | None:
    if value is None:
        return None
    return int(value)
