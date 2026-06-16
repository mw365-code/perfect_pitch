import math
import os
import tempfile
import wave
from array import array
from pathlib import Path

from domain.note_engine import SEMITONE_INDEX, normalize_note_name, note_to_frequency

TIMBRE_PRESETS: dict[str, tuple[tuple[float, float], ...]] = {
    "sine": ((1.0, 1.0),),
    "piano": ((1.0, 1.0), (2.0, 0.18), (3.0, 0.07), (4.0, 0.03)),
    "piano_pedal": ((1.0, 1.0), (2.0, 0.2), (3.0, 0.08), (4.0, 0.04), (5.0, 0.015)),
    "organ": ((1.0, 0.8), (2.0, 0.45), (3.0, 0.3), (4.0, 0.18)),
    "bell": ((1.0, 0.7), (2.76, 0.4), (4.07, 0.28), (5.43, 0.16)),
    "bell_sustain": ((1.0, 0.72), (2.76, 0.38), (4.07, 0.24), (5.43, 0.14)),
    "flute": ((1.0, 0.95), (2.0, 0.12), (3.0, 0.05)),
    "clarinet": ((1.0, 0.95), (3.0, 0.42), (5.0, 0.18), (7.0, 0.08)),
    "oboe": ((1.0, 0.85), (2.0, 0.32), (3.0, 0.22), (4.0, 0.1)),
    "guitar": ((1.0, 1.0), (2.0, 0.38), (3.0, 0.18), (5.0, 0.06)),
    "guitar_sustain": ((1.0, 1.0), (2.0, 0.34), (3.0, 0.16), (5.0, 0.06)),
    "harpsichord": ((1.0, 0.8), (2.0, 0.5), (3.0, 0.24), (4.0, 0.1)),
    "harpsichord_sustain": ((1.0, 0.82), (2.0, 0.46), (3.0, 0.2), (4.0, 0.08)),
    "brass": ((1.0, 0.75), (2.0, 0.52), (3.0, 0.35), (4.0, 0.14)),
    "strings": ((1.0, 0.8), (2.0, 0.28), (3.0, 0.18), (4.0, 0.08)),
    "vibraphone": ((1.0, 0.75), (2.0, 0.26), (3.97, 0.18), (6.11, 0.08)),
    "vibraphone_sustain": ((1.0, 0.78), (2.0, 0.24), (3.97, 0.16), (6.11, 0.07)),
}
SUPPORTED_TIMBRES = tuple(sorted(TIMBRE_PRESETS))
SUPPORTED_AUDIO_BACKENDS = ("builtin", "soundfont")
SOUNDFONT_PROGRAMS = {
    "bell": 10, "bell_sustain": 10, "brass": 61, "clarinet": 71, "flute": 73, "guitar": 24, "guitar_sustain": 24, "harpsichord": 6, "harpsichord_sustain": 6,
    "oboe": 68, "organ": 19, "piano": 0, "piano_pedal": 0, "sine": 80, "strings": 48, "vibraphone": 11,
    "vibraphone_sustain": 11,
}
ENVELOPE_PRESETS: dict[str, tuple[float, float, float, float, float]] = {
    "sine": (0.01, 0.04, 0.9, 0.12, 1.8), "piano": (0.03, 0.08, 0.22, 0.16, 2.8),
    "piano_pedal": (0.03, 0.1, 0.36, 0.32, 1.8),
    "organ": (0.03, 0.08, 0.8, 0.16, 0.4), "bell": (0.004, 0.12, 0.1, 0.24, 5.5),
    "bell_sustain": (0.012, 0.12, 0.22, 0.38, 2.4),
    "flute": (0.05, 0.06, 0.82, 0.14, 0.9), "clarinet": (0.03, 0.08, 0.72, 0.14, 1.2),
    "oboe": (0.025, 0.08, 0.68, 0.14, 1.5), "guitar": (0.004, 0.16, 0.18, 0.16, 4.2),
    "guitar_sustain": (0.02, 0.1, 0.3, 0.3, 1.8),
    "harpsichord": (0.003, 0.05, 0.12, 0.14, 4.8), "harpsichord_sustain": (0.018, 0.08, 0.22, 0.28, 2.1),
    "brass": (0.035, 0.08, 0.7, 0.16, 1.1),
    "strings": (0.08, 0.1, 0.75, 0.18, 0.8), "vibraphone": (0.01, 0.12, 0.22, 0.22, 3.2),
    "vibraphone_sustain": (0.02, 0.1, 0.3, 0.34, 1.8),
}
PEDAL_TIMBRES = {"piano_pedal", "guitar_sustain", "harpsichord_sustain", "bell_sustain", "vibraphone_sustain"}
MODULATED_TIMBRES = {"bell", "bell_sustain", "vibraphone", "vibraphone_sustain"}


def prepare_soundfont_env(soundfont_path: Path | None) -> None:
    if "HOMEBREW_PREFIX" in os.environ or soundfont_path is None:
        return
    brew_formula_prefix = Path("/opt/homebrew/opt/fluid-synth")
    if brew_formula_prefix.exists():
        os.environ["HOMEBREW_PREFIX"] = str(brew_formula_prefix)


def soundfont_backend_available(soundfont_path: Path | None) -> bool:
    if soundfont_path is None or not soundfont_path.exists():
        return False
    prepare_soundfont_env(soundfont_path)
    try:
        import fluidsynth

        synth = fluidsynth.Synth()
        synth.delete()
    except Exception:
        return False
    return True


class ToneGenerator:
    def __init__(self, sample_rate: int = 44100, backend: str = "builtin", soundfont_path: Path | None = None) -> None:
        self._sample_rate = sample_rate
        requested_backend = backend if backend in SUPPORTED_AUDIO_BACKENDS else "builtin"
        self._backend = "soundfont" if requested_backend == "soundfont" and soundfont_backend_available(soundfont_path) else "builtin"
        self._soundfont_path = soundfont_path

    def generate_note_file(
        self, note: str, octave: int, duration_seconds: float, a4_hz: float = 440.0, timbre: str = "sine",
    ) -> Path:
        if self._backend == "soundfont" and self._soundfont_path is not None:
            return self._generate_soundfont_note_file(note, octave, duration_seconds, timbre)
        return self._generate_builtin_note_file(note, octave, duration_seconds, a4_hz, timbre)

    def _generate_builtin_note_file(self, note: str, octave: int, duration_seconds: float, a4_hz: float, timbre: str) -> Path:
        timbre = timbre if timbre in TIMBRE_PRESETS else "sine"
        frequency = note_to_frequency(note, octave, a4_hz=a4_hz)
        total_samples = max(1, int(self._sample_rate * duration_seconds))
        partials = TIMBRE_PRESETS[timbre]
        samples = array("h")
        for idx in range(total_samples):
            t = idx / self._sample_rate
            value = sum(weight * math.sin(2.0 * math.pi * frequency * ratio * t) for ratio, weight in partials)
            if timbre in MODULATED_TIMBRES: value *= 1.0 + 0.12 * math.sin(2.0 * math.pi * 5.0 * t)
            samples.append(int(max(-1.0, min(1.0, value * self._envelope(t, duration_seconds, timbre) * 0.32)) * 32767))
        return self._write_wave_file(samples.tobytes(), channels=1)

    def _generate_soundfont_note_file(self, note: str, octave: int, duration_seconds: float, timbre: str) -> Path:
        prepare_soundfont_env(self._soundfont_path)
        import fluidsynth
        synth = fluidsynth.Synth()
        try:
            sfid = synth.sfload(str(self._soundfont_path))
            synth.program_select(0, sfid, 0, SOUNDFONT_PROGRAMS.get(timbre, 0))
            midi_note = 12 * (octave + 1) + SEMITONE_INDEX[normalize_note_name(note)]
            if timbre in PEDAL_TIMBRES:
                synth.cc(0, 64, 127)
            synth.noteon(0, midi_note, 110)
            frames = int(self._sample_rate * duration_seconds)
            body = synth.get_samples(frames)
            synth.noteoff(0, midi_note)
            if timbre in PEDAL_TIMBRES:
                body = body.tobytes() + synth.get_samples(int(self._sample_rate * 0.45)).tobytes()
                synth.cc(0, 64, 0)
                release = synth.get_samples(int(self._sample_rate * 0.45))
                return self._write_wave_file(body + release.tobytes(), channels=2)
            release = synth.get_samples(int(self._sample_rate * 0.25))
            return self._write_wave_file(body.tobytes() + release.tobytes(), channels=2)
        finally:
            synth.delete()

    def _write_wave_file(self, frames: bytes, channels: int) -> Path:
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(temp_file, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(frames)
        return Path(temp_file.name)

    @staticmethod
    def _envelope(t: float, duration_seconds: float, timbre: str) -> float:
        attack, decay, sustain, release, damping = ENVELOPE_PRESETS[timbre]
        release = min(release, duration_seconds * 0.4)
        if t < attack: return t / max(attack, 1e-6)
        if t < attack + decay:
            return 1.0 - (1.0 - sustain) * ((t - attack) / max(decay, 1e-6))
        if t < max(duration_seconds - release, attack + decay):
            return max(sustain * 0.5, math.exp(-(t - attack - decay) * damping))
        return sustain * max(duration_seconds - t, 0.0) / max(release, 1e-6)
