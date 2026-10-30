"""
Stretto: entradas del sujeto que empiezan antes de que la anterior haya acabado.

Un stretto no se puede 'inventar' para cualquier sujeto: hay que comprobar que
las voces solapadas siguen las reglas del contrapunto (consonancia en los
tiempos, sin quintas/octavas paralelas, sin cruzamientos). Por eso aquí el
sujeto se ELIGE entre los que admiten stretto, en vez de componer el stretto
alrededor de un sujeto cualquiera.

  chequear_pareja()   reglas del contrapunto entre dos líneas ya escritas
  cadenas_stretto()   todas las formas de encadenar 3 entradas con retardo d
  seccion_stretto()   sección final de la fuga con el mejor encadenamiento
  fuga_con_stretto()  fuga completa (fuga_episodios) + stretto final

Requiere fuga.py, fuga_larga.py y fuga_episodios.py en la misma carpeta.
"""
import itertools
import numpy as np
from fuga import (L, PASO, CONSONANCIAS, sujeto, colocar, muestrear_midi, paralelos,
                  nota_de_paso, componer, verificar, render)
from fuga_larga import wav_a_mp3
from fuga_episodios import fuga_completa

VOCES = ['soprano', 'alto', 'bajo']
ALTURA = {'soprano': 2, 'alto': 1, 'bajo': 0}            # orden de registro (2 = más agudo)
# Transposición (en grados de Re menor) del sujeto 'S' o de la respuesta 'A' en cada voz
OPCIONES = {'soprano': {'S': 7, 'A': 4}, 'alto': {'S': 0, 'A': -3}, 'bajo': {'S': -7, 'A': -10}}


# ------------------------------------------------------------- comprobación
def chequear_pareja(a, b, a_arriba):
    """¿Cumplen las reglas del contrapunto dos líneas ya escritas?
    Mira cada corchea donde suenan las dos:
      - sin cruzamiento (a por encima de b si a_arriba);
      - en los tiempos (negras), solo consonancias;
      - en las partes débiles, una disonancia solo si una de las dos voces
        la ataca por grado conjunto (nota de paso, floreo o escapada);
      - sin quintas ni octavas paralelas.
    Devuelve (ok, motivo)."""
    t0 = min(a[0][1], b[0][1])
    t1 = max(a[-1][1] + a[-1][2], b[-1][1] + b[-1][2])
    n = round((t1 - t0) / PASO)
    A, B = muestrear_midi(a, t0, n), muestrear_midi(b, t0, n)
    for k in range(n):
        if np.isnan(A[k]) or np.isnan(B[k]):
            continue
        if (a_arriba and A[k] <= B[k]) or (not a_arriba and A[k] >= B[k]):
            return False, 'cruce de voces'
        t = t0 + k * PASO
        if int(abs(A[k] - B[k])) % 12 not in CONSONANCIAS:
            if t % 1 == 0:
                return False, 'disonancia en un tiempo'
            if not (nota_de_paso(A, k) or nota_de_paso(B, k)):
                return False, 'disonancia débil sin grado conjunto'
        for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
            if kk >= 0 and paralelos(A[kk], A[k], B[kk], B[k]):
                return False, 'quintas u octavas paralelas'
    return True, ''


def pares_validos(S, dmax=None):
    """Para el sujeto S: (retardo, transposición del seguidor) válidos entre
    dos entradas (la primera sin transponer)."""
    dmax = dmax or L - 0.5
    lider = colocar(S, 0, 0)
    out = []
    for d in np.arange(0.5, dmax + 0.01, 0.5):
        for x in range(-14, 15):
            if x == 0:
                continue
            seg = colocar(S, x, float(d))
            ok, _ = chequear_pareja(seg, lider, True) if x > 0 else chequear_pareja(lider, seg, True)
            if ok:
                out.append((float(d), x))
    return out


def cadenas_stretto(S, dmax=4.0, dmin=0.5):
    """Encadenamientos válidos de 3 entradas separadas d, 2d (tiempos 0, d, 2d):
    qué voz entra en cada lugar y si lo hace con el sujeto ('S') o con la
    respuesta ('A'). Se exige que CADA par solapado cumpla las reglas.
    Ordenados de más a menos apretado (retardo menor), con preferencia por
    empezar en el alto como en la exposición. `dmin` evita retardos tan
    pequeños que el stretto se oye como un canon casi paralelo."""
    out = []
    for d in np.arange(dmin, dmax + 0.01, 0.5):
        d = float(d)
        for orden in itertools.permutations(VOCES):
            for tipos in itertools.product('SA', repeat=3):
                entradas = [(v, tp, colocar(S, OPCIONES[v][tp], i * d))
                            for i, (v, tp) in enumerate(zip(orden, tipos))]
                if all(chequear_pareja(l1, l2, ALTURA[v1] > ALTURA[v2])[0]
                       for (v1, _, l1), (v2, _, l2) in itertools.combinations(entradas, 2)):
                    out.append(dict(d=d, orden=orden, tipos=''.join(tipos)))
    out.sort(key=lambda c: (c['d'], c['orden'][0] != 'alto', c['tipos'].count('A')))
    return out


# --------------------------------------------------------------- la sección
def seccion_stretto(voces, t0, S, sem, dmax=4.0, dmin=0.5):
    """Añade a `voces` el stretto (3 entradas). Prueba los encadenamientos de
    mejor a peor hasta que toda la obra sigue verificando sin fallos
    (puede haber un problema en la unión con la sección anterior)."""
    for c in cadenas_stretto(S, dmax, dmin):
        nuevas = {v: list(n) for v, n in voces.items()}
        for i, (v, tp) in enumerate(zip(c['orden'], c['tipos'])):
            nuevas[v] += colocar(S, OPCIONES[v][tp], t0 + i * c['d'])
        if not any(verificar(nuevas).values()):
            seccion_stretto.elegida = c
            return nuevas, L + 2 * c['d']
    return None


def diagnostico_estricto(voces):
    """Revisión más estricta que `verificar()`: para cada par de voces cuenta
    cruzamientos, disonancias en tiempo, disonancias débiles sin grado
    conjunto y quintas/octavas paralelas, en toda la obra."""
    fin = max(t + d for v in voces.values() for _, t, d in v)
    n = round(fin / PASO)
    M = {v: muestrear_midi(notas, 0, n) for v, notas in voces.items()}
    res = {}
    for arriba, abajo in (('soprano', 'alto'), ('alto', 'bajo'), ('soprano', 'bajo')):
        A, B = M[arriba], M[abajo]
        c = dict(cruces=0, disonancias_en_tiempo=0, disonancias_debiles=0, paralelas=0, puntos=0)
        for k in range(n):
            if np.isnan(A[k]) or np.isnan(B[k]):
                continue
            c['puntos'] += 1
            c['cruces'] += int(A[k] <= B[k])
            t = k * PASO
            if int(abs(A[k] - B[k])) % 12 not in CONSONANCIAS:
                if t % 1 == 0:
                    c['disonancias_en_tiempo'] += 1
                elif not (nota_de_paso(A, k) or nota_de_paso(B, k)):
                    c['disonancias_debiles'] += 1
            for kk in ((k - 1, k - 2) if t % 1 == 0 else (k - 1,)):
                if kk >= 0 and paralelos(A[kk], A[k], B[kk], B[k]):
                    c['paralelas'] += 1
        res[f"{arriba}/{abajo}"] = c
    return res


def candidatos_stretto(semilla=1, intentos=300, dmin=2.0, dmax=3.0):
    """Sujetos (semillas) que admiten stretto con retardo en [dmin, dmax] y
    cuya exposición se puede componer, del stretto más apretado al más suelto."""
    out = []
    for s in range(semilla, semilla + intentos):
        c = cadenas_stretto(sujeto(s), dmax, dmin)
        if c and componer(s)[0] == s:
            out.append((c[0]['d'], s))
    return [s for _, s in sorted(out)]


def fuga_con_stretto(semilla=1, intentos=300, dmin=2.0, dmax=3.0):
    """Construye toda la fuga con el sujeto que admite el stretto más apretado
    posible (retardo entre `dmin` y `dmax` tiempos). Devuelve
    (sujeto, voces, marcas, cadena)."""
    for s in candidatos_stretto(semilla, intentos, dmin, dmax):
        try:
            sf, _, voces, marcas = fuga_completa(
                s, plan_extra=[('custom', dict(
                    fn=lambda v, t, S_, sem: seccion_stretto(v, t, S_, sem, dmax, dmin),
                    nombre='stretto'))])
        except RuntimeError:
            continue
        return sf, voces, marcas, seccion_stretto.elegida
    raise RuntimeError("No se encontró ningún sujeto con stretto en ese rango; amplía `intentos` o `dmax`.")


if __name__ == "__main__":
    import sys
    dmax = float(sys.argv[sys.argv.index('--dmax') + 1]) if '--dmax' in sys.argv else 3.0
    dmin = float(sys.argv[sys.argv.index('--dmin') + 1]) if '--dmin' in sys.argv else 2.0
    s, voces, marcas, c = fuga_con_stretto(1, dmin=dmin, dmax=dmax)
    S = sujeto(s)
    print(f"Sujeto de la semilla {s}: {[g for g, _, _ in S]}")
    print("Retardos y transposiciones que admite (sujeto con sujeto):",
          sorted({d for d, x in pares_validos(S)}))
    print(f"Stretto elegido: retardo {c['d']:g} tiempos; entradas {list(zip(c['orden'], c['tipos']))}")
    print("Verificación de toda la obra:", verificar(voces))
    for par, d in diagnostico_estricto(voces).items():
        print(f"  revisión estricta {par}: {d}")
    for nombre, t0, dur in marcas:
        print(f"  {nombre:9s} tiempos {t0:g}-{t0 + dur:g}")
    render(voces, "fuga_stretto.wav")
    wav_a_mp3("fuga_stretto.wav", "fuga_stretto.mp3")
    from midi_export import exportar_fuga
    for conjunto in ('organo', 'cuerdas', 'vientos'):
        exportar_fuga(voces, f"fuga_stretto_{conjunto}.mid", conjunto=conjunto)
    print("Escritos fuga_stretto.wav/.mp3 y fuga_stretto_{organo,cuerdas,vientos}.mid")
