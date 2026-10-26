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


# ---------- Transformaciones ----------
def voz(tema, retraso=0, trans=0, eje=None, factor=1):
    """
    retraso: desplazamiento en tiempos (canon a la distancia de ...)
    trans:   transposición en grados de la escala (4 = quinta, -7 = octava abajo)
    eje:     si no es None, movimiento contrario: g -> eje - g
    factor:  aumentación (2 = duraciones x2) o disminución (0.5)
    """
    out = []
    for g, t, d in tema:
        if eje is not None:
            g = eje - g
        out.append((g + trans, t * factor + retraso, d * factor))
    return out


def render(voces, archivo, ganancia=0.15):
    fin = max(t + d for v in voces for _, t, d in v) * beat
    total = int(sr * (fin + 4))
    mezcla = np.zeros(total)
    for v in voces:
        for g, t, d in v:
            s = tono(midi(g), d * beat) * ganancia
            i = int(sr * beat * t)
            mezcla[i : i + len(s)] += s[: total - i]

    # Reverb: convolución con ruido que decae
    ir = np.random.randn(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 3)
    humedo = fftconvolve(mezcla, ir)[:total]
    humedo *= np.abs(mezcla).max() / np.abs(humedo).max()
    mezcla = 0.75 * mezcla + 0.25 * humedo

    wavfile.write(archivo, sr, (mezcla / np.abs(mezcla).max() * 32767).astype(np.int16))


tema = melodia(32, seed=7)

# A) Movimiento contrario: la segunda voz es el espejo de la primera.
#    eje=6 refleja el rango (-3..9) sobre sí mismo.
render([voz(tema), voz(tema, retraso=4, eje=6)], "canon_contrario.wav")

# B) Aumentación: la segunda voz va a mitad de velocidad,
#    una octava abajo; dura el doble que el tema.
render([voz(tema), voz(tema, trans=-7, factor=2)], "canon_aumentacion.wav")

# C) Ambas a la vez, como en la Ofrenda Musical:
#    voz grave lenta y en espejo, sobre el tema original.
render(
    [voz(tema), voz(tema, trans=-7, eje=6, factor=2)], "canon_aumentacion_contrario.wav"
)
