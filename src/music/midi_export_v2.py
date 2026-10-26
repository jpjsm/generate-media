"""
Exporta a MIDI las piezas generadas. Todas son, en el fondo, listas de notas
(altura, inicio, duración), y eso es justo lo que describe un archivo MIDI.

  python midi_export.py      ->  fuga_organo.mid, fuga_cuerdas.mid, fuga_vientos.mid,
                                 winston.mid, yanni.mid

Requiere: mido  (pip install mido)
"""
import mido

PPQ = 480                                  # pulsos por negra


def guardar_midi(pistas, archivo, bpm, segundos=None, fin=None):
    """
    pistas:   {nombre: (programa_GM, [(midi, inicio, duración, velocidad 0-1), ...])}
              con inicio y duración en TIEMPOS (negras).
    bpm:      tempo fijo.
    segundos: opcional, función tiempo->segundos para reproducir un ritardando
              (se traduce a cambios de tempo cada negra). Necesita `fin`.
    """
    mid = mido.MidiFile(ticks_per_beat=PPQ, type=1)

    # Pista 0: mapa de tempo
    t0 = mido.MidiTrack()
    t0.append(mido.MetaMessage('track_name', name='Tempo', time=0))
    if segundos is None:
        tempos = [(0, mido.bpm2tempo(bpm))]
    else:
        tempos, previo = [], None
        for b in range(int(fin) + 1):
            us = round((segundos(b + 1) - segundos(b)) * 1e6)
            if previo is None or abs(us - previo) / previo > 0.005:
                tempos.append((b * PPQ, us))
                previo = us
    ultimo = 0
    for tick, us in tempos:
        t0.append(mido.MetaMessage('set_tempo', tempo=us, time=tick - ultimo))
        ultimo = tick
    mid.tracks.append(t0)

    # Una pista por instrumento
    for canal, (nombre, (programa, notas)) in enumerate(pistas.items()):
        canal = canal if canal < 9 else canal + 1        # el canal 10 es percusión GM
        eventos = []
        for m, ini, dur, vel in notas:
            v = max(1, min(127, int(round(vel * 127))))
            on = round(ini * PPQ)
            off = round((ini + max(dur, 0.05)) * PPQ)
            eventos.append((on, 1, mido.Message('note_on', note=int(m), velocity=v, channel=canal)))
            eventos.append((off, 0, mido.Message('note_off', note=int(m), velocity=0, channel=canal)))
        eventos.sort(key=lambda e: (e[0], e[1]))         # a igual tick, primero los note_off

        pista = mido.MidiTrack()
        pista.append(mido.MetaMessage('track_name', name=nombre, time=0))
        pista.append(mido.Message('program_change', program=programa, channel=canal, time=0))
        ultimo = 0
        for tick, _, msg in eventos:
            msg.time = tick - ultimo
            ultimo = tick
            pista.append(msg)
        mid.tracks.append(pista)

    mid.save(archivo)
    return archivo


# ------------------------------------------------------------------- fuga
# Programas General MIDI por voz (soprano, alto, bajo)
CONJUNTOS_FUGA = {
    'organo':  [('Órgano 1', 19), ('Órgano 2', 19), ('Órgano 3', 19)],
    'cuerdas': [('Violín', 40), ('Viola', 41), ('Violonchelo', 42)],
    'vientos': [('Flauta', 73), ('Clarinete', 71), ('Fagot', 70)],
}


def exportar_fuga(voces, archivo, bpm=76, conjunto='organo'):
    """`conjunto`: 'organo', 'cuerdas' o 'vientos' (o una lista propia de
    tres (nombre, programa_GM) para soprano, alto y bajo)."""
    from fuga import midi                 # grados de Re menor -> altura MIDI
    instrumentos = CONJUNTOS_FUGA[conjunto] if isinstance(conjunto, str) else conjunto
    pistas = {}
    for voz, (nombre, programa) in zip(('soprano', 'alto', 'bajo'), instrumentos):
        pistas[nombre] = (programa, [(midi(g), t, d, 0.7) for g, t, d in voces[voz]])
    return guardar_midi(pistas, archivo, bpm)


# --------------------------------------------------------------- Winston
def exportar_winston(eventos, b0, bend, archivo):
    import winston
    notas = [(m, t, d, v) for m, t, d, v in eventos]
    return guardar_midi({'Piano': (0, notas)}, archivo, winston.BPM,
                        segundos=lambda b: winston.segundos(b, b0, bend), fin=bend)


# ------------------------------------------------------------------ Yanni
PROGRAMA_YANNI = {'piano': 0, 'cuerdas': 48, 'violin': 40, 'cello': 42, 'timbal': 47}


def exportar_yanni(eventos, b0, bend, archivo):
    import yanni
    pistas = {n: (p, []) for n, p in PROGRAMA_YANNI.items()}
    for inst, m, t, d, vel, _pan in eventos:
        if inst in pistas:                 # el platillo es ruido: no tiene nota MIDI
            pistas[inst][1].append((m, t, d if d > 0 else 0.5, vel))
    pistas = {n: v for n, v in pistas.items() if v[1]}
    return guardar_midi(pistas, archivo, yanni.BPM,
                        segundos=lambda b: yanni.segundos(b, b0, bend), fin=bend)


if __name__ == "__main__":
    from fuga_episodios import fuga_completa
    _, _, voces, _ = fuga_completa(1)
    for conjunto in CONJUNTOS_FUGA:
        print(exportar_fuga(voces, f"fuga_{conjunto}.mid", conjunto=conjunto))

    import winston
    ev, b0, bend = winston.partitura(semilla=3)
    print(exportar_winston(ev, b0, bend, "winston.mid"))

    import yanni
    ev, b0, bend = yanni.partitura(semilla=1)
    print(exportar_yanni(ev, b0, bend, "yanni.mid"))
