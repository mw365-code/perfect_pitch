import tkinter as tk
from tkinter import messagebox

from app.training_controller import TrainingController
from domain.note_engine import NOTES


class TkApp:
    def __init__(self, controller: TrainingController, default_attempts: int) -> None:
        self._controller = controller
        self._default_attempts = default_attempts
        self._state = None
        self._root = tk.Tk()
        self._root.title("Perfect Pitch Trainer")
        self._root.geometry("520x360")
        self._root.bind("r", self._replay_prompt_event)
        self._root.bind("R", self._replay_prompt_event)
        self._status_var = tk.StringVar(value="Press Start Session")
        self._remaining_var = tk.StringVar(value="")
        self._feedback_var = tk.StringVar(value="")

        self._build_ui()

    def run(self) -> None:
        self._root.mainloop()

    def _build_ui(self) -> None:
        top = tk.Frame(self._root, padx=14, pady=14)
        top.pack(fill=tk.BOTH, expand=True)

        controls = tk.Frame(top)
        controls.pack(anchor=tk.W)
        tk.Button(controls, text="Start Session", command=self._start_session).pack(side=tk.LEFT)
        tk.Button(controls, text="Replay Tone (R)", command=self._replay_prompt).pack(
            side=tk.LEFT, padx=8
        )
        tk.Label(top, textvariable=self._status_var, pady=8).pack(anchor=tk.W)
        tk.Label(top, textvariable=self._remaining_var).pack(anchor=tk.W)
        tk.Label(top, textvariable=self._feedback_var, fg="blue").pack(anchor=tk.W, pady=8)

        grid = tk.Frame(top)
        grid.pack(fill=tk.X, pady=8)
        for idx, note in enumerate(NOTES):
            button = tk.Button(
                grid,
                text=note,
                width=6,
                command=lambda n=note: self._submit_guess(n),
            )
            button.grid(row=idx // 4, column=idx % 4, padx=4, pady=4, sticky="ew")

    def _start_session(self) -> None:
        self._state = self._controller.start_session(self._default_attempts)
        self._feedback_var.set("")
        self._next_prompt()

    def _next_prompt(self) -> None:
        if self._state is None:
            return
        if self._state.remaining_attempts <= 0 or self._controller.is_game_over():
            summary = self._controller.finish_session()
            report = self._controller.build_game_report()
            self._status_var.set(
                f"Session complete: {summary.accuracy:.1%} | total score {report.total_score}"
            )
            self._remaining_var.set("")
            return
        self._status_var.set("Listen and choose the note")
        self._remaining_var.set(f"Remaining attempts: {self._state.remaining_attempts}")
        self._controller.prepare_prompt()
        self._controller.play_current_prompt()

    def _submit_guess(self, note: str) -> None:
        if self._state is None:
            messagebox.showinfo("No session", "Start a session first.")
            return
        feedback = self._controller.submit_answer(note)
        if feedback.correct:
            self._feedback_var.set(f"Correct: {feedback.target_note}")
        else:
            self._feedback_var.set(
                f"Wrong: target {feedback.target_note}, guessed {feedback.guessed_note}"
            )
            while self._controller.has_active_manual_piece():
                self._controller.hard_drop_manual()
        self._next_prompt()

    def _replay_prompt_event(self, _event: tk.Event) -> None:
        self._replay_prompt()

    def _replay_prompt(self) -> None:
        if self._state is None:
            return
        try:
            self._controller.replay_current_prompt()
        except RuntimeError:
            return
