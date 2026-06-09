import argparse
from pathlib import Path

from app.training_controller import TrainingController
from domain.adaptation_service import AdaptationService
from domain.note_engine import NOTES
from domain.progress_service import ProgressService
from domain.session_service import SessionService
from infra.audio.player import AudioPlayer
from infra.audio.tone_generator import ToneGenerator
from infra.config import default_config
from infra.db.connection import connect
from infra.db.repositories import SqliteTrainingRepository
from infra.db.schema import initialize_schema
from ui.cli_app import CliApp
from ui.tk_app import TkApp


def build_controller(project_root: Path) -> tuple[TrainingController, int]:
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
    controller = TrainingController(
        session_service=session_service,
        progress_service=ProgressService(),
        tone_generator=ToneGenerator(),
        audio_player=AudioPlayer(),
        tone_seconds=config.tone_seconds,
        timbre=config.timbre,
        default_octave=config.default_octave,
    )
    return controller, config.session_attempts


def run_cli(project_root: Path) -> None:
    controller, attempts = build_controller(project_root)
    CliApp(controller=controller, default_attempts=attempts).run()


def run_gui(project_root: Path) -> None:
    controller, attempts = build_controller(project_root)
    TkApp(controller=controller, default_attempts=attempts).run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Perfect Pitch Trainer")
    parser.add_argument("--cli", action="store_true", help="Run CLI version")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    if args.cli:
        run_cli(project_root)
        return
    run_gui(project_root)
