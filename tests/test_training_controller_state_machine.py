import random
import unittest
from pathlib import Path

from app.round_models import RoundPhase
from app.training_controller import TrainingController
from domain.game_constants import NOTE_TO_TETROMINO
from domain.models import AttemptFeedback, Prompt, SessionSummary
from domain.tetris_rules import NOTE_TO_VALUE
class _FakeSessionService:
    def __init__(self) -> None:
        self.next_prompt_calls = 0
        self.recorded_guesses: list[str] = []
        self.last_record_payload: dict[str, object] | None = None
        self.record_attempt_calls = 0
        self.prompt_note = "C"
        self.forced_note: str | None = None
        self.use_forced_note = False

    def start_session(self) -> str:
        return "s-1"

    def next_prompt(self, octave: int = 4, forced_note: str | None = None) -> Prompt:
        self.next_prompt_calls += 1
        self.forced_note = forced_note
        target_note = forced_note if forced_note is not None and self.use_forced_note else self.prompt_note
        return Prompt(target_note=target_note, octave=octave)
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
    @staticmethod
    def _make_controller(
        session_service: _FakeSessionService | None = None,
        audio_player: _FakeAudioPlayer | None = None,
        rng: random.Random | None = None,
    ) -> TrainingController:
        return TrainingController(
            session_service=session_service or _FakeSessionService(),
            progress_service=_FakeProgressService(),
            tone_generator=_FakeToneGenerator(),
            audio_player=audio_player or _FakeAudioPlayer(),
            tone_seconds=0.1,
            timbre="sine",
            rng=rng,
        )

    @staticmethod
    def _load_rows(state: object, rows: tuple[str, ...]) -> None:
        for offset, row in enumerate(rows, start=len(rows)):
            state.board[-offset] = [1 if cell == "#" else 0 for cell in row]

    def test_round_phase_transitions_follow_stage2_order(self) -> None:
        session_service = _FakeSessionService()
        audio_player = _FakeAudioPlayer()
        controller = self._make_controller(session_service=session_service, audio_player=audio_player)
        state = controller.start_session(attempts=1)
        self.assertEqual(state.round_phase, RoundPhase.NEXT_ROUND)

        controller.prepare_prompt()
        self.assertEqual(state.round_phase, RoundPhase.PROMPT_NOTE)

        controller.play_current_prompt()
        self.assertEqual(state.round_phase, RoundPhase.AWAIT_ANSWER)
        self.assertEqual(audio_player.play_count, 1)

        controller.submit_answer("C")
        self.assertEqual(state.round_phase, RoundPhase.DROP_PHASE)
        self.assertTrue(controller.has_active_manual_piece())
        self.assertFalse(controller.can_control_active_piece())
        self.assertEqual(state.remaining_attempts, 1)

        controller.hard_drop_manual()
        self.assertEqual(state.round_phase, RoundPhase.NEXT_ROUND)
        self.assertIsNone(state.current_prompt)
        controller.prepare_prompt()
        self.assertEqual(state.round_phase, RoundPhase.PROMPT_NOTE)

    def test_replay_is_allowed_only_during_await_answer(self) -> None:
        audio_player = _FakeAudioPlayer()
        controller = self._make_controller(audio_player=audio_player)
        controller.start_session(attempts=2)
        controller.prepare_prompt()

        with self.assertRaises(RuntimeError):
            controller.replay_current_prompt()

        controller.play_current_prompt()
        controller.replay_current_prompt()
        self.assertEqual(audio_player.play_count, 2)

    def test_correct_answer_records_stage3_auto_drop_metadata(self) -> None:
        session_service = _FakeSessionService()
        controller = self._make_controller(session_service=session_service)
        controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()
        feedback = controller.submit_answer("C")
        self.assertTrue(feedback.correct)
        self.assertEqual(controller._state.round_phase, RoundPhase.DROP_PHASE)
        self.assertTrue(controller.has_active_manual_piece())
        self.assertEqual(session_service.record_attempt_calls, 0)

        controller.hard_drop_manual()
        self.assertIsNotNone(session_service.last_record_payload)
        assert session_service.last_record_payload is not None
        self.assertEqual(session_service.last_record_payload["selected_family"], "I")
        self.assertEqual(session_service.last_record_payload["generated_piece"], "I")
        self.assertEqual(session_service.last_record_payload["placement_outcome"], "auto_drop_applied")

    def test_correct_accidental_piece_keeps_light_note_value_on_board(self) -> None:
        session_service = _FakeSessionService()
        session_service.prompt_note = "C#"
        controller = self._make_controller(session_service=session_service)
        state = controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()
        feedback = controller.submit_answer("C#")
        self.assertTrue(feedback.correct)

        controller.hard_drop_manual()
        occupied_values = {cell for row in state.board for cell in row if cell}
        self.assertIn(NOTE_TO_VALUE["C#"], occupied_values)

    def test_incorrect_answer_starts_manual_drop_and_locks_on_hard_drop(self) -> None:
        session_service = _FakeSessionService()
        controller = self._make_controller(session_service=session_service)
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
        self.assertEqual(session_service.record_attempt_calls, 1)
        self.assertIsNotNone(session_service.last_record_payload)
        assert session_service.last_record_payload is not None
        self.assertEqual(session_service.last_record_payload["placement_outcome"], "incorrect_manual_locked")
        self.assertEqual(session_service.last_record_payload["selected_family"], "O")

    def test_prepare_prompt_randomizes_across_row_clearers(self) -> None:
        session_service = _FakeSessionService()
        session_service.use_forced_note = True
        controller = self._make_controller(session_service=session_service, rng=random.Random(3))
        state = controller.start_session(attempts=1)
        rows = ("#.##########", "#...#.###..#", "##..###..##.", "####.#..###.")
        self._load_rows(state, rows)
        prompt = controller.prepare_prompt()
        self.assertIn(prompt.target_note, ("C", "C#", "E", "F", "F#", "G", "G#", "A", "A#", "B"))
        self.assertIn(session_service.forced_note, ("C", "C#", "E", "F", "F#", "G", "G#", "A", "A#", "B"))

    def test_prepare_prompt_prefers_best_horizontal_fill_when_no_clear_exists(self) -> None:
        session_service = _FakeSessionService()
        session_service.use_forced_note = True
        controller = self._make_controller(session_service=session_service, rng=random.Random(5))
        state = controller.start_session(attempts=1)
        rows = ("..#.....##.#", "#...##...#.#", "#...##.....#", "....#..#....")
        self._load_rows(state, rows)
        prompt = controller.prepare_prompt()
        self.assertIn(prompt.target_note, ("E", "A", "A#", "B"))
        self.assertIn(session_service.forced_note, ("E", "A", "A#", "B"))

    def test_prepare_prompt_mixes_families_with_near_best_row_fill(self) -> None:
        session_service = _FakeSessionService()
        session_service.use_forced_note = True
        controller = self._make_controller(session_service=session_service, rng=random.Random(9))
        state = controller.start_session(attempts=1)
        rows = ("..#.....##.#", "#...##...#.#", "#...##.....#", "....#..#....")
        self._load_rows(state, rows)
        families: set[str] = set()
        streak = 0
        last_family = None
        for _ in range(8):
            prompt = controller.prepare_prompt()
            family = NOTE_TO_TETROMINO[prompt.target_note]
            families.add(family)
            streak = streak + 1 if family == last_family else 1
            last_family = family
            self.assertLessEqual(streak, 2)
            state.current_prompt = None
            state.round_phase = RoundPhase.NEXT_ROUND
        self.assertGreater(len(families), 1)

    def test_stage5_scores_and_report_are_exposed(self) -> None:
        session_service = _FakeSessionService()
        controller = self._make_controller(session_service=session_service)
        controller.start_session(attempts=1)
        controller.prepare_prompt()
        controller.play_current_prompt()
        controller.submit_answer("C")
        controller.hard_drop_manual()

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
