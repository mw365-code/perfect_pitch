import os
import platform
import shutil
import subprocess
from pathlib import Path


class AudioPlayer:
    def play(self, file_path: Path) -> None:
        system = platform.system().lower()
        if system == "darwin":
            self._play_command(["afplay", str(file_path)])
            return
        if system == "linux" and shutil.which("aplay"):
            self._play_command(["aplay", str(file_path)])
            return
        if system == "windows":
            import winsound

            winsound.PlaySound(str(file_path), winsound.SND_FILENAME)
            return
        # Fallback: no supported audio backend found.

    @staticmethod
    def _play_command(command: list[str]) -> None:
        if not shutil.which(command[0]):
            return
        subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def cleanup(file_path: Path) -> None:
        try:
            os.unlink(file_path)
        except OSError:
            pass
