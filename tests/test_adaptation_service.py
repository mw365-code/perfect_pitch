import random
import unittest

from domain.adaptation_service import AdaptationService
from domain.models import NoteAttempt


def _attempt(target: str, correct: bool, response_ms: int = 500) -> NoteAttempt:
    return NoteAttempt(
        session_id="s1",
        target_note=target,
        guessed_note=target if correct else "X",
        octave=4,
        correct=correct,
        response_ms=response_ms,
        timbre="sine",
        created_at="2026-05-26T00:00:00+00:00",
    )



class AdaptationServiceTests(unittest.TestCase):
    def test_weak_note_is_selected_more_often(self) -> None:
        notes = ["C", "D", "E"]
        attempts = [
            _attempt("C", False, 1800),
            _attempt("C", False, 1900),
            _attempt("C", False, 1700),
            _attempt("D", True, 300),
            _attempt("D", True, 280),
            _attempt("E", True, 290),
            _attempt("E", True, 310),
        ]
        service = AdaptationService(rng=random.Random(7))
        picks = [service.choose_next_note(notes, attempts) for _ in range(300)]
        self.assertGreater(picks.count("C"), picks.count("D"))
        self.assertGreater(picks.count("C"), picks.count("E"))


if __name__ == "__main__":
    unittest.main()
