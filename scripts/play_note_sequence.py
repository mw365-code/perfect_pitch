import argparse
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infra.audio.player import AudioPlayer
from infra.audio.tone_generator import SUPPORTED_AUDIO_BACKENDS, SUPPORTED_TIMBRES, ToneGenerator, soundfont_backend_available

DEFAULT_SEQUENCE = ["A", "B", "C", "D", "E", "F", "G", "A#", "C#", "D#", "F#", "G#"]
NOTE_SECONDS = 1.0
GAP_SECONDS = 0.5
DEFAULT_SOUNDFONT = PROJECT_ROOT / "data" / "soundfonts" / "VintageDreamsWaves-v2.sf2"
DEFAULT_AUDIO_BACKEND = "soundfont" if soundfont_backend_available(DEFAULT_SOUNDFONT) else "builtin"


def main() -> None:
    parser = argparse.ArgumentParser(description="Play a fixed note sequence")
    parser.add_argument("timbre", nargs="?", default="piano", choices=SUPPORTED_TIMBRES)
    parser.add_argument("--audio-backend", choices=SUPPORTED_AUDIO_BACKENDS, default=DEFAULT_AUDIO_BACKEND)
    parser.add_argument("--soundfont", help="Path to a .sf2 SoundFont file")
    args = parser.parse_args()
    soundfont = Path(args.soundfont).expanduser() if args.soundfont else DEFAULT_SOUNDFONT if DEFAULT_SOUNDFONT.exists() else None
    if args.audio_backend == "soundfont" and soundfont is None:
        parser.error("--soundfont is required when --audio-backend soundfont is used")
    if args.audio_backend == "soundfont" and not soundfont_backend_available(soundfont):
        parser.error(f"SoundFont backend is not available with {soundfont}")
    generator = ToneGenerator(backend=args.audio_backend, soundfont_path=soundfont)
    player = AudioPlayer()
    for note in DEFAULT_SEQUENCE:
        print(f"Playing {note} ({args.timbre})")
        tone_file = generator.generate_note_file(note, 4, duration_seconds=NOTE_SECONDS, timbre=args.timbre)
        try:
            player.play(tone_file)
        finally:
            player.cleanup(tone_file)
        time.sleep(GAP_SECONDS)


if __name__ == "__main__":
    main()
