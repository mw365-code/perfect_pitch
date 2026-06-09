from app.training_controller import TrainingController
from domain.note_engine import NOTES, normalize_note_name


class CliApp:
    def __init__(self, controller: TrainingController, default_attempts: int) -> None:
        self._controller = controller
        self._default_attempts = default_attempts

    def run(self) -> None:
        print("Perfect Pitch Trainer (CLI MVP)")
        print("Type note names like C, C#, D, D#, E, F, F#, G, G#, A, A#, B")
        state = self._controller.start_session(self._default_attempts)
        print(f"Session started: {state.session_id}")
        while state.remaining_attempts > 0:
            self._controller.prepare_prompt()
            self._controller.play_current_prompt()
            guess = self._read_guess()
            while guess == "REPLAY":
                self._controller.replay_current_prompt()
                guess = self._read_guess()
            feedback = self._controller.submit_answer(guess)
            status = "Correct" if feedback.correct else "Wrong"
            print(
                f"{status}: target={feedback.target_note}, "
                f"guess={feedback.guessed_note}, response={feedback.response_ms}ms"
            )
            print(f"Remaining: {state.remaining_attempts}")
        summary = self._controller.finish_session()
        print(
            f"Session complete: {summary.correct_attempts}/{summary.total_attempts} "
            f"({summary.accuracy:.1%})"
        )
        self._print_progress_snapshot()

    def _read_guess(self) -> str:
        while True:
            user_input = input("Your guess (or R to replay): ").strip()
            if user_input.upper() == "R":
                return "REPLAY"
            try:
                return normalize_note_name(user_input)
            except ValueError:
                print("Invalid note. Use one of: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B.")

    def _print_progress_snapshot(self) -> None:
        accuracy = self._controller.recent_accuracy_by_note(limit=500)
        if not accuracy:
            return
        print("Recent per-note accuracy:")
        for note in NOTES:
            if note in accuracy:
                print(f"  {note:<2} {accuracy[note]:.1%}")
