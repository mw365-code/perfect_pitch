import time

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
        print("Game mode: endless until the board is full.")
        while not self._controller.is_game_over():
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
            if self._controller.has_active_manual_piece():
                if self._controller.can_control_active_piece():
                    self._run_manual_drop_controls()
                else:
                    self._run_auto_drop()
            pitch_score, board_score, total_score = self._controller.game_scores()
            print(f"Scores: pitch={pitch_score}, board={board_score}, total={total_score}")
        summary = self._controller.finish_session()
        print(
            f"Session complete: {summary.correct_attempts}/{summary.total_attempts} "
            f"({summary.accuracy:.1%})"
        )
        report = self._controller.build_game_report()
        print(
            f"Lines={report.total_lines}, Survival={report.survival_seconds}s, "
            f"Pitch={report.pitch_score}, Board={report.board_score}, Total={report.total_score}"
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

    def _run_manual_drop_controls(self) -> None:
        print("Manual drop controls: a=left, d=right, w=rotate, s=soft drop, space=hard drop")
        while self._controller.has_active_manual_piece():
            snapshot = self._controller.active_piece_snapshot()
            if snapshot is not None:
                kind, x, y, rotation = snapshot
                print(f"Piece {kind} at x={x}, y={y}, rot={rotation}")
            command = input("Move: ").strip().lower()
            if command == "a":
                self._controller.move_manual_left()
                continue
            if command == "d":
                self._controller.move_manual_right()
                continue
            if command == "w":
                self._controller.rotate_manual()
                continue
            if command == "s":
                self._controller.soft_drop_manual()
                continue
            if command in (" ", "h", ""):
                self._controller.hard_drop_manual()
                continue
            print("Use a/d/w/s or space (or enter) for hard drop.")

    def _run_auto_drop(self) -> None:
        while self._controller.has_active_manual_piece():
            self._controller.soft_drop_manual()
            time.sleep(0.05)
