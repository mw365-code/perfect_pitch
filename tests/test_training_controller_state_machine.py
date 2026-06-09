import unittest
from pathlib import Path

from app.training_controller import RoundPhase, TrainingController
from domain.models import AttemptFeedback, Prompt, SessionSummary


class _FakeSessionService:
    def __init__(self) -> None:
        self.next_prompt_calls = 0
        self.recorded_guesses: list[str] = []

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
    ) -> AttemptFeedback:
        self.recorded_guesses.append(guessed_note)
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


class _FakeProgressService:
    def accuracy_by_note(self, attempts: list[object]) -> dict[str, float]:
        return {"C": 1.0}


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


if __name__ == "__main__":
    unittest.main()
