from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    default_octave: int = 4
    tone_seconds: float = 1.2
    session_attempts: int = 20
    timbre: str = "sine"


def default_config(project_root: Path) -> AppConfig:
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return AppConfig(db_path=data_dir / "perfect_pitch.db")
