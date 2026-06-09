from domain.game_constants import CHROMATIC_NOTES, canonicalize_note_name

NOTES: tuple[str, ...] = CHROMATIC_NOTES

SEMITONE_INDEX = {name: idx for idx, name in enumerate(CHROMATIC_NOTES)}


def note_to_frequency(note: str, octave: int, a4_hz: float = 440.0) -> float:
    note_name = canonicalize_note_name(note)
    semitone_from_a4 = (octave - 4) * 12 + SEMITONE_INDEX[note_name] - SEMITONE_INDEX["A"]
    return a4_hz * (2.0 ** (semitone_from_a4 / 12.0))


def normalize_note_name(note: str) -> str:
    return canonicalize_note_name(note)
