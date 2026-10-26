"""
Música generativa de estilo cinematográfico, al modo de Yanni
(Santorini, Reflections of Passion, Aria).

Forma (4/4, 84 negras por minuto):
  introducción (4 compases)  piano solo, ostinato de corcheas
  A  (8)                     melodía en el piano; entra el violonchelo
  B  (8)                     violín solista, cuerdas, timbales
  puente (8)                 secuencia ascendente que acaba en el dominante
                             de la nueva tonalidad (Si mayor)
  final (8)                  un tono arriba (Re menor -> Mi menor), todo el
                             conjunto, platillos y timbales
  coda (4)                   ritardando y acorde final

Requiere: numpy, scipy, lameenc (solo para mp3)

Notas de creación:

El script tarda unos 40 s en generarlo y escribe el MP3 con lameenc. Como siempre, no puedo oírlo: comprobé que las melodías cumplen las reglas, que el archivo es válido, que no hay saturación y que la intensidad sube hacia el final como se pretendía.

La forma (4/4, 84 negras por minuto)

Introducción (4 compases): piano solo, con bajo en octavas y un ostinato de corcheas sobre Dm – Bb – F – C.
A (8): la melodía la toca el piano, con notas largas y espaciadas, y a mitad entra el violonchelo.
B (8): el violín solista toma la melodía, con cuerdas y timbales suaves.
Puente (8): una secuencia ascendente (el mismo dibujo melódico sube un grado sobre cada acorde) por Bb – C – Dm – Gm – Bb – C – Am. Acaba en Si mayor, que es el dominante de Mi menor.
Final (8): cambio de tonalidad un tono arriba, de Re menor a Mi menor, como en los finales típicos de Yanni. Entran todos los instrumentos, el violín repite la melodía de B, el piano la dobla una octava abajo, y hay timbales y un platillo. Antes de este momento hay un redoble de timbales que crece durante un compás y un platillo que crece durante 6 tiempos hasta el golpe.
Coda (4): notas largas del violín, ritardando y un acorde final de Mi menor arpegiado.

Cómo se genera la melodía

Cada frase de 4 compases es: motivo, respuesta, el motivo repetido sobre el tercer acorde (una secuencia, como hacía Bach) y una cadencia que termina en una nota del acorde. Los tiempos fuertes caen siempre sobre notas del acorde y los débiles pueden ser notas de paso. La segunda mitad de A y de B repite los tres primeros compases y cambia solo la cadencia. Probé 8 semillas, y en todas hubo 0 fallos en los tiempos fuertes. Elegí la semilla 1 porque tiene un perfil melódico claro: sin notas repetidas y con un puente que sube limpiamente. La semilla 7, mi primera opción, tenía el mismo ritmo [3,1] en casi todos los compases y sonaba monótona.

Qué suena a qué

El piano es el mismo del estilo Winston. Las cuerdas, el violín y el violonchelo son osciladores en conjunto (3 voces desafinadas ±6 cents), con vibrato que aparece tras 0,4 s en el violín. Los timbales tienen un barrido de afinación y un golpe de ruido, y el platillo es ruido filtrado con un crescendo. Hay dos reverbs: una más corta para el piano y otra de sala grande para la orquesta.

Para ajustar

BPM cambia el tempo, y partitura(semilla=...) da melodías distintas.
PROG_A, PROG_P y PROG_C son las progresiones. Si quieres otro cambio de tonalidad, cambia la trans de las secciones final y coda (2 = un tono; 3 = tercera menor).
Las velocidades de cada sección están en vel_arp y en los diccionarios de cuerdas y timbal. Ahí se regula cuánto crece el final.

Con esto quedan hechos Winston, Kitaro y Yanni.
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve

sr = 44100
BPM = 84
SP = 60 / BPM
ESC_PCS = {2, 4, 5, 7, 9, 10, 0}  # Re menor natural: D E F G A Bb C

# Acorde = (fundamental en semitonos sobre Re, 'm' | 'M')
PROG_A = [(0, "m"), (-4, "M"), (3, "M"), (-2, "M")]  # Dm Bb F C
PROG_P = [
    (-4, "M"),
    (-2, "M"),
    (0, "m"),
    (5, "m"),
    (-4, "M"),
    (-2, "M"),
    (7, "m"),
    (9, "M"),
]  # Bb C Dm Gm Bb C Am B
PROG_C = [(0, "m"), (-4, "M"), (-2, "M"), (0, "m")]  # Dm Bb C Dm

SECCIONES = [  # (nombre, progresión, transposición)
    ("intro", PROG_A, 0),
    ("A", PROG_A * 2, 0),
    ("B", PROG_A * 2, 0),
    ("puente", PROG_P, 0),
    ("final", PROG_A * 2, 2),
    ("coda", PROG_C, 2),
]
RANGO = {
    "A": (69, 84, 76),
    "B": (72, 88, 79),
    "puente": (70, 86, 78),
}  # (min, max, centro)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tonos_pc(ac):
    raiz = (2 + ac[0]) % 12
    return {raiz, (raiz + (3 if ac[1] == "m" else 4)) % 12, (raiz + 7) % 12}


def notas_escala(lo, hi):
    return [m for m in range(lo, hi + 1) if m % 12 in ESC_PCS]


def notas_acorde(ac, lo, hi):
    pcs = tonos_pc(ac)
    return [m for m in range(lo, hi + 1) if m % 12 in pcs]


# ---------------------------------------------------------------- melodía
RITMOS = [
    [1.5, 0.5, 1, 1],
    [2, 1, 1],
    [1, 1, 2],
    [3, 1],
    [1, 0.5, 0.5, 2],
    [1, 1, 1, 1],
    [0.5, 0.5, 1, 2],
]


def es_fuerte(t, d):
    return t % 2 == 0 or (t % 1 == 0 and d >= 2)


def elegir(rng, previa, permitidas, centro, direccion, salto):
    cerca = [m for m in permitidas if abs(m - previa) <= salto] or permitidas
    w = []
    for m in cerca:
        p = np.exp(-abs(m - previa) / 2.0) * np.exp(-abs(m - centro) / 8)
        if m == previa:
            p *= 0.05
        if (m - previa) * direccion > 0:
            p *= 1.5
        w.append(p)
    w = np.array(w)
    return int(rng.choice(cerca, p=w / w.sum()))


def barra(rng, ac, previa, rango, direccion, ritmo=None, solo_acorde=False, salto=7):
    """Un compás de melodía: tiempos fuertes sobre notas del acorde."""
    lo, hi, centro = rango
    ritmo = ritmo or RITMOS[rng.integers(len(RITMOS))]
    notas, t = [], 0.0
    for d in ritmo:
        perm = (
            notas_acorde(ac, lo, hi)
            if (es_fuerte(t, d) or solo_acorde)
            else notas_escala(lo, hi)
        )
        nueva = elegir(rng, previa, perm, centro, direccion, salto)
        if nueva != previa:
            direccion = 1 if nueva > previa else -1
        previa = nueva
        notas.append((nueva, t, d))
        t += d
    return notas, previa, direccion


def secuenciar(base, ac, rango, desplaza):
    """Repite el dibujo melódico de `base` (mismo ritmo, mismos intervalos en
    grados de la escala) sobre otro acorde, `desplaza` grados más arriba."""
    lo, hi, _ = rango
    esc = notas_escala(lo - 12, hi + 12)
    idx = [esc.index(m) for m, _, _ in base]
    objetivo = esc[min(max(idx[0] + desplaza, 0), len(esc) - 1)]
    ancla = min(notas_acorde(ac, lo - 12, hi + 12), key=lambda m: abs(m - objetivo))
    shift = esc.index(ancla) - idx[0]
    dentro = notas_escala(lo, hi)
    out = []
    for (m, t, d), i in zip(base, idx):
        n = esc[min(max(i + shift, 0), len(esc) - 1)]
        n = min(dentro, key=lambda x: abs(x - n))
        if es_fuerte(t, d) and n % 12 not in tonos_pc(ac):
            n = min(notas_acorde(ac, lo, hi), key=lambda x: abs(x - n))
        out.append((n, t, d))
    return out


def cadencia(rng, ac, previa, rango, direccion=-1):
    ritmo = [[2, 2], [3, 1], [1, 1, 2]][rng.integers(3)]
    notas, _, _ = barra(rng, ac, previa, rango, direccion, ritmo=ritmo)
    m, t, d = notas[-1]  # la última nota, siempre del acorde
    if m % 12 not in tonos_pc(ac):
        m = min(notas_acorde(ac, rango[0], rango[1]), key=lambda x: abs(x - m))
    notas[-1] = (m, t, d)
    return notas


def frase(rng, acs, rango):
    """4 compases: motivo, respuesta, secuencia del motivo, cadencia."""
    centro = rango[2]
    b0, p, dr = barra(rng, acs[0], centro, rango, 1, salto=9)
    b1, p, dr = barra(rng, acs[1], p, rango, dr)
    b2 = secuenciar(b0, acs[2], rango, 1)
    b3 = cadencia(rng, acs[3], b2[-1][0], rango)
    return [b0, b1, b2, b3]


def variar(rng, base, acs, rango):
    """Mismos tres primeros compases, cadencia nueva."""
    return base[:3] + [cadencia(rng, acs[3], base[2][-1][0], rango)]


def melodia_puente(rng, acs, rango):
    b0, p, dr = barra(rng, acs[0], rango[2] - 4, rango, 1)
    b1 = secuenciar(b0, acs[1], rango, 1)
    b2 = secuenciar(b0, acs[2], rango, 2)
    b3 = secuenciar(b0, acs[3], rango, 3)
    b4, p, dr = barra(rng, acs[4], b3[-1][0], rango, 1, salto=9)
    b5 = secuenciar(b4, acs[5], rango, 1)
    b6, p, dr = barra(rng, acs[6], b5[-1][0], rango, dr)
    b7, _, _ = barra(rng, acs[7], b6[-1][0], rango, dr, ritmo=[2, 2], solo_acorde=True)
    return [b0, b1, b2, b3, b4, b5, b6, b7]


def melodias(semilla):
    rng = np.random.default_rng(semilla)
    pa = frase(rng, PROG_A, RANGO["A"])
    pb = frase(rng, PROG_A, RANGO["B"])
    return {
        "A": pa + variar(rng, pa, PROG_A, RANGO["A"]),
        "B": pb + variar(rng, pb, PROG_A, RANGO["B"]),
        "puente": melodia_puente(rng, PROG_P, RANGO["puente"]),
    }


# ---------------------------------------------------------------- partitura
def partitura(semilla=1):
    """Eventos (instrumento, midi, inicio, duración, velocidad, panorama),
    todo en tiempos musicales. Devuelve también el índice de tiempo del
    inicio del ritardando y el final."""
    mel = melodias(semilla)
    ev = []
    compas = 0
    inicio = {}
    ritmo_arp = [0, 1, 2, 3, 2, 3, 2, 1]
    vel_arp = {
        "intro": 0.50,
        "A": 0.55,
        "B": 0.50,
        "puente": 0.55,
        "final": 0.66,
        "coda": 0.50,
    }

    for nombre, prog, trans in SECCIONES:
        inicio[nombre] = compas
        for i, ac in enumerate(prog):
            t0 = 4 * compas
            raiz_pc = (2 + ac[0]) % 12
            pcs = tonos_pc(ac)
            graves = 36 + ((raiz_pc - 36) % 12)
            # Piano: bajo en octavas y ostinato de corcheas
            ev.append(("piano", graves + trans, t0, 4, 0.75, None))
            ev.append(("piano", graves + 12 + trans, t0, 4, 0.55, None))
            arp = [m for m in range(53, 80) if m % 12 in pcs][:4]
            for j, k in enumerate(ritmo_arp):
                v = vel_arp[nombre] + (0.08 if j == 0 else 0)
                ev.append(("piano", arp[k] + trans, t0 + j * 0.5, 4 - j * 0.5, v, None))
            # Orquesta
            if nombre in ("B", "puente", "final", "coda") or (nombre == "A" and i >= 4):
                ev.append(
                    (
                        "cello",
                        graves + trans,
                        t0,
                        4,
                        0.75 if nombre == "final" else 0.55,
                        0.38,
                    )
                )
            if nombre in ("B", "puente", "final", "coda"):
                v = {"B": 0.30, "puente": 0.38, "final": 0.64, "coda": 0.36}[nombre]
                for q, m in enumerate(m for m in range(55, 71) if m % 12 in pcs):
                    ev.append(("cuerdas", m + trans, t0, 4, v, 0.30 + 0.40 * (q % 2)))
            # Timbales
            if nombre in ("B", "puente", "final"):
                tim = 38 + ((raiz_pc - 38) % 12)
                v = {"B": 0.45, "puente": 0.55, "final": 0.92}[nombre]
                ev.append(("timbal", tim + trans, t0, 0, v, 0.5))
                if nombre in ("puente", "final"):
                    ev.append(("timbal", tim + trans, t0 + 2, 0, v * 0.8, 0.5))
            compas += 1

    # Melodía
    for nombre, secuencia in (
        ("A", mel["A"]),
        ("B", mel["B"]),
        ("puente", mel["puente"]),
        ("final", mel["B"]),
    ):
        trans = 2 if nombre == "final" else 0
        for c, notas in enumerate(secuencia):
            t0 = 4 * (inicio[nombre] + c)
            for m, t, d in notas:
                if nombre == "A":
                    ev.append(("piano", m, t0 + t, 4 - t, 0.85, None))
                else:
                    ev.append(
                        (
                            "violin",
                            m + trans,
                            t0 + t,
                            d,
                            0.85 if nombre != "final" else 0.95,
                            0.58,
                        )
                    )
                if nombre == "final":
                    ev.append(("piano", m + trans - 12, t0 + t, 4 - t, 0.70, None))

    # Coda: notas largas (en Mi menor: Fa#, Mi, Re, Mi)
    for c, m in enumerate([77, 74, 72, 74]):
        ev.append(("violin", m + 2, 4 * (inicio["coda"] + c), 4, 0.75, 0.58))

    # Percusión: platillos y redoble de timbales hacia el cambio de tonalidad
    t_final = 4 * inicio["final"]
    ev.append(("platillo", 0, 4 * inicio["B"] - 1, 1, 0.30, 0.5))  # entrada de B
    ev.append(("platillo", 0, t_final - 6, 6, 0.55, 0.5))  # crescendo + golpe
    for k in range(16):  # redoble en E2
        ev.append(("timbal", 40, t_final - 4 + k * 0.25, 0, 0.30 + 0.60 * k / 15, 0.5))

    # Acorde final de Mi menor, arpegiado
    t_fin = 4 * (inicio["coda"] + 4)
    for q, m in enumerate([40, 52, 59, 64, 67, 71]):
        ev.append(("piano", m, t_fin + q * 0.3, 12, 0.65, None))
        ev.append(
            (
                "cuerdas",
                m + 12 if m > 50 else m,
                t_fin + q * 0.3,
                10,
                0.40,
                0.30 + 0.40 * (q % 2),
            )
        )
    ev.append(("violin", 76, t_fin + 1.8, 10, 0.70, 0.58))
    ev.append(("timbal", 40, t_fin, 0, 0.5, 0.5))

    return ev, 4 * (inicio["coda"] + 2), t_fin + 4


# --------------------------------------------------------------- síntesis
def piano(m, dur, vel):
    f = hz(m)
    t = np.arange(int(sr * (dur + 0.5))) / sr
    tau0 = 8.0 * 2 ** (-(m - 45) / 24)
    s = np.zeros_like(t)
    for k in range(1, 8):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 9000:
            break
        a = vel * k ** -(1.0 + (1 - vel) * 1.5)
        s += a * np.sin(2 * np.pi * fk * t) * np.exp(-t / (tau0 / (1 + 0.6 * (k - 1))))
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1, np.exp(-(t - dur) * 9))
    return s * env


def cuerda(m, dur, vel, atk, rel, arm, vib, rng):
    """Conjunto de cuerdas: 3 voces desafinadas, con vibrato opcional."""
    f = hz(m)
    n = int(sr * (dur + rel))
    t = np.arange(n) / sr
    s = np.zeros(n)
    for cents in (-6, 0, 6):
        fc = f * 2 ** (cents / 1200)
        v_hz = 5.3 + rng.uniform(-0.25, 0.25)
        dev = vib * np.clip((t - 0.4) / 0.8, 0, 1)
        fase = (
            2 * np.pi * fc * t
            - (fc * dev / v_hz) * np.cos(2 * np.pi * v_hz * t)
            + rng.uniform(0, 2 * np.pi)
        )
        for k in range(1, arm + 1):
            if fc * k > 9000:
                break
            s += np.sin(k * fase) / k**1.1
    env = np.minimum(1, t / atk) ** 1.5 * np.where(
        t < dur, 1, np.exp(-(t - dur) * 5 / rel)
    )
    return s * env * vel / 3


def timbal(m, vel, rng):
    f0 = hz(m)
    t = np.arange(int(sr * 2.5)) / sr
    f = f0 * (1 + 0.35 * np.exp(-t / 0.06))
    fase = 2 * np.pi * np.cumsum(f) / sr
    s = np.sin(fase) * np.exp(-t / 0.9) + 0.4 * np.sin(2 * fase) * np.exp(-t / 0.5)
    b, a = butter(2, 600 / (sr / 2))
    golpe = lfilter(b, a, rng.standard_normal(len(t))) * np.exp(-t / 0.02) * 0.8
    return (s + golpe) * vel * 0.8


def platillo(dur_swell, vel, rng):
    """Redoble de platillo que crece durante `dur_swell` s y termina en golpe."""
    n = int(sr * (dur_swell + 3.5))
    t = np.arange(n) / sr
    b, a = butter(2, 4500 / (sr / 2), btype="high")
    ruido = lfilter(b, a, rng.standard_normal(n))
    env = np.where(
        t < dur_swell, 0.5 * (t / dur_swell) ** 2, np.exp(-(t - dur_swell) * 1.3)
    )
    return ruido * env * vel * 0.5


def reverb(x, rng, rt60, oscuro=0.8):
    n = int(sr * rt60)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / (sr * rt60))
    ir = lfilter([1 - oscuro], [1, -oscuro], ir)
    ir = np.concatenate([np.zeros(int(0.025 * sr)), ir])
    h = fftconvolve(x, ir)[: len(x)]
    return h * (np.abs(x).max() / max(np.abs(h).max(), 1e-9))


def segundos(b, b0, bend, r=0.8):
    """Segundos del tiempo musical b, con ritardando entre b0 y bend."""
    if b <= b0:
        return b * SP
    x = min(b - b0, bend - b0)
    s = b0 * SP + SP * (x + r * x * x / (2 * (bend - b0)))
    return s + max(b - bend, 0) * SP * (1 + r)


def render(ev, b0, bend, archivo, semilla=0):
    rng = np.random.default_rng(semilla)
    fin = max(segundos(t + d, b0, bend) for _, _, t, d, _, _ in ev)
    total = int(sr * (fin + 8))
    buses = {
        "piano": [np.zeros(total), np.zeros(total)],
        "orq": [np.zeros(total), np.zeros(total)],
    }

    for inst, m, t, d, vel, pan in ev:
        ini = segundos(t, b0, bend) + (rng.normal(0, 0.005) if inst == "piano" else 0)
        dur = max(segundos(t + d, b0, bend) - segundos(t, b0, bend), 0.15)
        v = float(np.clip(vel + rng.normal(0, 0.03), 0.1, 1.0))
        if inst == "piano":
            s = piano(m, dur, v)
            p = 0.30 + 0.40 * (m - 33) / 55 if pan is None else pan
            bus = "piano"
        else:
            bus = "orq"
            p = pan if pan is not None else 0.5
            if inst == "violin":
                s = cuerda(m, dur * 0.98, v, 0.10, 0.35, 9, 0.010, rng) * 1.1
            elif inst == "cuerdas":
                s = cuerda(m, dur, v, 0.7, 0.9, 5, 0.0, rng)
            elif inst == "cello":
                s = cuerda(m, dur, v, 0.20, 0.5, 6, 0.004, rng) * 1.3
            elif inst == "timbal":
                s = timbal(m, v, rng)
            else:  # platillo: t = comienzo del redoble
                dur_s = segundos(t + d, b0, bend) - segundos(t, b0, bend)
                s = platillo(dur_s, v, rng)
        i = max(int(sr * ini), 0)
        s = s[: total - i]
        L, R = buses[bus]
        L[i : i + len(s)] += s * np.cos(p * np.pi / 2)
        R[i : i + len(s)] += s * np.sin(p * np.pi / 2)

    canales = []
    for k in (0, 1):
        pi, orq = buses["piano"][k], buses["orq"][k]
        canales.append(
            0.80 * pi
            + 0.20 * reverb(pi, rng, 2.8)
            + 0.66 * orq
            + 0.34 * reverb(orq, rng, 3.8) * 0.9
        )
    est = np.stack(canales, axis=1)
    fade = np.ones(len(est))
    fade[: int(0.3 * sr)] = np.linspace(0, 1, int(0.3 * sr))
    fade[-int(6 * sr) :] = np.linspace(1, 0, int(6 * sr)) ** 2
    est = est * fade[:, None]
    est = est / np.abs(est).max() * 0.9
    wavfile.write(archivo, sr, (est * 32767).astype(np.int16))
    return len(est) / sr


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
    ev, b0, bend = partitura(semilla=1)
    dur = render(ev, b0, bend, "yanni.wav")
    wav_a_mp3("yanni.wav", "yanni.mp3")
    print(f"{len(ev)} eventos, {dur:.0f} s -> yanni.wav, yanni.mp3")
