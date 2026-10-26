"""
Exporta a MIDI las piezas generadas. Todas son, en el fondo, listas de notas
(altura, inicio, duración), y eso es justo lo que describe un archivo MIDI.

  python midi_export.py      ->  fuga_episodios.mid, winston.mid, yanni.mid

Requiere: mido  (pip install mido)

Notas de creación:
Que tan difícil es grabar el resultado de estos programas en MIDI, además del `wav` y `mp3`?

Es bastante fácil, porque todas las piezas ya son listas de notas (altura, inicio, duración). Voy a escribir y probar un módulo de exportación para que lo veas funcionando.

Es fácil, porque todas las piezas ya son listas de notas (altura, inicio, duración) y eso es justo lo que contiene un archivo MIDI. Escribí midi_export.py y exporté tres piezas: fuga_episodios.mid, winston.mid y yanni.mid.

Cómo funciona

La función central es guardar_midi(). Recibe una pista por instrumento, con programa General MIDI (órgano 19, piano 0, cuerdas 48, violín 40, violonchelo 42, timbales 47) y las notas en tiempos musicales. Usa la biblioteca mido:

pip install mido
python midi_export.py

Cada pieza necesita un adaptador pequeño:

Fuga: convierte los grados de Re menor a altura MIDI con la misma función midi() y pone una pista por voz (soprano, alto y bajo).
Winston: una pista de piano.
Yanni: cinco pistas (piano, cuerdas, violín, violonchelo y timbales).

Los ritardandos

Winston y Yanni terminan frenando. Eso se exporta como un mapa de tempo, con un cambio de tempo cada negra durante el ritardando: Winston baja de 66 a 39 BPM, y Yanni de 84 a 47.

Comprobación

Releí los tres archivos con mido. Los conteos de notas coinciden con los eventos de cada pieza (Winston: 296; fuga: 119 + 101 + 74) y las duraciones concuerdan con las del audio, sin contar la cola de reverb. Pero no puedo oír el resultado en un sintetizador.

Lo que se pierde al pasar a MIDI

Los timbres: el sonido lo pone el sintetizador que abra el archivo, no mi síntesis. Con un buen SoundFont de piano, Winston puede sonar incluso mejor.
La humanización (pequeñas variaciones aleatorias de tiempo y volumen), el panorama estéreo y la reverb.
El platillo de Yanni: es ruido filtrado, no una nota, así que se omite.

Qué no exporté

Kitaro: sus pads y el drone se generan dentro de componer() con tiempos en segundos, y no se recogen en una lista de eventos. Se podría refactorizar, pero su carácter depende sobre todo de la síntesis (osciladores desafinados y filtros que respiran), que MIDI no guarda.

Para qué sirve

Abrir el .mid en MuseScore para ver la partitura y revisar las secuencias y cadencias de la fuga.
Cargarlo en un DAW (Reaper, Ableton, LMMS) y probar otros instrumentos.
Convertirlo a audio con FluidSynth y un SoundFont: fluidsynth -ni fuente.sf2 fuga_episodios.mid -F salida.wav.

Con MuseScore vas a ver la fuga con claridad, porque cada voz queda en su propia pista. Que disfrutes estudiando el código.

"""

import mido

PPQ = 480  # pulsos por negra


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
    t0.append(mido.MetaMessage("track_name", name="Tempo", time=0))
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
        t0.append(mido.MetaMessage("set_tempo", tempo=us, time=tick - ultimo))
        ultimo = tick
    mid.tracks.append(t0)

    # Una pista por instrumento
    for canal, (nombre, (programa, notas)) in enumerate(pistas.items()):
        canal = canal if canal < 9 else canal + 1  # el canal 10 es percusión GM
        eventos = []
        for m, ini, dur, vel in notas:
            v = max(1, min(127, int(round(vel * 127))))
            on = round(ini * PPQ)
            off = round((ini + max(dur, 0.05)) * PPQ)
            eventos.append(
                (on, 1, mido.Message("note_on", note=int(m), velocity=v, channel=canal))
            )
            eventos.append(
                (
                    off,
                    0,
                    mido.Message("note_off", note=int(m), velocity=0, channel=canal),
                )
            )
        eventos.sort(key=lambda e: (e[0], e[1]))  # a igual tick, primero los note_off

        pista = mido.MidiTrack()
        pista.append(mido.MetaMessage("track_name", name=nombre, time=0))
        pista.append(
            mido.Message("program_change", program=programa, channel=canal, time=0)
        )
        ultimo = 0
        for tick, _, msg in eventos:
            msg.time = tick - ultimo
            ultimo = tick
            pista.append(msg)
        mid.tracks.append(pista)

    mid.save(archivo)
    return archivo


# ------------------------------------------------------------------- fuga
def exportar_fuga(voces, archivo, bpm=76):
    from fuga import midi  # grados de Re menor -> altura MIDI

    pistas = {
        nombre: (19, [(midi(g), t, d, 0.7) for g, t, d in notas])  # 19 = órgano
        for nombre, notas in voces.items()
    }
    return guardar_midi(pistas, archivo, bpm)


# --------------------------------------------------------------- Winston
def exportar_winston(eventos, b0, bend, archivo):
    import winston

    notas = [(m, t, d, v) for m, t, d, v in eventos]
    return guardar_midi(
        {"Piano": (0, notas)},
        archivo,
        winston.BPM,
        segundos=lambda b: winston.segundos(b, b0, bend),
        fin=bend,
    )


# ------------------------------------------------------------------ Yanni
PROGRAMA_YANNI = {"piano": 0, "cuerdas": 48, "violin": 40, "cello": 42, "timbal": 47}


def exportar_yanni(eventos, b0, bend, archivo):
    import yanni

    pistas = {n: (p, []) for n, p in PROGRAMA_YANNI.items()}
    for inst, m, t, d, vel, _pan in eventos:
        if inst in pistas:  # el platillo es ruido: no tiene nota MIDI
            pistas[inst][1].append((m, t, d if d > 0 else 0.5, vel))
    pistas = {n: v for n, v in pistas.items() if v[1]}
    return guardar_midi(
        pistas,
        archivo,
        yanni.BPM,
        segundos=lambda b: yanni.segundos(b, b0, bend),
        fin=bend,
    )


if __name__ == "__main__":
    from fuga_episodios import fuga_completa

    _, _, voces, _ = fuga_completa(1)
    print(exportar_fuga(voces, "fuga_episodios.mid"))

    import winston

    ev, b0, bend = winston.partitura(semilla=3)
    print(exportar_winston(ev, b0, bend, "winston.mid"))

    import yanni

    ev, b0, bend = yanni.partitura(semilla=1)
    print(exportar_yanni(ev, b0, bend, "yanni.mid"))
