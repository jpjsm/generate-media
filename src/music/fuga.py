"""
Exposición de una fuga a tres voces en Re menor.

  1. Sujeto (alto)
  2. Respuesta a la quinta (soprano) + contrasujeto (alto)
  3. Sujeto (bajo) + contrasujeto (soprano) + voz libre (alto)

El contrasujeto y la voz libre se generan por búsqueda con retroceso
(backtracking) bajo reglas de contrapunto. El contrasujeto debe cumplirlas
contra la respuesta Y contra el sujeto del bajo (contrapunto invertible).

Requiere: numpy, scipy
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve

sr, bpm = 44100, 76
beat = 60 / bpm
PASO = 0.5  # rejilla de comprobación: corcheas
L = 8  # duración del sujeto, en tiempos
ESCALA = [0, 2, 3, 5, 7, 8, 10]  # Re menor natural
CONSONANCIAS = {0, 3, 4, 7, 8, 9}  # 8ª, 3as, 5ª, 6as (clase de intervalo)


def midi(grado, tonica=62):
    octava, i = divmod(int(grado), 7)
    return tonica + 12 * octava + ESCALA[i]


# ---------------------------------------------------------------- utilidades
def colocar(voz, despl, t0):
    """Transpone `despl` grados y desplaza `t0` tiempos."""
    return [(g + despl, t + t0, d) for g, t, d in voz]


def muestrear_midi(voz, t0, n):
    """Altura MIDI sonando en cada punto de la rejilla (NaN = silencio)."""
    arr = np.full(n, np.nan)
    for g, t, d in voz:
        k0, k1 = round((t - t0) / PASO), round((t + d - t0) / PASO)
        k0, k1 = max(k0, 0), min(k1, n)
        if k0 < k1:
            arr[k0:k1] = midi(g)
    return arr


def paralelos(v0, v1, p0, p1):
    """¿Quintas u octavas paralelas entre dos puntos consecutivos?"""
    if np.isnan([v0, v1, p0, p1]).any():
        return False
    if v0 == v1 or p0 == p1:  # una voz quieta: movimiento oblicuo
        return False
    if (v1 - v0) * (p1 - p0) <= 0:  # movimiento contrario
        return False
    i0, i1 = int(abs(v0 - p0)) % 12, int(abs(v1 - p1)) % 12
    return i0 == i1 and i0 in (0, 7)


def nota_de_paso(Pm, k):
    """Disonancia débil provocada por la pareja: ataca en k y entra por grado
    conjunto (<= 2 semitonos): nota de paso, floreo o escapada."""
    if k < 1 or np.isnan(Pm[k - 1 : k + 1]).any():
        return False
    return Pm[k] != Pm[k - 1] and abs(Pm[k] - Pm[k - 1]) <= 2


# -------------------------------------------------------------------- sujeto
def sujeto(semilla):
    """Sujeto de L tiempos: empieza y acaba en la tónica, salto inicial
    ascendente, un único punto culminante, cierre por grado conjunto."""
    rng = np.random.default_rng(semilla)
    while True:
        ritmo, t = [], 0.0
        while t < L - 2:
            ritmo += [0.5, 0.5] if rng.random() < 0.55 else [1.0]
            t += 1
        ritmo.append(2.0)
        n = len(ritmo)
        if n < 9:
            continue
        g = [0, int(rng.choice([2, 3, 4]))]
        for _ in range(n - 2):
            paso = rng.choice(
                [-2, -1, 1, 2, -3, 3], p=[0.12, 0.38, 0.3, 0.1, 0.05, 0.05]
            )
            g.append(g[-1] + int(paso))
        if g[-1] != 0 or g[-2] not in (-1, 1):
            continue
        if not (5 <= max(g) <= 7) or min(g) < -2 or g.count(max(g)) != 1:
            continue
        out, t = [], 0.0
        for gi, d in zip(g, ritmo):
            out.append((gi, t, d))
            t += d
        return out


# ------------------------------------------------------------- contrapunto
SALTOS = np.array([-4, -3, -2, -1, 1, 2, 3, 4])
PESOS = np.array([0.07, 0.08, 0.25, 0.6, 0.6, 0.25, 0.08, 0.07])
PESOS = PESOS / PESOS.sum()


def contrapunto(escenarios, ritmo, rango, semilla=0, max_nodos=60000, triada=(0, 2, 4)):
    """
    Genera una voz con el `ritmo` dado, válida en TODOS los escenarios.

    escenario = (despl, t0, parejas, previa)
        despl:   desplazamiento en grados de la voz en ese escenario
        t0:      tiempo en que empieza
        parejas: [(voz_ya_colocada, '<' | '>')]  la nueva voz queda
                 debajo ('<') o encima ('>') de esa pareja
        previa:  último grado (absoluto) que tocó esa voz antes, o None

    Reglas duras:
      - consonancia con todas las parejas en cada tiempo (negra);
      - en las corcheas débiles, disonancia solo como nota de paso/floreo
        (entrada y salida por grado conjunto);
      - sin quintas ni octavas paralelas (entre puntos consecutivos y
        entre tiempos consecutivos);
      - sin cruzamiento de voces;
      - saltos de hasta una quinta; tras un salto de 4ª o más, grado
        conjunto en dirección contraria;
      - la última nota pertenece a `triada` (grados mod 7; por defecto el
        acorde de Re menor; None = sin regla).
    """
    rng = np.random.default_rng(semilla)
    ks = np.concatenate([[0], np.cumsum([round(d / PASO) for d in ritmo])]).astype(int)
    n = int(ks[-1])
    prep = []
    for despl, t0, parejas, previa in escenarios:
        P = [(muestrear_midi(v, t0, n), lado) for v, lado in parejas]
        prep.append((despl, t0, P, previa, np.full(n, np.nan)))
    seq, obligado = [], []
    nodos = [0]

    def nota_ok(i, g):
        a, b = ks[i], ks[i + 1]
        disonante = False
        for despl, t0, P, previa, V in prep:
            m = midi(g + despl)
            if i == 0 and previa is not None and abs(g + despl - previa) > 4:
                return False, False
            if (
                triada is not None
                and i == len(ritmo) - 1
                and (g + despl) % 7 not in triada
            ):
                return False, False
            V[a:b] = m
            for k in range(a, b):
                t = t0 + k * PASO
                for Pm, lado in P:
                    p = Pm[k]
                    if np.isnan(p):
                        continue
                    if (lado == "<" and m >= p) or (lado == ">" and m <= p):
                        return False, False
                    if int(abs(m - p)) % 12 not in CONSONANCIAS:
                        if t % 1 == 0:  # tiempo: prohibido
                            return False, False
                        if k == a:  # la nueva voz ataca:
                            if i == 0 or abs(g - seq[i - 1]) > 1:
                                return False, False  # solo paso/floreo
                            disonante = True
                        elif not nota_de_paso(Pm, k):  # la nueva voz sostiene:
                            return (
                                False,
                                False,
                            )  # la pareja debe entrar por grado conjunto
                    previos = (k - 1, k - 2) if t % 1 == 0 else (k - 1,)
                    for kk in previos:
                        if kk >= 0 and paralelos(V[kk], m, Pm[kk], p):
                            return False, False
        return True, disonante

    def dfs(i):
        if i == len(ritmo):
            return True
        nodos[0] += 1
        if nodos[0] > max_nodos:
            return False
        if i == 0:
            cand = [int(x) for x in rng.permutation(np.arange(rango[0], rango[1] + 1))]
        else:
            prev = seq[i - 1]
            deltas = [
                int(d) for d in rng.choice(SALTOS, size=8, replace=False, p=PESOS)
            ]
            if i >= 2 and abs(prev - seq[i - 2]) >= 3:
                s = -int(np.sign(prev - seq[i - 2]))
                deltas = [d for d in deltas if d == s]
            if obligado[i - 1]:
                deltas = [d for d in deltas if abs(d) == 1]
            cand = [prev + d for d in deltas if rango[0] <= prev + d <= rango[1]]
        for g in cand:
            ok, dis = nota_ok(i, g)
            if ok:
                seq.append(g)
                obligado.append(dis)
                if dfs(i + 1):
                    return True
                seq.pop()
                obligado.pop()
        return False

    if not dfs(0):
        return None
    voz, t = [], 0.0
    for g, d in zip(seq, ritmo):
        voz.append((g, t, d))
        t += d
    return voz


# --------------------------------------------------------------- composición
def componer(semilla=1, intentos=200):
    ritmo_cs = [0.5] * (2 * (L - 1)) + [1.0]  # corcheas continuas
    ritmo_libre = [1.0] * L  # negras

    for s in range(semilla, semilla + intentos):
        S = sujeto(s)
        sujeto_alto = colocar(S, 0, 0)
        respuesta = colocar(S, 4, L)  # a la quinta, soprano
        sujeto_bajo = colocar(S, -7, 2 * L)  # una octava abajo

        # Contrasujeto: debe funcionar bajo la respuesta (alto, t=L)
        # y sobre el sujeto del bajo (soprano, +una octava, t=2L).
        # Se piden varias soluciones distintas hasta dar con una con perfil
        # melódico (no un vaivén sobre dos o tres notas).
        cs = None
        for v in range(40):
            cand = contrapunto(
                [
                    (0, L, [(respuesta, "<")], sujeto_alto[-1][0]),
                    (7, 2 * L, [(sujeto_bajo, ">")], respuesta[-1][0]),
                ],
                ritmo_cs,
                rango=(-2, 6),
                semilla=1000 * s + v,
            )
            if cand is None:
                break
            gs = [g for g, _, _ in cand]
            if len(set(gs)) >= 5 and max(gs) - min(gs) >= 4:
                cs = cand
                break
        if cs is None:
            continue
        cs_alto = colocar(cs, 0, L)
        cs_sop = colocar(cs, 7, 2 * L)

        # Voz libre (alto, t=2L): entre el contrasujeto y el bajo.
        libre = contrapunto(
            [(0, 2 * L, [(cs_sop, "<"), (sujeto_bajo, ">")], cs_alto[-1][0])],
            ritmo_libre,
            rango=(-4, 6),
            semilla=s,
        )
        if libre is None:
            continue
        libre = colocar(libre, 0, 2 * L)

        return s, {
            "soprano": respuesta + cs_sop,
            "alto": sujeto_alto + cs_alto + libre,
            "bajo": sujeto_bajo,
        }
    raise RuntimeError("No se encontró solución; prueba otra semilla.")


def verificar(voces):
    """Recuenta fallos en toda la pieza, par de voces por par de voces."""
    fin = max(t + d for v in voces.values() for _, t, d in v)
    n = int(fin / PASO)
    S = {k: muestrear_midi(v, 0, n) for k, v in voces.items()}
    nombres = list(S)
    fallos = {"disonancias en tiempo": 0, "quintas/octavas paralelas": 0}
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = S[nombres[i]], S[nombres[j]]
            for k in range(n):
                if np.isnan(a[k]) or np.isnan(b[k]):
                    continue
                t = k * PASO
                if t % 1 == 0 and int(abs(a[k] - b[k])) % 12 not in CONSONANCIAS:
                    fallos["disonancias en tiempo"] += 1
                for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
                    if kk >= 0 and paralelos(a[kk], a[k], b[kk], b[k]):
                        fallos["quintas/octavas paralelas"] += 1
    return fallos


# ---------------------------------------------------------------- síntesis
def tono(m, dur):
    """Timbre tipo órgano: ataque corto, sostenido, relajación breve."""
    f = 440 * 2 ** ((m - 69) / 12)
    dur *= 0.97
    t = np.arange(int(sr * (dur + 0.3))) / sr
    s = sum(
        a * np.sin(2 * np.pi * f * k * t)
        for k, a in enumerate([1, 0.6, 0.4, 0.25, 0.15, 0.1], 1)
    )
    env = np.minimum(1, t / 0.01) * np.where(t < dur, 1, np.exp(-(t - dur) * 20))
    return s * env * 0.12


def render(voces, archivo, panorama={"soprano": 0.7, "alto": 0.5, "bajo": 0.3}):
    fin = max(t + d for v in voces.values() for _, t, d in v) * beat
    total = int(sr * (fin + 4))
    izq, der = np.zeros(total), np.zeros(total)
    for nombre, notas in voces.items():
        buf = np.zeros(total)
        for g, t, d in notas:
            s = tono(midi(g), d * beat)
            i = int(sr * beat * t)
            buf[i : i + len(s)] += s[: total - i]
        izq += buf * np.cos(panorama[nombre] * np.pi / 2)
        der += buf * np.sin(panorama[nombre] * np.pi / 2)

    rng = np.random.default_rng(0)
    canales = []
    for x in (izq, der):  # reverb ligeramente distinta por canal
        ir = rng.standard_normal(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 2.5)
        humedo = fftconvolve(x, ir)[:total]
        humedo *= np.abs(x).max() / np.abs(humedo).max()
        canales.append(0.75 * x + 0.25 * humedo)
    est = np.stack(canales, axis=1)
    wavfile.write(archivo, sr, (est / np.abs(est).max() * 32767).astype(np.int16))


if __name__ == "__main__":
    semilla, voces = componer(semilla=7)
    print(f"Semilla del sujeto: {semilla}")
    print("Verificación:", verificar(voces))
    render(voces, "fuga.wav")
    print("Escrito fuga.wav")
