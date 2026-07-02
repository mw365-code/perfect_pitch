import unittest
from pathlib import Path

from infra.audio.tone_generator import SUPPORTED_TIMBRES, ToneGenerator


class ToneGeneratorTests(unittest.TestCase):
    def test_sustained_fast_attack_timbres_are_supported(self) -> None:
        for timbre in (
            "piano_pedal",
            "guitar_sustain",
            "harpsichord_sustain",
            "bell_sustain",
            "vibraphone_sustain",
        ):
            with self.subTest(timbre=timbre):
                self.assertIn(timbre, SUPPORTED_TIMBRES)

    def test_builtin_generator_renders_sustained_fast_attack_timbres(self) -> None:
        generator = ToneGenerator(backend="builtin")
        for timbre in ("piano_pedal", "guitar_sustain", "harpsichord_sustain", "bell_sustain", "vibraphone_sustain"):
            with self.subTest(timbre=timbre):
                note_file = generator.generate_note_file("C", 4, duration_seconds=0.1, timbre=timbre)
                self.addCleanup(note_file.unlink, missing_ok=True)
                self.assertIsInstance(note_file, Path)
                self.assertTrue(note_file.exists())
