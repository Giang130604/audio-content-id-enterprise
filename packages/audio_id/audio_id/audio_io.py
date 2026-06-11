from __future__ import annotations

import array
import wave
from pathlib import Path

from .models import AudioSignal


def load_wav_pcm(path: str | Path) -> AudioSignal:
    """Load a PCM WAV file as normalized mono float samples."""

    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())

    if channels <= 0:
        raise ValueError("WAV file has no channels")

    if sample_width == 1:
        raw = array.array("B", frames)
        values = [(sample - 128) / 128.0 for sample in raw]
    elif sample_width == 2:
        raw = array.array("h")
        raw.frombytes(frames)
        values = [sample / 32768.0 for sample in raw]
    elif sample_width == 4:
        raw = array.array("i")
        raw.frombytes(frames)
        values = [sample / 2147483648.0 for sample in raw]
    else:
        raise ValueError(f"unsupported WAV sample width: {sample_width}")

    if channels == 1:
        return AudioSignal(tuple(values), sample_rate)

    mono: list[float] = []
    for index in range(0, len(values), channels):
        frame = values[index : index + channels]
        if frame:
            mono.append(sum(frame) / len(frame))
    return AudioSignal(tuple(mono), sample_rate)

