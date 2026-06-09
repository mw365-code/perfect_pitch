import unittest

from domain.note_engine import NOTES, normalize_note_name, note_to_frequency


class NoteEngineTests(unittest.TestCase):
    def test_notes_has_12_semitones(self) -> None:
        self.assertEqual(len(NOTES), 12)

    def test_a4_is_440hz(self) -> None:
        self.assertAlmostEqual(note_to_frequency("A", 4), 440.0, places=4)

    def test_octave_doubles_frequency(self) -> None:
        f3 = note_to_frequency("C", 3)
        f4 = note_to_frequency("C", 4)
        self.assertAlmostEqual(f4, 2.0 * f3, places=3)

    def test_normalize_supports_flats(self) -> None:
        self.assertEqual(normalize_note_name("Db"), "C#")
        self.assertEqual(normalize_note_name("Gb"), "F#")


if __name__ == "__main__":
    unittest.main()
