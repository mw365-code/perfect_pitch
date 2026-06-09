from collections import defaultdict

from domain.models import NoteAttempt


class ProgressService:
    def accuracy_by_note(self, attempts: list[NoteAttempt]) -> dict[str, float]:
        totals: dict[str, int] = defaultdict(int)
        correct: dict[str, int] = defaultdict(int)
        for attempt in attempts:
            totals[attempt.target_note] += 1
            if attempt.correct:
                correct[attempt.target_note] += 1
        return {
            note: (correct[note] / total if total else 0.0)
            for note, total in totals.items()
        }

    def confusion_matrix(self, attempts: list[NoteAttempt]) -> dict[tuple[str, str], int]:
        confusion: dict[tuple[str, str], int] = defaultdict(int)
        for attempt in attempts:
            if attempt.correct:
                continue
            confusion[(attempt.target_note, attempt.guessed_note)] += 1
        return dict(confusion)
