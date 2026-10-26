"""
Música generativa ambiental al estilo de Kitaro (Silk Road, Oasis).

  - Drone grave (Re - La - Re) con osciladores desafinados y filtro que respira.
  - Pads de ataque lento sobre Dm9 - Bbmaj7 - Fmaj7 - Cadd9, con unísonos
    desafinados repartidos en el estéreo.
  - Flauta pentatónica (Re menor) con vibrato tardío y soplo.
  - Pulso suave de pizzicatos sobre las notas del acorde, con eco ping-pong.
  - Reverb muy amplia. Duración: unos 3 minutos.

Requiere: numpy, scipy, lameenc (solo para mp3)

Notas de creación:
El script tarda cerca de un minuto en generarlo y escribe el MP3 con lameenc, como antes. No puedo oírlo: lo que comprobé es que el archivo es válido, que no hay saturación ni valores corruptos, y que la intensidad crece a lo largo de la pieza como se pretendía.

Cómo está hecho

Drone: Re2 - La2 - Re3 durante toda la pieza, con entrada de 10 s. Cada nota son tres osciladores de diente de sierra desafinados (−9, 0 y +8 cents) repartidos de izquierda a derecha. Un LFO muy lento (periodo de 11 a 25 s) abre y cierra el brillo, y esa lenta respiración es lo que da la sensación de movimiento sin cambiar de nota.
Pads: Dm9 - Bbmaj7 - Fmaj7 - Cadd9, 12 s por acorde y 3 vueltas. Tienen ataque lento de 3,5 s, y como cada pad dura más que su acorde, cada uno se funde con el siguiente sin cortes.
Flauta: tipo shakuhachi, en Re pentatónica menor (Re, Fa, Sol, La, Do), con una frase por acorde de 2 o 3 notas largas con silencios. Lleva vibrato que aparece tras medio segundo y un soplo de ruido filtrado. Usé la pentatónica porque funciona sobre los cuatro acordes sin choques.
Pulso: pizzicatos suaves sobre las notas de cada acorde, con eco ping-pong (alterna derecha e izquierda). La flauta tiene su propio eco, más lento.
Reverb: cola de 5 s, más oscura y cálida que la de las otras piezas.

Forma: el drone entra solo; la primera vuelta añade los pads; en la segunda aparecen la flauta (centrada en La4) y el pulso; en la tercera suben el volumen y la tesitura (centro en Re5); termina con un Dm9 largo, dos notas de flauta y desvanecimiento.

Para ajustar

CH cambia la duración de cada acorde, y CICLOS la longitud total.
En el pad, brillo=(0.3, 0.8) controla cuánto se abre el timbre. Valores más bajos dan algo más oscuro y más cercano a Kitaro de Oasis.
La reverb (rt60) y la mezcla seco/húmedo (0.62 / 0.38) son lo que más cambia el carácter. Si lo quieres más espacial, sube la parte húmeda.
Cambiando la semilla en componer(semilla=...) salen otras frases de flauta.
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve

sr = 44100
CH = 12.0  # duración de cada acorde (s)
T_INTRO = 10.0  # solo el drone
CICLOS = 3  # vueltas a la progresión

ACORDES = [  # (nombre, voicing MIDI)
    ("Dm9", [50, 57, 60, 65, 76]),
    ("Bbmaj7", [46, 53, 57, 62, 65]),
    ("Fmaj7", [41, 48, 57, 60, 64]),
    ("Cadd9", [48, 55, 62, 64, 67]),
]
PENTA = [62, 65, 67, 69, 72, 74, 77, 79, 81]  # Re pentatónica menor: D F G A C


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- pad / drone
def pad(notas, dur, rng, atk=3.5, rel=5.0, brillo=(0.3, 0.8), vel=1.0):
    """Cada nota = 3 osciladores 'diente de sierra' desafinados (-9, 0, +8
    cents), con un LFO lento que abre y cierra el brillo (más o menos
    armónicos), repartidos de izquierda a derecha. Devuelve (izq, der)."""
    n = int(sr * (dur + rel))
    t = np.arange(n) / sr
    izq, der = np.zeros(n), np.zeros(n)
    for m in notas:
        for cents, pan in ((-9, 0.25), (0, 0.5), (8, 0.75)):
            f = hz(m) * 2 ** (cents / 1200)
            fase = rng.uniform(0, 2 * np.pi)
            lfo = 0.5 + 0.5 * np.sin(
                2 * np.pi * rng.uniform(0.04, 0.09) * t + rng.uniform(0, 2 * np.pi)
            )
            b = brillo[0] + (brillo[1] - brillo[0]) * lfo
            r = np.exp(-1.2 * (1 - b))  # b alto -> armónicos agudos presentes
            amp, v = np.ones(n), np.zeros(n)
            for k in range(1, 9):
                if f * k > 8000:
                    break
                v += amp / k * np.sin(2 * np.pi * f * k * t + fase * k)
                amp = amp * r
            izq += v * np.cos(pan * np.pi / 2)
            der += v * np.sin(pan * np.pi / 2)
    ataque = np.sin(np.minimum(1, t / atk) * np.pi / 2) ** 2
    env = ataque * np.where(t < dur, 1, np.exp(-(t - dur) * 5 / rel))
    norm = vel / (len(notas) * 3)
    return izq * env * norm, der * env * norm


# -------------------------------------------------------------------- flauta
def flauta(m, dur, vel, rng):
    """Flauta tipo shakuhachi: vibrato que aparece tras 0,5 s y soplo."""
    f = hz(m)
    n = int(sr * (dur + 0.6))
    t = np.arange(n) / sr
    prof = 0.007 * np.clip((t - 0.5) / 1.0, 0, 1)  # profundidad del vibrato
    v_hz = 5.2
    fase = 2 * np.pi * f * t - (f * prof / v_hz) * np.cos(2 * np.pi * v_hz * t)
    s = np.sin(fase) + 0.30 * np.sin(2 * fase) + 0.12 * np.sin(3 * fase)
    b, a = butter(2, [1500 / (sr / 2), 4500 / (sr / 2)], btype="band")
    soplo = lfilter(b, a, rng.standard_normal(n)) * 0.10
    env = (
        np.minimum(1, t / 0.15)
        * (0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t))
        * np.where(t < dur, 1, np.exp(-(t - dur) * 8))
    )
    return (s + soplo) * env * vel


def pluck(m, vel):
    f = hz(m)
    t = np.arange(int(sr * 2.5)) / sr
    s = sum(
        a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.2 + 1.2 * k))
        for k, a in enumerate([1, 0.45, 0.25, 0.12, 0.06], 1)
    )
    return s * vel * np.minimum(1, t / 0.003)


# ------------------------------------------------------------------- partitura
def melodia(rng, t_ini, centro):
    """Una frase por acorde: 2-3 notas largas con silencios, en la pentatónica."""
    notas, t, idx = [], t_ini + rng.uniform(0.8, 2.0), centro
    fin = t_ini + CH - 1.0
    while True:
        d = float(rng.choice([2.0, 3.0, 4.0], p=[0.4, 0.4, 0.2]))
        if t + d > fin:
            break
        notas.append((PENTA[idx], t, d, float(rng.uniform(0.7, 0.95))))
        t += d + rng.uniform(0.3, 1.5)
        pasos = np.array([-2, -1, 1, 2])
        w = np.array([0.15, 0.35, 0.35, 0.15])
        w = w * np.exp(-np.abs(np.clip(idx + pasos, 0, 8) - centro) / 3)
        idx = int(np.clip(idx + rng.choice(pasos, p=w / w.sum()), 0, 8))
    return notas


def notas_de_acorde(voicing):
    """Notas del acorde llevadas a la zona 62-79 para el pulso."""
    out = set()
    for m in voicing:
        while m < 62:
            m += 12
        while m > 79:
            m -= 12
        out.add(m)
    return sorted(out)


# ---------------------------------------------------------------- mezcla
def poner(buf, senal, t0):
    i = int(t0 * sr)
    if i < len(buf):
        buf[i : i + len(senal)] += senal[: len(buf) - i]


def eco(x, retardo, fb, reps=6):
    """Eco ping-pong: las repeticiones alternan entre derecha e izquierda."""
    izq, der = 0.7 * x.copy(), 0.7 * x.copy()
    d = int(retardo * sr)
    for i in range(1, reps + 1):
        if i * d >= len(x):
            break
        sh = np.zeros_like(x)
        sh[i * d :] = x[: len(x) - i * d]
        if i % 2:
            der += fb**i * sh
        else:
            izq += fb**i * sh
    return izq, der


def reverb(x, rng, rt60=5.0):
    n = int(sr * rt60)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / (sr * rt60))
    ir = lfilter([0.2], [1, -0.8], ir)  # cola oscura y cálida
    ir = np.concatenate([np.zeros(int(0.03 * sr)), ir])
    h = fftconvolve(x, ir)[: len(x)]
    return h * (np.abs(x).max() / np.abs(h).max())


def componer(semilla=5, archivo="kitaro.wav"):
    rng = np.random.default_rng(semilla)
    t_acordes = T_INTRO + CICLOS * 4 * CH
    t_final = t_acordes + 20
    total = int(sr * (t_final + 12 + 4))

    pads = [np.zeros(total), np.zeros(total)]
    drone = [np.zeros(total), np.zeros(total)]
    mel, pul = np.zeros(total), np.zeros(total)

    # Drone: Re2 - La2 - Re3 durante toda la pieza
    l, r = pad([38, 45, 50], t_final, rng, atk=10, rel=12, brillo=(0.1, 0.4), vel=1.6)
    poner(drone[0], l, 0)
    poner(drone[1], r, 0)

    # Pads, melodía y pulso
    for i in range(CICLOS * 4):
        nombre, voicing = ACORDES[i % 4]
        t0 = T_INTRO + i * CH
        ciclo = i // 4
        vel = 0.9 + 0.1 * ciclo
        l, r = pad(voicing, CH + 2, rng, vel=vel)
        poner(pads[0], l, t0)
        poner(pads[1], r, t0)
        if ciclo >= 1:
            centro = 3 if ciclo == 1 else 5
            for m, t, d, v in melodia(rng, t0, centro):
                poner(mel, flauta(m, d, v, rng), t)
            tonos = notas_de_acorde(voicing)
            patron = [0, 2, 1, 3, 2, 4, 3, 1]
            for j in range(int(CH / 0.5)):
                m = tonos[patron[j % 8] % len(tonos)]
                v = (0.20 if ciclo == 1 else 0.28) * (1.15 if j % 8 == 0 else 1.0)
                poner(pul, pluck(m, v), t0 + j * 0.5)

    # Acorde final y nota larga de flauta
    l, r = pad(ACORDES[0][1], 20, rng, atk=4, rel=8, vel=1.1)
    poner(pads[0], l, t_acordes)
    poner(pads[1], r, t_acordes)
    poner(mel, flauta(74, 9, 0.85, rng), t_acordes + 1.5)
    poner(mel, flauta(69, 8, 0.7, rng), t_acordes + 11)

    # Mezcla: pads + drone + (flauta y pulso con eco) + reverb
    mel_l, mel_r = eco(mel * 0.9, 0.55, 0.45)
    pul_l, pul_r = eco(pul, 0.375, 0.40)
    canales = []
    for k, (ml, pl) in enumerate(((mel_l, pul_l), (mel_r, pul_r))):
        seco = pads[k] * 1.0 + drone[k] * 0.9 + ml + pl
        canales.append(0.62 * seco + 0.38 * reverb(seco, rng))
    est = np.stack(canales, axis=1)

    # Entrada y salida suaves
    n = len(est)
    fade = np.ones(n)
    fade[: int(4 * sr)] = np.linspace(0, 1, int(4 * sr)) ** 2
    fade[-int(10 * sr) :] = np.linspace(1, 0, int(10 * sr)) ** 2
    est = est * fade[:, None]
    est = est / np.abs(est).max() * 0.9
    wavfile.write(archivo, sr, (est * 32767).astype(np.int16))
    return n / sr


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
    dur = componer(semilla=5)
    wav_a_mp3("kitaro.wav", "kitaro.mp3")
    print(f"{dur:.0f} s -> kitaro.wav, kitaro.mp3")
