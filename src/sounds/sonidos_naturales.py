"""
Sonidos naturales (y alguno no tanto) por síntesis, sin muestras grabadas.

  olas             oleaje con espuma
  rio              agua de río: caudal profundo y burbujas grandes
  arroyo           agua de arroyo: más burbujas, más pequeñas y brillantes
  cascada          caudal ancho y brillante
  viento_bosque    ráfagas con hojas y silbido entre ramas
  lluvia_suave     lluvia fina con goteo de hojas y charcos
  tormenta         lluvia intensa que se acerca, pasa por encima y se aleja
  campanas_metal   campanas de viento de tubo metálico (pentatónica)
  campanas_madera  campanas de viento de madera/bambú
  fuego            fuego de leña con chasquidos
  goteo_cueva      gotas en una cueva con reverb larga
  grillos          noche de verano
  bosque_nocturno  mezcla: arroyo + viento suave + grillos

Técnicas: ruido de color (espectro 1/f^beta), modulación aleatoria lenta
(ráfagas), modelo de burbuja de Minnaert para el agua, tomas de Poisson para
gotas y chasquidos, síntesis modal para las campanas.

Uso:  python sonidos_naturales.py                 (todos, con duración de muestra)
      python sonidos_naturales.py rio tormenta    (solo algunos)
      python sonidos_naturales.py rio --dur 120 --semilla 3

Requiere: numpy, scipy, lameenc (para mp3)
"""

import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve, lfilter

sr = 44100


# ------------------------------------------------------------------ utilidades
def _sos(lo, hi, orden):
    ny = sr / 2
    if lo and hi:
        return butter(orden, [lo / ny, min(hi, 0.98 * ny) / ny], "band", output="sos")
    if hi:
        return butter(orden, min(hi, 0.98 * ny) / ny, "low", output="sos")
    return butter(orden, lo / ny, "high", output="sos")


def banda(x, lo=None, hi=None, orden=2):
    """Filtro paso banda (lo y hi), paso bajo (solo hi) o paso alto (solo lo)."""
    return sosfilt(_sos(lo, hi, orden), x)


def unit(x):
    """Normaliza a valor eficaz (RMS) 1."""
    return x / (np.sqrt(np.mean(x**2)) + 1e-12)


def ruido_color(n, beta, rng):
    """Ruido con densidad espectral de potencia ~ 1/f^beta
    (0 = blanco, 1 = rosa, 2 = marrón)."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / sr)
    f[0] = f[1]
    X *= f ** (-beta / 2)
    X[0] = 0
    return unit(np.fft.irfft(X, n))


def lento(n, rng, tau, fs=100):
    """Variación aleatoria suave (tiempo característico ~tau s), media 0, desvío 1."""
    m = int(n / sr * fs) + 4
    y = sosfilt(butter(2, (1.0 / tau) / (fs / 2), output="sos"), rng.standard_normal(m))
    y = (y - y.mean()) / (y.std() + 1e-12)
    return np.interp(np.arange(n) / sr, np.arange(m) / fs, y)


def rafaga(n, rng, tau, sesgo=0.3):
    """0 = calma, 1 = racha fuerte; las rachas son escasas y suaves."""
    return 1 / (1 + np.exp(-1.8 * (lento(n, rng, tau) - sesgo)))


def tren(n, rng, tasa, amp_exp=1.0):
    """Impulsos de Poisson (`tasa` por segundo, escalar o array) con amplitud
    aleatoria de cola pesada."""
    return (rng.random(n) < np.clip(tasa / sr, 0, 0.5)) * rng.exponential(
        1.0, n
    ) ** amp_exp


def suma(a, b):
    """Suma dos señales de distinta longitud (la corta se rellena con ceros)."""
    out = np.zeros(max(len(a), len(b)))
    out[: len(a)] += a
    out[: len(b)] += b
    return out


def poner(buf, s, i):
    if i >= len(buf) or i + len(s) <= 0:
        return
    a = max(0, -i)
    s, i = s[a:], max(i, 0)
    buf[i : i + len(s)] += s[: len(buf) - i]


def paneo(x, p):
    return x * np.cos(p * np.pi / 2), x * np.sin(p * np.pi / 2)


def reverb(x, rng, rt60, oscuro=0.75):
    n = int(sr * rt60)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / (sr * rt60))
    ir = lfilter([1 - oscuro], [1, -oscuro], ir)
    h = fftconvolve(x, ir)[: len(x)]
    return h * (np.sqrt(np.mean(x**2)) / (np.sqrt(np.mean(h**2)) + 1e-12))


def acabar(
    L,
    R,
    modo="rms",
    objetivo=0.10,
    entrada=2.0,
    salida=3.0,
    rng=None,
    rt60=None,
    mezcla=0.0,
):
    """Reverb opcional, normalización (por RMS o por pico), entrada y salida suaves."""
    if rt60:
        L = (1 - mezcla) * L + mezcla * reverb(L, rng, rt60)
        R = (1 - mezcla) * R + mezcla * reverb(R, rng, rt60)
    est = np.stack([L, R], axis=1)
    if modo == "rms":
        est = est * objetivo / (np.sqrt(np.mean(est**2)) + 1e-12)
        est = 0.9 * np.tanh(est / 0.9)  # limitador suave: techo en 0,9
    else:
        est = est / (np.abs(est).max() + 1e-12) * objetivo
    n = len(est)
    fade = np.ones(n)
    a, b = int(entrada * sr), int(salida * sr)
    fade[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    fade[-b:] = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return est * fade[:, None]


# ------------------------------------------------------------ piezas básicas
def burbuja(f0, amp):
    """Burbuja de aire en el agua (Minnaert / van den Doel): senoide amortiguada
    cuya frecuencia sube ~10 % mientras se extingue. f0 ~ 3,26 / radio(m) Hz."""
    d = 0.043 * f0 + 0.0014 * f0**1.5
    n = int(sr * min(8 / d, 0.25)) + 1
    t = np.arange(n) / sr
    fase = 2 * np.pi * np.cumsum(f0 * (1 + 0.1 * d * t)) / sr
    return amp * np.sin(fase) * np.exp(-d * t)


def ping(f, tau, amp, rng=None, ruido=0.0):
    t = np.arange(int(sr * 8 * tau)) / sr
    s = np.sin(2 * np.pi * f * t)
    if ruido:
        s = s + ruido * rng.standard_normal(len(t))
    return amp * s * np.exp(-t / tau)


# ----------------------------------------------------------------------- olas
def olas(dur, semilla=1, periodo=(6.5, 11.0)):
    """Cada ola: rumor grave que crece ~5 s, cresta y decae; la espuma (siseo
    agudo) llega con la cresta y se apaga antes. Cada ola recorre la playa
    (el panorama se desplaza)."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    gr = [unit(banda(ruido_color(n, 2.0, rng), None, 900)) for _ in range(3)]
    sp = [unit(banda(rng.standard_normal(n), 1800, 7000)) for _ in range(3)]
    L, R = 0.10 * gr[1], 0.10 * gr[2]  # rumor de fondo del mar
    t = rng.uniform(2.5, 4.5)
    while t < dur - 1:
        a = rng.uniform(0.6, 1.0)
        idx = np.arange(max(int((t - 5) * sr), 0), min(int((t + 10) * sr), n))
        tt = idx / sr - t
        env = (
            np.where(tt < 0, np.clip(1 + tt / 5.0, 0, 1) ** 2.2, np.exp(-tt / 2.6)) * a
        )
        esp = (
            np.where(
                tt < 0, np.clip(1 + (tt + 1.0) / 3.5, 0, 1) ** 3, np.exp(-tt / 2.0)
            )
            * a
        )
        esp = esp**1.5
        p = np.clip(0.5 + rng.uniform(-0.3, 0.3) + 0.04 * tt, 0.05, 0.95)
        c, s = np.cos(p * np.pi / 2), np.sin(p * np.pi / 2)
        L[idx] += env * (c * gr[0][idx] + 0.4 * gr[1][idx]) + 0.5 * esp * (
            c * sp[0][idx] + 0.4 * sp[1][idx]
        )
        R[idx] += env * (s * gr[0][idx] + 0.4 * gr[2][idx]) + 0.5 * esp * (
            s * sp[0][idx] + 0.4 * sp[2][idx]
        )
        t += rng.uniform(*periodo)
    return acabar(L, R, rng=rng, rt60=2.0, mezcla=0.12)


# ----------------------------------------------------------------------- agua
def agua(
    dur,
    semilla=1,
    tasa=260,
    r_mm=(1.2, 12.0),
    grave=1.0,
    medio=0.6,
    siseo=0.15,
    burbujas=1.0,
    tau=8.0,
):
    """Agua corriente = turbulencia (ruido de color filtrado) + burbujas.
    Las burbujas siguen un proceso de Poisson de tasa variable; el radio fija
    su tono (burbujas grandes = sonidos graves 'gluglú'; pequeñas = agudos)."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    fl = 0.85 + 0.3 / (1 + np.exp(-1.2 * lento(n, rng, tau)))  # caudal 0,85..1,15
    lam_max = tasa * 1.3
    ti = np.sort(rng.uniform(0, dur, rng.poisson(lam_max * dur)))
    ti = ti[
        rng.random(len(ti))
        < tasa * fl[np.minimum((ti * sr).astype(int), n - 1)] / lam_max
    ]
    radios = np.exp(rng.uniform(np.log(r_mm[0]), np.log(r_mm[1]), len(ti)))
    Lb, Rb = np.zeros(n), np.zeros(n)
    for t0, r in zip(ti, radios):
        s = burbuja(3.26 / (r * 1e-3), r**0.8 * rng.uniform(0.5, 1.0))
        l, rr = paneo(s, rng.uniform(0.1, 0.9))
        i = int(t0 * sr)
        poner(Lb, l, i)
        poner(Rb, rr, i)
    out = []
    for b in (Lb, Rb):
        fondo = (
            grave * unit(banda(ruido_color(n, 2.0, rng), None, 350))
            + medio * unit(banda(ruido_color(n, 1.0, rng), 200, 4000))
            + siseo * unit(banda(rng.standard_normal(n), 3500, 9000))
        )
        out.append(fl * (fondo + burbujas * 1.2 * unit(b)))
    return acabar(out[0], out[1], rng=rng)


def rio(dur, semilla=1):
    return agua(
        dur,
        semilla,
        tasa=260,
        r_mm=(1.2, 12.0),
        grave=1.0,
        medio=0.6,
        siseo=0.15,
        tau=9.0,
    )


def arroyo(dur, semilla=1):
    return agua(
        dur,
        semilla,
        tasa=700,
        r_mm=(0.4, 4.0),
        grave=0.15,
        medio=0.35,
        siseo=0.40,
        burbujas=1.3,
        tau=5.0,
    )


def cascada(dur, semilla=1):
    return agua(
        dur,
        semilla,
        tasa=500,
        r_mm=(0.6, 8.0),
        grave=1.6,
        medio=1.0,
        siseo=0.9,
        burbujas=0.5,
        tau=12.0,
    )


# ---------------------------------------------------------------------- viento
def viento_bosque(dur, semilla=1, fuerza=1.0):
    """Ráfagas: cuanto más fuerte es la racha, más brillante el timbre (más
    agudos y más hojas). Un silbido estrecho se asoma entre ramas."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    g0, g1 = rafaga(n, rng, 7.0), rafaga(n, rng, 7.0)
    out = []
    for gc in (g0, 0.7 * g0 + 0.3 * g1):
        grave = unit(banda(ruido_color(n, 2.0, rng), None, 260))
        medio = unit(banda(ruido_color(n, 1.0, rng), 350, 1000))
        agudo = unit(banda(rng.standard_normal(n), 1200, 3800))
        silbo = unit(banda(rng.standard_normal(n), 480, 620))
        hojas = unit(
            banda(
                rng.standard_normal(n) * (rng.random(n) < 300 * gc**1.6 / sr),
                2500,
                9000,
            )
        )
        out.append(
            fuerza
            * (
                0.5 * (0.35 + 0.65 * gc**0.6) * grave
                + 0.45 * gc**1.1 * medio
                + 0.28 * gc**2 * agudo
                + 0.12 * gc**1.5 * silbo
                + 0.35 * (0.4 + 0.6 * gc) * hojas
            )
        )
    return acabar(out[0], out[1], rng=rng, rt60=1.2, mezcla=0.1)


# ----------------------------------------------------------------------- lluvia
def lluvia_suave(dur, semilla=1, intensidad=0.35):
    """Miles de microimpactos por segundo (textura) + gotas medianas +
    goteo de hojas (pings) + burbujas de charco."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    out = []
    for _ in range(2):
        textura = unit(banda(tren(n, rng, 500 + 2500 * intensidad), 1500, 9000))
        medias = unit(banda(tren(n, rng, 25 + 90 * intensidad, 1.0), 900, 5000))
        siseo = unit(banda(rng.standard_normal(n), 3000, 9000))
        out.append(1.0 * textura + 0.45 * medias + 0.3 * siseo)
    Lg, Rg = np.zeros(n), np.zeros(n)
    for tasa, fmin, fmax, kind in (
        (4 + 8 * intensidad, 800, 3000, "burbuja"),
        (2 + 4 * intensidad, 600, 1400, "ping"),
    ):
        for t0 in np.sort(rng.uniform(0, dur, rng.poisson(tasa * dur))):
            f = rng.uniform(fmin, fmax)
            s = (
                burbuja(f, rng.uniform(0.5, 1))
                if kind == "burbuja"
                else ping(f, 0.025, rng.uniform(0.3, 0.8))
            )
            l, r = paneo(s, rng.uniform(0.1, 0.9))
            poner(Lg, l, int(t0 * sr))
            poner(Rg, r, int(t0 * sr))
    L = out[0] + 0.3 * unit(Lg)
    R = out[1] + 0.3 * unit(Rg)
    return acabar(L, R, rng=rng)


def trueno(seg, cerca, rng):
    """Retumbo grave con envolvente irregular; el chasquido inicial solo se
    oye si la tormenta está cerca."""
    m = int(seg * sr)
    t = np.arange(m) / sr
    base = unit(banda(ruido_color(m, 2.0, rng), None, 70 + 160 * cerca))
    env = np.zeros(m)
    for _ in range(rng.integers(3, 7)):
        t0 = rng.uniform(0, 0.35 * seg)
        env += (
            rng.uniform(0.3, 1.0)
            * np.exp(-(t - t0).clip(0) / rng.uniform(0.8, 2.2))
            * (t >= t0)
        )
    env *= np.minimum(1, t / 0.12)
    crack = (
        3
        * cerca**2
        * unit(banda(rng.standard_normal(m), 1200, 6000))
        * np.exp(-t / 0.06)
    )
    return base * env / (env.max() + 1e-12) + crack


def tormenta(dur=100, semilla=1, t_pico=0.48, wa=0.22, wd=0.26):
    """Lluvia que se acerca, pasa por encima y se aleja.
    N(t)   cercanía (0..1): gaussiana asimétrica con máximo en t_pico.
    Bandas lejos = solo graves (el aire absorbe los agudos); cerca = todo.
    Panorama: el centro de la tormenta cruza de izquierda a derecha; al
    pasar por encima el sonido se abre a todo el estéreo (ancho)."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    t = np.arange(n) / sr
    tp, sa, sd = t_pico * dur, wa * dur, wd * dur
    N = np.where(
        t < tp, np.exp(-(((t - tp) / sa) ** 2)), np.exp(-(((t - tp) / sd) ** 2))
    )
    A = 0.06 + 0.94 * N**1.2
    x = np.clip((t - (tp - 1.6 * sa)) / (1.6 * sa + 1.6 * sd), 0, 1)
    pc = 0.15 + 0.70 * x * x * (3 - 2 * x)
    ancho = N**0.7
    lam = 500 + 7000 * N**1.5
    L, R = np.zeros(n), np.zeros(n)
    for lo, hi, ex, peso in (
        (250, 1500, 0.8, 1.0),
        (1200, 5000, 1.0, 1.0),
        (4000, 12000, 1.6, 0.8),
    ):
        mono, il, ir = (unit(banda(tren(n, rng, lam), lo, hi)) for _ in range(3))
        g = peso * A**ex
        L += g * ((1 - ancho) * np.cos(pc * np.pi / 2) * mono + ancho * il)
        R += g * ((1 - ancho) * np.sin(pc * np.pi / 2) * mono + ancho * ir)
    # gotas grandes, solo cuando está cerca
    for canal in (L, R):
        canal += (
            0.8 * N**1.5 * unit(banda(tren(n, rng, 4 + 110 * N**3, 1.5), 700, 6000))
        )
    # burbujas de charco
    Lc, Rc = np.zeros(n), np.zeros(n)
    for t0 in np.sort(rng.uniform(0, dur, rng.poisson(10 * dur))):
        i = min(int(t0 * sr), n - 1)
        if rng.random() < 0.15 + 0.85 * N[i] ** 2:
            l, r = paneo(
                burbuja(rng.uniform(700, 3000), rng.uniform(0.5, 1)),
                rng.uniform(0.1, 0.9),
            )
            poner(Lc, l, i)
            poner(Rc, r, i)
    L += 0.25 * unit(Lc) * N**0.8
    R += 0.25 * unit(Rc) * N**0.8
    # truenos: dos lejanos, uno encima y uno que se aleja
    for frac in (0.22, 0.40, t_pico + 0.02, t_pico + 0.12, 0.80):
        t0 = frac * dur
        cerca = float(N[min(int(t0 * sr), n - 1)])
        s = trueno(9.0, cerca, rng) * (0.25 + 0.9 * cerca)
        p = rng.uniform(0.25, 0.75)
        l, r = paneo(s, p)
        poner(L, 0.9 * l + 0.1 * s, int(t0 * sr))
        poner(R, 0.9 * r + 0.1 * s, int(t0 * sr))
    return acabar(L, R, rng=rng, entrada=4.0, salida=5.0)


# --------------------------------------------------------------- campanas
RATIOS_BARRA = [1, 2.756, 5.404, 8.933]  # modos de una barra libre-libre
METAL = [74, 76, 78, 81, 83, 86, 88, 90]  # Re mayor pentatónica
MADERA = [62, 64, 66, 69, 71, 74, 76]


def campana(f0, vel, rng, material="metal"):
    """Síntesis modal: suma de parciales inarmónicos con decaimiento propio."""
    k = (440 / f0) ** 0.3
    if material == "metal":
        taus = [1.8 * k / (1 + 0.9 * j) for j in range(4)]
        amps = [1.0, 0.55, 0.30, 0.15]
        fuentes = [(f0, 0.6, taus[0]), (f0 * 1.0025, 0.5, taus[0])] + [
            (f0 * r, a, tau) for r, a, tau in zip(RATIOS_BARRA[1:], amps[1:], taus[1:])
        ]
        seg, knock = 7 * taus[0] ** 1.0 / 1.0, (2500, 9000, 0.004, 0.25)
    else:
        taus = [0.30 * k, 0.10 * k, 0.05 * k]
        fuentes = [
            (f0, 1.0, taus[0]),
            (f0 * 2.76, 0.5, taus[1]),
            (f0 * 5.4, 0.3, taus[2]),
        ]
        seg, knock = 8 * taus[0] + 0.3, (500, 3000, 0.010, 0.6)
    m = int(sr * min(seg, 12))
    t = np.arange(m) / sr
    s = sum(
        a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
        for f, a, tau in fuentes
    )
    lo, hi, tk, ak = knock
    golpe = banda(rng.standard_normal(m), lo, hi, orden=1) * np.exp(-t / tk) * ak
    return vel * (s + 3 * golpe) * np.minimum(1, t / 0.0008)


def campanas(dur, semilla=1, material="metal"):
    """Rachas de viento: cada una hace chocar varias campanas vecinas
    (la posición del badajo es un paseo aleatorio por los tubos)."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    notas = METAL if material == "metal" else MADERA
    K = len(notas)
    L, R = np.zeros(n), np.zeros(n)
    t = rng.exponential(2.0)
    while t < dur - 2:
        pos = int(rng.integers(0, K))
        tt = t
        for j in range(int(rng.integers(3, 14))):
            f = 440 * 2 ** ((notas[pos] - 69) / 12)
            s = campana(f, rng.uniform(0.3, 1.0), rng, material)
            l, r = paneo(s, 0.2 + 0.6 * pos / (K - 1))
            poner(L, l, int(tt * sr))
            poner(R, r, int(tt * sr))
            tt += rng.exponential(0.20) * (1 + 0.15 * j)
            pos = int(np.clip(pos + rng.choice([-2, -1, 1, 2]), 0, K - 1))
        t += rng.exponential(7.0) + 2.0
    return acabar(
        L, R, modo="pico", objetivo=0.8, rng=rng, rt60=1.5, mezcla=0.2, salida=4.0
    )


def campanas_metal(dur, semilla=1):
    return campanas(dur, semilla, "metal")


def campanas_madera(dur, semilla=1):
    return campanas(dur, semilla, "madera")


# ------------------------------------------------------------------- otros
def fuego(dur, semilla=1):
    """Rugido grave (ruido marrón) + siseo + chasquidos en racimos + algún estallido."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    mod = 0.75 + 0.25 / (1 + np.exp(-lento(n, rng, 2.5)))
    act = 0.5 + 1.0 / (1 + np.exp(-lento(n, rng, 4.0)))  # actividad 0,5..1,5
    lam_max = 9 * 1.5
    ti = np.sort(rng.uniform(0, dur, rng.poisson(lam_max * dur)))
    ti = ti[
        rng.random(len(ti))
        < 9 * act[np.minimum((ti * sr).astype(int), n - 1)] / lam_max
    ]
    Lc, Rc = np.zeros(n), np.zeros(n)
    for t0 in ti:
        for c in range(int(rng.integers(1, 5))):
            s = ping(
                rng.uniform(1200, 5000),
                rng.uniform(0.002, 0.008),
                np.exp(rng.normal(0, 0.9)),
                rng,
                ruido=0.5,
            )
            l, r = paneo(s, rng.uniform(0.15, 0.85))
            i = int((t0 + c * rng.uniform(0.004, 0.02)) * sr)
            poner(Lc, l, i)
            poner(Rc, r, i)
    for t0 in rng.uniform(0, dur, rng.poisson(0.35 * dur)):  # estallidos
        s = suma(
            burbuja(rng.uniform(250, 900), 3.0),
            ping(rng.uniform(1500, 3500), 0.004, 2.0, rng, 0.5),
        )
        l, r = paneo(s, rng.uniform(0.2, 0.8))
        poner(Lc, l, int(t0 * sr))
        poner(Rc, r, int(t0 * sr))
    out = []
    for c in (Lc, Rc):
        rug = unit(banda(ruido_color(n, 2.0, rng), None, 450))
        sis = unit(banda(rng.standard_normal(n), 2500, 9000))
        out.append(mod * (0.6 * rug + 0.12 * sis) + 0.45 * unit(c))
    return acabar(out[0], out[1], rng=rng)


def goteo_cueva(dur, semilla=1, tasa=0.4):
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    L, R = np.zeros(n), np.zeros(n)
    for t0 in np.sort(rng.uniform(0, dur, rng.poisson(tasa * dur))):
        f0 = rng.uniform(500, 2400)
        s = suma(
            burbuja(f0, rng.uniform(0.5, 1.0)),
            ping(rng.uniform(2500, 6000), 0.003, 0.3, rng, 0.3),
        )
        l, r = paneo(s, rng.uniform(0.1, 0.9))
        poner(L, l, int(t0 * sr))
        poner(R, r, int(t0 * sr))
    aire = [0.05 * unit(banda(ruido_color(n, 2.0, rng), None, 150)) for _ in range(2)]
    scale = np.abs(L).max() + 1e-12
    return acabar(
        L / scale + aire[0],
        R / scale + aire[1],
        modo="pico",
        objetivo=0.8,
        rng=rng,
        rt60=6.5,
        mezcla=0.65,
        entrada=3.0,
        salida=5.0,
    )


def grillos(dur, semilla=1, n_grillos=8):
    """Cada grillo: portadora de 4,2-5,1 kHz en pulsos de ~12 ms agrupados en
    trinos (3-4 pulsos) que se repiten 2-3 veces por segundo."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    L, R = np.zeros(n), np.zeros(n)
    for _ in range(n_grillos):
        fc = rng.uniform(4200, 5100)
        ritmo = rng.uniform(1.8, 3.4)
        npul = int(rng.integers(3, 5))
        amp = rng.uniform(0.3, 1.0)
        p = rng.uniform(0.05, 0.95)
        tp = np.arange(int(0.012 * sr)) / sr
        pulso = np.sin(2 * np.pi * fc * tp) * np.hanning(len(tp))
        t = rng.uniform(0, 1 / ritmo)
        while t < dur - 0.3:
            for k in range(npul):
                l, r = paneo(amp * pulso, p)
                i = int((t + k * 0.028) * sr)
                poner(L, l, i)
                poner(R, r, i)
            t += rng.uniform(0.9, 1.1) / ritmo
    aire = [0.04 * unit(banda(ruido_color(n, 1.0, rng), None, 3000)) for _ in range(2)]
    sc = np.sqrt(np.mean(L**2)) + 1e-12
    return acabar(
        L / sc * 0.3 + aire[0], R / sc * 0.3 + aire[1], rng=rng, rt60=1.0, mezcla=0.1
    )


def bosque_nocturno(dur, semilla=1):
    capas = (
        (arroyo(dur, semilla), 1.0),
        (viento_bosque(dur, semilla + 1, fuerza=0.35), 0.35),
        (grillos(dur, semilla + 2), 0.5),
    )
    est = sum(g * e for e, g in capas)
    return acabar(
        est[:, 0],
        est[:, 1],
        rng=np.random.default_rng(semilla),
        entrada=3.0,
        salida=4.0,
    )


# ------------------------------------------------------------------ salida
PIEZAS = {  # nombre: (función, duración de muestra en s)
    "olas": (olas, 45),
    "rio": (rio, 45),
    "arroyo": (arroyo, 45),
    "cascada": (cascada, 45),
    "viento_bosque": (viento_bosque, 45),
    "lluvia_suave": (lluvia_suave, 45),
    "tormenta": (tormenta, 100),
    "campanas_metal": (campanas_metal, 45),
    "campanas_madera": (campanas_madera, 45),
    "fuego": (fuego, 45),
    "goteo_cueva": (goteo_cueva, 45),
    "grillos": (grillos, 45),
    "bosque_nocturno": (bosque_nocturno, 75),
}


def guardar(est, nombre, kbps=192):
    import lameenc

    wavfile.write(f"sonido_{nombre}.wav", sr, (est * 32767).astype(np.int16))
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(sr)
    enc.set_channels(2)
    enc.set_quality(2)
    with open(f"sonido_{nombre}.mp3", "wb") as f:
        f.write(enc.encode((est * 32767).astype(np.int16).tobytes()) + enc.flush())


if __name__ == "__main__":
    args = sys.argv[1:]
    dur = float(args[args.index("--dur") + 1]) if "--dur" in args else None
    semilla = int(args[args.index("--semilla") + 1]) if "--semilla" in args else 1
    nombres = [
        a
        for i, a in enumerate(args)
        if not a.startswith("--")
        and (i == 0 or args[i - 1] not in ("--dur", "--semilla"))
    ] or list(PIEZAS)
    for nombre in nombres:
        print(f"Generando 'sonido_{nombre}'")
        f, d = PIEZAS[nombre]
        guardar(f(dur or d, semilla), nombre)
        print(f"\tsonido_{nombre}.mp3 ({dur or d:g} s)")
