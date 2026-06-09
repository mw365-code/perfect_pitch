import unittest
from pathlib import Path

from app.round_models import RoundPhase
from app.training_controller import TrainingController
from domain.models import AttemptFeedback, Prompt, SessionSummary


class _FakeSessionService:
    def __init__(self) -> None:
        self.next_prompt_calls = 0
        self.recorded_guesses: list[str] = []
        self.last_record_payload: dict[str, object] | None = None
        self.record_attempt_calls = 0

    def start_session(self) -> str:
        return "s-1"

    def next_prompt(self, octave: int = 4) -> Prompt:
        self.next_prompt_calls += 1
        return Prompt(target_note="C", octave=octave)

    def record_attempt(
        self,
        session_id: str,
        target_note: str,
        guessed_note: str,
        octave: int,
        response_ms: int,
        timbre: str,
        selected_note: str | None = None,
        selected_family: str | None = None,
        generated_piece: str | None = None,
        placement_outcome: str | None = None,
        board_height_after: int | None = None,
        lines_cleared_after: int | None = None,
    ) -> AttemptFeedback:
        self.record_attempt_calls += 1
        self.recorded_guesses.append(guessed_note)
        self.last_record_payload = {
            "selected_note": selected_note,
            "selected_family": selected_family,
            "generated_piece": generated_piece,
            "placement_outcome": placement_outcome,
            "board_height_after": board_height_after,
            "lines_cleared_after": lines_cleared_after,
        }
        return AttemptFeedback(
            correct=guessed_note == target_note,
            target_note=target_note,
            guessed_note=guessed_note,
            response_ms=response_ms,
        )

    def finish_session(self, session_id: str) -> SessionSummary:
        return SessionSummary(
            session_id=session_id,
            total_attempts=1,
            correct_attempts=1,
            accuracy=1.0,
        )

    def list_recent_attempts(self, limit: int = 500) -> list[object]:
        return []

    def list_attempts_for_session(self, session_id: str) -> list[object]:
        return []

    def finalize_session_metrics(
        self,
        session_id: str,
        mode: str,
        total_lines: int,
        max_streak: int,
        survival_seconds: int,
    ) -> SessionSummary:
        return SessionSummary(
            session_id=session_id,
            total_attempts=self.record_attempt_calls,
            correct_attempts=self.record_attempt_calls,
            accuracy=1.0 if self.record_attempt_calls else 0.0,
            mode=mode,
            total_lines=total_lines,
            max_streak=max_streak,
            survival_seconds=survival_seconds,
        )


class _FakeProgressService:
    def accuracy_by_note(self, attempts: list[object]) -> dict[str, float]:
        return {"C": 1.0}

    def confusion_matrix(self, attempts: list[object]) -> dict[tuple[str, str], int]:
        return {}


class _FakeToneGenerator:
    def generate_note_file(
        self,
        note: str,
        octave: int,
        duration_seconds: float,
        a4_hz: float = 440.0,
    ) -> Path:
        return Path("/tmp/fake_note.wav")


class _FakeAudioPlayer:
    def __init__(self) -> None:
        self.play_count = 0
        self.cleanup_count = 0

    def play(self, _file_path: Path) -> None:
        self.play_count += 1

    def cleanup(self, _file_path: Path) -> None:
        self.cleanup_count += 1


class TrainingControllerStateMachineTests(unittest.TestCase):
    def test_round_phase_transitions_follow_stage2_order(self) -> None:
        session_service = _FakeSessionService()
        audio_player = _FakeAudioPlayer()
        controller = TrainingController(
            session_service=session_service,
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=audio_player,
            tone_seconds=0.1,
            timbre="sine",
        )
        state = controller.start_session(attempts=1)
        self.assertEqual(state.round_phase, RoundPhase.NEXT_ROUND)

        controller.prepare_prompt()
        self.assertEqual(state.round_phase, RoundPhase.PROMPT_NOTE)

        controller.play_current_prompt()
        self.assertEqual(state.round_phase, RoundPhase.AWAIT_ANSWER)
        self.assertEqual(audio_player.play_count, 1)

        controller.submit_answer("C")
        self.assertEqual(state.round_phase, RoundPhase.NEXT_ROUND)
        self.assertEqual(state.remaining_attempts, 0)
        self.assertIsNone(state.current_prompt)

    def test_replay_is_allowed_only_during_await_answer(self) -> None:
        audio_player = _FakeAudioPlayer()
        controller = TrainingController(
            session_service=_FakeSessionService(),
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=audio_player,
            tone_seconds=0.1,
            timbre="sine",
        )
        controller.start_session(attempts=2)
        controller.prepare_prompt()

        with self.assertRaises(RuntimeError):
            controller.replay_current_prompt()

        controller.play_current_prompt()
        controller.replay_current_prompt()
        self.assertEqual(audio_player.play_count, 2)

    def test_correct_answer_records_stage3_auto_drop_metadata(self) -> None:
        session_service = _FakeSessionService()
        controller = TrainingController(
            session_service=session_service,
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=_FakeAudioPlayer(),
            tone_seconds=0.1,
            timbre="sine",
        )
        controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()
        feedback = controller.submit_answer("C")
        self.assertTrue(feedback.correct)
        self.assertIsNotNone(session_service.last_record_payload)
        assert session_service.last_record_payload is not None
        self.assertEqual(session_service.last_record_payload["selected_family"], "I")
        self.assertEqual(session_service.last_record_payload["generated_piece"], "I")
        self.assertEqual(session_service.last_record_payload["placement_outcome"], "auto_drop_applied")

    def test_incorrect_answer_starts_manual_drop_and_locks_on_hard_drop(self) -> None:
        session_service = _FakeSessionService()
        controller = TrainingController(
            session_service=session_service,
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=_FakeAudioPlayer(),
            tone_seconds=0.1,
            timbre="sine",
        )
        state = controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()

        feedback = controller.submit_answer("D")
        self.assertFalse(feedback.correct)
        self.assertEqual(state.round_phase, RoundPhase.DROP_PHASE)
        self.assertTrue(controller.has_active_manual_piece())
        self.assertEqual(state.remaining_attempts, 1)
        self.assertEqual(session_service.record_attempt_calls, 0)

        controller.hard_drop_manual()
        self.assertFalse(controller.has_active_manual_piece())
        self.assertEqual(state.round_phase, RoundPhase.NEXT_ROUND)
        self.assertEqual(state.remaining_attempts, 0)
        self.assertEqual(session_service.record_attempt_calls, 1)
        self.assertIsNotNone(session_service.last_record_payload)
        assert session_service.last_record_payload is not None
        self.assertEqual(session_service.last_record_payload["placement_outcome"], "incorrect_manual_locked")
        self.assertEqual(session_service.last_record_payload["selected_family"], "O")

    def test_stage5_scores_and_report_are_exposed(self) -> None:
        session_service = _FakeSessionService()
        controller = TrainingController(
            session_service=session_service,
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=_FakeAudioPlayer(),
            tone_seconds=0.1,
            timbre="sine",
        )
        controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()
        controller.submit_answer("C")

        pitch, board, total = controller.game_scores()
        self.assertGreaterEqual(pitch, 100)
        self.assertGreaterEqual(total, pitch + board)

        summary = controller.finish_session()
        report = controller.build_game_report()
        self.assertEqual(summary.mode, "game")
        self.assertEqual(summary.total_lines, report.total_lines)
        self.assertEqual(total, report.total_score)


if __name__ == "__main__":
    unittest.main()
