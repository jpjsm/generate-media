"""
Comprobaciones objetivas de sonidos_naturales.py.

Estas pruebas NO sustituyen al oído: miden propiedades que sí se pueden
medir (pendiente espectral, periodicidad, evolución del brillo y del
panorama, frecuencias de los modos...), para detectar errores de síntesis.

  python verificar_sonidos.py
"""
import numpy as np
from scipy.signal import welch, find_peaks, hilbert
import sonidos_naturales as S
import sonidos_meditativos as M

sr = S.sr


def mono(est):
    return est.mean(axis=1)


def ventanas(x, seg=1.0):
    m = int(seg * sr)
    return [x[i:i + m] for i in range(0, len(x) - m + 1, m)]


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def centroide(x):
    esp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * esp).sum() / (esp.sum() + 1e-12))


def curva(est, f, seg=1.0, banda=None):
    """RMS (dB) y centroide (Hz) por ventanas de `seg` segundos."""
    x = mono(est)
    if banda:
        x = S.banda(x, *banda)
    v = ventanas(x, seg)
    return np.array([rms_db(w) for w in v]), np.array([f(w) for w in v])


# ------------------------------------------------------------------- pruebas
def t_ruido_color():
    rng = np.random.default_rng(0)
    res = []
    for beta in (1.0, 2.0):
        x = S.ruido_color(sr * 60, beta, rng)
        f, p = welch(x, sr, nperseg=2 ** 15)
        m = (f > 50) & (f < 5000)
        pend = np.polyfit(np.log10(f[m]), np.log10(p[m]), 1)[0]
        res.append((abs(pend + beta) < 0.1, f"beta={beta}: pendiente medida {pend:.2f} (teórica {-beta})"))
    return all(r[0] for r in res), '; '.join(r[1] for r in res)


def t_olas():
    est = S.olas(120, 1)
    env = np.array([np.sqrt(np.mean(w ** 2)) for w in ventanas(mono(est), 0.5)])
    env = np.convolve(env, np.ones(6) / 6, 'same')
    picos, _ = find_peaks(env, distance=int(4 / 0.5), prominence=0.15 * env.max())
    sep = np.diff(picos) * 0.5
    ok = 6.0 <= np.median(sep) <= 12.0
    return ok, f"{len(picos)} olas detectadas en 120 s; separación mediana {np.median(sep):.1f} s (generada: 6,5-11)"


def t_agua():
    c = {n: np.mean(curva(getattr(S, n)(40, 1), centroide)[1]) for n in ('rio', 'arroyo', 'cascada')}
    ok = c['arroyo'] > c['rio']
    return ok, ', '.join(f"{n} {v:.0f} Hz" for n, v in c.items()) + " (centroide medio; el arroyo debe ser más brillante que el río)"


def t_viento():
    est = S.viento_bosque(120, 1)
    nivel, cen = curva(est, centroide)
    r = np.corrcoef(nivel, cen)[0, 1]
    return r > 0.4, f"correlación nivel-brillo {r:.2f} (las rachas fuertes deben ser más brillantes); rango de nivel {nivel.max() - nivel.min():.1f} dB"


def t_lluvia():
    est = S.lluvia_suave(60, 1)
    nivel, cen = curva(est, centroide)
    nivel, cen = nivel[4:-5], cen[4:-5]              # sin los fundidos de entrada y salida
    var = nivel.std()
    return (var < 1.0 and 2000 < cen.mean() < 7000), f"variación de nivel {var:.2f} dB (estacionaria); centroide {cen.mean():.0f} Hz"


def t_tormenta():
    dur, tp = 100, 0.48
    est = S.tormenta(dur, 1, t_pico=tp)
    # lluvia = banda 1-10 kHz (el trueno es grave y queda fuera)
    nivel, cen = curva(est, centroide, seg=1.0, banda=(1000, 10000))
    suave = np.convolve(nivel, np.ones(5) / 5, 'same')
    t_max = np.argmax(suave)
    ok1 = abs(t_max - tp * dur) < 0.08 * dur
    salto = suave[t_max] - min(suave[:8].mean(), suave[-8:].mean())
    ok2 = salto > 12
    cen_s = np.convolve(cen, np.ones(5) / 5, 'same')
    ok3 = cen_s[t_max] > cen_s[:6].mean() and cen_s[t_max] > cen_s[-6:].mean()
    L, R = est[:, 0], est[:, 1]
    k = int(0.15 * dur * sr)
    izq_ini = np.mean(L[:k] ** 2) / np.mean(R[:k] ** 2)
    izq_fin = np.mean(L[-k:] ** 2) / np.mean(R[-k:] ** 2)
    ok4 = izq_ini > 1.3 and izq_fin < 0.77
    return (ok1 and ok2 and ok3 and ok4), (
        f"máximo en t={t_max} s (esperado ~{tp * dur:.0f}); subida {salto:.0f} dB; "
        f"centroide al inicio/pico/final {cen_s[:6].mean():.0f}/{cen_s[t_max]:.0f}/{cen_s[-6:].mean():.0f} Hz; "
        f"relación L/R inicio {izq_ini:.1f}, final {izq_fin:.2f}")


def _picos_en(x, objetivo, tol=0.015):
    esp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    ref = esp.max()
    out = []
    for fo in objetivo:
        m = (f > fo * (1 - tol)) & (f < fo * (1 + tol))
        out.append(20 * np.log10(esp[m].max() / ref + 1e-12))
    return out


def t_campanas():
    rng = np.random.default_rng(0)
    f0 = 440 * 2 ** ((74 - 69) / 12)
    c = S.campana(f0, 1.0, rng, 'metal')
    niv = _picos_en(c, [f0 * r for r in S.RATIOS_BARRA[:3]])
    w = S.campana(f0, 1.0, rng, 'madera')

    def t30(x):                       # tiempo en caer 30 dB desde el máximo
        env = np.abs(hilbert(x))
        env = np.convolve(env, np.ones(220) / 220, 'same')
        i = np.argmax(env)
        j = np.argmax(env[i:] < env[i] * 10 ** (-30 / 20)) if (env[i:] < env[i] * 10 ** (-30 / 20)).any() else len(env) - i
        return j / sr
    tm, tw = t30(c), t30(w)
    ok = all(n > -45 for n in niv) and tw < tm / 2
    return ok, (f"metal: parciales a f0·[1; 2,756; 5,404] con niveles {', '.join(f'{n:.0f}' for n in niv)} dB; "
                f"caída de 30 dB: metal {tm:.2f} s, madera {tw:.2f} s")


def t_fuego():
    est = S.fuego(60, 1)
    x = S.banda(mono(est), 1000, 9000)
    k = float(((x - x.mean()) ** 4).mean() / (x.var() ** 2))
    return k > 5, f"curtosis de la banda aguda {k:.1f} (ruido gaussiano = 3; el fuego debe ser impulsivo)"


def t_grillos():
    est = S.grillos(40, 1)
    x = mono(est)
    esp = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    m = (f > 3000) & (f < 6500)
    fpico = f[m][np.argmax(esp[m])]
    env = np.abs(hilbert(S.banda(x, 4000, 5300)))
    env = env[::20]                                     # fs = 2205 Hz
    fr, p = welch(env - env.mean(), sr / 20, nperseg=4096)
    mm = (fr > 10) & (fr < 150)
    fmod = fr[mm][np.argmax(p[mm])]
    return (4000 < fpico < 5200 and 30 < fmod < 42), f"portadora dominante {fpico:.0f} Hz; modulación de pulsos {fmod:.1f} Hz (generada: 1/0,028 = 35,7 Hz)"


def t_general():
    malos = []
    for nombre, (f, d) in {**S.PIEZAS, **M.PIEZAS}.items():
        est = f(min(d, 30), 2)
        r = rms_db(est)
        if np.isnan(est).any() or np.abs(est).max() > 0.91 or r < -45:
            malos.append(f"{nombre} (rms {r:.0f} dB, pico {np.abs(est).max():.2f})")
    return not malos, "todas las piezas: sin NaN, pico <= 0,9, nivel audible" if not malos else "problemas: " + ', '.join(malos)


# ---------------------------------------------------- sonidos meditativos
def t_cuencos():
    rng = np.random.default_rng(0)
    f0 = 220.0
    c = M.cuenco(f0, 1.0, rng, 'golpe', dur=40)
    niv = _picos_en(c[:20 * sr], [f0 * r for r in M.RATIOS_CUENCO[:3]], tol=0.02)
    # pulsación: modulación lenta de la envolvente alrededor de la fundamental
    x = S.banda(c[:20 * sr], f0 - 8, f0 + 8)
    env = np.abs(hilbert(x))[::441]                        # 100 Hz
    le = np.log(env[50:] + 1e-9)
    le = le - np.polyval(np.polyfit(np.arange(len(le)), le, 3), np.arange(len(le)))
    fr, p = welch(le, 100, nperseg=1024)
    mm = (fr > 0.15) & (fr < 3)
    f_batido = fr[mm][np.argmax(p[mm])]
    # tiempo de caída de 60 dB, extrapolado de la pendiente entre 2 y 12 s
    nivel = 20 * np.log10(np.abs(hilbert(S.banda(c, f0 - 8, f0 + 8)))[::441] + 1e-12)
    pend = np.polyfit(np.arange(200, 1200) / 100, nivel[200:1200], 1)[0]
    t60 = -60 / pend
    # cuenco frotado: tiempo en alcanzar el 90 % de su nivel máximo
    fr_ = M.cuenco(f0, 1.0, np.random.default_rng(1), 'frotado', 28.0)
    e = np.array([np.sqrt(np.mean(w ** 2)) for w in ventanas(fr_, 0.5)])
    t90 = np.argmax(e > 0.9 * e.max()) * 0.5
    ok = all(n > -45 for n in niv) and 0.15 < f_batido < 3 and 20 < t60 < 45 and 4 <= t90 <= 12
    return ok, (f"modos a f0*[1; 2,71; 5,15] con niveles {', '.join(f'{n:.0f}' for n in niv)} dB; pulsación {f_batido:.2f} Hz; "
                f"T60 {t60:.0f} s; el cuenco frotado alcanza el 90 % a los {t90:.1f} s")


def t_mar():
    est = M.mar_profundo(90, 1, ballenas=False)
    x = mono(est)
    esp = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / sr)
    frac = esp[f < 800].sum() / esp.sum()
    nivel = np.array([rms_db(w) for w in ventanas(x, 1.0)])[8:-10]
    rng = np.random.default_rng(0)
    w = M.llamada_ballena(rng, 7.0)
    cw = centroide(w)
    ok = frac > 0.9 and 1.5 < nivel.std() < 12 and 70 < cw < 500
    return ok, (f"{100 * frac:.1f} % de la energía por debajo de 800 Hz; oleaje: variación de nivel {nivel.std():.1f} dB; "
                f"centroide de una llamada de ballena {cw:.0f} Hz")


def t_fractal():
    dur = 90
    est = M.fractal(dur, 1)
    x = est[:, 0]
    N = 2 ** 15
    betas = M.curva_beta(dur, (0.2, 2.2), N)
    err, filas = 0, []
    for c in range(15, 80, 10):
        seg = x[int((c - 5) * sr):int((c + 5) * sr)]
        f, p = welch(seg, sr, nperseg=2 ** 14)
        m = (f > 100) & (f < 8000)
        pend = -np.polyfit(np.log10(f[m]), np.log10(p[m]), 1)[0]
        esperado = float(np.mean(betas[int((c - 5) * sr / (N // 2)):int((c + 5) * sr / (N // 2)) + 1]))
        err = max(err, abs(pend - esperado))
        filas.append(f"{c}s:{pend:.2f}/{esperado:.2f}")
    return err < 0.3, (f"beta medida/esperada {' '.join(filas)}; error máx. {err:.2f}; "
                       f"para beta=2,2: H={M.hurst(2.2):.2f}, D={M.dimension_fractal(2.2):.2f}")


def _freq_inst(x, lo, hi):
    a = hilbert(S.banda(x, lo, hi))
    f = np.diff(np.unwrap(np.angle(a))) * sr / (2 * np.pi)
    return float(np.mean(f[int(0.3 * sr):-int(0.3 * sr)]))


def t_binaural():
    dur, f0, b = 60, 200.0, (10.0, 4.0)
    est = M.binaural(dur, 1, portadora=f0, beat=b)
    errs, filas = [], []
    for c in (15, 30, 45):
        a, z = int((c - 2) * sr), int((c + 2) * sr)
        fL, fR = _freq_inst(est[a:z, 0], 170, 230), _freq_inst(est[a:z, 1], 170, 230)
        esperado = b[0] + (b[1] - b[0]) * c / dur
        errs.append(abs((fR - fL) - esperado))
        filas.append(f"{c}s: L {fL:.2f} R {fR:.2f} dif {fR - fL:.2f} (esperado {esperado:.2f})")
    # separación: cada oído debe tener SOLO su tono
    seg = est[int(20 * sr):int(28 * sr)]
    fL, fR = _freq_inst(seg[:, 0], 170, 230), _freq_inst(seg[:, 1], 170, 230)
    esp_L = np.abs(np.fft.rfft(seg[:, 0] * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1 / sr)
    pico = lambda e, fo: e[(fr > fo - 0.4) & (fr < fo + 0.4)].max()
    sep = 20 * np.log10(pico(esp_L, fR) / pico(esp_L, fL))
    return (max(errs) < 0.3 and sep < -20), "; ".join(filas) + f"; tono del oído derecho dentro del izquierdo: {sep:.0f} dB"


def t_isocronico():
    est = M.isocronico(60, 1, portadora=180.0, ritmo=(10.0, 6.0))
    seg = est[int(5 * sr):int(15 * sr), 0]
    env = np.abs(hilbert(S.banda(seg, 150, 210)))[::20]
    fr, p = welch(env - env.mean(), sr / 20, nperseg=4096)
    m = (fr > 3) & (fr < 20)
    fpico = fr[m][np.argmax(p[m])]
    esperado = 10 + (6 - 10) * 10 / 60
    return abs(fpico - esperado) < 1.0, f"ritmo de los pulsos {fpico:.1f} Hz (esperado ~{esperado:.1f} Hz entre 5 y 15 s)"


PRUEBAS = [t_ruido_color, t_olas, t_agua, t_viento, t_lluvia, t_tormenta,
           t_campanas, t_fuego, t_grillos, t_cuencos, t_mar, t_fractal,
           t_binaural, t_isocronico, t_general]

if __name__ == "__main__":
    fallos = 0
    for p in PRUEBAS:
        ok, msg = p()
        fallos += not ok
        print(f"{'OK  ' if ok else 'FALLA'} {p.__name__[2:]:12s} {msg}")
    print(f"\n{len(PRUEBAS) - fallos}/{len(PRUEBAS)} pruebas superadas")
