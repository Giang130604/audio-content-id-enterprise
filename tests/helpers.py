from __future__ import annotations

import math
import random

from audio_id.models import AudioSignal


def synthetic_reference(sample_rate: int = 8000) -> AudioSignal:
    samples: list[float] = []
    pattern = [
        (220.0, 0.20, 0.12),
        (330.0, 0.70, 0.10),
        (440.0, 0.35, 0.08),
        (550.0, 0.85, 0.11),
        (660.0, 0.45, 0.09),
        (330.0, 0.95, 0.13),
    ]
    for repeat in range(4):
        for frequency, amplitude, duration in pattern:
            count = int(sample_rate * duration)
            for index in range(count):
                t = index / sample_rate
                envelope = 0.5 - 0.5 * math.cos(2 * math.pi * index / max(1, count))
                samples.append(amplitude * envelope * math.sin(2 * math.pi * frequency * t))
        samples.extend([0.0] * int(sample_rate * 0.03 * (repeat + 1)))
    return AudioSignal(tuple(samples), sample_rate)


def add_noise(signal: AudioSignal, amount: float = 0.015) -> AudioSignal:
    random.seed(42)
    samples = [
        max(-1.0, min(1.0, sample + random.uniform(-amount, amount)))
        for sample in signal.samples
    ]
    return AudioSignal(tuple(samples), signal.sample_rate)


def speed_change(signal: AudioSignal, factor: float) -> AudioSignal:
    if factor <= 0:
        raise ValueError("factor must be positive")
    output_len = max(1, int(len(signal.samples) / factor))
    samples: list[float] = []
    for index in range(output_len):
        source = index * factor
        left = int(source)
        right = min(left + 1, len(signal.samples) - 1)
        fraction = source - left
        value = signal.samples[left] * (1 - fraction) + signal.samples[right] * fraction
        samples.append(value)
    return AudioSignal(tuple(samples), signal.sample_rate)

