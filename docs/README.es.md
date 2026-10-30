# Música generativa en Python

Un recorrido de aprendizaje: de los fractales a una **fuga a tres voces con episodios modulantes**, más tres piezas de estilo libre (**George Winston**, **Kitaro** y **Yanni**), con exportación a **WAV, MP3 y MIDI**.

Todo se genera con código: nada está grabado ni compuesto a mano. Cada pieza es un programa que decide notas, ritmos y estructura (con reglas y azar controlado por una *semilla*) y luego sintetiza el audio con NumPy y SciPy.

---

## Autoría y procedencia (leer primero)

La conversación detallada entre Claude y JP está disponible en
[Del Contrapunto al New Age: El Arte de Diseñar Emociones](/docs/diario-de-desarrollo-con-claude.md)

> **Todo el código de este repositorio fue escrito por Claude**, un modelo de IA de Anthropic, en una conversación con JP en claude.ai entre el 24 y el 29 de octubre de 2026. El modelo pudo variar entre mensajes de la conversación.

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
| Que cada script se ejecuta de principio a fin y escribe archivos válidos (WAV, MP3 de 160 o 192 kbps, MIDI releído con `mido`) | La calidad musical de cada semilla (varias se descartaron por *leer* sus melodías, no por oírlas) |
| Que no hay saturación ni valores corruptos, y que la intensidad evoluciona como se diseñó (RMS por tramos) | Pruebas unitarias formales: no existen; la verificación fue con scripts de prueba puntuales |
| Que el MIDI conserva el número de notas y las duraciones de cada pieza | La coherencia armónica fuera de las reglas codificadas (p. ej. los cruces entre secciones solo se comprueban por paralelismos y disonancias en tiempo) |
| Fuga con **stretto** (`fuga_stretto.py`): `verificar()` da 0 disonancias en tiempo y 0 paralelas, y `diagnostico_estricto()` da 0 cruzamientos, 0 disonancias débiles sin grado conjunto y 0 paralelas en 472 posiciones comparadas. | **Los fragmentos iniciales de la conversación** (Mandelbrot, copo de Koch, olas con ruido marrón, primer canon y sus variantes de movimiento contrario y aumentación) **nunca se ejecutaron**. No están en el repositorio como archivos. |
| Fuga **tonal** (`fuga_tonal.py`): `verificar_midi()` da 0 y 0, y `diagnostico_estricto_midi()` da 0 en las cuatro categorías sobre 460 posiciones. La tonalidad de cada sección se estima con Krumhansl-Schmuckler. |  **El comando `fluidsynth -ni fuente.sf2 fuga.mid -F salida.wav`** que se propuso en la conversación no se probó. |
| **Sonidos** (`verificar_sonidos.py`): 15 pruebas objetivas superadas (pendiente espectral del ruido de color, periodicidad de las olas, brillo del agua y del viento, estabilidad de la lluvia, evolución de nivel, brillo y panorama de la tormenta, modos y decaimiento de campanas y cuencos, impulsividad del fuego, portadora y pulsos de los grillos, energía grave del mar, pendiente del ruido fractal, diferencia de frecuencia entre oídos del binaural y ritmo del isocrónico, más una prueba general de nivel y de ausencia de NaN). | **El nombre del botón de MuseScore** para sustituir instrumentos tampoco se verificó. |
| | **La estimación de tonalidad es estadística**, no es oído. Además, en `fuga_tonal.py` la tonalidad esperada de cada sección es un **criterio de selección** (el programa descarta variantes hasta que se cumple), así que las cifras que salen son en parte por construcción: indican que las notas encajan con la tonalidad, no que suene a modulación. |
| | **El tiempo real**: solo se midió la velocidad de generación fuera de línea. No existe ni se probó ningún prototipo de reproducción en directo. |
| | **Binaural e isocrónico**: se verificó que las frecuencias y los pulsos son los previstos, no que tengan ningún efecto sobre quien los escucha. La evidencia al respecto es mixta. |

---

## Contenido del repositorio

| Archivo | Líneas | Qué es | Salida |
|---------|-------:|--------|--------|
| `fuga.py` | 317 | Exposición de la fuga + **motor de contrapunto** | `fuga.wav` |
| `fuga_larga.py` | 147 | Secciones extra: sujeto en inversión y aumentación | `fuga_larga.wav/.mp3` |
| `fuga_episodios.py` | 152 | Fuga completa con episodios modulantes Re → Fa → Re; admite secciones propias (`plan_extra`) | `fuga_episodios.wav/.mp3` |
| `fuga_stretto.py` | 190 | **Stretto**: qué sujetos y retardos lo admiten; fuga con stretto final | `fuga_stretto.wav/.mp3`, `fuga_stretto_{organo,cuerdas,vientos}.mid` |
| `fuga_tonal.py` | 537 | **Modulación a la dominante** (Re → La → Re) con alteraciones y cadencias con sensible | `fuga_tonal.wav/.mp3`, `fuga_tonal_{organo,cuerdas,vientos}.mid` |
| `winston.py` | 204 | Piano estilo Winston | `winston.wav/.mp3` |
| `kitaro.py` | 229 | Ambiental estilo Kitaro | `kitaro.wav/.mp3` |
| `yanni.py` | 389 | Cinematográfico estilo Yanni | `yanni.wav/.mp3` |
| `sonidos_naturales.py` | 505 | 13 paisajes sonoros: olas, río, arroyo, cascada, viento, lluvia, tormenta, campanas, fuego, goteo, grillos, bosque nocturno | `sonido_*.wav/.mp3` |
| `sonidos_meditativos.py` | 224 | Cuencos tibetanos, mar profundo, ruido fractal, binaural e isocrónico | `sonido_*.wav/.mp3` |
| `verificar_sonidos.py` | 283 | 15 pruebas objetivas de los dos módulos de sonido | informe en pantalla |
| `midi_export.py` | 124 | Exporta fuga, Winston y Yanni a MIDI | `*.mid` |

### Dependencias entre archivos

```txt
fuga.py  ←  fuga_larga.py  ←  fuga_episodios.py  ←  fuga_stretto.py
   ↑              ↑                                       (MIDI: midi_export.py)
   └──────────────┴────────  fuga_tonal.py                (MIDI: midi_export.py)

sonidos_naturales.py  ←  sonidos_meditativos.py
        ↑                         ↑
        └─────────  verificar_sonidos.py

winston.py, kitaro.py, yanni.py: independientes entre sí
midi_export.py: importa fuga_episodios, winston y yanni (solo en su bloque principal)

```

`fuga_tonal.py` solo toma de `fuga_larga.py` la función `wav_a_mp3`, y de `fuga.py` la exposición y la síntesis. No depende de `fuga_episodios.py` ni de `fuga_stretto.py`.

> Los primeros ejemplos de la conversación (fractales de Mandelbrot y Koch, olas con ruido marrón, y el primer canon) se escribieron como fragmentos en el chat y **no** forman parte de estos archivos. Sus ideas reaparecen en `fuga_larga.py` (`inversion`, `aumentacion`).

### Audio y MIDI de ejemplo que se pueden subir

`fuga_larga.mp3`, `fuga_episodios.mp3`, `fuga_stretto.mp3`, `fuga_tonal.mp3`, `winston.mp3`, `kitaro.mp3`, `yanni.mp3`, los 18 `sonido_*.mp3` (unos 13 MB los 13 naturales), y los MIDI `fuga_organo.mid`, `fuga_cuerdas.mid`, `fuga_vientos.mid`, `fuga_stretto_*.mid`, `fuga_tonal_*.mid`, `winston.mid`, `yanni.mid`.

### `.gitignore` recomendado

```.gitignore
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
python fuga_stretto.py                  # ≈ 12 s; --dmin 2 --dmax 3 (por defecto) fija qué retardos admite
python fuga_tonal.py                    # ≈ 5 s: fuga con modulación a La menor
python sonidos_naturales.py             # ≈ 47 s los 13; o: python sonidos_naturales.py rio tormenta --dur 120
python sonidos_meditativos.py           # ≈ 26 s los 5
python verificar_sonidos.py             # ≈ 58 s; imprime 15/15 si todo va bien
```

> Los tiempos son los medidos en el entorno de pruebas; en otro equipo variarán. `midi_export.py` genera los MIDI de la fuga anterior; `fuga_stretto.py` y `fuga_tonal.py` escriben los suyos al ejecutarse.

**Reproducibilidad:** todo el azar sale de `numpy.random.default_rng(semilla)`. Con la misma semilla y la misma versión de NumPy debe salir la misma pieza; entre versiones de NumPy no está garantizado.

**Ver la fuga escrita:** abre los `.mid` en MuseScore Studio. Cada voz es una pista, así que se ven las secuencias, las cadencias y las entradas del sujeto.

---

## Qué hace cada pieza

- **Fuga (`fuga.py`, `fuga_larga.py`, `fuga_episodios.py`).** En Re menor, a tres voces. La exposición presenta el sujeto, la respuesta a la quinta y el contrasujeto. `fuga_larga.py` añade entradas con el sujeto invertido y aumentado. `fuga_episodios.py` construye la forma completa: exposición, episodio modulante a Fa mayor, entradas en Fa, episodio de regreso y entradas finales en Re menor. El contrapunto no es azar suelto: se **busca** con reglas (consonancia, sin paralelas, saltos limitados) y se comprueba al final.
- **Winston (`winston.py`).** Progresión lenta Am–F–C–G, arpegio continuo en la mano izquierda, melodía espaciada, pedal de sustain, piano sintetizado, estructura A A′ B B′ A y ritardando.
- **Kitaro (`kitaro.py`).** Drone con osciladores desafinados, pads de ataque lento sobre Dm9–Bbmaj7–Fmaj7–Cadd9, flauta pentatónica con vibrato, pulso de pizzicatos con eco ping-pong y reverb de 5 s.
- **Yanni (`yanni.py`).** Ostinato de piano, melodía con secuencias, violonchelo, cuerdas, violín solista, timbales y platillos, puente ascendente que acaba en el dominante de la nueva tonalidad y cambio de Re menor a Mi menor.
- **Stretto (`fuga_stretto.py`).** Entradas del sujeto que empiezan antes de que acabe la anterior. No sirve cualquier sujeto: el programa comprueba cuáles admiten un stretto con retardo corto y construye la fuga completa con el que lo permite, con un stretto de tres entradas al final.
- **Modulación a la dominante (`fuga_tonal.py`).** Re menor → La menor → Re menor, con episodios cuya secuencia cruza de una escala a otra, entradas del sujeto en La menor (transposición real) y cadencias auténticas con sensible (Sol♯ y Do♯). Las notas son alturas MIDI, así que caben las alteraciones.
- **Paisajes sonoros (`sonidos_naturales.py`).** Agua (modelo físico de burbujas), oleaje, viento con ráfagas, lluvia suave, una tormenta que se acerca, pasa por encima y se aleja (con truenos y panorama en movimiento), campanas de viento de metal y de madera, fuego, goteo en una cueva, grillos y una mezcla de bosque nocturno.
- **Sonidos meditativos (`sonidos_meditativos.py`).** Cuencos tibetanos (golpeados y frotados), mar profundo con llamadas de ballena opcionales, ruido fractal cuya pendiente espectral cambia con el tiempo, y tonos binaurales e isocrónicos.

---

# Guía de estudio del código

Esta guía es una referencia para estudiar el código sin tener que preguntar de nuevo. Está pensada para alguien con base sólida en programación y matemáticas, pero no necesariamente en teoría musical.

## Cómo usar la guía

1. Lee primero **"Formatos de datos"** (la clave de todo) y el **glosario** del final.
2. Sigue el **orden de lectura** recomendado.
3. Por cada archivo: lee la sección de esta guía, luego el código, y haz **al menos un experimento** de los propuestos (cambiar una constante y volver a escuchar).
4. Contesta las **preguntas de autoevaluación**. Si no sabes responder una, esa es la parte que conviene releer.

## Orden de lectura recomendado

### Generadores de música

| Paso | Archivo | Dificultad | Qué aprendes |
|-----:|---------|:----------:|--------------|
| 1 | `winston.py` | ★☆☆ | El patrón general: generar eventos → sintetizar → mezclar. Síntesis aditiva y melodía con reglas |
| 2 | `kitaro.py` | ★★☆ | Procesado de señal: osciladores, LFO, eco, reverb por convolución |
| 3 | `yanni.py` | ★★☆ | Estructura por secciones, transposición, secuencias melódicas |
| 4 | `fuga.py` | ★★★ | **Búsqueda con retroceso** aplicada al contrapunto (el corazón intelectual) |
| 5 | `fuga_larga.py` | ★★☆ | Reutilizar el motor con transformaciones del tema |
| 6 | `fuga_episodios.py` | ★★★ | Secuencias reales con *escenarios*; cadencias; modulación |
| 7 | `midi_export.py` | ★☆☆ | El formato MIDI (eventos, ticks, mapa de tempo) |
| 8 | `sonidos_naturales.py` | ★★☆ | Un conjunto de generadores sobre unas pocas piezas básicas: ruido de color, modulación lenta, eventos de Poisson, síntesis modal |
| 9 | `sonidos_meditativos.py` | ★★☆ | Pulsaciones, solapamiento de tramos con pendiente variable, acumulación de fase |
| 10 | `verificar_sonidos.py` | ★★☆ | Cómo comprobar con números lo que no se puede oír |
| 11 | `fuga_stretto.py` | ★★★ | Búsqueda de combinaciones que cumplan restricciones por pares |
| 12 | `fuga_tonal.py` | ★★★★ | Escalas por sección, secuencias que cruzan de tonalidad, cadencias con sensible y estimación de tonalidad |

### Generadores de sonido

Una forma práctica de empezar los sonidos: lee `ruido_color`, `lento`, `tren`, `burbuja` y `acabar` de `sonidos_naturales.py` antes de cualquier generador; todo lo demás se construye con ellas.

## Formatos de datos (la clave de todo)

**Tiempo musical.** La unidad es la negra, llamada "tiempo". Un compás de 4/4 son 4 tiempos; una corchea es 0,5. Para pasar a segundos: `segundos(b, b0, bend)` en Winston y Yanni (incluye el ritardando) y `beat = 60 / bpm` en la fuga. Kitaro trabaja directamente en segundos.

**Altura.**

- *Fuga:* grados diatónicos de Re menor natural, como enteros. `0` = Re4 (MIDI 62), `1` = Mi4, `2` = Fa4, `3` = Sol4, `4` = La4, `5` = Si♭4, `6` = Do5, `7` = Re5; los negativos bajan (`-7` = Re3). `midi(grado)` los convierte a MIDI. Transponer por grados es sumar un entero, y **no cambia la escala**: por eso la respuesta a la quinta es `+4` y el cambio al relativo mayor (Fa) es `+2`.
- *Winston, Yanni, Kitaro:* números MIDI directos (60 = Do4, 69 = La4 = 440 Hz).
- *`fuga_tonal.py`:* alturas MIDI, no grados de Re menor, porque necesita alteraciones (Sol♯ y Do♯ no existen en Re menor natural). `a_midi()` convierte a MIDI las voces de `fuga.py`.

**Nota y evento.**
- *Fuga:* una voz es una lista de `(grado, inicio, duración)`, y la obra es `voces = {'soprano': [...], 'alto': [...], 'bajo': [...]}`.
- *`fuga_tonal.py`:* una voz es una lista de `(altura_midi, inicio, duración)`; la obra sigue siendo `{'soprano': [...], 'alto': [...], 'bajo': [...]}`.
- *Winston:* `(midi, inicio, duración_hasta_levantar_el_pedal, velocidad 0–1)`.
- *Yanni:* `(instrumento, midi, inicio, duración, velocidad, panorama_o_None)`.
- *Kitaro:* no hay una lista común de eventos: `componer()` coloca las señales en un búfer a medida que las genera.

**Convención de posición en el contrapunto.** `(voz, '<')` significa "la voz nueva queda por **debajo** de esa voz"; `'>'`, por encima.

**Escalas y grados en `fuga_tonal.py`.** `Escala(tonica, modo)`: el índice 0 es la tónica y `esc.midi(i)` da la altura del grado `i`. Re menor es `Escala(62)` y La menor `Escala(69)`; el modo `'armonica'` sube el séptimo grado (la sensible). La voz que genera `contrapunto_tonal()` son **índices relativos** de escala: la altura final es `esc.midi(g + despl)`, y cada *escenario* puede traer su propia escala. `triada` son clases de altura (módulo 12), no grados: `{9, 0, 4}` es el acorde de La menor.

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
  - la primera nota cerca de la anterior (`previa`) y la última dentro de `triada` (por defecto, la tríada de Re menor; `triada=None` quita la regla, y otras secciones le pasan la de Fa mayor o la de la tónica de llegada).
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
- **`seccion()` admite `triada` y `rangos` propios**, necesarios para escribir en otra tonalidad (Fa mayor en `fuga_episodios.py`). Sus valores por defecto reproducen el comportamiento original.

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
- **`fuga_completa(semilla, intentos, plan_extra=())`** acepta secciones de tipo `'custom'` con una función propia `fn(voces, t0, S, sem) -> (voces, duración)`. Así se enganchó el stretto (`fuga_stretto.py`) sin tocar el resto.

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

## 8. `sonidos_naturales.py`

**Flujo:** cada generador (`olas`, `rio`, `tormenta`...) construye señales con unas piezas básicas, las mezcla y las pasa por `acabar()`, que aplica reverb opcional, normalización y fundidos. `guardar()` escribe WAV y MP3.

**Piezas básicas (léelas primero)**
- `ruido_color(n, beta, rng)`: ruido con espectro de potencia ∝ 1/f^β, creado dando forma a la FFT de ruido blanco.
- `lento(n, rng, tau)` y `rafaga()`: variación aleatoria suave con escala de tiempo `tau`, calculada a baja frecuencia de muestreo e interpolada. Es lo que mueve los caudales, las ráfagas y el fuego.
- `tren(n, rng, tasa)`: impulsos de Poisson con amplitud de cola pesada (muchos pequeños, pocos grandes). Es la base de la lluvia, los chasquidos del fuego y la tormenta.
- `burbuja(f0, amp)`: modelo de Minnaert / van den Doel: una senoide amortiguada cuya frecuencia sube alrededor de un 10 % mientras se apaga, con `f0 ≈ 3,26 / radio(m)` Hz. Las burbujas grandes dan graves ("gluglú"), las pequeñas agudos.
- `acabar()`: normaliza por RMS (con un limitador suave con techo en 0,9) o por pico (para sonidos escasos, como las campanas).

**Cómo está hecho cada sonido (en una línea)**
- `olas`: rumor grave que crece ~5 s, cresta y decae; la espuma es un siseo agudo más corto; cada ola desplaza el panorama.
- `agua` (río, arroyo, cascada): turbulencia + burbujas de Poisson de tasa variable. Solo cambian los parámetros `tasa`, `r_mm`, `grave`, `medio`, `siseo`.
- `viento_bosque`: cuanto más fuerte la ráfaga, más agudo el timbre (se mezclan bandas con exponentes crecientes de la ráfaga), más hojas y un silbido estrecho.
- `lluvia_suave`: miles de microimpactos por segundo + gotas medianas + goteo de hojas (`ping`) + burbujas de charco.
- `tormenta`: la cercanía N(t) es una gaussiana asimétrica; lejos solo suenan los graves (el aire absorbe los agudos) y cerca suena todo; el centro de la tormenta cruza de izquierda a derecha y, al pasar por encima, el sonido se abre a todo el estéreo. Los truenos (`trueno`) son más fuertes cuanto más cerca está.
- `campana` / `campanas`: síntesis modal. Metal: parciales de una barra libre (1; 2,756; 5,404; 8,933) con decaimiento propio. Madera: parciales que se extinguen rápido y un golpe seco. Una ráfaga de viento hace chocar varias campanas vecinas.
- `fuego`, `goteo_cueva`, `grillos`, `bosque_nocturno`: ver el código; todos usan las mismas piezas.

**Experimentos:** cambia `tasa` y `r_mm` en `rio` o `arroyo` y compara; en `tormenta`, mueve `t_pico`, `wa` y `wd`; en `viento_bosque`, prueba otro `sesgo` en `rafaga`; en `campanas`, sustituye las notas de `METAL`; cambia el `beta` de un `ruido_color` (por ejemplo, de 2.0 a 1.0 en `olas`) y mira cómo cambia el timbre.

**Preguntas:** ¿por qué `lento()` trabaja a 100 Hz y no a 44100? ¿Qué diferencia hay entre normalizar por RMS y por pico, y por qué las campanas usan pico? ¿Por qué la tormenta mezcla bandas con exponentes distintos de la cercanía? ¿Qué relación hay entre el radio de una burbuja y su tono?

## 9. `sonidos_meditativos.py`

- **Cuencos** (`cuenco`): cada uno de los 4 modos inarmónicos (`RATIOS_CUENCO`) se desdobla en dos frecuencias separadas de 0,25 a 1,4 Hz; su suma da pulsaciones lentas (el "latido"). Golpeado: cada modo decae solo (los agudos antes). Frotado: excitación continua y los modos agudos entran poco a poco. Las proporciones de los modos son valores típicos tomados de la literatura, no medidos en un cuenco real.
- **Mar profundo** (`mar_profundo`): casi todo por debajo de 800 Hz: presión (< 110 Hz), oleaje lejano amortiguado de ~10 s, burbujas grandes y llamadas de ballena (`llamada_ballena`, con `ballenas=False` se desactivan), con reverb de 7 s.
- **Ruido fractal** (`fractal`): la pendiente β cambia en el tiempo (`curva_beta`: triangular de 0,2 a 2,2 y vuelta). Cada tramo de 0,74 s es ruido con su β propio, y los tramos se solapan a la mitad con ventana senoidal, de modo que la potencia total es constante. `hurst(β) = (β − 1)/2` y `dimension_fractal(β) = 2 − H` convierten la pendiente en el exponente de Hurst y en la dimensión fractal de la gráfica de la señal (válido para 1 < β < 3).
- **Binaural** (`binaural`): oído izquierdo a `portadora − beat/2` y derecho a `portadora + beat/2`; el `beat` baja de 10 a 4 Hz. La fase se calcula con `cumsum` de la frecuencia (si no, el cambio de frecuencia produciría saltos de fase). Necesita auriculares.
- **Isocrónico** (`isocronico`): un tono cuya amplitud late a `ritmo` Hz; funciona en altavoces.

**Experimentos:** `beta=(1.0, 1.0)` en `fractal` da ruido rosa estable; prueba `beat=(8, 8)` en `binaural` y mide en `verificar_sonidos.py` que la diferencia entre oídos es 8 Hz; sube `delta` máximo (en `cuenco`) y observa la velocidad del latido.

**Preguntas:** ¿por qué se usa ventana senoidal y no de Hann al solapar tramos de ruido independientes? ¿Por qué hace falta acumular la fase en el binaural? ¿Cómo se relaciona la pendiente espectral con la dimensión fractal? ¿Por qué los parciales de un cuenco son inarmónicos?

## 10. `verificar_sonidos.py`

Cada prueba mide una propiedad que sí se puede medir:

| Prueba | Mide |
|--------|------|
| `t_ruido_color` | pendiente log-log del espectro, comparada con la β teórica |
| `t_olas` | separación mediana entre las crestas detectadas |
| `t_agua` | el arroyo es más brillante (centroide espectral) que el río |
| `t_viento` | correlación entre nivel y brillo de las ráfagas |
| `t_lluvia` | estabilidad del nivel y brillo medio (sin los fundidos) |
| `t_tormenta` | instante del máximo, subida de nivel, brillo creciente en el pico y relación L/R al inicio y al final |
| `t_campanas` | parciales en f0·[1; 2,756; 5,404] y que la madera decae más deprisa que el metal |
| `t_fuego` | curtosis de la banda aguda (impulsividad) |
| `t_grillos` | portadora dominante y ritmo de los pulsos |
| `t_cuencos` | modos, pulsación, tiempo de caída de 60 dB y tiempo de subida del cuenco frotado |
| `t_mar` | fracción de energía bajo 800 Hz y variación de nivel |
| `t_fractal` | β medida frente a la prevista a lo largo de la pieza |
| `t_binaural` | diferencia de frecuencia entre oídos y fuga de un tono al otro oído |
| `t_isocronico` | ritmo de los pulsos |
| `t_general` | sin NaN, techo de pico y nivel audible, en todas las piezas |

**Lo que no hace:** no dice si algo suena bien. Una prueba que falla suele indicar un error de síntesis o de medida (ver la lección 8). Para añadir una prueba: escribe `t_algo()` que devuelva `(ok, mensaje)` y añádela a `PRUEBAS`.

## 11. `fuga_stretto.py`

**Flujo:** `cadenas_stretto(S)` busca encadenamientos válidos de tres entradas → `seccion_stretto` los prueba por orden hasta que toda la obra verifica → `fuga_con_stretto` elige el sujeto.

**Conceptos clave**
- **Stretto**: entradas del sujeto con retardo menor que su duración. Para que sea válido, las voces solapadas deben cumplir las reglas del contrapunto.
- **`chequear_pareja(a, b, a_arriba)`**: reglas entre dos líneas ya escritas, cada corchea donde suenan las dos: sin cruzamiento, solo consonancias en los tiempos, disonancia débil solo si una voz la ataca por grado conjunto, sin quintas ni octavas paralelas. Devuelve `(ok, motivo)`.
- **`pares_validos(S)`**: qué (retardo, transposición) admite el sujeto consigo mismo.
- **`cadenas_stretto(S)`**: para tres voces, cada una con el sujeto `'S'` o la respuesta `'A'` (transposiciones en `OPCIONES`: soprano {S: +7, A: +4}, alto {S: 0, A: −3}, bajo {S: −7, A: −10}), en cada orden de entrada y con retardos d = 0 / d / 2d. **Cada par** que se solape debe ser válido. Se ordenan de retardo menor a mayor.
- **Elegir el sujeto, no solo el stretto**: `candidatos_stretto` recorre semillas y conserva las que admiten stretto Y permiten componer la exposición (`componer(s)[0] == s`). `fuga_con_stretto` construye la fuga con el más apretado.
- **`diagnostico_estricto`**: revisión de toda la obra más severa que `verificar()`.

**Resultados (con las semillas por defecto)**
- El sujeto original (semilla 2) solo admite retardo de 4 tiempos, y solo a la octava.
- De 300 sujetos candidatos, 19 admiten un retardo de 3 tiempos o menos, y 7 de ellos permiten además componer la exposición.
- Se eligió el de la semilla 5, con retardo de 3 tiempos (alto, soprano, bajo, todos con el sujeto).
- El sujeto de la semilla 71 admite, entre **dos** entradas, muchos retardos (1; 2; 2,5; 3; 4...). Al encadenar **tres** entradas solo admite 1 tiempo, y ese encadenamiento mezcla respuesta y sujeto (alto con la respuesta, luego bajo y soprano con el sujeto).

**Experimentos:** `python fuga_stretto.py --dmin 0.5 --dmax 1` usa un sujeto con stretto de 1 tiempo; añade posiciones a `OPCIONES`; amplía el rango de `cadenas_stretto` a `dmax=6`; cuenta con `pares_validos(sujeto(s))` cuántos retardos admite cada semilla.

**Preguntas:** ¿por qué hay que elegir el sujeto en vez de componer el stretto alrededor de uno cualquiera? ¿Por qué `cadenas_stretto` comprueba todos los pares y no solo los consecutivos? ¿Por qué `candidatos_stretto` exige que la exposición se pueda componer con ese mismo sujeto?

## 12. `fuga_tonal.py` (el módulo más largo)

**Flujo:** exposición de `fuga.py` → `a_midi` → siete pasos (episodio I, dos entradas en La menor, episodio II, dos entradas en Re menor y cadencia final), cada uno con su tonalidad esperada → `verificar_midi`.

**Conceptos clave**
- **Por qué alturas MIDI**: Re menor natural no contiene Sol♯ ni Do♯, que son las sensibles de La y Re menor. Con grados de Re menor no se pueden escribir.
- **`Escala`** (índice 0 = tónica) y **`contrapunto_tonal`**: cada escenario lleva su escala, y la voz generada son índices relativos válidos en todas. Reglas nuevas: la nota anterior se mide en semitonos (≤ 7) y no hay segundas aumentadas (Fa → Sol♯ en La menor armónica).
- **Transposición real frente a diatónica**: el sujeto en La menor es el de Re menor + 7 semitonos, que conserva todos los intervalos y solo cambia Si♭ por Si natural. El paso a Fa mayor de `fuga_episodios.py` usaba el mismo grado de otra tónica: mismas notas, intervalos distintos.
- **`episodio_tonal`**: la secuencia baja un grado por repetición, y la última repetición se escribe en la escala de llegada con un desplazamiento de −4 (Re → La) o +4 (La → Re) grados, que compensa el cambio de tónica (una quinta son unos 4 grados) para que la altura siga bajando un grado y no salte. El contramotivo del alto se genera una vez y es válido en las tres repeticiones aunque la última tenga otra escala.
- **`cadencia`**: enumera combinaciones de notas para tres voces y dos acordes (dominante → tónica) y elige la de menor movimiento. Reglas: bajo en la fundamental, sensible en una voz aguda que sube un semitono a la tónica, acorde de tónica con fundamental **y tercera**, consonancia entre todas las voces, sin paralelas, sin segundas aumentadas.
- **`seccion_tonal`**: como `fuga_larga.seccion`, pero en MIDI y con tríada por clases de altura.
- **`estimar_tonalidad`**: algoritmo de Krumhansl-Schmuckler. Se acumula la duración de cada una de las 12 clases de altura en un tramo y se correlaciona con el perfil de cada una de las 24 tonalidades. Es una estimación estadística. **`informe_tonal`** la imprime por tramos junto con el tiempo que suena cada alteración.
- **La tonalidad esperada es un criterio de selección**: `fuga_tonal()` solo acepta una sección si su tonalidad estimada es la prevista; por eso se descartaron variantes hasta encontrar la 8.
- **`render_midi` / `exportar_midi`**: lo mismo que `fuga.render` y `midi_export` pero con alturas MIDI.

**Experimentos**
- Quita la comprobación `esperada` en `paso()` y mira qué tonalidad estima el informe en cada sección.
- Usa `LA_ARM` (La menor armónica) en las entradas en La menor para que aparezca Sol♯ en las voces generadas.
- Cambia `k` y `paso` en `episodio_tonal` o el orden de los pasos.
- Pide el episodio II con el destino contrario (`'La'` en lugar de `'Re'`) y comprueba qué falla.

**Preguntas:** ¿por qué la cadencia exige la tercera en el acorde de tónica? ¿Qué problema aparecería si la secuencia pasara a la escala nueva sin el desplazamiento de ±4 grados? ¿Por qué el estimador de tonalidad confunde el tramo de las secuencias? ¿Qué cambia entre una transposición real y una diatónica?

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
| Stretto más apretado o más suelto | `fuga_stretto.py` | `--dmin`, `--dmax` o los argumentos de `fuga_con_stretto` |
| Otras voces o transposiciones en el stretto | `fuga_stretto.py` | `OPCIONES`, `VOCES` |
| Modulación distinta o episodios distintos | `fuga_tonal.py` | la lista `pasos`, `episodio_tonal(k, paso)`, `esperada` |
| Entradas con sensible en la voz generada | `fuga_tonal.py` | usar `LA_ARM` / `RE_ARM` en `seccion_tonal` |
| Otra forma de la tormenta | `sonidos_naturales.py` | `t_pico`, `wa`, `wd` en `tormenta` |
| Agua más lenta o más rápida | `sonidos_naturales.py` | `tasa`, `r_mm`, `grave`, `siseo` en `agua` |
| Viento menos violento | `sonidos_naturales.py` | `fuerza` y el `sesgo` de `rafaga` |
| Lluvia menos áspera | `sonidos_naturales.py` | los 9000 Hz de `banda` en `lluvia_suave`, `intensidad` |
| Otras campanas | `sonidos_naturales.py` | `METAL`, `MADERA`, `RATIOS_BARRA` |
| Cuencos distintos | `sonidos_meditativos.py` | `AFINACION`, `RATIOS_CUENCO`, la constante `tau` en `cuenco` |
| Ruido fractal distinto | `sonidos_meditativos.py` | `beta=(inicio, fin)` en `fractal` |
| Otro batido binaural | `sonidos_meditativos.py` | `portadora`, `beat` |

---

## Lecciones de diseño (lo que falló al probar y cómo se resolvió)

1. **Pedir que una nota sostenida sea consonante con todo lo que se mueve a su alrededor no tiene solución.** La primera versión de la voz libre falló por esto. Se relajó la regla: una disonancia en parte débil es válida si la voz que se mueve entra por grado conjunto (`nota_de_paso`), como en el estilo barroco.
2. **El orden de generación importa.** En las secciones nuevas, compuesta primero la voz rápida, no había solución; compuesta primero la lenta, sí.
3. **Las uniones entre secciones son un punto débil.** Cada sección se compone por separado y pueden aparecer paralelismos entre una y otra. Solución: verificar la obra completa y reintentar con otra semilla.
4. **Un contrasujeto "válido" puede ser aburrido.** El primero que encontró el algoritmo oscilaba sobre dos o tres notas. Se añadió un filtro de variedad (≥5 notas distintas, rango ≥4 grados).
5. **Las cadencias necesitan tiempo.** Dominante y tónica no pueden sonar a la vez, así que cada episodio dura 10 tiempos y no 8.
6. **El azar necesita regularización.** En Winston y Yanni, las primeras semillas repetían notas o hacían saltos de séptima. Se penalizó la repetición y los saltos, y se eligió la semilla leyendo las melodías y midiendo repeticiones, saltos máximos y notas ajenas al acorde en tiempo fuerte.
7. **El volumen normalizado oculta la forma.** En Yanni, el final apenas sonaba más fuerte que el resto porque el pico (timbal y platillo) fijaba la normalización. Se ajustaron las velocidades por sección y se midió el RMS cada 10 s.
8. **Mide antes de ajustar.** La prueba de la lluvia falló porque incluía los fundidos de entrada y salida en el cálculo de estabilidad, pero se interpretó como lluvia poco estable y se retocó el generador sin necesidad. El problema estaba en la medida (la variación real era de 0,23 dB).
9. **Un stretto depende del sujeto.** Solo 19 de 300 sujetos admiten un retardo de 3 tiempos o menos. Los encadenamientos válidos que se encontraron son casi todos a la octava (sujeto con sujeto o respuesta con respuesta); con las reglas usadas no apareció uno que alterne sujeto y respuesta, que es lo habitual en Bach.
10. **Las cadencias necesitan tercera.** La primera versión terminaba en un acorde de fundamental y quinta, y el estimador de tonalidad lo leyó como Re mayor (0,79). Al exigir la tercera, la cadencia final se estima como Re menor (0,88).
11. **Si la métrica es el criterio, los resultados salen en parte por construcción.** `fuga_tonal.py` solo acepta una sección si su tonalidad estimada es la prevista. Eso garantiza que las notas encajan, no que suene a modulación.
12. **Transposición real frente a diatónica.** Pasar a La menor sumando 7 semitonos conserva todos los intervalos; pasar a Fa mayor sumando 2 grados conserva las notas pero no los intervalos. Es la diferencia entre dos modulaciones que se pueden distinguir.
13. **Una secuencia puede cruzar de tonalidad.** Basta con cambiar la escala de la última repetición y compensar el cambio de tónica con ±4 grados.
14. **Con restricciones acumuladas, falla el orden de generación o el tamaño de la cadencia.** Ya pasó en la fuga (voz lenta primero, cadencia de 4 tiempos); en `fuga_tonal.py` la cadencia se resuelve por enumeración en lugar de por búsqueda.

---

## Limitaciones conocidas e ideas siguientes

**Limitaciones**
- La fuga usa **respuesta real** (transposición exacta), no la *respuesta tonal* de Bach.
- En el MIDI, **todas las notas tienen la misma velocidad** (0,7): las cuerdas sonarán planas.
- **Código duplicado** entre `winston.py`, `kitaro.py` y `yanni.py`: `wav_a_mp3`, `hz`, `piano` (casi igual en Winston y Yanni) y varias versiones de `reverb`. Candidato a un módulo común (`audio.py`).
- Sin **pruebas unitarias** formales.
- `fuga_tonal.py` **no integra el stretto ni la sección en Fa mayor**; son versiones separadas.
- Las entradas en La menor usan la menor natural; **Sol♯ y Do♯ solo aparecen en las cadencias**. La inversión en La menor es diatónica, no cromática.
- Los stretti encontrados son casi todos **a la octava**; falta probar si alternar sujeto y respuesta es imposible con estas reglas o solo con estas transposiciones.
- La aumentación en Re menor es el tramo con la tonalidad más débil de `fuga_tonal.py` (Re menor 0,69 frente a Sol mayor 0,68).
- **Código duplicado**: `wav_a_mp3` aparece en cuatro archivos, y hay varias versiones de `reverb` y de la síntesis de piano. Candidato a un módulo común (`audio.py`).
- **Tiempo real**: todo se genera entero de una vez. Convertirlo a bloques exige estado entre bloques (filtros, fases) y cambiar el ruido por FFT y la reverb por convolución por soluciones recursivas o por bloques. Sin prototipo.
- **Timbres sintetizados** de flauta, clarinete, fagot y cuerdas para el audio de la fuga: solo existen como programas MIDI.
- Kitaro no se exporta a MIDI.

**Ideas**
- Perfil dinámico en el MIDI (crescendo hacia los puntos culminantes y en las secuencias).
- *Stretto* (entradas solapadas) y entrada del sujeto en la subdominante.
- Respuesta tonal y alteraciones para modular a la dominante.
- Refactorizar Kitaro para recoger eventos y poder exportarlo a MIDI.
- Extraer el código común a `audio.py` y escribir pruebas (por ejemplo, que `verificar()` detecte una quinta paralela puesta a propósito).
- Un prototipo de reproducción en directo con `sounddevice` (lluvia, viento, binaural, cuencos, campanas) con controles en vivo.
- Combinar stretto y modulación a la dominante en una sola obra.
- Una modulación a otras tonalidades (`destino` ahora solo admite `'La'` y `'Re'`).
- Pájaros, ranas y mar con oleaje fuerte entre los sonidos.
- Sustituir la síntesis aditiva por un SoundFont (FluidSynth).

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
- **Stretto:** entradas del sujeto que empiezan antes de que acabe la anterior.
- **Dominante:** la tonalidad construida sobre el quinto grado (La menor respecto a Re menor); también, el acorde del quinto grado.
- **Sensible:** la nota que está un semitono por debajo de la tónica y tiende a subir a ella (Sol♯ en La menor, Do♯ en Re menor).
- **Menor armónica:** escala menor con el séptimo grado elevado (la sensible).
- **Cadencia auténtica (V–i):** dominante → tónica, con la sensible subiendo a la tónica.
- **Transposición real / diatónica:** la real mueve todas las notas el mismo número de semitonos y conserva los intervalos; la diatónica las mueve el mismo número de grados de una escala y puede cambiar su calidad.
- **Acorde de dominante, de tónica:** los acordes sobre el quinto y el primer grado.
- **Acorde pivote:** acorde común a dos tonalidades, que sirve de puente al modular.
- **Cuenco tibetano:** objeto metálico con modos de vibración inarmónicos que suena al golpearlo o frotarlo.
- **Pulsación (latido):** variación lenta de volumen que resulta de sumar dos sonidos de frecuencia casi igual.

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
- **Ruido 1/f^β (de color):** ruido cuya potencia decae como 1/f^β; β = 0 blanco, 1 rosa, 2 marrón.
- **Exponente de Hurst (H) y dimensión fractal:** para un movimiento browniano fraccionario, la pendiente es β = 2H + 1 y la gráfica tiene dimensión D = 2 − H.
- **Proceso de Poisson:** eventos independientes con una tasa media por segundo; modela gotas, chasquidos y burbujas.
- **Burbuja de Minnaert:** modelo físico de la burbuja de aire en el agua: resuena a una frecuencia inversamente proporcional a su radio.
- **Síntesis modal:** sumar los modos de vibración de un objeto, cada uno con su frecuencia y su decaimiento.
- **Tono binaural:** dos tonos de frecuencia casi igual, uno por oído; su diferencia (el batido) solo existe en la percepción.
- **Tono isocrónico:** un tono que late a un ritmo fijo; funciona en altavoces.
- **Solapamiento-suma (overlap-add):** construir una señal larga con tramos que se solapan; con ventana senoidal y tramos independientes la potencia total es constante.
- **Krumhansl-Schmuckler:** algoritmo que estima la tonalidad de un fragmento correlacionando la duración de cada clase de altura con 24 perfiles (12 mayores y 12 menores).
- **Centroide espectral:** la "frecuencia media" del espectro; mide el brillo de un sonido.
- **Curtosis:** medida de cuán impulsiva es una señal; el ruido gaussiano tiene curtosis 3.
- **RMS:** valor eficaz de una señal, la medida habitual de su volumen medio.

---

## Estado de lo pendiente

| Pendiente | Estado |
| ----------- | -------- |
| Stretto | Hecho (`fuga_stretto.py`) |
| Modulación a la dominante | Hecho (`fuga_tonal.py`) |
| Cuencos, mar profundo, ruido fractal, binaural | Hechos (`sonidos_meditativos.py`) |
| Sonidos naturales (río, arroyo, viento, lluvia, tormenta, campanas, otros) | Hechos (`sonidos_naturales.py`). JP volverá con comentarios de ajuste |
| ¿Qué se puede generar en tiempo real? | Respondido con mediciones; sin prototipo |
| Timbres sintetizados de vientos y cuerdas para la fuga | Pendiente |
| Perfil dinámico (velocidades) en el MIDI | Pendiente |
| Ejecutar los fragmentos iniciales (Mandelbrot, Koch, olas, canon y variantes) | Pendiente |
| Exportar Kitaro a MIDI | Pendiente |
| Prototipo de tiempo real con `sounddevice` | Pendiente |

## Contexto útil si necesitas pedir ayuda sobre este código

Aporta: el archivo y la función concreta, la semilla y los parámetros que usas, lo que esperabas y lo que ocurrió (y, si es una pieza, en qué compás o minuto lo oyes). Ese contexto vale más que la descripción general del proyecto.
