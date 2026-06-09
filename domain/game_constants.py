from dataclasses import dataclass

CHROMATIC_NOTES: tuple[str, ...] = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)

ENHARMONIC_LABELS: dict[str, tuple[str, ...]] = {
    "C": ("C",),
    "C#": ("C#", "Db"),
    "D": ("D",),
    "D#": ("D#", "Eb"),
    "E": ("E",),
    "F": ("F",),
    "F#": ("F#", "Gb"),
    "G": ("G",),
    "G#": ("G#", "Ab"),
    "A": ("A",),
    "A#": ("A#", "Bb"),
    "B": ("B",),
}

NOTE_ALIASES: dict[str, str] = {
    "DB": "C#",
    "EB": "D#",
    "GB": "F#",
    "AB": "G#",
    "BB": "A#",
}

TETROMINO_FAMILIES: tuple[str, ...] = ("I", "O", "T", "S", "Z", "J", "L")

NATURAL_NOTE_TO_TETROMINO: dict[str, str] = {
    "C": "I",
    "D": "O",
    "E": "T",
    "F": "S",
    "G": "Z",
    "A": "J",
    "B": "L",
}

NOTE_TO_TETROMINO: dict[str, str] = {
    "C": "I",
    "C#": "I",
    "D": "O",
    "D#": "O",
    "E": "T",
    "F": "S",
    "F#": "S",
    "G": "Z",
    "G#": "Z",
    "A": "J",
    "A#": "J",
    "B": "L",
}

BASE_TETROMINO_COLORS: dict[str, str] = {
    "I": "#00BCD4",
    "O": "#FBC02D",
    "T": "#8E44AD",
    "S": "#43A047",
    "Z": "#E53935",
    "J": "#1E88E5",
    "L": "#FB8C00",
}

ACCIDENTAL_TETROMINO_COLORS: dict[str, str] = {
    "I": "#80DEEA",
    "O": "#FFF59D",
    "T": "#C39BD3",
    "S": "#A5D6A7",
    "Z": "#FF8A80",
    "J": "#90CAF9",
    "L": "#FFCC80",
}

ACCIDENTAL_NOTES: set[str] = {"C#", "D#", "F#", "G#", "A#"}


@dataclass(frozen=True)
class NoteVisualMapping:
    canonical_note: str
    labels: tuple[str, ...]
    tetromino_family: str
    color_hex: str
    is_accidental: bool


def canonicalize_note_name(note: str) -> str:
    value = note.strip().upper()
    if value in CHROMATIC_NOTES:
        return value
    alias = NOTE_ALIASES.get(value)
    if alias is not None:
        return alias
    raise ValueError(f"Unsupported note name: {note}")


def visual_mapping_for_note(note: str) -> NoteVisualMapping:
    canonical = canonicalize_note_name(note)
    family = NOTE_TO_TETROMINO[canonical]
    is_accidental = canonical in ACCIDENTAL_NOTES
    color = (
        ACCIDENTAL_TETROMINO_COLORS[family]
        if is_accidental
        else BASE_TETROMINO_COLORS[family]
    )
    return NoteVisualMapping(
        canonical_note=canonical,
        labels=ENHARMONIC_LABELS[canonical],
        tetromino_family=family,
        color_hex=color,
        is_accidental=is_accidental,
    )
