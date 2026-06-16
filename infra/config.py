from dataclasses import dataclass
from pathlib import Path

from infra.audio.tone_generator import soundfont_backend_available


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    default_octave: int = 4
    tone_seconds: float = 1.2
    session_attempts: int = 20
    timbre: str = "sine"
    audio_backend: str = "builtin"
    soundfont_path: Path | None = None


def default_config(project_root: Path) -> AppConfig:
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    soundfont = data_dir / "soundfonts" / "VintageDreamsWaves-v2.sf2"
    soundfont_path = soundfont if soundfont.exists() else None
    audio_backend = "soundfont" if soundfont_backend_available(soundfont_path) else "builtin"
    return AppConfig(
        db_path=data_dir / "perfect_pitch.db",
        audio_backend=audio_backend,
        soundfont_path=soundfont_path,
    )
