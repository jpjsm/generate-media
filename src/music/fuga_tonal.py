"""
Fuga con modulación a la DOMINANTE (Re menor -> La menor -> Re menor) y
cadencias auténticas con sensible (V -> i).

Qué cambia respecto a fuga.py / fuga_episodios.py (que siguen intactos):

  - Las notas son alturas MIDI y no grados de Re menor natural, así que ya
    caben las alteraciones: Sol# (sensible de La menor) y Do# (sensible de
    Re menor), que no existen en Re menor natural.
  - Cada sección tiene su `Escala`: Re menor, La menor o, en las cadencias,
    sus versiones con sensible. contrapunto_tonal() acepta una escala distinta
    en cada escenario, así una secuencia puede cruzar de una tonalidad a otra.
  - La entrada del sujeto en La menor es una transposición real (+7
    semitonos): conserva todos los intervalos y solo sustituye Si♭ por Si
    natural. (El paso a Fa mayor de fuga_episodios.py transponía por grados:
    mismas notas, otros intervalos.)

Forma (en tiempos):
  0-24    Exposición                    Re menor   (la de fuga.py)
  24-34   Episodio I                    Re -> La   secuencia que cruza de escala
                                                   y cadencia  Mi mayor -> La menor
  34-50   Entradas en La menor          La menor   sujeto (alto) e inversión (bajo)
  50-60   Episodio II                   La -> Re   y cadencia  La mayor -> Re menor
  60-84   Entradas en Re menor          Re menor   sujeto en aumentación y sujeto
  84-90   Cadencia final                Re menor   La mayor -> Re menor

Requiere fuga.py en la misma carpeta (y midi_export.py para el MIDI).
"""
import copy
import itertools
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve
from fuga import (L, PASO, CONSONANCIAS, SALTOS, PESOS, paralelos, nota_de_paso,
                  sujeto, componer, midi as midi_re, tono, sr, beat)
from fuga_larga import wav_a_mp3

ORDEN = ['soprano', 'alto', 'bajo']                       # de agudo a grave
RANGOS = {'soprano': (69, 84), 'alto': (55, 74), 'bajo': (40, 62)}      # alturas MIDI


# ------------------------------------------------------------------- escalas
class Escala:
    """Escala de 7 notas por octava. El índice 0 es la tónica (a la altura
    `tonica`) y cada unidad es un grado de la escala."""
    INTERVALOS = {'natural': [0, 2, 3, 5, 7, 8, 10],       # menor natural
                  'armonica': [0, 2, 3, 5, 7, 8, 11]}      # menor armónica (con sensible)

    def __init__(self, tonica, modo='natural'):
        self.tonica, self.iv = tonica, self.INTERVALOS[modo]

    def midi(self, i):
        o, k = divmod(int(i), 7)
        return self.tonica + 12 * o + self.iv[k]

    def indice(self, m):
        """Índice de la altura m en la escala, o None si no pertenece."""
        o, r = divmod(m - self.tonica, 12)
        return 7 * o + self.iv.index(r) if r in self.iv else None


RE, LA = Escala(62), Escala(69)                           # menores naturales
RE_ARM, LA_ARM = Escala(62, 'armonica'), Escala(69, 'armonica')
TRIADA_RE, TRIADA_LA = {2, 5, 9}, {9, 0, 4}               # clases de altura (mod 12)


def rango_idx(esc, lo, hi):
    gs = [g for g in range(-50, 51) if lo <= esc.midi(g) <= hi]
    return min(gs), max(gs)


# ------------------------------------------------------------------ utilidades
def a_midi(voces):
    """Convierte voces en grados de Re menor (fuga.py) a alturas MIDI."""
    return {v: [(midi_re(g), t, d) for g, t, d in notas] for v, notas in voces.items()}


def muestrear(voz, t0, n):
    """Altura que suena en cada punto de la rejilla (NaN = silencio)."""
    arr = np.full(n, np.nan)
    for m, t, d in voz:
        k0, k1 = max(round((t - t0) / PASO), 0), min(round((t + d - t0) / PASO), n)
        if k0 < k1:
            arr[k0:k1] = m
    return arr


def colocar_t(voz_rel, esc, despl, t0):
    """Voz en índices de escala -> alturas MIDI, con inicio t0."""
    return [(esc.midi(g + despl), t + t0, d) for g, t, d in voz_rel]


def tema_en(esc, S, despl, t0):
    """El sujeto (en grados) sobre la escala `esc`, `despl` grados desplazado."""
    return [(esc.midi(g + despl), t + t0, d) for g, t, d in S]


def inversion(S, eje=0):
    return [(eje - g, t, d) for g, t, d in S]


def aumentacion(S, f=2):
    return [(g, t * f, d * f) for g, t, d in S]


def ritmo_corcheas(dur):
    return [0.5] * (2 * (int(dur) - 1)) + [1.0]


def con_perfil(voz_rel):
    gs = [g for g, _, _ in voz_rel]
    return len(set(gs)) >= 5 and max(gs) - min(gs) >= 4


# ------------------------------------------------------------------ contrapunto
def contrapunto_tonal(escenarios, ritmo, rango, semilla=0, max_nodos=60000, triada=None):
    """Como fuga.contrapunto(), pero con notas MIDI y escala propia por escenario.

    escenario = (escala, despl, t0, parejas, previa)
        escala:  Escala en la que se interpretan los índices en ese escenario
        despl:   desplazamiento en grados de esa escala
        t0:      tiempo en que empieza la voz
        parejas: [(voz_MIDI_ya_colocada, '<' | '>')]  la voz queda debajo/encima
        previa:  última altura MIDI de esa voz antes de t0, o None
    La voz generada son índices relativos (válidos en todos los escenarios).
    `triada`: clases de altura (mod 12) que puede tener la última nota, o None.

    Reglas: las de fuga.contrapunto() más una melódica nueva: sin segundas
    aumentadas (p. ej. Fa -> Sol# en La menor armónica)."""
    rng = np.random.default_rng(semilla)
    ks = np.concatenate([[0], np.cumsum([round(d / PASO) for d in ritmo])]).astype(int)
    n = int(ks[-1])
    prep = []
    for esc, despl, t0, parejas, previa in escenarios:
        P = [(muestrear(v, t0, n), lado) for v, lado in parejas]
        prep.append((esc, despl, t0, P, previa, np.full(n, np.nan)))
    seq, obligado = [], []
    nodos = [0]

    def nota_ok(i, g):
        a, b = ks[i], ks[i + 1]
        disonante = False
        for esc, despl, t0, P, previa, V in prep:
            m = esc.midi(g + despl)
            if i == 0 and previa is not None and abs(m - previa) > 7:
                return False, False
            if i > 0 and abs(g - seq[i - 1]) == 1 and abs(m - esc.midi(seq[i - 1] + despl)) > 2:
                return False, False                                  # segunda aumentada
            if triada is not None and i == len(ritmo) - 1 and m % 12 not in triada:
                return False, False
            V[a:b] = m
            for k in range(a, b):
                t = t0 + k * PASO
                for Pm, lado in P:
                    p = Pm[k]
                    if np.isnan(p):
                        continue
                    if (lado == '<' and m >= p) or (lado == '>' and m <= p):
                        return False, False
                    if int(abs(m - p)) % 12 not in CONSONANCIAS:
                        if t % 1 == 0:
                            return False, False
                        if k == a:
                            if i == 0 or abs(g - seq[i - 1]) > 1:
                                return False, False
                            disonante = True
                        elif not nota_de_paso(Pm, k):
                            return False, False
                    for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
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
            deltas = [int(d) for d in rng.choice(SALTOS, size=8, replace=False, p=PESOS)]
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


# -------------------------------------------------------------------- cadencia
def _consonantes(ms):
    return all(int(abs(a - b)) % 12 in CONSONANCIAS for a, b in itertools.combinations(ms, 2))


def cadencia(voces, t0, destino, durs=(2.0, 2.0), semilla=0):
    """Cadencia auténtica V -> i con sensible en la tonalidad `destino`
    ('La' o 'Re', menor armónica). Busca, entre las notas de cada acorde,
    una combinación que cumpla:
      - dominante: el bajo en la fundamental y la sensible en UNA voz aguda;
      - tónica: el bajo en la fundamental, el acorde con su tercera (si no, una
        quinta vacía no dice 'menor') y la sensible sube un semitono a la tónica;
      - consonancia entre todas las voces en los dos acordes y sin cruzamientos;
      - sin quintas ni octavas paralelas entre los dos acordes;
      - voces cercanas a su nota anterior (<= 9 semitonos), sin segundas aumentadas.
    Entre las válidas elige la de menor movimiento total. Devuelve las voces
    ampliadas, o None."""
    tonica = 9 if destino == 'La' else 2
    dom = (tonica + 7) % 12
    sens = (tonica - 1) % 12
    V = {dom, (dom + 4) % 12, (dom + 7) % 12}
    I = {tonica, (tonica + 3) % 12, (tonica + 7) % 12}
    previa = {v: voces[v][-1][0] for v in ORDEN}
    rng = np.random.default_rng(semilla)

    def cand(v, pcs, ref, lim):
        lo, hi = RANGOS[v]
        return [m for m in range(lo, hi + 1) if m % 12 in pcs and abs(m - ref) <= lim]

    mejores = []
    c1 = {v: cand(v, {dom} if v == 'bajo' else V, previa[v], 9) for v in ORDEN}
    for s1, a1, b1 in itertools.product(c1['soprano'], c1['alto'], c1['bajo']):
        if not (s1 > a1 > b1) or not _consonantes((s1, a1, b1)):
            continue
        if [s1 % 12, a1 % 12].count(sens) != 1:
            continue
        c2 = {'soprano': cand('soprano', I, s1, 5), 'alto': cand('alto', I, a1, 5),
              'bajo': cand('bajo', {tonica}, b1, 7)}
        for s2, a2, b2 in itertools.product(c2['soprano'], c2['alto'], c2['bajo']):
            if not (s2 > a2 > b2) or not _consonantes((s2, a2, b2)):
                continue
            pcs2 = {s2 % 12, a2 % 12, b2 % 12}
            if tonica not in pcs2 or (tonica + 3) % 12 not in pcs2:      # fundamental Y tercera
                continue
            x1, x2 = {'soprano': s1, 'alto': a1, 'bajo': b1}, {'soprano': s2, 'alto': a2, 'bajo': b2}
            if any(x1[v] % 12 == sens and x2[v] != x1[v] + 1 for v in ('soprano', 'alto')):
                continue                                              # la sensible resuelve
            if any(abs(x2[v] - x1[v]) in (3,) for v in ORDEN):
                continue
            if any(paralelos(x1[u], x2[u], x1[w], x2[w])
                   for u, w in (('soprano', 'alto'), ('soprano', 'bajo'), ('alto', 'bajo'))):
                continue
            coste = sum(abs(x1[v] - previa[v]) + abs(x2[v] - x1[v]) for v in ORDEN) + rng.random()
            mejores.append((coste, x1, x2))
    if not mejores:
        return None
    _, x1, x2 = min(mejores, key=lambda x: x[0])
    nuevas = copy.deepcopy(voces)
    for v in ORDEN:
        nuevas[v] += [(x1[v], t0, durs[0]), (x2[v], t0 + durs[0], durs[1])]
    return nuevas


# -------------------------------------------------------------------- episodio
def episodio_tonal(voces, t0, S, destino, semilla, k=3, dur_motivo=2, paso=1):
    """Episodio modulante de 10 tiempos: secuencia de k repeticiones (6
    tiempos) y cadencia V -> i con sensible (4 tiempos).

    La secuencia desciende un grado por repetición y la ÚLTIMA repetición pasa a
    la escala de llegada (el desplazamiento de -4 o +4 grados compensa el cambio
    de tónica para que la altura siga bajando un grado y no salte).
      destino 'La': Re menor -> La menor      destino 'Re': La menor -> Re menor
    """
    origen, llegada = (RE, LA) if destino == 'La' else (LA, RE)
    base_s = 7 if destino == 'La' else 3
    ajuste = -4 if destino == 'La' else 4
    escalas = [origen] * (k - 1) + [llegada]
    despl = [-r * paso + (ajuste if r == k - 1 else 0) for r in range(k)]
    motivo = [(g, t, d) for g, t, d in S if t < dur_motivo]
    sop = []
    for r in range(k):
        sop += [(escalas[r].midi(g + base_s + despl[r]), t0 + dur_motivo * r + t, d) for g, t, d in motivo]
    t_seq = t0 + dur_motivo * k

    escenarios = [(escalas[r], despl[r], t0 + dur_motivo * r, [(sop, '<')], None) for r in range(k)]
    for v in range(40):
        alto_mot = contrapunto_tonal(escenarios, [0.5] * int(2 * dur_motivo), (-4, 6),
                                     semilla=semilla * 1000 + v)
        if alto_mot is None:
            continue
        alto = []
        for r in range(k):
            alto += colocar_t(alto_mot, escalas[r], despl[r], t0 + dur_motivo * r)
        # bajo: 4 tiempos en la escala de origen y 2 en la de llegada
        pasadas = [(origen, t0, 4), (llegada, t0 + 4, 2)]
        bajo, previa = [], voces['bajo'][-1][0]
        for esc, ini, nb in pasadas:
            tr = contrapunto_tonal([(esc, 0, ini, [(sop, '<'), (alto, '<')], previa)],
                                   [1.0] * nb, rango_idx(esc, *RANGOS['bajo']),
                                   semilla=semilla * 1000 + v)
            if tr is None:
                bajo = None
                break
            tramo = colocar_t(tr, esc, 0, ini)
            bajo += tramo
            previa = tramo[-1][0]
        if bajo is None:
            continue
        parcial = copy.deepcopy(voces)
        parcial['soprano'] += sop
        parcial['alto'] += alto
        parcial['bajo'] += bajo
        final = cadencia(parcial, t_seq, destino, (2.0, 2.0), semilla)
        if final is not None:
            return final
    return None


# ---------------------------------------------------------------------- sección
def seccion_tonal(voces, tema, voz_tema, t0, esc, triada, semilla):
    """Coloca `tema` (ya en MIDI y con su tiempo de inicio) en `voz_tema` y
    compone las otras dos voces contra él, en la escala `esc`: primero la lenta
    (negras) y después la de corcheas."""
    dur = int(round(max(t + d for _, t, d in tema) - t0))
    v_rap, v_len = [v for v in ORDEN if v != voz_tema]
    lado = lambda v, w: '<' if ORDEN.index(v) > ORDEN.index(w) else '>'
    for a in range(15):
        lenta = contrapunto_tonal([(esc, 0, t0, [(tema, lado(v_len, voz_tema))], voces[v_len][-1][0])],
                                  [1.0] * dur, rango_idx(esc, *RANGOS[v_len]),
                                  semilla=semilla * 100 + a, triada=triada)
        if lenta is None:
            continue
        lenta = colocar_t(lenta, esc, 0, t0)
        parejas = [(tema, lado(v_rap, voz_tema)), (lenta, lado(v_rap, v_len))]
        for k in range(20):
            rapida = contrapunto_tonal([(esc, 0, t0, parejas, voces[v_rap][-1][0])],
                                       ritmo_corcheas(dur), rango_idx(esc, *RANGOS[v_rap]),
                                       semilla=semilla * 100 + 50 + k, triada=triada)
            if rapida is None:
                break
            if con_perfil(rapida):
                nuevas = copy.deepcopy(voces)
                nuevas[voz_tema] += tema
                nuevas[v_len] += lenta
                nuevas[v_rap] += colocar_t(rapida, esc, 0, t0)
                return nuevas
    return None


# ------------------------------------------------------------------ verificación
def verificar_midi(voces):
    """Disonancias en tiempo y quintas/octavas paralelas, voz contra voz."""
    fin = max(t + d for v in voces.values() for _, t, d in v)
    n = round(fin / PASO)
    S = {k: muestrear(v, 0, n) for k, v in voces.items()}
    fallos = {'disonancias en tiempo': 0, 'quintas/octavas paralelas': 0}
    for a, b in itertools.combinations(S, 2):
        A, B = S[a], S[b]
        for k in range(n):
            if np.isnan(A[k]) or np.isnan(B[k]):
                continue
            t = k * PASO
            if t % 1 == 0 and int(abs(A[k] - B[k])) % 12 not in CONSONANCIAS:
                fallos['disonancias en tiempo'] += 1
            for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
                if kk >= 0 and paralelos(A[kk], A[k], B[kk], B[k]):
                    fallos['quintas/octavas paralelas'] += 1
    return fallos


def diagnostico_estricto_midi(voces):
    """Además: cruzamientos y disonancias débiles sin grado conjunto."""
    fin = max(t + d for v in voces.values() for _, t, d in v)
    n = round(fin / PASO)
    M = {v: muestrear(notas, 0, n) for v, notas in voces.items()}
    tot = dict(cruces=0, disonancias_en_tiempo=0, disonancias_debiles=0, paralelas=0, puntos=0)
    for arriba, abajo in (('soprano', 'alto'), ('alto', 'bajo'), ('soprano', 'bajo')):
        A, B = M[arriba], M[abajo]
        for k in range(n):
            if np.isnan(A[k]) or np.isnan(B[k]):
                continue
            tot['puntos'] += 1
            tot['cruces'] += int(A[k] <= B[k])
            t = k * PASO
            if int(abs(A[k] - B[k])) % 12 not in CONSONANCIAS:
                if t % 1 == 0:
                    tot['disonancias_en_tiempo'] += 1
                elif not (nota_de_paso(A, k) or nota_de_paso(B, k)):
                    tot['disonancias_debiles'] += 1
            for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
                if kk >= 0 and paralelos(A[kk], A[k], B[kk], B[k]):
                    tot['paralelas'] += 1
    return tot


# Perfiles de tonalidad de Krumhansl y Kessler (1982): cuánto 'encaja' cada clase
# de altura en una tonalidad. Sirven para estimar la tonalidad de un fragmento.
PERFIL = {'mayor': np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]),
          'menor': np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])}
NOMBRES = ['Do', 'Do♯', 'Re', 'Mi♭', 'Mi', 'Fa', 'Fa♯', 'Sol', 'Sol♯/La♭', 'La', 'Si♭', 'Si']


def estimar_tonalidad(voces, a, b, n=3):
    """Las `n` tonalidades que mejor correlacionan con la duración de cada clase
    de altura entre los tiempos a y b (algoritmo de Krumhansl-Schmuckler)."""
    h = np.zeros(12)
    for notas in voces.values():
        for m, t, d in notas:
            ini, fin = max(t, a), min(t + d, b)
            if fin > ini:
                h[int(m) % 12] += fin - ini
    res = [(float(np.corrcoef(h, np.roll(PERFIL[modo], ton))[0, 1]), f"{NOMBRES[ton]} {modo}")
           for ton in range(12) for modo in PERFIL]
    return sorted(res, reverse=True)[:n]


def informe_tonal(voces, marcas):
    """Tonalidad estimada y alteraciones en cada tramo de la obra."""
    tramos = []
    for nombre, t0, dur in marcas:
        if nombre.startswith('episodio'):
            tramos += [(nombre + ', secuencia', t0, t0 + 6), (nombre + ', cadencia', t0 + 6, t0 + dur)]
        else:
            tramos.append((nombre, t0, t0 + dur))
    tramos.insert(0, ('exposición', 0, 3 * L))

    def dur_pc(a, b, pc):
        return sum(max(0, min(t + d, b) - max(t, a)) for notas in voces.values()
                   for m, t, d in notas if m % 12 == pc)
    filas = []
    for nombre, a, b in tramos:
        (r1, k1), (r2, k2) = estimar_tonalidad(voces, a, b, 2)
        alt = ' '.join(f"{n} {dur_pc(a, b, pc):.1f}" for n, pc in (('Si♭', 10), ('Si', 11), ('Sol♯', 8), ('Do♯', 1)))
        filas.append(f"  {nombre[:42]:42s} {a:>3g}-{b:<3g} {k1} ({r1:.2f}), {k2} ({r2:.2f}) | {alt}")
    return filas


# ------------------------------------------------------------------------ obra
def fuga_tonal(semilla=1, intentos=200):
    s, expo = componer(semilla)
    S = sujeto(s)
    base = a_midi(expo)

    for variante in range(intentos):
        sem = s + 10 * variante
        voces, t0, marcas = copy.deepcopy(base), 3 * L, []

        def paso(nombre, nuevas, dur, esperada, desde):
            """Acepta la sección solo si la tonalidad estimada en su tramo
            (desde `desde` tiempos tras el inicio) es la prevista."""
            nonlocal voces, t0
            if nuevas is None:
                return False
            if estimar_tonalidad(nuevas, t0 + desde, t0 + dur, 1)[0][1] != esperada:
                return False
            marcas.append((nombre, t0, dur))
            voces, t0 = nuevas, t0 + dur
            return True

        # (nombre, función, duración, tonalidad esperada, desde qué tiempo se mide)
        pasos = [
            ('episodio I (Re -> La)', lambda: episodio_tonal(voces, t0, S, 'La', sem), 10, 'La menor', 6),
            ('entrada en La menor: sujeto (alto)',
             lambda: seccion_tonal(voces, tema_en(LA, S, -7, t0), 'alto', t0, LA, TRIADA_LA, sem + 1),
             8, 'La menor', 0),
            ('entrada en La menor: inversión (bajo)',
             lambda: seccion_tonal(voces, tema_en(LA, inversion(S, 0), -7, t0), 'bajo', t0, LA, TRIADA_LA, sem + 2),
             8, 'La menor', 0),
            ('episodio II (La -> Re)', lambda: episodio_tonal(voces, t0, S, 'Re', sem + 3), 10, 'Re menor', 6),
            ('entrada en Re menor: aumentación (alto)',
             lambda: seccion_tonal(voces, tema_en(RE, aumentacion(S), 0, t0), 'alto', t0, RE, TRIADA_RE, sem + 4),
             16, 'Re menor', 0),
            ('entrada en Re menor: sujeto (bajo)',
             lambda: seccion_tonal(voces, tema_en(RE, S, -7, t0), 'bajo', t0, RE, TRIADA_RE, sem + 5),
             8, 'Re menor', 0),
            ('cadencia final (La -> Re)', lambda: cadencia(voces, t0, 'Re', (2.0, 4.0), sem + 6), 6, 'Re menor', 0),
        ]
        if all(paso(n, f(), d, e, ds) for n, f, d, e, ds in pasos) and not any(verificar_midi(voces).values()):
            return s, variante, voces, marcas
    raise RuntimeError("No se encontró una versión sin fallos; prueba otra semilla.")


# ---------------------------------------------------------------------- salida
def render_midi(voces, archivo, panorama={'soprano': .7, 'alto': .5, 'bajo': .3}):
    """Igual que fuga.render() pero con alturas MIDI."""
    fin = max(t + d for v in voces.values() for _, t, d in v) * beat
    total = int(sr * (fin + 4))
    izq, der = np.zeros(total), np.zeros(total)
    for nombre, notas in voces.items():
        buf = np.zeros(total)
        for m, t, d in notas:
            s = tono(m, d * beat)
            i = int(sr * beat * t)
            buf[i:i + len(s)] += s[:total - i]
        izq += buf * np.cos(panorama[nombre] * np.pi / 2)
        der += buf * np.sin(panorama[nombre] * np.pi / 2)
    rng = np.random.default_rng(0)
    canales = []
    for x in (izq, der):
        ir = rng.standard_normal(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 2.5)
        humedo = fftconvolve(x, ir)[:len(x)]
        humedo *= np.abs(x).max() / np.abs(humedo).max()
        canales.append(0.75 * x + 0.25 * humedo)
    est = np.stack(canales, axis=1)
    wavfile.write(archivo, sr, (est / np.abs(est).max() * 32767).astype(np.int16))


def exportar_midi(voces, archivo, conjunto='organo', bpm=76):
    from midi_export import guardar_midi, CONJUNTOS_FUGA
    inst = CONJUNTOS_FUGA[conjunto]
    pistas = {nombre: (prog, [(m, t, d, 0.7) for m, t, d in voces[voz]])
              for voz, (nombre, prog) in zip(ORDEN, inst)}
    return guardar_midi(pistas, archivo, bpm)


if __name__ == "__main__":
    s, variante, voces, marcas = fuga_tonal(1)
    print(f"Sujeto semilla {s}, variante {variante}")
    print("Verificación:", verificar_midi(voces))
    print("Revisión estricta:", diagnostico_estricto_midi(voces))
    print("Tonalidad estimada (Krumhansl-Schmuckler) y tiempo sonando de cada alteración:")
    print("\n".join(informe_tonal(voces, marcas)))
    render_midi(voces, "fuga_tonal.wav")
    wav_a_mp3("fuga_tonal.wav", "fuga_tonal.mp3")
    for conjunto in ('organo', 'cuerdas', 'vientos'):
        exportar_midi(voces, f"fuga_tonal_{conjunto}.mid", conjunto)
    print("Escritos fuga_tonal.wav/.mp3 y fuga_tonal_{organo,cuerdas,vientos}.mid")
