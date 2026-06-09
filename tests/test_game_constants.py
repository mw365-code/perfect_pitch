import unittest

from domain.game_constants import (
    ACCIDENTAL_NOTES,
    CHROMATIC_NOTES,
    NOTE_TO_TETROMINO,
    canonicalize_note_name,
    visual_mapping_for_note,
)


class GameConstantsTests(unittest.TestCase):
    def test_chromatic_notes_has_12(self) -> None:
        self.assertEqual(len(CHROMATIC_NOTES), 12)

    def test_all_notes_have_tetromino_mapping(self) -> None:
        for note in CHROMATIC_NOTES:
            self.assertIn(note, NOTE_TO_TETROMINO)

    def test_flat_aliases_are_normalized(self) -> None:
        self.assertEqual(canonicalize_note_name("Db"), "C#")
        self.assertEqual(canonicalize_note_name("eb"), "D#")
        self.assertEqual(canonicalize_note_name(" Bb "), "A#")

    def test_accidental_mapping_uses_light_color(self) -> None:
        mapping = visual_mapping_for_note("Db")
        self.assertTrue(mapping.is_accidental)
        self.assertEqual(mapping.canonical_note, "C#")
        self.assertIn("Db", mapping.labels)

    def test_natural_mapping_uses_base_color(self) -> None:
        mapping = visual_mapping_for_note("E")
        self.assertFalse(mapping.is_accidental)
        self.assertNotIn(mapping.canonical_note, ACCIDENTAL_NOTES)


if __name__ == "__main__":
    unittest.main()
