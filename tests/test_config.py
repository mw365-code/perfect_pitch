import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from infra.config import default_config


class DefaultConfigTests(unittest.TestCase):
    def test_defaults_to_builtin_without_soundfont(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = default_config(Path(tmp))
        self.assertEqual(config.audio_backend, "builtin")
        self.assertIsNone(config.soundfont_path)

    def test_defaults_to_soundfont_when_default_sf2_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            soundfont_dir = root / "data" / "soundfonts"
            soundfont_dir.mkdir(parents=True, exist_ok=True)
            soundfont_path = soundfont_dir / "VintageDreamsWaves-v2.sf2"
            soundfont_path.write_bytes(b"sf2")

            with patch("infra.config.soundfont_backend_available", return_value=True):
                config = default_config(root)

        self.assertEqual(config.audio_backend, "soundfont")
        self.assertEqual(config.soundfont_path, soundfont_path)

    def test_defaults_to_builtin_when_sf2_exists_but_backend_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            soundfont_dir = root / "data" / "soundfonts"
            soundfont_dir.mkdir(parents=True, exist_ok=True)
            soundfont_path = soundfont_dir / "VintageDreamsWaves-v2.sf2"
            soundfont_path.write_bytes(b"sf2")

            with patch("infra.config.soundfont_backend_available", return_value=False):
                config = default_config(root)

        self.assertEqual(config.audio_backend, "builtin")
        self.assertEqual(config.soundfont_path, soundfont_path)
