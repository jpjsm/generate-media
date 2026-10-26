# Música generativa en Python

Un recorrido de aprendizaje: de los fractales a una **fuga a tres voces con episodios modulantes**, más tres piezas de estilo libre (**George Winston**, **Kitaro** y **Yanni**), con exportación a **WAV, MP3 y MIDI**.

Todo se genera con código: nada está grabado ni compuesto a mano. Cada pieza es un programa que decide notas, ritmos y estructura (con reglas y azar controlado por una *semilla*) y luego sintetiza el audio con NumPy y SciPy.

---

## Autoría y procedencia (leer primero)

> **Todo el código de este repositorio fue escrito por Claude**, un modelo de IA de Anthropic, en una conversación con JP en claude.ai entre el 24 y el 26 de octubre de 2026. Esta versión del README también la redactó Claude (Sonnet 5.5); el modelo pudo variar entre mensajes de la conversación.

- **Qué hizo JP:** dirigió el proyecto. Eligió los temas (fractales, sonidos relajantes, canon y fuga de Bach, Winston, Kitaro, Yanni), el orden de trabajo (una pieza a la vez), pidió ampliaciones (alargar la fuga, el episodio modulante, MIDI, cambio de instrumentos) y juzgó los resultados.
- **Qué hizo Claude:** diseñó la arquitectura, escribió todo el código, lo ejecutó y probó en un entorno aislado, corrigió los fallos que fueron apareciendo y redactó las explicaciones.
- **Ninguna línea fue escrita a mano por un humano** hasta la fecha de este README. Si modificas el código, anótalo en la tabla de abajo para que la autoría siga siendo clara.

| Fecha | Quién | Archivo | Cambio |
|-------|-------|---------|--------|
| *(vacío)* | | | |

**Licencia:** pendiente de elegir por el propietario del repositorio. Las dependencias (NumPy, SciPy, lameenc, mido) tienen sus propias licencias.

### Qué se verificó y qué no

| Verificado automáticamente | NO verificado |
|----------------------------|---------------|
| La fuga: 0 disonancias en tiempo y 0 quintas/octavas paralelas, entre todas las voces y en toda la pieza (`verificar()`) | **Nadie de la parte de IA ha oído las piezas**: Claude no puede escuchar audio. Los juicios estéticos son de JP |
| Que cada script se ejecuta de principio a fin y escribe archivos válidos (WAV, MP3 de 192 kbps, MIDI releído con `mido`) | La calidad musical de cada semilla (varias se descartaron por *leer* sus melodías, no por oírlas) |
| Que no hay saturación ni valores corruptos, y que la intensidad evoluciona como se diseñó (RMS por tramos) | Pruebas unitarias formales: no existen; la verificación fue con scripts de prueba puntuales |
| Que el MIDI conserva el número de notas y las duraciones de cada pieza | La coherencia armónica fuera de las reglas codificadas (p. ej. los cruces entre secciones solo se comprueban por paralelismos y disonancias en tiempo) |

---

## Contenido del repositorio

| Archivo | Líneas | Qué es | Salida |
|---------|-------:|--------|--------|
| `fuga.py` | 317 | Exposición de la fuga + **motor de contrapunto** (el núcleo) | `fuga.wav` |
| `fuga_larga.py` | 147 | Secciones extra: sujeto en inversión y aumentación | `fuga_larga.wav/.mp3` |
| `fuga_episodios.py` | 147 | Fuga completa con **episodios modulantes** Re → Fa → Re | `fuga_episodios.wav/.mp3` |
| `winston.py` | 204 | Piano estilo Winston (Am–F–C–G, arpegios, pedal) | `winston.wav/.mp3` |
| `kitaro.py` | 229 | Ambiental estilo Kitaro (drone, pads, flauta, eco) | `kitaro.wav/.mp3` |
| `yanni.py` | 389 | Cinematográfico estilo Yanni (piano, cuerdas, timbales, cambio de tonalidad) | `yanni.wav/.mp3` |
| `midi_export.py` | 124 | Exporta fuga, Winston y Yanni a MIDI | `*.mid` |

Dependencias entre archivos: `fuga.py` ← `fuga_larga.py` ← `fuga_episodios.py`; `midi_export.py` importa `fuga_episodios`, `winston` y `yanni`. `winston.py`, `kitaro.py` y `yanni.py` son independientes entre sí.

Audio de ejemplo incluido (si lo subes): `fuga_larga.mp3`, `fuga_episodios.mp3`, `winston.mp3`, `kitaro.mp3`, `yanni.mp3`, y los MIDI `fuga_organo.mid`, `fuga_cuerdas.mid`, `fuga_vientos.mid`, `winston.mid`, `yanni.mid`.

> Los primeros ejemplos de la conversación (fractales de Mandelbrot y Koch, olas con ruido marrón, y el primer canon) se escribieron como fragmentos en el chat y **no** forman parte de estos archivos. Sus ideas reaparecen en `fuga_larga.py` (`inversion`, `aumentacion`).

### `.gitignore` recomendado

```
*.wav
__pycache__/
```

Los WAV pesan decenas de MB y se regeneran con cada ejecución; los MP3 y MIDI sí merece la pena conservarlos.

---

## Instalación y ejecución

Probado con Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, lameenc 1.9.0 y mido 1.3.3.

```bash
pip install numpy scipy lameenc mido
```

```bash
python fuga.py              # exposición → fuga.wav
python fuga_larga.py        # + variaciones → fuga_larga.wav y .mp3
python fuga_episodios.py    # fuga completa con episodios → .wav y .mp3
python winston.py           # ≈ 2 min de audio
python kitaro.py            # ≈ 3 min de audio; tarda cerca de 1 minuto
python yanni.py             # ≈ 2 min 20 s de audio; tarda unos 40 s
python midi_export.py       # fuga (3 versiones), Winston y Yanni → .mid
```

**Reproducibilidad:** todo el azar sale de `numpy.random.default_rng(semilla)`. Con la misma semilla y la misma versión de NumPy debe salir la misma pieza; entre versiones de NumPy no está garantizado.

**Ver la fuga escrita:** abre los `.mid` en MuseScore Studio. Cada voz es una pista, así que se ven las secuencias, las cadencias y las entradas del sujeto.

---

## Qué hace cada pieza

- **Fuga (`fuga.py`, `fuga_larga.py`, `fuga_episodios.py`).** En Re menor, a tres voces. La exposición presenta el sujeto, la respuesta a la quinta y el contrasujeto. `fuga_larga.py` añade entradas con el sujeto invertido y aumentado. `fuga_episodios.py` construye la forma completa: exposición, episodio modulante a Fa mayor, entradas en Fa, episodio de regreso y entradas finales en Re menor. El contrapunto no es azar suelto: se **busca** con reglas (consonancia, sin paralelas, saltos limitados) y se comprueba al final.
- **Winston (`winston.py`).** Progresión lenta Am–F–C–G, arpegio continuo en la mano izquierda, melodía espaciada, pedal de sustain, piano sintetizado, estructura A A′ B B′ A y ritardando.
- **Kitaro (`kitaro.py`).** Drone con osciladores desafinados, pads de ataque lento sobre Dm9–Bbmaj7–Fmaj7–Cadd9, flauta pentatónica con vibrato, pulso de pizzicatos con eco ping-pong y reverb de 5 s.
- **Yanni (`yanni.py`).** Ostinato de piano, melodía con secuencias, violonchelo, cuerdas, violín solista, timbales y platillos, puente ascendente que acaba en el dominante de la nueva tonalidad y cambio de Re menor a Mi menor.

---

# Guía de estudio del código

Esta guía es una referencia para estudiar el código sin tener que preguntar de nuevo. Está pensada para alguien con base sólida en programación y matemáticas, pero no necesariamente en teoría musical.

## Cómo usar la guía

1. Lee primero **"Formatos de datos"** (la clave de todo) y el **glosario** del final.
2. Sigue el **orden de lectura** recomendado.
3. Por cada archivo: lee la sección de esta guía, luego el código, y haz **al menos un experimento** de los propuestos (cambiar una constante y volver a escuchar).
4. Contesta las **preguntas de autoevaluación**. Si no sabes responder una, esa es la parte que conviene releer.

## Orden de lectura recomendado

| Paso | Archivo | Dificultad | Qué aprendes |
|-----:|---------|:----------:|--------------|
| 1 | `winston.py` | ★☆☆ | El patrón general: generar eventos → sintetizar → mezclar. Síntesis aditiva y melodía con reglas |
| 2 | `kitaro.py` | ★★☆ | Procesado de señal: osciladores, LFO, eco, reverb por convolución |
| 3 | `yanni.py` | ★★☆ | Estructura por secciones, transposición, secuencias melódicas |
| 4 | `fuga.py` | ★★★ | **Búsqueda con retroceso** aplicada al contrapunto (el corazón intelectual) |
| 5 | `fuga_larga.py` | ★★☆ | Reutilizar el motor con transformaciones del tema |
| 6 | `fuga_episodios.py` | ★★★ | Secuencias reales con *escenarios*; cadencias; modulación |
| 7 | `midi_export.py` | ★☆☆ | El formato MIDI (eventos, ticks, mapa de tempo) |

## Formatos de datos (la clave de todo)

**Tiempo musical.** La unidad es la negra, llamada "tiempo". Un compás de 4/4 son 4 tiempos; una corchea es 0,5. Para pasar a segundos: `segundos(b, b0, bend)` en Winston y Yanni (incluye el ritardando) y `beat = 60 / bpm` en la fuga. Kitaro trabaja directamente en segundos.

**Altura.**
- *Fuga:* grados diatónicos de Re menor natural, como enteros. `0` = Re4 (MIDI 62), `1` = Mi4, `2` = Fa4, `3` = Sol4, `4` = La4, `5` = Si♭4, `6` = Do5, `7` = Re5; los negativos bajan (`-7` = Re3). `midi(grado)` los convierte a MIDI. Transponer por grados es sumar un entero, y **no cambia la escala**: por eso la respuesta a la quinta es `+4` y el cambio al relativo mayor (Fa) es `+2`.
- *Winston, Yanni, Kitaro:* números MIDI directos (60 = Do4, 69 = La4 = 440 Hz).

**Nota y evento.**
- *Fuga:* una voz es una lista de `(grado, inicio, duración)`, y la obra es `voces = {'soprano': [...], 'alto': [...], 'bajo': [...]}`.
- *Winston:* `(midi, inicio, duración_hasta_levantar_el_pedal, velocidad 0–1)`.
- *Yanni:* `(instrumento, midi, inicio, duración, velocidad, panorama_o_None)`.
- *Kitaro:* no hay una lista común de eventos: `componer()` coloca las señales en un búfer a medida que las genera.

**Convención de posición en el contrapunto.** `(voz, '<')` significa "la voz nueva queda por **debajo** de esa voz"; `'>'`, por encima.

---

## 1. `winston.py`

**Flujo:** `partitura()` → lista de eventos → `render()` → WAV → `wav_a_mp3()`.

**Conceptos clave**
- **Melodía como paseo aleatorio ponderado** (`elegir_nota`): cada nota candidata recibe un peso `exp(-distancia/2)` (prefiere notas cercanas), otro que la atrae hacia un registro central, un castigo ×0,05 si repite la nota anterior y un premio ×1,6 si sigue en la misma dirección. En los tiempos fuertes solo se permiten notas del acorde.
- **Variación por repetición parcial** (`frase`, argumento `base`): la segunda frase copia tres compases y recompone solo el último.
- **Pedal de sustain:** cada nota dura hasta el final de su compás (`fin_pedal - inicio`).
- **Piano aditivo** (`piano`): suma de 8 parciales ligeramente inarmónicos; los agudos decaen más rápido; las notas graves duran más; las notas suaves son menos brillantes.
- **Humanización** (`render`): ±6 ms de desfase en cada ataque y ±0,04 de velocidad.
- **Ritardando** (`segundos`): el tempo se frena con una función cuadrática entre `b0` y `bend`.
- **Reverb por convolución** (`reverb`): la respuesta al impulso es ruido con decaimiento exponencial, suavizado con un filtro de un polo.

**Lectura sugerida:** constantes → `elegir_nota` → `compas_melodia` → `frase` → `partitura` → `piano` → `segundos` → `render`.

**Experimentos:** cambia `BPM`; cambia `PROG` y añade el acorde nuevo a `ACORDES`; sube el `0.05` de la repetición y oye cómo la melodía se estanca; amplía `REGISTRO`; cambia `rt60` en `reverb`.

**Preguntas:** ¿por qué `fuerte` exige `d >= 1`? ¿Qué pasaría sin el factor de dirección? ¿Cómo se consigue el efecto de pedal sin una variable "pedal"? ¿Por qué `segundos()` es cuadrática y no lineal?

## 2. `kitaro.py`

**Flujo:** `componer()` construye búferes separados (pads, drone, flauta, pulso), aplica eco a la flauta y al pulso, mezcla, añade reverb y escribe el WAV.

**Conceptos clave**
- **Osciladores desafinados** (`pad`): cada nota son 3 voces diente de sierra a −9, 0 y +8 cents, repartidas en el estéreo. La mezcla produce *batidos* lentos, que dan la sensación de "coro".
- **LFO que abre y cierra el timbre:** el brillo `b` oscila entre dos valores; la amplitud de cada armónico es `amp *= exp(-1.2·(1−b))`, así que con `b` alto aparecen más armónicos agudos. Es un filtro paso bajo móvil hecho a base de armónicos.
- **Flauta** (`flauta`): vibrato por **modulación de fase** (aparece tras 0,5 s) y soplo con ruido filtrado en banda.
- **Eco ping-pong** (`eco`): repeticiones que alternan entre izquierda y derecha, cada una atenuada por `fb**i`.
- **Melodía pentatónica** (`melodia`): una frase por acorde, con notas largas y silencios. La pentatónica de Re menor sirve sobre los cuatro acordes sin choques.
- **Reverb larga** (`reverb`, `rt60=5`).

**Experimentos:** cambia `brillo=(0.3, 0.8)`; cambia `CH` (duración de cada acorde) y `CICLOS`; prueba otro `retardo` y otro `fb` en `eco`; sustituye `PENTA` por otra escala.

**Preguntas:** ¿por qué tres voces desafinadas suenan más "anchas" que una? ¿Qué diferencia hay entre modular la frecuencia y modular la fase? ¿Por qué se mezcla `0.62·seco + 0.38·reverb`?

## 3. `yanni.py`

**Flujo:** `partitura()` → eventos con instrumento → `render()` (dos buses, piano y orquesta, con reverbs distintas) → WAV.

**Conceptos clave**
- **Acordes como (fundamental, calidad):** `(0,'m')` = Re menor, `(-4,'M')` = Si♭ mayor, etc. La fundamental se expresa en semitonos sobre Re.
- **Secuencia melódica** (`secuenciar`): repite el dibujo de un compás sobre otro acorde, desplazado `desplaza` grados de escala, y ajusta los tiempos fuertes a notas del acorde. Es el recurso que da la sensación de "ascenso" en el puente.
- **Frase de 4 compases** (`frase`): motivo, respuesta, secuencia del motivo y cadencia.
- **Cambio de tonalidad** (`SECCIONES`): el tercer elemento de cada sección es una transposición en semitonos. El salto de Re menor a Mi menor es `trans=2`.
- **Tensión hacia el cambio:** el puente acaba en Si mayor (dominante de Mi menor), con un redoble de timbales y un platillo que crecen hasta el golpe.
- **Orquestación por sección:** quién entra y cuándo está en `partitura()` (violonchelo desde la mitad de A; cuerdas y timbales desde B; todo el conjunto en el final).
- **Instrumentos sintetizados:** `cuerda` (3 voces desafinadas con vibrato opcional, sirve para violín, violonchelo y conjunto), `timbal` (barrido de afinación + golpe de ruido), `platillo` (ruido filtrado con crescendo).

**Experimentos:** cambia `trans` en `final` y `coda` (3 = tercera menor); invierte el sentido de `desplaza`; cambia `vel_arp` y los diccionarios de velocidades de `cuerdas` y `timbal` para regular cuánto crece el final; prueba otra `semilla` en `partitura`.

**Preguntas:** ¿por qué la melodía del puente usa solo notas del acorde en el último compás? ¿Qué hace `es_fuerte` y por qué importa? ¿Cómo se asegura que la melodía de `final` quede en Mi menor sin reescribirla?

## 4. `fuga.py` (el núcleo)

**Flujo de la exposición**

```
sujeto(semilla)  →  respuesta (sujeto + 4 grados)  →  bajo (sujeto − 7 grados)
        ↓
contrapunto(...)  →  contrasujeto   (válido contra la respuesta Y contra el bajo)
        ↓
contrapunto(...)  →  voz libre
        ↓
verificar()  →  render()
```

**Conceptos clave**
- **Rejilla de comprobación** (`PASO = 0.5`): se mira la pieza cada corchea. `muestrear_midi` devuelve la altura que suena en cada punto de la rejilla.
- **Consonancia** (`CONSONANCIAS`): unísono/octava, terceras, quinta y sextas. Se evalúa con la clase de intervalo (`semitonos mod 12`).
- **Paralelas** (`paralelos`): quintas u octavas seguidas con las dos voces moviéndose en la misma dirección.
- **Notas de paso** (`nota_de_paso`): se permite una disonancia en parte débil si la voz que la causa entra por grado conjunto.
- **Generación del sujeto** (`sujeto`): *muestreo con rechazo*: se generan candidatos al azar y se descartan los que incumplen las reglas (empieza y acaba en la tónica, salto inicial, un único punto culminante, cierre por grado conjunto).
- **Contrapunto como búsqueda con retroceso** (`contrapunto`): es un problema de satisfacción de restricciones.
  - `dfs(i)` elige la nota `i`; `nota_ok(i, g)` comprueba las reglas y **poda** si se incumplen.
  - Los candidatos se prueban en orden aleatorio (según `SALTOS` y `PESOS`) para que distintas semillas den distintas soluciones.
  - `max_nodos` limita el esfuerzo; si se agota, devuelve `None` y quien llama prueba otra semilla.
- **Escenarios** (`escenarios`): una lista de `(desplazamiento, inicio, parejas, previa)`. La voz generada debe cumplir las reglas **en todos a la vez**. Así el contrasujeto sirve contra la respuesta y contra el bajo (contrapunto invertible), y en los episodios sirve en las tres repeticiones de una secuencia.
- **Reglas de `contrapunto`:**
  - consonancia en cada tiempo (negra);
  - disonancia en parte débil solo como nota de paso, floreo o escapada;
  - sin quintas ni octavas paralelas entre puntos consecutivos ni entre tiempos consecutivos;
  - sin cruzamiento de voces;
  - saltos de hasta una quinta, y tras un salto de cuarta o más, grado conjunto en sentido contrario;
  - la primera nota cerca de la anterior (`previa`) y la última dentro de `triada`.
- **Reintentos** (`componer`): prueba semillas sucesivas hasta que el contrasujeto y la voz libre existen; además exige un contrasujeto con perfil melódico (≥5 notas distintas y rango ≥4 grados). Por eso `componer(semilla=1)` puede devolver el sujeto de la semilla 2.
- **Verificación independiente** (`verificar`): recorre la pieza entera, par de voces por par de voces, y cuenta disonancias en tiempo y paralelas.

**Lectura sugerida:** constantes → `midi` → `colocar` → `muestrear_midi` → `paralelos` → `nota_de_paso` → `sujeto` → **`contrapunto`** (con calma: `nota_ok` primero, luego `dfs`) → `componer` → `verificar` → `tono` y `render`.

**Experimentos**
- Añade `5` a `CONSONANCIAS` (cuarta) y observa cómo cambia el carácter.
- Quita la llamada a `nota_de_paso` y mira cuántas semillas dejan de tener solución.
- Cambia `L` (duración del sujeto) o `SALTOS`.
- Llama a `contrapunto` con `triada=None` para quitar la regla de la nota final.

**Preguntas:** ¿por qué la rejilla es de corcheas y no de negras? ¿Qué significa el `'<'` en una pareja? ¿Por qué el contrasujeto necesita dos escenarios? ¿Por qué se recorren los candidatos en orden aleatorio y no en orden fijo? ¿Qué no detecta `verificar()`?

## 5. `fuga_larga.py`

**Concepto central:** `seccion()` coloca el sujeto (transformado) en una voz y **compone las otras dos contra él**, reutilizando `contrapunto()`.

- **Transformaciones:** `inversion(voz, eje)` refleja la melodía (`g → eje − g`, movimiento contrario); `aumentacion(voz, f)` multiplica tiempos y duraciones.
- **Orden de generación:** primero la voz **lenta** (negras) y luego la de **corcheas**. La rápida puede adornar con notas de paso; la lenta no. Al revés, no había solución.
- **Reintentos anidados:** si la voz rápida no encuentra solución, se prueba otra voz lenta.
- **Cada sección se compone por separado**, así que puede haber un paralelismo en la **unión** entre dos secciones. `fuga_larga()` repite con otras semillas hasta que `verificar()` da cero fallos en toda la pieza.
- **`PLAN`:** la lista de entradas `(transformación, voz)`; editarla es la forma más fácil de cambiar la obra.

**Experimentos:** edita `PLAN` (añade una disminución con `aumentacion(S, 0.5)`); cambia `RANGO`; cambia `REG`.

**Preguntas:** ¿por qué compone primero la voz lenta? ¿Qué problema resuelve el bucle de reintentos de `fuga_larga()`? ¿Por qué una inversión en el bajo con `eje=0` queda en el registro correcto?

## 6. `fuga_episodios.py`

**Estructura (en tiempos):** exposición 0–24 · episodio I 24–34 · entradas en Fa 34–50 · episodio II 50–60 · entradas finales en Re 60–84 · acorde final.

**Conceptos clave**
- **Episodio** (`episodio`, 10 tiempos = 6 de secuencia + 4 de cadencia):
  - *Soprano:* el motivo (los dos primeros tiempos del sujeto) repetido tres veces, cada una un grado más grave.
  - *Alto:* un contramotivo en corcheas **generado una sola vez y válido en las tres repeticiones** (tres escenarios). Es una secuencia real: los intervalos son idénticos en cada repetición.
  - *Bajo:* negras compuestas contra las otras dos voces, y al final **dominante → tónica** (o sensible/subtónica → tónica), que es lo que hace que la llegada suene a cadencia.
- **Modulación a Fa mayor:** Fa mayor es la relativa de Re menor y usa **exactamente las mismas siete notas**. No hay alteraciones: la tonalidad se afirma por la secuencia, la cadencia en el bajo (Do → Fa), las entradas del sujeto sobre Fa y los acordes de llegada (`TRIADA_FA`, `TRIADA_RE` fijan qué notas pueden cerrar cada sección).
- **Transposiciones en grados:** `despl=2` lleva el sujeto a Fa; la inversión en Fa usa `eje=-5` para empezar y acabar en la nota Fa.
- **`fuga_completa()`** encadena el plan y reintenta con otras semillas hasta que toda la obra verifica.

**Por qué 10 tiempos y no 8:** la primera versión pedía una cadencia en solo 2 tiempos y no tenía solución, porque el bajo no puede estar en el dominante al mismo tiempo que el soprano ya llega a la tónica. Con 4 tiempos de cadencia (2 de dominante y 2 de tónica) sí.

**Experimentos:** `paso=-1` en `episodio` (secuencia ascendente); `k=2` o `k=4` repeticiones; cambia `base_s`; edita `plan` (por ejemplo, una entrada más en Fa).

**Preguntas:** ¿cómo garantizan los *escenarios* que el alto sea una secuencia real? ¿Por qué la modulación a la dominante (La menor) exigiría extender el sistema? ¿Qué fija `TRIADA_FA`?

## 7. `midi_export.py`

**Concepto:** una pieza es una lista de notas, y un archivo MIDI es una lista de mensajes `note_on` y `note_off` con **tiempos relativos en ticks** (`PPQ = 480` por negra).

- `guardar_midi(pistas, archivo, bpm, segundos=None, fin=None)`: una pista por instrumento más una pista 0 con el **mapa de tempo**. Con `segundos`, el ritardando se traduce a cambios de tempo cada negra.
- Los mensajes se ordenan por tick, y con el mismo tick los `note_off` van **antes** que los `note_on` (evita cortar notas repetidas).
- Se evita el canal 10 (percusión de General MIDI).
- `CONJUNTOS_FUGA` define instrumentos por voz: órgano (19), cuerdas (40/41/42: violín, viola, violonchelo) y vientos (73/71/70: flauta, clarinete, fagot). Para otro conjunto: `exportar_fuga(voces, "x.mid", conjunto=[('Oboe', 68), ('Corno inglés', 69), ('Fagot', 70)])`.
- **No exporta:** Kitaro (se genera en segundos y sin lista de eventos), los timbres propios, la humanización, el panorama ni la reverb. El platillo de Yanni se omite (es ruido, no una nota).

**Preguntas:** ¿por qué los `note_off` van antes que los `note_on` en el mismo tick? ¿Qué es un delta time? ¿Por qué se pasa el ritardando como cambios de tempo y no como notas más largas?

---

## Parámetros para experimentar (resumen)

| Quiero... | Archivo | Qué tocar |
|-----------|---------|-----------|
| Otro tempo | `winston.py`, `yanni.py`, `fuga.py` | `BPM` / `bpm` |
| Otra armonía | `winston.py`, `kitaro.py`, `yanni.py` | `PROG`, `ACORDES`, `PROG_A/P/C` |
| Melodías distintas | todos | la `semilla` |
| Más o menos reverb | `winston.py`, `kitaro.py`, `yanni.py` | `rt60` y la proporción seco/húmedo en `render` |
| Más brillo en los pads | `kitaro.py` | `brillo` |
| Más o menos crecimiento al final | `yanni.py` | `vel_arp`, diccionarios de velocidades |
| Otra tonalidad de llegada | `yanni.py` | `trans` en `SECCIONES` |
| Fuga más larga o distinta | `fuga_larga.py`, `fuga_episodios.py` | `PLAN` / `plan` |
| Episodios más largos o ascendentes | `fuga_episodios.py` | `k`, `paso`, `base_s` |
| Otros instrumentos MIDI | `midi_export.py` | `CONJUNTOS_FUGA`, `PROGRAMA_YANNI` |

---

## Lecciones de diseño (lo que falló al probar y cómo se resolvió)

1. **Pedir que una nota sostenida sea consonante con todo lo que se mueve a su alrededor no tiene solución.** La primera versión de la voz libre falló por esto. Se relajó la regla: una disonancia en parte débil es válida si la voz que se mueve entra por grado conjunto (`nota_de_paso`), como en el estilo barroco.
2. **El orden de generación importa.** En las secciones nuevas, compuesta primero la voz rápida, no había solución; compuesta primero la lenta, sí.
3. **Las uniones entre secciones son un punto débil.** Cada sección se compone por separado y pueden aparecer paralelismos entre una y otra. Solución: verificar la obra completa y reintentar con otra semilla.
4. **Un contrasujeto "válido" puede ser aburrido.** El primero que encontró el algoritmo oscilaba sobre dos o tres notas. Se añadió un filtro de variedad (≥5 notas distintas, rango ≥4 grados).
5. **Las cadencias necesitan tiempo.** Dominante y tónica no pueden sonar a la vez, así que cada episodio dura 10 tiempos y no 8.
6. **El azar necesita regularización.** En Winston y Yanni, las primeras semillas repetían notas o hacían saltos de séptima. Se penalizó la repetición y los saltos, y se eligió la semilla leyendo las melodías y midiendo repeticiones, saltos máximos y notas ajenas al acorde en tiempo fuerte.
7. **El volumen normalizado oculta la forma.** En Yanni, el final apenas sonaba más fuerte que el resto porque el pico (timbal y platillo) fijaba la normalización. Se ajustaron las velocidades por sección y se midió el RMS cada 10 s.

---

## Limitaciones conocidas e ideas siguientes

**Limitaciones**
- La fuga usa **respuesta real** (transposición exacta), no la *respuesta tonal* de Bach.
- Todo está en **Re menor natural**, sin la sensible (Do♯): las cadencias son modales (VII–i) más que tonales (V–I).
- La modulación es solo al **relativo mayor**; otra tonalidad (p. ej. La menor) exigiría alteraciones, y el sistema trabaja con los grados de Re menor natural.
- No hay **stretto** ni más de tres voces.
- En el MIDI, **todas las notas tienen la misma velocidad** (0,7): las cuerdas sonarán planas.
- **Código duplicado** entre `winston.py`, `kitaro.py` y `yanni.py`: `wav_a_mp3`, `hz`, `piano` (casi igual en Winston y Yanni) y varias versiones de `reverb`. Candidato a un módulo común (`audio.py`).
- Sin **pruebas unitarias** formales.

**Ideas**
- Perfil dinámico en el MIDI (crescendo hacia los puntos culminantes y en las secuencias).
- *Stretto* (entradas solapadas) y entrada del sujeto en la subdominante.
- Respuesta tonal y alteraciones para modular a la dominante.
- Refactorizar Kitaro para recoger eventos y poder exportarlo a MIDI.
- Extraer el código común a `audio.py` y escribir pruebas (por ejemplo, que `verificar()` detecte una quinta paralela puesta a propósito).
- Sustituir la síntesis aditiva por muestras (SoundFont) con FluidSynth.

---

## Glosario

**Musical**
- **Canon:** una melodía que se imita a sí misma con retraso (y a veces transformada).
- **Fuga:** forma contrapuntística construida alrededor de un tema (sujeto) que entra sucesivamente en cada voz.
- **Sujeto:** el tema de la fuga. **Respuesta:** el sujeto transportado a la quinta. **Contrasujeto:** la melodía que acompaña al sujeto cuando entra otra voz.
- **Exposición:** primera parte de la fuga, donde entran todas las voces. **Episodio:** pasaje entre entradas del sujeto, hecho con fragmentos del tema.
- **Secuencia:** repetición de un dibujo melódico en otra altura (p. ej. un grado más grave cada vez).
- **Inversión (movimiento contrario):** reflejo de la melodía; lo que sube, baja. **Aumentación:** la misma melodía con duraciones multiplicadas.
- **Contrapunto invertible:** dos voces que siguen siendo correctas al cambiar de posición (la de arriba pasa abajo).
- **Cadencia:** cierre armónico. **V–I:** dominante → tónica. **VII–i:** subtónica → tónica (en menor natural).
- **Tónica, dominante:** el primer grado de la escala, y el quinto.
- **Relativo mayor:** la tonalidad mayor que comparte las notas con la menor (Fa mayor con Re menor).
- **Modulación:** cambio de centro tonal. **Pedal de sustain:** pedal del piano que deja sonar las notas.
- **Tiempo fuerte / débil:** posición dentro del compás (en 4/4 los tiempos 1 y 3 son fuertes).
- **Nota de paso, floreo, escapada:** disonancias breves en parte débil, aprobadas por la teoría porque entran o salen por grado conjunto.
- **Quintas/octavas paralelas:** dos voces que se mueven a la vez manteniendo un intervalo de quinta u octava; se evitan porque las voces pierden independencia.
- **Pentatónica:** escala de cinco notas (Re, Fa, Sol, La, Do).

**Técnico**
- **Síntesis aditiva:** construir un sonido sumando senoidales (parciales).
- **LFO:** oscilador de baja frecuencia que modula otro parámetro.
- **Convolución / reverb por convolución:** simular una sala convolucionando la señal con su respuesta al impulso.
- **ADSR / envolvente:** cómo evoluciona el volumen de una nota (ataque, sostenido, relajación).
- **Backtracking (búsqueda con retroceso):** explorar soluciones paso a paso, deshaciendo la última decisión cuando se llega a un callejón sin salida.
- **CSP (problema de satisfacción de restricciones):** encontrar valores que cumplan todas las reglas a la vez.
- **Muestreo con rechazo:** generar candidatos al azar y descartar los que no cumplen las reglas.
- **Semilla (`seed`):** valor inicial del generador pseudoaleatorio; misma semilla, mismo resultado.
- **Ticks / PPQ:** unidad de tiempo de un archivo MIDI y su resolución (pulsos por negra).
- **Programa General MIDI:** número (0–127) que identifica un instrumento estándar.

---

## Contexto útil si necesitas pedir ayuda sobre este código

Aporta: el archivo y la función concreta, la semilla y los parámetros que usas, lo que esperabas y lo que ocurrió (y, si es una pieza, en qué compás o minuto lo oyes). Ese contexto vale más que la descripción general del proyecto.
