import random
from collections import defaultdict

from domain.models import NoteAttempt


class AdaptationService:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def choose_next_note(self, notes: list[str], recent_attempts: list[NoteAttempt]) -> str:
        if not notes:
            raise ValueError("Notes must not be empty")
        if not recent_attempts:
            return self._rng.choice(notes)
        weights = self._build_weights(notes, recent_attempts)
        return self._rng.choices(notes, weights=weights, k=1)[0]

    def _build_weights(self, notes: list[str], attempts: list[NoteAttempt]) -> list[float]:
        total_by_note: dict[str, int] = defaultdict(int)
        correct_by_note: dict[str, int] = defaultdict(int)
        rt_sum_by_note: dict[str, int] = defaultdict(int)
        incorrect_by_note: dict[str, int] = defaultdict(int)

        for attempt in attempts:
            target = attempt.target_note
            total_by_note[target] += 1
            rt_sum_by_note[target] += max(attempt.response_ms, 1)
            if attempt.correct:
                correct_by_note[target] += 1
            else:
                incorrect_by_note[target] += 1

        weights: list[float] = []
        for note in notes:
            total = total_by_note[note]
            if total == 0:
                weights.append(2.2)
                continue
            accuracy = correct_by_note[note] / total
            avg_rt = rt_sum_by_note[note] / total
            confusion = incorrect_by_note[note] / total
            weakness = 1.0 + (1.0 - accuracy) * 2.0 + min(avg_rt / 3000.0, 1.0) + confusion
            weights.append(max(0.1, weakness))
        return weights
