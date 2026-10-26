"""
Música generativa al estilo de George Winston (Autumn / December).

  - Progresión lenta Am - F - C - G (un compás por acorde).
  - Mano izquierda: arpegio continuo de corcheas, subiendo y bajando.
  - Mano derecha: melodía simple y espaciada sobre notas del acorde.
  - Pedal de sustain: todo suena hasta el cambio de acorde.
  - Estructura A A' B B' A, con introducción, ritardando y acorde final.

Requiere: numpy, scipy, lameenc (solo para mp3)

Notas de creación:
Aquí tienes winston.py y winston.mp3 (2 min 8 s, estéreo). El script escribe también el MP3 al final, con lameenc como antes. Como siempre, no puedo oírlo: lo que revisé es el código, las melodías generadas y el nivel de la mezcla (sin saturación).

Cómo está hecho

Armonía: Am - F - C - G, un compás por acorde, a 66 negras por minuto.
Mano izquierda: arpegio continuo de 8 corcheas por compás, subiendo y bajando sobre fundamental, quinta, octava, tercera y quinta (La2, Mi3, La3, Do4, Mi4 en el primer acorde).
Melodía: generada compás a compás. En los tiempos fuertes usa notas del acorde y en los débiles notas de paso. Los saltos son cortos, se evita repetir la misma nota y se favorece seguir en la misma dirección. Los patrones rítmicos incluyen notas largas y silencios, para que quede espaciada.
Pedal de sustain: todo suena hasta el cambio de acorde y se apaga con una relajación corta.
Piano: síntesis aditiva con parciales ligeramente inarmónicos. Las notas graves duran más, los agudos decaen antes y las notas suaves son menos brillantes.
Detalles de interpretación: pequeñas variaciones de tiempo y volumen, un arco dinámico en cada frase, panorama estéreo según la altura (graves a la izquierda) y reverb cálida de unos 3 s.
Forma: introducción solo con la mano izquierda, luego A, A′ (se repiten tres compases y cambia el último), B (más densa y más aguda), B′, vuelta de A, un ciclo final solo con arpegios con ritardando, y un acorde de La menor arpegiado lentamente.

Una corrección de rumbo

La primera versión de la melodía repetía mucho las notas (A4 A4, G4 G4 G4) y daba saltos de séptima. Penalizar la repetición y los saltos lo arregló: en las pruebas con varias semillas quedan 0-2 repeticiones por frase.

Para ajustar el resultado

BPM cambia el tempo, y partitura(semilla=...) da melodías distintas.
Si lo quieres más cerca de Autumn, prueba a bajar BPM a 56-60 y a acentuar más la primera corchea del arpegio (el 0.08 de velocidad).
Para más variedad armónica, cambia PROG (por ejemplo Am - F - C - E, o Am - G - F - G) y añade el acorde nuevo a ACORDES.
"""

import copy
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, lfilter

sr = 44100
BPM = 66
SP = 60 / BPM  # segundos por tiempo

# Cada acorde: arpegio de 5 notas (fundamental, quinta, octava, tercera, quinta)
ACORDES = {
    "Am": dict(arp=[45, 52, 57, 60, 64], pcs={9, 0, 4}),
    "F": dict(arp=[41, 48, 53, 57, 60], pcs={5, 9, 0}),
    "C": dict(arp=[48, 55, 60, 64, 67], pcs={0, 4, 7}),
    "G": dict(arp=[43, 50, 55, 59, 62], pcs={7, 11, 2}),
}
PROG = ["Am", "F", "C", "G"]
PATRON_ARP = [0, 1, 2, 3, 4, 3, 2, 1]  # 8 corcheas por compás
BLANCAS = {0, 2, 4, 5, 7, 9, 11}  # La menor natural = teclas blancas

# Ritmos de un compás de 4 tiempos; los negativos son silencios.
PATRONES = {
    "A": [[2, 2], [4], [1, 1, 2], [3, 1], [2, 1, 1], [-1, 1, 2]],
    "B": [
        [1, 1, 1, 1],
        [1, 1, 2],
        [0.5, 0.5, 1, 2],
        [1.5, 0.5, 1, 1],
        [1, 1, 1, 0.5, 0.5],
    ],
}
REGISTRO = {"A": (64, 76, 70), "B": (67, 81, 74)}  # (mínimo, máximo, centro) MIDI


# ---------------------------------------------------------------- melodía
def elegir_nota(rng, previa, pcs, fuerte, lo, hi, centro, direccion):
    """Nota cercana a la anterior; en tiempo fuerte, nota del acorde.
    Se penaliza repetir la nota y los saltos, y se favorece seguir en la
    misma dirección (perfiles melódicos ondulantes, no vaivenes)."""
    cand = [
        m
        for m in range(lo, hi + 1)
        if m % 12 in BLANCAS and (not fuerte or m % 12 in pcs)
    ]
    cerca = [m for m in cand if abs(m - previa) <= 5] or cand
    w = []
    for m in cerca:
        p = np.exp(-abs(m - previa) / 2.0) * np.exp(-abs(m - centro) / 9)
        if m == previa:
            p *= 0.05
        if (m - previa) * direccion > 0:
            p *= 1.6
        w.append(p)
    w = np.array(w)
    return int(rng.choice(cerca, p=w / w.sum()))


def compas_melodia(rng, acorde, previa, seccion, direccion):
    lo, hi, centro = REGISTRO[seccion]
    pat = PATRONES[seccion][rng.integers(len(PATRONES[seccion]))]
    notas, t = [], 0.0
    for d in pat:
        if d < 0:
            t += -d
            continue
        fuerte = (t % 2 == 0) and d >= 1
        nueva = elegir_nota(
            rng, previa, ACORDES[acorde]["pcs"], fuerte, lo, hi, centro, direccion
        )
        if nueva != previa:
            direccion = 1 if nueva > previa else -1
        previa = nueva
        notas.append((previa, t, d))
        t += d
    return notas, previa, direccion


def frase(seccion, semilla, base=None):
    """4 compases de melodía. Si se da `base`, se repiten los 3 primeros
    compases y solo se recompone el último (variación)."""
    rng = np.random.default_rng(semilla)
    lo, hi, centro = REGISTRO[seccion]
    compases, previa, direccion = [], centro, 1
    for i, acorde in enumerate(PROG):
        if base is not None and i < 3:
            compases.append(base[i])
            if base[i]:
                previa = base[i][-1][0]
            continue
        notas, previa, direccion = compas_melodia(
            rng, acorde, previa, seccion, direccion
        )
        compases.append(notas)
    return compases


# ---------------------------------------------------------------- partitura
def partitura(semilla=3):
    """Devuelve (eventos, ritardando_desde, fin) con tiempos en 'tiempos'.
    evento = (midi, inicio, duración_hasta_pedal, velocidad)"""
    A = frase("A", semilla)
    A2 = frase("A", semilla + 1, base=A)
    B = frase("B", semilla + 2)
    B2 = frase("B", semilla + 3, base=B)
    estructura = [None, A, A2, B, B2, A, None]  # None = solo mano izquierda

    ev, tiempo = [], 0.0
    for ciclo, mel in enumerate(estructura):
        fuerte_mi = 0.52 if ciclo in (3, 4) else 0.45
        for c, nombre in enumerate(PROG):
            arp = ACORDES[nombre]["arp"]
            fin_pedal = tiempo + 4
            for j, idx in enumerate(PATRON_ARP):
                vel = fuerte_mi + (0.08 if j == 0 else 0.0)
                ev.append(
                    (arp[idx], tiempo + j * 0.5, fin_pedal - (tiempo + j * 0.5), vel)
                )
            if mel is not None:
                n = len(mel[c])
                for k, (m, t, d) in enumerate(mel[c]):
                    arco = 0.78 + 0.10 * np.sin(
                        np.pi * (c + t / 4) / 4
                    )  # arco dinámico
                    ev.append((m, tiempo + t, fin_pedal - (tiempo + t), arco))
            tiempo += 4

    # Compás final: Am arpegiado lentamente, con la nota aguda al final
    ritardando_desde = 6 * 16
    for i, m in enumerate([33, 45, 52, 57, 60, 64, 69]):
        ev.append((m, tiempo + i * 0.35, 12, 0.55))
    ev.append((76, tiempo + 3.2, 11, 0.6))
    return ev, ritardando_desde, tiempo + 4


# --------------------------------------------------------------- síntesis
def segundos(b, b0, bend, r=0.7):
    """Tiempo (en s) del tiempo musical b, con ritardando entre b0 y bend."""
    if b <= b0:
        return b * SP
    x = min(b - b0, bend - b0)
    s = b0 * SP + SP * (x + r * x * x / (2 * (bend - b0)))
    return s + max(b - bend, 0) * SP * (1 + r)


def piano(m, dur, vel):
    """Piano aditivo: parciales ligeramente inarmónicos que decaen más rápido
    cuanto más agudos; las notas graves duran más. `dur` = hasta levantar el pedal."""
    f = 440 * 2 ** ((m - 69) / 12)
    t = np.arange(int(sr * (dur + 0.5))) / sr
    tau0 = 8.0 * 2 ** (-(m - 45) / 24)  # constante de decaimiento (s)
    s = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 9000:
            break
        a = vel * k ** -(1.0 + (1 - vel) * 1.5)  # más suave = menos brillo
        s += a * np.sin(2 * np.pi * fk * t) * np.exp(-t / (tau0 / (1 + 0.6 * (k - 1))))
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1, np.exp(-(t - dur) * 9))
    return s * env


def reverb(x, rng, rt60=3.0):
    n = int(sr * rt60)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / (sr * rt60))
    ir = lfilter([0.25], [1, -0.75], ir)  # IR más oscura y cálida
    ir = np.concatenate([np.zeros(int(0.02 * sr)), ir])
    h = fftconvolve(x, ir)[: len(x)]
    return h * (np.abs(x).max() / np.abs(h).max())


def render(eventos, b0, bend, archivo, semilla=0):
    rng = np.random.default_rng(semilla)
    fin = max(segundos(t + d, b0, bend) for _, t, d, _ in eventos)
    total = int(sr * (fin + 4))
    izq, der = np.zeros(total), np.zeros(total)
    for m, t, d, vel in eventos:
        ini = segundos(t, b0, bend) + rng.normal(0, 0.006)  # humanización
        dur = segundos(t + d, b0, bend) - segundos(t, b0, bend)
        v = float(np.clip(vel + rng.normal(0, 0.04), 0.2, 1.0))
        s = piano(m, max(dur, 0.2), v)
        i = max(int(sr * ini), 0)
        pan = 0.3 + 0.4 * (m - 33) / 55  # graves a la izq.
        s = s[: total - i]
        izq[i : i + len(s)] += s * np.cos(pan * np.pi / 2)
        der[i : i + len(s)] += s * np.sin(pan * np.pi / 2)
    canales = [0.72 * x + 0.28 * reverb(x, rng) for x in (izq, der)]
    est = np.stack(canales, axis=1)
    est = est / np.abs(est).max() * 0.9
    wavfile.write(archivo, sr, (est * 32767).astype(np.int16))
    return fin


def wav_a_mp3(wav, mp3, kbps=192):
    import lameenc

    sr_, x = wavfile.read(wav)
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(sr_)
    enc.set_channels(x.shape[1])
    enc.set_quality(2)
    with open(mp3, "wb") as f:
        f.write(enc.encode(x.astype(np.int16).tobytes()) + enc.flush())


if __name__ == "__main__":
    ev, b0, bend = partitura(semilla=6)
    dur = render(ev, b0, bend, "winston.wav")
    wav_a_mp3("winston.wav", "winston.mp3")
    print(f"{len(ev)} notas, {dur:.0f} s -> winston.wav, winston.mp3")
