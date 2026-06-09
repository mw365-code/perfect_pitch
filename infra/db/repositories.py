import sqlite3

from domain.models import NoteAttempt, SessionSummary
from domain.ports import AttemptStore, SessionStore


class SqliteTrainingRepository(AttemptStore, SessionStore):
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def start_session(self, session_id: str, started_at: str) -> None:
        self._connection.execute(
            "INSERT INTO sessions(id, started_at, mode) VALUES(?, ?, ?)",
            (session_id, started_at, "training"),
        )
        self._connection.commit()

    def finish_session(self, summary: SessionSummary, ended_at: str) -> None:
        self._connection.execute(
            """
            UPDATE sessions
            SET ended_at = ?, total_attempts = ?, accuracy = ?, mode = ?, total_lines = ?, max_streak = ?, survival_seconds = ?
            WHERE id = ?
            """,
            (
                ended_at,
                summary.total_attempts,
                summary.accuracy,
                summary.mode,
                summary.total_lines,
                summary.max_streak,
                summary.survival_seconds,
                summary.session_id,
            ),
        )
        self._connection.commit()

    def add_attempt(self, attempt: NoteAttempt) -> None:
        self._connection.execute(
            """
            INSERT INTO attempts(
                session_id, target_note, guessed_note, octave, correct,
                response_ms, timbre, created_at, selected_note, selected_family,
                generated_piece, placement_outcome, board_height_after, lines_cleared_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.session_id,
                attempt.target_note,
                attempt.guessed_note,
                attempt.octave,
                1 if attempt.correct else 0,
                attempt.response_ms,
                attempt.timbre,
                attempt.created_at,
                attempt.selected_note,
                attempt.selected_family,
                attempt.generated_piece,
                attempt.placement_outcome,
                attempt.board_height_after,
                attempt.lines_cleared_after,
            ),
        )
        self._connection.commit()

    def list_recent_attempts(self, limit: int = 500) -> list[NoteAttempt]:
        rows = self._connection.execute(
            """
            SELECT session_id, target_note, guessed_note, octave, correct, response_ms, timbre, created_at,
                   selected_note, selected_family, generated_piece, placement_outcome, board_height_after, lines_cleared_after
            FROM attempts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._row_to_attempt(row) for row in rows]

    def list_attempts_for_session(self, session_id: str) -> list[NoteAttempt]:
        rows = self._connection.execute(
            """
            SELECT session_id, target_note, guessed_note, octave, correct, response_ms, timbre, created_at,
                   selected_note, selected_family, generated_piece, placement_outcome, board_height_after, lines_cleared_after
            FROM attempts
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
        return [self._row_to_attempt(row) for row in rows]

    @staticmethod
    def _row_to_attempt(row: sqlite3.Row) -> NoteAttempt:
        return NoteAttempt(
            session_id=row["session_id"],
            target_note=row["target_note"],
            guessed_note=row["guessed_note"],
            octave=row["octave"],
            correct=bool(row["correct"]),
            response_ms=row["response_ms"],
            timbre=row["timbre"],
            created_at=row["created_at"],
            selected_note=row["selected_note"],
            selected_family=row["selected_family"],
            generated_piece=row["generated_piece"],
            placement_outcome=row["placement_outcome"],
            board_height_after=row["board_height_after"],
            lines_cleared_after=row["lines_cleared_after"],
        )
