"""
Alarga la fuga de fuga.py con secciones adicionales: el sujeto reaparece
(normal, en inversión, en aumentación) en distintas voces, y las otras dos
voces se componen contra él con las mismas reglas de contrapunto.

Requiere fuga.py en la misma carpeta, y lameenc (pip install lameenc) para mp3.
"""
import copy
import numpy as np
from fuga import (L, colocar, contrapunto, componer, verificar, render, sr)

ORDEN = ['soprano', 'alto', 'bajo']                    # de agudo a grave
RANGO = {'soprano': (4, 12), 'alto': (-2, 6), 'bajo': (-8, 0)}
REG = {'normal': {'soprano': 7, 'alto': 0, 'bajo': -7},
       'inversion': {'soprano': 14, 'alto': 7, 'bajo': 0},
       'aumentacion': {'soprano': 7, 'alto': 0, 'bajo': -7}}


# ------------------------------------------------------- transformaciones
def inversion(voz, eje=0):
    return [(eje - g, t, d) for g, t, d in voz]


def aumentacion(voz, f=2):
    return [(g, t * f, d * f) for g, t, d in voz]


TRANSFORMACION = {'normal': lambda v: v, 'inversion': inversion,
                  'aumentacion': aumentacion}


def ritmo_corcheas(dur):
    return [0.5] * (2 * (int(dur) - 1)) + [1.0]


def ritmo_negras(dur):
    return [1.0] * int(dur)


def con_perfil(voz):
    gs = [g for g, _, _ in voz]
    return len(set(gs)) >= 5 and max(gs) - min(gs) >= 4


# ---------------------------------------------------------------- sección
def seccion(voces, tema, voz_tema, t0, despl, semilla, triada=(0, 2, 4), rangos=None):
    """Coloca `tema` en `voz_tema` desde t0 y compone las otras dos voces
    contra él: la más aguda en corcheas, la otra en negras. Se compone
    primero la lenta (la rápida puede adornar con notas de paso, la lenta
    no) y, si la rápida no encuentra solución, se prueba otra lenta.
    Devuelve las voces ampliadas, o None si no hay solución."""
    dur = max(t + d for _, t, d in tema)
    tema_col = colocar(tema, despl, t0)
    v_rap, v_len = [v for v in ORDEN if v != voz_tema]
    rg = rangos or RANGO

    def lado(v, w):                      # la voz v queda debajo ('<') o encima ('>') de w
        return '<' if ORDEN.index(v) > ORDEN.index(w) else '>'

    def previa(v):
        return voces[v][-1][0] if voces[v] else None

    for a in range(15):
        lenta = contrapunto(
            [(0, t0, [(tema_col, lado(v_len, voz_tema))], previa(v_len))],
            ritmo_negras(dur), rg[v_len], semilla=semilla * 100 + a, triada=triada)
        if lenta is None:
            continue
        lenta = colocar(lenta, 0, t0)
        parejas = [(tema_col, lado(v_rap, voz_tema)), (lenta, lado(v_rap, v_len))]
        for k in range(20):
            rapida = contrapunto(
                [(0, t0, parejas, previa(v_rap))],
                ritmo_corcheas(dur), rg[v_rap], semilla=semilla * 100 + 50 + k, triada=triada)
            if rapida is None:
                break
            if con_perfil(rapida):
                nuevas = copy.deepcopy(voces)
                nuevas[voz_tema] += tema_col
                nuevas[v_len] += lenta
                nuevas[v_rap] += colocar(rapida, 0, t0)
                return nuevas
    return None


def acorde_final(voces, t0, dur=4):
    """Acorde de Re menor: A4 - F4 - D3."""
    voces['soprano'].append((4, t0, dur))
    voces['alto'].append((2, t0, dur))
    voces['bajo'].append((-7, t0, dur))


# ------------------------------------------------------------------ obra
PLAN = [('normal', 'soprano'),
        ('inversion', 'bajo'),
        ('aumentacion', 'alto'),
        ('normal', 'bajo')]


def fuga_larga(semilla=1, plan=PLAN, intentos=40):
    """Exposición + secciones del plan + acorde final. Como cada sección se
    compone por separado, puede aparecer un paralelismo en la unión entre
    dos secciones; se repite con otras semillas hasta que `verificar` da 0."""
    from fuga import sujeto
    s, expo = componer(semilla)
    S = sujeto(s)
    for variante in range(intentos):
        voces, t0, fallo = copy.deepcopy(expo), 3 * L, False
        for i, (transf, voz) in enumerate(plan):
            tema = TRANSFORMACION[transf](S)
            nuevas = seccion(voces, tema, voz, t0, REG[transf][voz],
                             semilla=s + i + 10 * variante)
            if nuevas is None:
                fallo = True
                break
            voces = nuevas
            t0 += max(t + d for _, t, d in tema)
        if fallo:
            continue
        acorde_final(voces, t0)
        if not any(verificar(voces).values()):
            return s, voces
    raise RuntimeError("No se encontró una versión sin fallos; prueba otra semilla.")


# --------------------------------------------------------------------- mp3
def wav_a_mp3(wav, mp3, kbps=192):
    import lameenc
    from scipy.io import wavfile
    sr_, x = wavfile.read(wav)
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(sr_)
    enc.set_channels(x.shape[1] if x.ndim > 1 else 1)
    enc.set_quality(2)
    with open(mp3, 'wb') as f:
        f.write(enc.encode(x.astype(np.int16).tobytes()) + enc.flush())


if __name__ == "__main__":
    s, voces = fuga_larga(1)
    print("Semilla:", s, "| verificación:", verificar(voces))
    dur = max(t + d for v in voces.values() for _, t, d in v)
    print(f"Duración: {dur} tiempos")
    render(voces, "fuga_larga.wav")
    wav_a_mp3("fuga_larga.wav", "fuga_larga.mp3")
    print("Escritos fuga_larga.wav y fuga_larga.mp3")
