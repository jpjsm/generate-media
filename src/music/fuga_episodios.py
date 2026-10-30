"""
Fuga completa en Re menor, con episodios modulantes.

  Exposición            Re menor   sujeto, respuesta, sujeto (fuga.py)
  Episodio I            Re -> Fa   secuencia descendente del motivo del sujeto
  Entradas en Fa mayor  Fa mayor   sujeto (alto) y su inversión (bajo)
  Episodio II           Fa -> Re   secuencia descendente que vuelve a la tónica
  Entradas finales      Re menor   sujeto en aumentación (alto) y sujeto (bajo)
  Acorde final

Fa mayor es la tonalidad relativa de Re menor y usa exactamente las mismas
siete notas, así que la modulación se afirma con la conducción de las voces
(secuencia, cadencia al Fa en el bajo, entradas del sujeto sobre Fa) y no con
alteraciones.

Requiere fuga.py y fuga_larga.py en la misma carpeta.

Notas de creación:
Voy a ampliar contrapunto() para aceptar otras tonalidades (el acorde final ya no será siempre el de Re menor) y a construir los episodios, probándolo todo antes de darte nada.

Ya hay una versión válida, con cadencias Do→Fa y La→Re en el bajo; estoy puliendo la salida del script y verificando el resultado antes de entregarlo.

Aquí está el episodio modulante: fuga_episodios.py y el audio fuga_episodios.mp3 (1 min 14 s). Los otros dos scripts, fuga.py y fuga_larga.py, van actualizados y deben estar en la misma carpeta. Como siempre, no puedo oírlo. Lo que comprobé es el contrapunto de toda la pieza (0 disonancias en tiempo y 0 quintas u octavas paralelas), la estructura de las secuencias y las cadencias.

La forma completa

Exposición en Re menor (tiempos 0-24), igual que antes.
Episodio I (24-34), de Re a Fa mayor.
Entradas en Fa mayor (34-50): el sujeto en el alto y su inversión en el bajo.
Episodio II (50-60), de Fa de vuelta a Re.
Entradas finales en Re menor (60-84): el sujeto en aumentación en el alto, el sujeto en el bajo y el acorde final de Re menor.

Cómo funciona cada episodio

Soprano: repite el motivo (los 2 primeros tiempos del sujeto) tres veces, cada vez un grado más grave. Es una secuencia descendente.
Alto: lleva un contramotivo en corcheas que se genera una sola vez y es válido en las tres repeticiones a la vez. Comprobé que los intervalos son idénticos en las tres, así que es una secuencia real y no tres frases parecidas.
Cadencia: los últimos 4 tiempos son 2 de dominante y 2 de tónica de llegada. El bajo hace Do→Fa en el episodio I y La→Re en el II (en este caso, dominante→tónica de Re menor).

Sobre la modulación

Fa mayor es la relativa de Re menor y usa exactamente las mismas siete notas, así que no hay alteraciones que la delaten. La tonalidad se afirma por la cadencia en el bajo, por las entradas del sujeto sobre Fa y por los acordes de llegada. Sonará como un cambio de centro tonal, pero más suave que una modulación con accidentales.

Si quieres una modulación más marcada, por ejemplo a La menor (la dominante), haría falta introducir alteraciones (Sol♯ y Si natural). Hoy todo se calcula con los grados de Re menor natural, así que eso exigiría extender el sistema.

Dos cosas que descubrí al probarlo

La primera versión del episodio pedía la cadencia en solo 2 tiempos, y no tenía solución: el bajo no puede estar en el dominante a la vez que el soprano ya llega a la tónica. Por eso cada episodio dura 10 tiempos y no 8.
El script reintenta con otras semillas hasta que toda la pieza verifica sin fallos. Con la semilla actual lo logró en la variante 30, en unos 6 segundos.

Para ajustar

paso y k en episodio() cambian la longitud y la dirección de la secuencia (por ejemplo, ascendente con paso=-1).
plan en fuga_completa() permite reordenar o añadir entradas (por ejemplo, otra en la subdominante).
base_s cambia la altura inicial del soprano en cada episodio.
"""

import copy
from fuga import L, colocar, contrapunto, componer, sujeto, verificar, render
from fuga_larga import seccion, inversion, aumentacion, acorde_final, wav_a_mp3, RANGO

TRIADA_FA = (2, 4, 6)  # F A C (grados mod 7, con Re = 0)
TRIADA_RE = (0, 2, 4)  # D F A


def clase_cercana(g, clase):
    """Grado más próximo a g cuya clase (mod 7) es `clase`."""
    return min(
        (x for x in range(g - 6, g + 7) if x % 7 == clase), key=lambda x: abs(x - g)
    )


# ----------------------------------------------------------------- episodio
def episodio(voces, t0, S, base_s, tonica, semilla, paso=1, k=3, dur_motivo=2):
    """Episodio de 10 tiempos: k repeticiones del motivo (6 tiempos) + una
    cadencia de 4 tiempos (dominante, 2 tiempos; tónica de llegada, 2 tiempos).

    Soprano: el motivo (los 2 primeros tiempos del sujeto) repetido k veces,
             cada vez `paso` grados más grave (secuencia descendente).
    Alto:    contramotivo en corcheas, generado UNA vez y válido en las k
             repeticiones a la vez (así también es una secuencia real).
    Bajo:    línea en negras compuesta contra las otras dos, que llega a la
             fundamental de la tonalidad de llegada desde su dominante o su
             sensible/subtónica (cadencia V-I o VII-I).
    Devuelve las voces ampliadas, o None si no hay solución."""
    dur_cad = 4
    motivo = [(g, t, d) for g, t, d in S if t < dur_motivo]
    sop = []
    for r in range(k):
        sop += colocar(motivo, base_s - paso * r, t0 + dur_motivo * r)
    t_cad = t0 + dur_motivo * k
    dom = tuple((tonica + x) % 7 for x in (4, 6, 1))  # tríada de la dominante
    tri = tuple((tonica + x) % 7 for x in (0, 2, 4))  # tríada de la tónica
    n1 = min(
        (x for x in range(sop[-1][0] - 5, sop[-1][0] + 6) if x % 7 in dom),
        key=lambda x: abs(x - sop[-1][0]),
    )
    n2 = min(
        (x for x in range(n1 - 5, n1 + 6) if x % 7 == tonica), key=lambda x: abs(x - n1)
    )
    sop += [(n1, t_cad, 2.0), (n2, t_cad + 2, 2.0)]

    # Contramotivo del alto: mismo dibujo en las k repeticiones
    escenarios = [
        (-paso * r, t0 + dur_motivo * r, [(sop, "<")], None) for r in range(k)
    ]
    alto_mot = contrapunto(
        escenarios,
        [0.5] * int(2 * dur_motivo),
        rango=(-4, 6),
        semilla=semilla,
        triada=None,
    )
    if alto_mot is None:
        return None
    alto = []
    for r in range(k):
        alto += colocar(alto_mot, -paso * r, t0 + dur_motivo * r)
    cad = contrapunto(
        [(0, t_cad, [(sop, "<")], alto[-1][0])],
        [2.0, 2.0],
        rango=(-4, 6),
        semilla=semilla,
        triada=tri,
    )
    if cad is None:
        return None
    alto += colocar(cad, 0, t_cad)

    # Bajo: negras y, al final, dominante (2 tiempos) -> tónica (2 tiempos)
    previas = {(tonica + 4) % 7, (tonica - 1) % 7}
    bajo = None
    for v in range(60):
        cand = contrapunto(
            [(0, t0, [(sop, "<"), (alto, "<")], voces["bajo"][-1][0])],
            [1.0] * 6 + [2.0, 2.0],
            rango=(-12, 0),
            semilla=semilla * 1000 + v,
            triada=(tonica,),
        )
        if cand is not None and cand[-2][0] % 7 in previas:
            bajo = cand
            break
    if bajo is None:
        return None
    bajo = colocar(bajo, 0, t0)

    nuevas = copy.deepcopy(voces)
    nuevas["soprano"] += sop
    nuevas["alto"] += alto
    nuevas["bajo"] += bajo
    return nuevas


# -------------------------------------------------------------------- obra
def fuga_completa(semilla=7, intentos=80):
    s, expo = componer(semilla)
    S = sujeto(s)
    rangos_fa = dict(RANGO, soprano=(5, 15), bajo=(-12, 0))

    # (tipo, parámetros)
    plan = [
        ("episodio", dict(base_s=7, tonica=2)),
        (
            "entrada",
            dict(tema=S, voz="alto", despl=2, triada=TRIADA_FA, rangos=rangos_fa),
        ),
        (
            "entrada",
            dict(
                tema=inversion(S, -5),
                voz="bajo",
                despl=0,
                triada=TRIADA_FA,
                rangos=rangos_fa,
            ),
        ),
        ("episodio", dict(base_s=9, tonica=0)),
        ("entrada", dict(tema=aumentacion(S), voz="alto", despl=0, triada=TRIADA_RE)),
        ("entrada", dict(tema=S, voz="bajo", despl=-7, triada=TRIADA_RE)),
    ]

    for variante in range(intentos):
        voces, t0, fallo = copy.deepcopy(expo), 3 * L, False
        marcas = []
        for i, (tipo, p) in enumerate(plan):
            sem = s + i + 10 * variante
            if tipo == "episodio":
                nuevas = episodio(voces, t0, S, semilla=sem, **p)
                dur = 10
            else:
                p = dict(p)
                tema = p.pop("tema")
                nuevas = seccion(
                    voces, tema, p.pop("voz"), t0, p.pop("despl"), semilla=sem, **p
                )
                dur = max(t + d for _, t, d in tema)
            if nuevas is None:
                fallo = True
                break
            marcas.append((tipo, t0, dur))
            voces, t0 = nuevas, t0 + dur
        if fallo:
            continue
        acorde_final(voces, t0)
        if not any(verificar(voces).values()):
            return s, variante, voces, marcas
    raise RuntimeError("No se encontró una versión sin fallos; prueba otra semilla.")


if __name__ == "__main__":
    s, variante, voces, marcas = fuga_completa(1)
    print(f"Sujeto semilla {s}, variante {variante} | verificación: {verificar(voces)}")
    for tipo, t0, dur in marcas:
        print(f"  {tipo:9s} tiempos {t0:g}-{t0 + dur:g}")
    render(voces, "fuga_episodios.wav")
    wav_a_mp3("fuga_episodios.wav", "fuga_episodios.mp3")
    print("Escritos fuga_episodios.wav y fuga_episodios.mp3")
