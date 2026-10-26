import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve

sr, bpm = 44100, 72
beat = 60 / bpm
escala = [0, 2, 3, 5, 7, 8, 10]  # Re menor natural


def midi(grado, tonica=62):
    octava, i = divmod(grado, 7)
    return tonica + 12 * octava + escala[i]


def melodia(beats=32, seed=None):
    rng = np.random.default_rng(seed)
    g, t, out = 0, 0.0, []
    while t < beats:
        d = rng.choice([0.5, 0.5, 1, 1, 2])
        out.append((g, t, d))
        g += rng.choice([-2, -1, 0, 1, 2], p=[0.1, 0.35, 0.1, 0.35, 0.1])
        g = int(np.clip(g, -3, 9))
        t += d
    return out


def tono(m, dur):
    f = 440 * 2 ** ((m - 69) / 12)
    t = np.arange(int(sr * (dur + 2))) / sr
    s = sum(
        a * np.sin(2 * np.pi * f * k * t)
        for k, a in enumerate([1, 0.5, 0.25, 0.12, 0.06], 1)
    )
    return s * np.exp(-t * 2.5) * np.minimum(1, t / 0.005)


# (retraso en tiempos, transposición en grados)
voces = [(0, 0), (4, 4), (8, -7)]
tema = melodia(32, seed=7)

total = int(sr * (beat * (32 + 8) + 4))
mezcla = np.zeros(total)
for retraso, trans in voces:
    for g, t, d in tema:
        s = tono(midi(g + trans), d * beat) * 0.15
        i = int(sr * beat * (t + retraso))
        mezcla[i : i + len(s)] += s[: total - i]

# Reverb: convolución con ruido que decae
ir = np.random.randn(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 3)
mezcla = 0.7 * mezcla + 0.3 * fftconvolve(mezcla, ir)[:total] * 0.02
wavfile.write("canon.wav", sr, (mezcla / np.abs(mezcla).max() * 32767).astype(np.int16))
