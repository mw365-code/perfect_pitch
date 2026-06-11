import time
import tkinter as tk
from tkinter import messagebox

from app.round_models import RoundPhase
from app.training_controller import TrainingController
from domain.game_constants import BASE_TETROMINO_COLORS, visual_mapping_for_note
from domain.tetris_rules import BOARD_HEIGHT, BOARD_WIDTH, VALUE_TO_NOTE, VALUE_TO_PIECE_KIND, piece_cells

ACCIDENTAL_KEYMAP: dict[str, str] = {"1": "C#", "2": "D#", "3": "F#", "4": "G#", "5": "A#"}
BOARD_BG = "#d9d9d9"
BOARD_GRID = "#aaaaaa"
class TkApp:
    def __init__(self, controller: TrainingController, default_attempts: int) -> None:
        self._controller = controller
        self._default_attempts = default_attempts
        self._state = None
        self._errors = 0
        self._cell = 28
        self._root = tk.Tk()
        self._root.title("Perfect Pitch Tetris")
        self._root.geometry("430x900")
        self._root.configure(bg="#0f1216")
        self._status_var = tk.StringVar(value="Press Start Session")
        self._feedback_var = tk.StringVar(value="")
        self._remaining_var = tk.StringVar(value="")
        self._score_var = tk.StringVar(value="Score 0")
        self._streak_var = tk.StringVar(value="Streak 0")
        self._lines_var = tk.StringVar(value="Lines 0")
        self._errors_var = tk.StringVar(value="Errors 0")
        self._survival_var = tk.StringVar(value="Time 0s")
        self._canvas: tk.Canvas | None = None
        self._gravity_seconds = 0.30
        self._last_gravity_tick = time.monotonic()
        self._post_lock_delay_ms = 2000
        self._next_prompt_after_lock_scheduled = False
        self._build_ui()
        self._bind_keys()
        self._tick()

    def run(self) -> None:
        self._root.mainloop()
    def _build_ui(self) -> None:
        bezel = tk.Frame(
            self._root,
            width=406,
            height=860,
            bg="#0b0d10",
            highlightthickness=1,
            highlightbackground="#2b3138",
        )
        bezel.pack(padx=14, pady=18)
        bezel.pack_propagate(False)
        root = tk.Frame(bezel, padx=10, pady=10, bg="#181c20", width=390, height=844)
        root.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        root.pack_propagate(False)
        top = tk.Frame(root, bg="#181c20")
        top.pack(fill=tk.X)
        tk.Button(top, text="Start", width=8, command=self._start_session).pack(side=tk.LEFT)
        tk.Button(top, text="Replay", width=8, command=self._replay_prompt).pack(side=tk.LEFT, padx=6)
        tk.Label(
            top,
            textvariable=self._status_var,
            fg="#d7dde5",
            bg="#181c20",
            anchor="w",
            justify="left",
            wraplength=190,
        ).pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        stats = tk.Frame(root, pady=8, bg="#181c20")
        stats.pack(fill=tk.X)
        for var in (self._remaining_var, self._score_var, self._lines_var):
            tk.Label(stats, textvariable=var, fg="#a9b3bf", bg="#181c20").pack(side=tk.LEFT, padx=6)
        stats2 = tk.Frame(root, pady=2, bg="#181c20")
        stats2.pack(fill=tk.X)
        for var in (self._streak_var, self._errors_var, self._survival_var):
            tk.Label(stats2, textvariable=var, fg="#a9b3bf", bg="#181c20").pack(side=tk.LEFT, padx=6)
        notes_grid = tk.Frame(root, bg="#181c20")
        notes_grid.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        panel = tk.Frame(root, bg="#181c20")
        panel.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            panel,
            textvariable=self._feedback_var,
            fg="#89c1ff",
            bg="#181c20",
            anchor="w",
            justify="left",
            wraplength=330,
        ).pack(anchor=tk.W, pady=(2, 8), fill=tk.X)
        self._canvas = tk.Canvas(
            panel,
            width=BOARD_WIDTH * self._cell + 2,
            height=BOARD_HEIGHT * self._cell + 2,
            bg=BOARD_BG,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(anchor=tk.N, pady=(0, 8))
        natural_row = ("C", "D", "E", "F", "G", "A", "B")
        accidental_positions = {0: "C#", 1: "D#", 3: "F#", 4: "G#", 5: "A#"}
        for col in range(7):
            notes_grid.grid_columnconfigure(col, weight=1, uniform="notes")
        for col, note in enumerate(natural_row):
            self._note_button(notes_grid, note).grid(row=0, column=col, padx=1, pady=1, sticky="ew")
        for col in range(7):
            note = accidental_positions.get(col)
            if note is None:
                tk.Label(notes_grid, text="", bg="#181c20").grid(row=1, column=col, padx=1, pady=1, sticky="ew")
            else:
                self._note_button(notes_grid, note).grid(row=1, column=col, padx=1, pady=1, sticky="ew")
    def _bind_keys(self) -> None:
        self._root.bind("r", self._replay_prompt_event)
        self._root.bind("R", self._replay_prompt_event)
        for key in ("c", "d", "e", "f", "g", "a", "b"):
            self._root.bind(key, self._natural_note_key)
            self._root.bind(key.upper(), self._natural_note_key)
        for key in ACCIDENTAL_KEYMAP:
            self._root.bind(key, self._accidental_note_key)
        self._root.bind("<Left>", self._manual_piece_key)
        self._root.bind("<Right>", self._manual_piece_key)
        self._root.bind("<Up>", self._manual_piece_key)
        self._root.bind("<Down>", self._manual_piece_key)
        self._root.bind("<space>", self._manual_piece_key)
    def _note_button(self, parent: tk.Widget, note: str) -> tk.Button:
        mapping = visual_mapping_for_note(note)
        return tk.Button(
            parent,
            text=note,
            width=2,
            height=1,
            bg=mapping.color_hex,
            activebackground=mapping.color_hex,
            relief=tk.FLAT,
            bd=0,
            padx=1,
            pady=1,
            font=("TkDefaultFont", 9),
            command=lambda n=note: self._submit_guess(n),
        )
    def _start_session(self) -> None:
        self._state = self._controller.start_session(self._default_attempts)
        self._errors = 0
        self._last_gravity_tick = time.monotonic()
        self._feedback_var.set("")
        self._next_prompt()
    def _next_prompt(self) -> None:
        if self._state is None:
            return
        if self._controller.is_game_over():
            summary = self._controller.finish_session()
            report = self._controller.build_game_report()
            self._status_var.set(f"Session complete: {summary.accuracy:.1%}")
            self._feedback_var.set(f"Total {report.total_score} | pitch {report.pitch_score} | board {report.board_score}")
            self._refresh_stats()
            self._draw_board()
            return
        self._status_var.set("Listen and identify the note")
        self._controller.prepare_prompt()
        self._controller.play_current_prompt()
        self._refresh_stats()
        self._draw_board()
    def _submit_guess(self, note: str) -> None:
        if self._state is None:
            messagebox.showinfo("No session", "Start a session first.")
            return
        if not self._can_answer_now():
            return
        feedback = self._controller.submit_answer(note)
        self._last_gravity_tick = time.monotonic()
        if feedback.correct:
            self._feedback_var.set(f"Correct: {feedback.target_note}")
            self._status_var.set("Correct piece dropping")
        else:
            self._errors += 1
            self._feedback_var.set(f"Wrong: target {feedback.target_note}, guessed {feedback.guessed_note}")
            self._status_var.set("Place the falling piece")
        if not self._controller.has_active_manual_piece():
            self._schedule_next_prompt_after_lock()
        self._refresh_stats()
        self._draw_board()
    def _manual_piece_key(self, event: tk.Event) -> None:
        if not self._controller.can_control_active_piece():
            return
        key = event.keysym
        if key == "Left":
            self._controller.move_manual_left()
        elif key == "Right":
            self._controller.move_manual_right()
        elif key == "Up":
            self._controller.rotate_manual(clockwise=True)
        elif key == "Down":
            self._controller.soft_drop_manual()
        elif key == "space":
            self._controller.hard_drop_manual()
        if not self._controller.has_active_manual_piece():
            self._schedule_next_prompt_after_lock()
        self._draw_board()
    def _natural_note_key(self, event: tk.Event) -> None:
        note = event.char.upper()
        if note in ("C", "D", "E", "F", "G", "A", "B"):
            self._submit_guess(note)
    def _accidental_note_key(self, event: tk.Event) -> None:
        note = ACCIDENTAL_KEYMAP.get(event.char)
        if note is not None:
            self._submit_guess(note)
    def _replay_prompt_event(self, _event: tk.Event) -> None:
        self._replay_prompt()
    def _replay_prompt(self) -> None:
        if self._state is None:
            return
        try:
            self._controller.replay_current_prompt()
        except RuntimeError:
            return
    def _can_answer_now(self) -> bool:
        if self._state is None or self._controller.has_active_manual_piece():
            return False
        return self._state.round_phase == RoundPhase.AWAIT_ANSWER
    def _refresh_stats(self) -> None:
        if self._state is None:
            return
        pitch, board, total = self._controller.game_scores()
        self._remaining_var.set("Mode Endless")
        self._score_var.set(f"Score {total} ({pitch}+{board})")
        self._streak_var.set(f"Streak {self._state.current_streak}")
        self._lines_var.set(f"Lines {self._state.total_lines_cleared}")
        self._errors_var.set(f"Errors {self._errors}")
        self._survival_var.set(f"Time {self._controller.survival_seconds()}s")
    def _draw_board(self) -> None:
        if self._canvas is None:
            return
        self._canvas.delete("all")
        board = self._state.board if self._state is not None and self._state.board is not None else [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                x0, y0 = x * self._cell + 1, y * self._cell + 1
                x1, y1 = x0 + self._cell, y0 + self._cell
                cell = board[y][x]
                if cell:
                    note = VALUE_TO_NOTE.get(cell)
                    kind = VALUE_TO_PIECE_KIND.get(cell, "T")
                    color = visual_mapping_for_note(note).color_hex if note is not None else BASE_TETROMINO_COLORS.get(kind, "#6c7a89")
                    outline = "#2a3036"
                else:
                    color = BOARD_BG
                    outline = BOARD_GRID
                self._canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline)
        active = self._state.active_piece if self._state is not None else None
        if active is not None:
            pending = self._state.pending_attempt if self._state is not None else None
            color = visual_mapping_for_note(pending.display_note).color_hex if pending is not None and pending.display_note is not None else BASE_TETROMINO_COLORS.get(active.kind, "#ffffff")
            outline = "#1b1b1b" if pending is not None and pending.display_note is not None else "#ffffff"
            for x, y in piece_cells(active):
                if y < 0:
                    continue
                x0, y0 = x * self._cell + 1, y * self._cell + 1
                x1, y1 = x0 + self._cell, y0 + self._cell
                self._canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline)
        width = BOARD_WIDTH * self._cell + 1
        height = BOARD_HEIGHT * self._cell + 1
        self._canvas.create_rectangle(1, 1, width, height, outline="#d32f2f", width=3)
    def _tick(self) -> None:
        if self._state is not None:
            now = time.monotonic()
            gravity_seconds = self._gravity_seconds if self._controller.can_control_active_piece() else self._gravity_seconds / 1.5
            if self._controller.has_active_manual_piece() and now - self._last_gravity_tick >= gravity_seconds:
                locked = self._controller.soft_drop_manual()
                self._last_gravity_tick = now
                self._refresh_stats()
                self._draw_board()
                if locked:
                    self._schedule_next_prompt_after_lock()
                    self._root.after(200, self._tick)
                    return
            else:
                self._refresh_stats()
        self._draw_board()
        self._root.after(200, self._tick)
    def _schedule_next_prompt_after_lock(self) -> None:
        if self._next_prompt_after_lock_scheduled:
            return
        self._next_prompt_after_lock_scheduled = True
        self._status_var.set("Locked. Next note in 2s")
        self._root.after(self._post_lock_delay_ms, self._run_scheduled_next_prompt)
    def _run_scheduled_next_prompt(self) -> None:
        self._next_prompt_after_lock_scheduled = False
        self._advance_to_next_prompt_if_ready()
    def _advance_to_next_prompt_if_ready(self) -> None:
        if self._state is None or self._state.round_phase != RoundPhase.NEXT_ROUND:
            return
        self._next_prompt()
