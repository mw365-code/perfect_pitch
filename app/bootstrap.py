import argparse
from pathlib import Path

from app.training_controller import TrainingController
from domain.adaptation_service import AdaptationService
from domain.note_engine import NOTES
from domain.progress_service import ProgressService
from domain.session_service import SessionService
from infra.audio.player import AudioPlayer
from infra.audio.tone_generator import SUPPORTED_AUDIO_BACKENDS, SUPPORTED_TIMBRES, ToneGenerator, soundfont_backend_available
from infra.config import default_config
from infra.db.connection import connect
from infra.db.repositories import SqliteTrainingRepository
from infra.db.schema import initialize_schema
from ui.cli_app import CliApp
from ui.tk_app import TkApp


def build_controller(
    project_root: Path,
    timbre: str | None = None,
    audio_backend: str | None = None,
    soundfont_path: str | None = None,
) -> tuple[TrainingController, int]:
    config = default_config(project_root)
    connection = connect(config.db_path)
    initialize_schema(connection)
    repository = SqliteTrainingRepository(connection)

    session_service = SessionService(
        attempt_store=repository,
        session_store=repository,
        adaptation_service=AdaptationService(),
        notes=list(NOTES),
    )
    backend = audio_backend or config.audio_backend
    soundfont = Path(soundfont_path).expanduser() if soundfont_path else config.soundfont_path
    controller = TrainingController(
        session_service=session_service,
        progress_service=ProgressService(),
        tone_generator=ToneGenerator(backend=backend, soundfont_path=soundfont),
        audio_player=AudioPlayer(),
        tone_seconds=config.tone_seconds,
        timbre=timbre or config.timbre,
        default_octave=config.default_octave,
    )
    return controller, config.session_attempts


def run_cli(project_root: Path, timbre: str | None = None, audio_backend: str | None = None, soundfont_path: str | None = None) -> None:
    controller, attempts = build_controller(project_root, timbre=timbre, audio_backend=audio_backend, soundfont_path=soundfont_path)
    CliApp(controller=controller, default_attempts=attempts).run()


def run_gui(project_root: Path, timbre: str | None = None, audio_backend: str | None = None, soundfont_path: str | None = None) -> None:
    controller, attempts = build_controller(project_root, timbre=timbre, audio_backend=audio_backend, soundfont_path=soundfont_path)
    TkApp(controller=controller, default_attempts=attempts).run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Perfect Pitch Trainer")
    parser.add_argument("--cli", action="store_true", help="Run CLI version")
    parser.add_argument("--timbre", choices=SUPPORTED_TIMBRES, help="Choose synthesized instrument")
    parser.add_argument("--audio-backend", choices=SUPPORTED_AUDIO_BACKENDS, help="Choose audio synthesis backend")
    parser.add_argument("--soundfont", help="Path to a .sf2 SoundFont file for the soundfont backend")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    config = default_config(project_root)
    selected_soundfont = Path(args.soundfont).expanduser() if args.soundfont else config.soundfont_path
    if args.audio_backend == "soundfont":
        if selected_soundfont is None:
            parser.error("--soundfont is required when --audio-backend soundfont is used")
        if not soundfont_backend_available(selected_soundfont):
            parser.error(f"SoundFont backend is not available with {selected_soundfont}")
    if args.cli:
        run_cli(project_root, timbre=args.timbre, audio_backend=args.audio_backend, soundfont_path=args.soundfont)
        return
    run_gui(project_root, timbre=args.timbre, audio_backend=args.audio_backend, soundfont_path=args.soundfont)
