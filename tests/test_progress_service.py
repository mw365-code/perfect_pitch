import unittest

from domain.models import NoteAttempt
from domain.progress_service import ProgressService


def _attempt(target: str, guess: str, correct: bool) -> NoteAttempt:
    return NoteAttempt(
        session_id="s1",
        target_note=target,
        guessed_note=guess,
        octave=4,
        correct=correct,
        response_ms=500,
        timbre="sine",
        created_at="2026-05-26T00:00:00+00:00",
    )


class ProgressServiceTests(unittest.TestCase):
    def test_accuracy_by_note(self) -> None:
        attempts = [
            _attempt("C", "C", True),
            _attempt("C", "D", False),
            _attempt("D", "D", True),
        ]
        service = ProgressService()
        accuracy = service.accuracy_by_note(attempts)
        self.assertAlmostEqual(accuracy["C"], 0.50, places=2)
        self.assertAlmostEqual(accuracy["D"], 1.00, places=2)

    def test_confusion_matrix(self) -> None:
        attempts = [
            _attempt("C", "D", False),
            _attempt("C", "D", False),
            _attempt("C", "C", True),
        ]
        service = ProgressService()
        confusion = service.confusion_matrix(attempts)
        self.assertEqual(confusion[("C", "D")], 2)


if __name__ == "__main__":
    unittest.main()
