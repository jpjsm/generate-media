"""
Sonidos meditativos por síntesis (continúa sonidos_naturales.py).

  cuencos      cuencos tibetanos: golpeados (se apagan solos) y frotados (cantan)
  mar_profundo rumor submarino, oleaje lejano amortiguado, burbujas y llamadas
               de ballena (opcionales)
  fractal      ruido fractal evolutivo: la pendiente espectral beta cambia
               lentamente (blanco -> rosa -> marrón -> rosa -> blanco)
  binaural     dos tonos casi iguales, uno en cada oído (¡con auriculares!)
  isocronico   un tono pulsado al ritmo del 'batido'; funciona en altavoces

Matemática del ruido fractal (ruido con espectro de potencia ~ 1/f^beta):
  beta = 0       ruido blanco
  beta = 1       ruido rosa (1/f)
  beta = 2       ruido marrón (movimiento browniano)
  1 < beta < 3   movimiento browniano fraccionario de Hurst H = (beta - 1)/2;
                 su gráfica tiene dimensión fractal D = 2 - H = (5 - beta)/2

Uso:  python sonidos_meditativos.py                (todos)
      python sonidos_meditativos.py binaural --dur 300

Requiere: numpy, scipy, lameenc y sonidos_naturales.py
"""
import sys
import numpy as np
from sonidos_naturales import (sr, banda, unit, ruido_color, lento, poner, paneo,
                               reverb, acabar, burbuja, guardar)

TAU = 2 * np.pi


# ------------------------------------------------------------ cuencos tibetanos
RATIOS_CUENCO = [1.0, 2.71, 5.15, 8.30]            # modos de un cuenco (inarmónicos)
AFINACION = [146.83, 174.61, 220.0, 261.63, 293.66, 349.23]    # Re3 Fa3 La3 Do4 Re4 Fa4


def cuenco(f0, vel, rng, modo='golpe', dur=36.0):
    """Cada modo se desdobla en dos frecuencias muy próximas (el cuenco no es
    perfectamente simétrico): su suma produce pulsaciones lentas (0,3-2 Hz),
    que son el 'latido' característico.
      golpe:   cada modo decae exponencialmente (los agudos antes).
      frotado: excitación continua; los modos agudos entran poco a poco."""
    n = int(sr * dur)
    t = np.arange(n) / sr
    s = np.zeros(n)
    for k, r in enumerate(RATIOS_CUENCO):
        a = 1.0 / (1 + 1.2 * k)
        fk = f0 * r
        delta = rng.uniform(0.25, 1.4) * (1 + 0.3 * k)                 # Hz de pulsación
        par = 0.5 * (np.sin(TAU * fk * t + rng.uniform(0, TAU))
                     + np.sin(TAU * (fk + delta) * t + rng.uniform(0, TAU)))
        if modo == 'golpe':
            tau = 4.5 / (1 + 0.9 * k) * (220 / f0) ** 0.2
            s += a * par * np.exp(-t / tau)
        else:
            subida = np.clip((t - 1.2 * k) / 4.0, 0, 1) ** 2
            temblor = 1 + 0.15 * np.sin(TAU * rng.uniform(0.08, 0.25) * t + rng.uniform(0, TAU))
            s += a * par * subida * temblor
    if modo == 'golpe':
        s *= np.minimum(1, t / 0.006)
        s += 0.05 * unit(banda(rng.standard_normal(n), 100, 900)) * np.exp(-t / 0.03)
    else:
        s *= np.cos(np.clip((t - (dur - 8)) / 8, 0, 1) * np.pi / 2) ** 2
    return vel * s


def cuencos(dur, semilla=1):
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    L, R = np.zeros(n), np.zeros(n)
    t = rng.uniform(1.0, 3.0)
    while t < dur - 5:
        f = float(rng.choice(AFINACION))
        l, r = paneo(cuenco(f, rng.uniform(0.5, 1.0), rng, 'golpe'), rng.uniform(0.2, 0.8))
        poner(L, l, int(t * sr))
        poner(R, r, int(t * sr))
        t += rng.uniform(7.0, 13.0)
    for t0, f, p in ((0.15 * dur, AFINACION[0], 0.35), (0.50 * dur, AFINACION[2], 0.65)):
        l, r = paneo(cuenco(f, 0.35, rng, 'frotado', 28.0), p)
        poner(L, l, int(t0 * sr))
        poner(R, r, int(t0 * sr))
    return acabar(L, R, modo='pico', objetivo=0.8, rng=rng, rt60=4.5, mezcla=0.35,
                  entrada=1.0, salida=6.0)


# ----------------------------------------------------------------- mar profundo
def llamada_ballena(rng, dur=7.0):
    """Gemido con glissando suave (70-300 Hz) y dos armónicos."""
    n = int(sr * dur)
    t = np.arange(n) / sr
    u = t / dur
    fa = rng.uniform(70, 150)
    fb = fa * rng.choice([rng.uniform(1.3, 2.0), rng.uniform(0.6, 0.8)])
    f = (fa + (fb - fa) * (3 * u ** 2 - 2 * u ** 3)) * (1 + 0.01 * np.sin(TAU * 4 * t))
    fase = TAU * np.cumsum(f) / sr
    return (np.sin(fase) + 0.5 * np.sin(2 * fase) + 0.25 * np.sin(3 * fase)) * np.sin(np.pi * u) ** 2


def mar_profundo(dur, semilla=1, ballenas=True):
    """Casi todo es grave: presión (< 110 Hz), oleaje lejano amortiguado que
    sube y baja con un ritmo de ~10 s, y poco agua. Las burbujas y las
    ballenas pasan por una reverb muy larga."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    sw = 1 / (1 + np.exp(-1.5 * lento(n, rng, 10)))
    base = []
    for _ in range(2):
        presion = unit(banda(ruido_color(n, 2.0, rng), None, 110))
        oleaje = unit(banda(ruido_color(n, 1.5, rng), 30, 450)) * (0.25 + 0.75 * sw ** 1.5)
        agua = unit(banda(ruido_color(n, 1.0, rng), 200, 900)) * 0.15 * (0.3 + sw)
        base.append(presion + 0.8 * oleaje + agua)
    Le, Re = np.zeros(n), np.zeros(n)
    for t0 in np.sort(rng.uniform(0, dur, rng.poisson(0.5 * dur))):    # burbujas grandes
        r = rng.uniform(6, 20)
        l, rr = paneo(burbuja(3.26 / (r * 1e-3), rng.uniform(0.5, 1.0)), rng.uniform(0.1, 0.9))
        poner(Le, l, int(t0 * sr))
        poner(Re, rr, int(t0 * sr))
    Le, Re = 0.25 * unit(Le), 0.25 * unit(Re)
    if ballenas:
        t = rng.uniform(8, 15)
        while t < dur - 10:
            tt = t
            for _ in range(int(rng.integers(2, 4))):
                l, r = paneo(llamada_ballena(rng, rng.uniform(5, 9)), rng.uniform(0.15, 0.85))
                poner(Le, 0.5 * l, int(tt * sr))
                poner(Re, 0.5 * r, int(tt * sr))
                tt += rng.uniform(7, 11)
            t += rng.uniform(40, 60)
    Lm = 0.4 * Le + 0.6 * reverb(Le, rng, 7.0, oscuro=0.85)
    Rm = 0.4 * Re + 0.6 * reverb(Re, rng, 7.0, oscuro=0.85)
    return acabar(base[0] + Lm, base[1] + Rm, entrada=4.0, salida=6.0)


# ----------------------------------------------------------------- ruido fractal
def hurst(beta):
    """Exponente de Hurst de un movimiento browniano fraccionario con espectro 1/f^beta."""
    return (beta - 1) / 2


def dimension_fractal(beta):
    """Dimensión fractal de la gráfica de la señal: D = 2 - H (para 1 < beta < 3)."""
    return 2 - hurst(beta)


def _proceso_fractal(n, betas, N, rng):
    """Superposición de tramos de ruido de pendiente `beta` distinta, solapados
    a la mitad con ventana senoidal (potencia total constante)."""
    hop = N // 2
    f = np.fft.rfftfreq(N, 1 / sr)
    f[0] = f[1]
    ven = np.sin(np.pi * (np.arange(N) + 0.5) / N)
    out = np.zeros(hop * (len(betas) + 1) + N)
    for i, b in enumerate(betas):
        mag = f ** (-b / 2)
        mag[0] = 0
        fr = np.fft.irfft(mag * np.exp(1j * rng.uniform(0, TAU, len(f))), N)
        out[i * hop:i * hop + N] += fr / (fr.std() + 1e-12) * ven
    return out[hop:hop + n]


def curva_beta(dur, beta=(0.2, 2.2), N=2 ** 15):
    """beta(t) triangular: beta[0] -> beta[1] -> beta[0]."""
    n_tramos = int(dur * sr / (N // 2)) + 2
    u = np.linspace(0, 1, n_tramos)
    return beta[0] + (beta[1] - beta[0]) * (1 - np.abs(2 * u - 1))


def fractal(dur, semilla=1, beta=(0.2, 2.2)):
    rng = np.random.default_rng(semilla)
    N = 2 ** 15
    n = int(dur * sr)
    betas = curva_beta(dur, beta, N)
    L = _proceso_fractal(n, betas, N, rng)
    R = _proceso_fractal(n, betas, N, rng)
    return acabar(L, R, objetivo=0.08, entrada=4.0, salida=6.0)


# --------------------------------------------------------------------- binaural
def binaural(dur, semilla=1, portadora=200.0, beat=(10.0, 4.0), ruido=0.5):
    """Oído izquierdo: portadora - beat/2; derecho: portadora + beat/2. La
    diferencia (el 'batido') baja linealmente de beat[0] a beat[1] Hz
    (10 Hz = banda alfa, 4 Hz = theta). Sobre un lecho de ruido rosa."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    t = np.arange(n) / sr
    b = np.linspace(beat[0], beat[1], n)
    pL = TAU * np.cumsum(portadora - b / 2) / sr
    pR = TAU * np.cumsum(portadora + b / 2) / sr
    respira = 1 + 0.08 * np.sin(TAU * 0.07 * t)
    L = 0.35 * respira * np.sin(pL)
    R = 0.35 * respira * np.sin(pR)
    L = L + ruido * 0.35 * unit(banda(ruido_color(n, 1.0, rng), None, 2500))
    R = R + ruido * 0.35 * unit(banda(ruido_color(n, 1.0, rng), None, 2500))
    return acabar(L, R, objetivo=0.07, entrada=6.0, salida=10.0)


def isocronico(dur, semilla=1, portadora=180.0, ritmo=(10.0, 6.0), ruido=0.4):
    """Tono cuya amplitud late a `ritmo` Hz (pulsos suaves). A diferencia del
    binaural, no necesita auriculares."""
    rng = np.random.default_rng(semilla)
    n = int(dur * sr)
    t = np.arange(n) / sr
    f = np.linspace(ritmo[0], ritmo[1], n)
    pulso = np.sin(TAU * np.cumsum(f) / sr / 2) ** 2          # (1 - cos fase)/2: frecuencia f
    tono = 0.5 * np.sin(TAU * portadora * t) * pulso
    L = tono + ruido * 0.3 * unit(banda(ruido_color(n, 1.0, rng), None, 2500))
    R = tono + ruido * 0.3 * unit(banda(ruido_color(n, 1.0, rng), None, 2500))
    return acabar(L, R, objetivo=0.07, entrada=6.0, salida=10.0)


PIEZAS = {'cuencos': (cuencos, 90), 'mar_profundo': (mar_profundo, 90),
          'fractal': (fractal, 90), 'binaural': (binaural, 120), 'isocronico': (isocronico, 60)}


if __name__ == "__main__":
    args = sys.argv[1:]
    dur = float(args[args.index('--dur') + 1]) if '--dur' in args else None
    semilla = int(args[args.index('--semilla') + 1]) if '--semilla' in args else 1
    nombres = [a for i, a in enumerate(args) if not a.startswith('--')
               and (i == 0 or args[i - 1] not in ('--dur', '--semilla'))] or list(PIEZAS)
    for nombre in nombres:
        f, d = PIEZAS[nombre]
        guardar(f(dur or d, semilla), nombre)
        print(f"sonido_{nombre}.mp3 ({dur or d:g} s)")
