import math
import tempfile
import wave
from array import array
from pathlib import Path

from domain.note_engine import note_to_frequency


class ToneGenerator:
    def __init__(self, sample_rate: int = 44100) -> None:
        self._sample_rate = sample_rate

    def generate_note_file(
        self,
        note: str,
        octave: int,
        duration_seconds: float,
        a4_hz: float = 440.0,
    ) -> Path:
        frequency = note_to_frequency(note, octave, a4_hz=a4_hz)
        total_samples = max(1, int(self._sample_rate * duration_seconds))
        amplitude = 0.35
        samples = array("h")
        for idx in range(total_samples):
            value = amplitude * math.sin(2.0 * math.pi * frequency * idx / self._sample_rate)
            samples.append(int(value * 32767))

        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(temp_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(samples.tobytes())
        return Path(temp_file.name)
