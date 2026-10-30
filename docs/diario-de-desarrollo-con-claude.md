# Del Contrapunto al New Age: El Arte de Diseñar Emociones

Un recorrido de arquitectura musical a través de las matemáticas y el código
con Claude.

## Índice de contenidos

- [Generación de Fractales](#generación-de-fractales)
- [Generación de sonidos tranquilizantes](#generación-de-sonidos-tranquilizantes)
- [Música generativa](#música-generativa)
- [Los cinco pasos del diseño](#los-cinco-pasos-del-diseño)
  - [1. Canon por movimiento contrario](#1-canon-por-movimiento-contrario)
  - [2. Fuga: sujeto, respuesta a la quinta, y contrasujeto con reglas de contrapunto](#2-fuga-sujeto-respuesta-a-la-quinta-y-contrasujeto-con-reglas-de-contrapunto)
    - [2.1 Ahondando en la fuga](#21-ahondando-en-la-fuga)
  - [3. Composición estilo Winston](#3-composición-estilo-winston)
  - [5. Composición estilo Kitaro](#5-composición-estilo-kitaro)
  - [4. Composición estilo Yanni](#4-composición-estilo-yanni)
  - [1. (cont) El episodio modulante de la fuga, con secuencias y modulación](#1-cont-el-episodio-modulante-de-la-fuga-con-secuencias-y-modulación)
- [Generar MIDI](#generar-midi)
- [Por dónde empezar a estudiar el código](#por-dónde-empezar-a-estudiar-el-código)
- [Variaciones de instrumentos en la fuga](#variaciones-de-instrumentos-en-la-fuga)
  - [Vientos](#vientos)
  - [Cuerdas](#cuerdas)
- [Preguntas sin investigar](#preguntas-sin-investigar)
  - [Plan de trabajo para los pendientes](#plan-de-trabajo-para-los-pendientes)

---

## Generación de Fractales

> los dibujos a partir de fractales se pueden escribir en python?

Sí, y es de los mejores ejemplos para aprender Python gráfico. Hay dos grandes
familias:

**1. Fractales por iteración (Mandelbrot, Julia)**: calculas para cada píxel si
una secuencia compleja diverge. Con NumPy y Matplotlib:

```python
import numpy as np
import matplotlib.pyplot as plt

def mandelbrot(w=800, h=600, max_iter=100):
    x = np.linspace(-2.5, 1, w)
    y = np.linspace(-1, 1, h)
    c = x[np.newaxis, :] + 1j * y[:, np.newaxis]
    z = np.zeros_like(c)
    n = np.zeros(c.shape, dtype=int)
    for i in range(max_iter):
        mask = np.abs(z) <= 2
        z[mask] = z[mask]**2 + c[mask]
        n[mask] = i
    return n

plt.imshow(mandelbrot(), cmap="magma", extent=(-2.5, 1, -1, 1))
plt.axis("off")
plt.show()
```

**2. Fractales geométricos/recursivos (copo de Koch, triángulo de Sierpinski,
árboles)**: se definen con recursión. Con `turtle`:

```python
import turtle

def koch(t, largo, nivel):
    if nivel == 0:
        t.forward(largo)
    else:
        for ang in (60, -120, 60, 0):
            koch(t, largo / 3, nivel - 1)
            t.left(ang)

t = turtle.Turtle()
t.speed(0)
for _ in range(3):
    koch(t, 300, 3)
    t.right(120)
turtle.done()
```

**Otras opciones útiles:**

- **Sistemas L**: reglas de reescritura de cadenas, dibujadas con turtle
(helechos, plantas).
- **IFS (Iterated Function Systems)**: el helecho de Barnsley, con puntos
aleatorios y transformaciones afines.
- **Rendimiento**: para zooms profundos, usa Numba, o CuPy/CUDA si quieres
aprovechar la GPU.
- **Bibliotecas**: Pillow para guardar imágenes, Pygame o Pyglet para
exploración interactiva.

---

## Generación de sonidos tranquilizantes

Sí, y hay una conexión directa con los fractales: el **ruido rosa (1/f)** y el
**ruido marrón** tienen estructura autosimilar, y son la base de muchos sonidos
relajantes (lluvia, oleaje, viento).

Este ejemplo genera olas del mar con NumPy y las guarda en un WAV:

```python
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

sr = 44100
dur = 30
n = sr * dur

# Ruido marrón: integral del ruido blanco
brown = np.cumsum(np.random.randn(n))
brown -= brown.mean()
brown /= np.abs(brown).max()

# Filtro pasa-bajos para suavizar
b, a = butter(2, 800 / (sr / 2))
sound = lfilter(b, a, brown)

# Modulación lenta de volumen = oleaje
t = np.arange(n) / sr
olas = 0.6 + 0.4 * np.sin(2 * np.pi * t / 8)
sound *= olas

wavfile.write("olas.wav", sr, (sound / np.abs(sound).max() * 32767).astype(np.int16))
```

**Otras ideas en la misma línea:**

- **Ruido rosa**: se genera en el dominio de la frecuencia, escalando el
espectro por 1/√f con `np.fft`.
- **Música generativa**: caminatas aleatorias sobre una escala pentatónica,
con notas largas y mucha reverberación.
- **Sonidos binaurales**: dos senos con frecuencias ligeramente distintas
en cada oído.
- **Síntesis de drones**: varios osciladores sinusoidales desafinados apenas
entre sí.

**Bibliotecas útiles:**

- `sounddevice` para reproducir en tiempo real
- `pyo` para síntesis y efectos
- `pedalboard` (de Spotify) para reverb y filtros
- `librosa` para análisis

¿Te interesa más la parte de ruido (fractal), la música generativa o algo
en tiempo real?

---

## Música generativa

> música generativa.
>
> Algo en el estilo de los cuadernos de estudio de cánones y fugas de
J. S. Bach. O, sin demeritar en nada, la música de George Winston, Yanni,
Kitaro, y otros similares.

Sí, y los dos estilos se pueden modelar bien. El canon de Bach es casi un
algoritmo: una melodía que se imita a sí misma con retraso y transposición. Este
código genera una melodía aleatoria en Re menor y la superpone como canon a tres
voces (a la quinta, y una octava abajo), con reverberación:

```python
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve

sr, bpm = 44100, 72
beat = 60 / bpm
escala = [0, 2, 3, 5, 7, 8, 10]  # Re menor natural

def midi(grado, tonica=62):
    octava, i = divmod(grado, 7)
    return tonica + 12 * octava + escala[i]

def melodia(beats=32, seed=None):
    rng = np.random.default_rng(seed)
    g, t, out = 0, 0.0, []
    while t < beats:
        d = rng.choice([0.5, 0.5, 1, 1, 2])
        out.append((g, t, d))
        g += rng.choice([-2, -1, 0, 1, 2], p=[.1, .35, .1, .35, .1])
        g = int(np.clip(g, -3, 9))
        t += d
    return out

def tono(m, dur):
    f = 440 * 2 ** ((m - 69) / 12)
    t = np.arange(int(sr * (dur + 2))) / sr
    s = sum(a * np.sin(2 * np.pi * f * k * t)
            for k, a in enumerate([1, .5, .25, .12, .06], 1))
    return s * np.exp(-t * 2.5) * np.minimum(1, t / 0.005)

# (retraso en tiempos, transposición en grados)
voces = [(0, 0), (4, 4), (8, -7)]
tema = melodia(32, seed=7)

total = int(sr * (beat * (32 + 8) + 4))
mezcla = np.zeros(total)
for retraso, trans in voces:
    for g, t, d in tema:
        s = tono(midi(g + trans), d * beat) * 0.15
        i = int(sr * beat * (t + retraso))
        mezcla[i:i + len(s)] += s[:total - i]

# Reverb: convolución con ruido que decae
ir = np.random.randn(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 3)
mezcla = 0.7 * mezcla + 0.3 * fftconvolve(mezcla, ir)[:total] * 0.02
wavfile.write("canon.wav", sr, (mezcla / np.abs(mezcla).max() * 32767).astype(np.int16))
```

**Para acercarlo más a Bach:**

- Canon por movimiento contrario (`-g` en la segunda voz), o por aumentación (duraciones ×2).
- Fuga: sujeto, respuesta a la quinta, y contrasujeto con reglas de contrapunto
(prohibir quintas y octavas paralelas, preferir consonancias en tiempos
fuertes).
- Si usas `pretty_midi` o `mido`, exportas MIDI y lo reproduces con un
SoundFont de piano real (FluidSynth), que suena mucho mejor que la síntesis
aditiva.

**Para el estilo Winston, Yanni o Kitaro:**

- Progresión lenta de acordes (Am, F, C, G), con arpegios continuos en la mano
izquierda y una melodía simple y espaciada arriba.
- Pedal de sustain: notas con decaimiento largo y reverb amplio.
- Para Kitaro, añade drones con osciladores desafinados y pads suaves con
ataque lento.

¿Quieres que haga primero la versión estilo Winston (arpegios sobre acordes)
o la fuga con reglas de contrapunto?

## Los cinco pasos del diseño

>antes de seguir adelante...
>
>Felicitaciones por todas las piezas de código.
>
>En especial por el canon; Pitágoras haría grandes elogios de tu trabajo: Música
> a través de las matemáticas!!
>
> Me gustaría ver las cinco cosas que sugieres:
>
> `Para acercarlo más a Bach:`
>
> - `Canon por movimiento contrario (`-g` en la segunda voz), o por aumentación
> (duraciones ×2).`
> - `Fuga: sujeto, respuesta a la quinta, y contrasujeto con reglas de
>contrapunto (prohibir quintas y octavas paralelas, preferir consonancias
>en tiempos fuertes).`
>
> `Para el estilo Winston, Yanni o Kitaro:`
>
> - `Progresión lenta de acordes (Am, F, C, G), con arpegios continuos en la
> mano izquierda y una melodía simple y espaciada arriba.`
> - `Pedal de sustain: notas con decaimiento largo y reverb amplio.`
> - `Para Kitaro, añade drones con osciladores desafinados y pads suaves con
> ataque lento.`
>
> `Vamos de una en una...`
>
> 1. `Canon por movimiento contrario (`-g` en la segunda voz), o por aumentación
> (duraciones ×2).`

### 1. Canon por movimiento contrario

¡Gracias! La referencia a Pitágoras viene al caso: el canon es música hecha de
transformaciones (traslación, reflexión, escalado), es decir, geometría
aplicada al tiempo y a la altura.

Estas dos transformaciones son las que Bach combina en la *Ofrenda Musical*,
en el "Canon per augmentationem, contrario motu". El código siguiente reutiliza
la melodía y la síntesis anteriores, pero separa la transformación de cada voz
en una función, para que puedas componerlas libremente.

```python
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve

sr, bpm = 44100, 72
beat = 60 / bpm
escala = [0, 2, 3, 5, 7, 8, 10]  # Re menor natural


def midi(grado, tonica=62):
    octava, i = divmod(grado, 7)
    return tonica + 12 * octava + escala[i]


def melodia(beats=32, seed=None):
    rng = np.random.default_rng(seed)
    g, t, out = 0, 0.0, []
    while t < beats:
        d = rng.choice([0.5, 0.5, 1, 1, 2])
        out.append((g, t, d))
        g += rng.choice([-2, -1, 0, 1, 2], p=[.1, .35, .1, .35, .1])
        g = int(np.clip(g, -3, 9))
        t += d
    return out


def tono(m, dur):
    f = 440 * 2 ** ((m - 69) / 12)
    t = np.arange(int(sr * (dur + 2))) / sr
    s = sum(a * np.sin(2 * np.pi * f * k * t)
            for k, a in enumerate([1, .5, .25, .12, .06], 1))
    return s * np.exp(-t * 2.5) * np.minimum(1, t / 0.005)


# ---------- Transformaciones ----------
def voz(tema, retraso=0, trans=0, eje=None, factor=1):
    """
    retraso: desplazamiento en tiempos (canon a la distancia de ...)
    trans:   transposición en grados de la escala (4 = quinta, -7 = octava abajo)
    eje:     si no es None, movimiento contrario: g -> eje - g
    factor:  aumentación (2 = duraciones x2) o disminución (0.5)
    """
    out = []
    for g, t, d in tema:
        if eje is not None:
            g = eje - g
        out.append((g + trans, t * factor + retraso, d * factor))
    return out


def render(voces, archivo, ganancia=0.15):
    fin = max(t + d for v in voces for _, t, d in v) * beat
    total = int(sr * (fin + 4))
    mezcla = np.zeros(total)
    for v in voces:
        for g, t, d in v:
            s = tono(midi(g), d * beat) * ganancia
            i = int(sr * beat * t)
            mezcla[i:i + len(s)] += s[:total - i]

    # Reverb: convolución con ruido que decae
    ir = np.random.randn(sr * 2) * np.exp(-np.arange(sr * 2) / sr * 3)
    humedo = fftconvolve(mezcla, ir)[:total]
    humedo *= np.abs(mezcla).max() / np.abs(humedo).max()
    mezcla = 0.75 * mezcla + 0.25 * humedo

    wavfile.write(archivo, sr, (mezcla / np.abs(mezcla).max() * 32767).astype(np.int16))


tema = melodia(32, seed=7)

# A) Movimiento contrario: la segunda voz es el espejo de la primera.
#    eje=6 refleja el rango (-3..9) sobre sí mismo.
render([voz(tema),
        voz(tema, retraso=4, eje=6)],
       "canon_contrario.wav")

# B) Aumentación: la segunda voz va a mitad de velocidad,
#    una octava abajo; dura el doble que el tema.
render([voz(tema),
        voz(tema, trans=-7, factor=2)],
       "canon_aumentacion.wav")

# C) Ambas a la vez, como en la Ofrenda Musical:
#    voz grave lenta y en espejo, sobre el tema original.
render([voz(tema),
        voz(tema, trans=-7, eje=6, factor=2)],
       "canon_aumentacion_contrario.wav")
```

**Qué esperar al escucharlo:**

- En **A**, cuando el tema sube, la segunda voz baja, y viceversa. Es una
inversión diatónica: refleja los grados de la escala, no los semitonos, así que
las notas se mantienen dentro de Re menor.
- En **B**, la voz lenta dura 64 tiempos frente a los 32 del tema, así que la
pieza termina cuando acaba la voz aumentada. Las dos voces arrancan juntas
porque en un canon por aumentación el desfase ya lo produce la diferencia
de velocidad.
- En **C**, la voz grave se oye como una versión "estirada y volteada" del tema.

**Una limitación importante:** la melodía es aleatoria, así que no está diseñada
para que las voces armonicen entre sí. Habrá choques disonantes. Eso es lo que
resuelve el siguiente paso, la fuga con reglas de contrapunto, donde el sujeto
se genera con restricciones (o se filtra descartando melodías que produzcan
quintas paralelas o disonancias en tiempos fuertes). También puedes probar otros
valores de `seed` hasta encontrar un tema que suene bien en canon.

¿Seguimos con el punto 2, la fuga?

### 2. Fuga: sujeto, respuesta a la quinta, y contrasujeto con reglas de contrapunto

> Listo para "Fuga: sujeto, respuesta a la quinta, y contrasujeto con reglas de
contrapunto (prohibir quintas y octavas paralelas, preferir consonancias en
tiempos fuertes)."

*Voy a escribir el código y probarlo antes de dártelo, porque con restricciones
de contrapunto es fácil que una regla se rompa sin que se note.*

*Sigo con la fuga: el contrasujeto ya sale, pero la voz libre falla en la
mayoría de los sujetos, así que estoy buscando qué regla la deja sin solución.*

Ya está probado y funciona; voy a entregarte el script y el audio generado.

Te dejo `fuga.py` y, para que escuches el resultado sin ejecutar nada,
`fuga.wav` (23 s, estéreo, timbre de órgano).

#### **Qué hace**

Genera la exposición de una fuga a tres voces en Re menor:

1. **Sujeto** en el alto (8 tiempos).
2. **Respuesta a la quinta** en el soprano, con el **contrasujeto** en el alto.
3. **Sujeto** en el bajo (una octava abajo), el contrasujeto en el soprano y una
**voz libre** en el alto.

El sujeto se genera con reglas: empieza y acaba en la tónica, tiene un salto
inicial ascendente, un único punto culminante y cierra por grado conjunto.

El contrasujeto y la voz libre se generan por **búsqueda con retroceso**
(`contrapunto()`), con estas reglas duras:

- consonancia con todas las demás voces en cada tiempo;
- sin quintas ni octavas paralelas, ni entre corcheas consecutivas ni entre
tiempos consecutivos;
- sin cruzamiento de voces;
- saltos de hasta una quinta, y tras un salto grande, grado conjunto en sentido
contrario;
- la última nota pertenece al acorde de tónica.

El contrasujeto tiene que cumplir las reglas contra la respuesta **y** contra el
sujeto del bajo a la vez. Eso es contrapunto invertible, y es lo que permite
reutilizarlo en dos entradas distintas.

#### **Lo que verifiqué y lo que no**

`verificar()` recorre la pieza completa, voz contra voz, y da
**0 disonancias en tiempo y 0 quintas u octavas paralelas**. Pero no puedo oír
el audio: la corrección contrapuntística está comprobada, la calidad musical no.

#### **Un ajuste que tuve que hacer**

Mi primera versión daba cero soluciones para la voz libre. Exigía que una nota
sostenida fuera consonante con las corcheas que se mueven a su alrededor, y eso
es imposible. Ahora se permite la disonancia en la parte débil del tiempo si la
voz que se mueve entra por grado conjunto (nota de paso, floreo o escapada), que
es lo que hace la práctica barroca.

#### **Limitaciones conocidas**

- La respuesta es una transposición diatónica exacta. Una fuga de Bach usa
respuesta *tonal*, que ajusta el principio del sujeto para no salir de la
tonalidad.
- Uso Re menor natural, sin la sensible (Do♯). Por eso las cadencias suenan
modales, no tonales.
- Es solo la exposición: faltan los episodios, las entradas en otras tonalidades
y el stretto.

Prueba `componer(semilla=...)` con otros valores para obtener sujetos distintos.
El siguiente paso podría ser ese: episodios con secuencias y modulación. O
seguimos con el punto 3, el estilo Winston con arpegios sobre Am–F–C–G, como
prefieras.

### 2.1 Ahondando en la fuga

> antes de pasar al estilo Winston...
>
> - ¿Cómo puedo aumentar la duración de la fuga, como variaciones del tema?
> - ¿Como puedo generar una copia del archivo WAV en formato mp3?
>
> No he olvidado la sugerencia "El siguiente paso podría ser ese: episodios con
> secuencias y modulación."
>
> la pasé para el final despues de Kitaro

*Voy a probarlo antes de responderte: hay que ver que las variaciones cumplan las
mismas reglas y que la conversión a mp3 funcione de verdad.*

*Sigo depurando: la primera sección ya sale; ahora falla la inversión en el bajo, y estoy mirando qué voz no encuentra solución.*

Las dos cosas están resueltas en `fuga_larga.py`, que va junto a `fuga.py`. Te
dejo también `fuga_larga.mp3`, que dura 58 s frente a los 23 s de la exposición
sola.

#### **1. Alargar la fuga con variaciones del tema**

La idea es que cada sección nueva sea una "entrada" del sujeto, con una
transformación, en una voz distinta. Las otras dos voces se componen contra él
con las mismas reglas de contrapunto, usando la función `contrapunto()` de
antes. Se define con una lista:

```python
PLAN = [('normal',      'soprano'),
        ('inversion',   'bajo'),
        ('aumentacion', 'alto'),
        ('normal',      'bajo')]
```

Las transformaciones son las del canon: `inversion` (movimiento contrario,
`eje - g`) y `aumentacion` (duraciones ×2, así que esa sección dura 16 tiempos).
Añadir o reordenar entradas es editar esa lista, y la pieza termina con un
acorde de Re menor. Si quisieras más, también podrías añadir una disminución
(`aumentacion` con factor 0.5) o un stretto.

Detalles que descubrí al probarlo:

- Cada sección se compone por separado, así que puede aparecer una quinta o una
octava paralela en la **unión** entre dos secciones. Al principio me salieron 2.
Ahora `fuga_larga()` repite con otras semillas hasta que `verificar()` da cero
fallos en la pieza completa, y el resultado actual tiene 0 disonancias en tiempo
y 0 paralelas.
- Se compone primero la voz lenta (negras) y luego la de corcheas. Al revés no
hallaba solución, porque la voz lenta no puede adornar con notas de paso.

Sigue siendo todo en Re menor, sin modulación. Para alargar mucho más sin que
suene monótono hacen falta los episodios modulantes, que ya dejaste para después
de Kitaro.

#### **2. WAV a MP3**

Con Python, sin instalar ffmpeg, usa `lameenc`:

```sh
pip install lameenc
```

```python
from fuga_larga import wav_a_mp3
wav_a_mp3("fuga_larga.wav", "fuga_larga.mp3", kbps=192)
```

El script ya lo hace al final. Comprobé que el archivo es un MP3 válido (192
kbps, 44,1 kHz, estéreo). Si ya tienes ffmpeg, también basta una línea en la
terminal:

```sh
ffmpeg -i fuga_larga.wav -b:a 192k fuga_larga.mp3
```

Como antes, la corrección contrapuntística está comprobada, pero no puedo oír el
resultado, así que dime qué tal suena. Cuando quieras, pasamos al estilo
Winston.

### 3. Composición estilo Winston

> Espectacular !!!
> Vamos por Winston

Voy a escribirlo y probarlo, como con la fuga.

Ya terminé las pruebas; ahora te entrego el script y el audio.

Aquí tienes `winston.py` y `winston.mp3` (2 min 8 s, estéreo). El script escribe
también el MP3 al final, con `lameenc` como antes. Como siempre, no puedo oírlo:
lo que revisé es el código, las melodías generadas y el nivel de la mezcla (sin
saturación).

#### **Cómo está hecho**

- **Armonía:** Am – F – C – G, un compás por acorde, a 66 negras por minuto.
- **Mano izquierda:** arpegio continuo de 8 corcheas por compás, subiendo y
bajando sobre fundamental, quinta, octava, tercera y quinta (La2, Mi3, La3, Do4,
Mi4 en el primer acorde).
- **Melodía:** generada compás a compás. En los tiempos fuertes usa notas del
acorde y en los débiles notas de paso. Los saltos son cortos, se evita repetir
la misma nota y se favorece seguir en la misma dirección. Los patrones rítmicos
incluyen notas largas y silencios, para que quede espaciada.
- **Pedal de sustain:** todo suena hasta el cambio de acorde y se apaga con una
relajación corta.
- **Piano:** síntesis aditiva con parciales ligeramente inarmónicos. Las notas
graves duran más, los agudos decaen antes y las notas suaves son menos
brillantes.
- **Detalles de interpretación:** pequeñas variaciones de tiempo y volumen, un
arco dinámico en cada frase, panorama estéreo según la altura (graves a la
izquierda) y reverb cálida de unos 3 s.
- **Forma:** introducción solo con la mano izquierda, luego A, A′ (se repiten
tres compases y cambia el último), B (más densa y más aguda), B′, vuelta de A,
un ciclo final solo con arpegios con ritardando, y un acorde de La menor
arpegiado lentamente.

#### **Una corrección de rumbo**

La primera versión de la melodía repetía mucho las notas (A4 A4, G4 G4 G4) y
daba saltos de séptima. Penalizar la repetición y los saltos lo arregló: en las
pruebas con varias semillas quedan 0–2 repeticiones por frase.

#### **Para ajustar el resultado**

- `BPM` cambia el tempo, y `partitura(semilla=...)` da melodías distintas.
- Si lo quieres más cerca de *Autumn*, prueba a bajar `BPM` a 56–60 y a acentuar
más la primera corchea del arpegio (el `0.08` de velocidad).
- Para más variedad armónica, cambia `PROG` (por ejemplo Am – F – C – E, o
Am – G – F – G) y añade el acorde nuevo a `ACORDES`.

Cuando quieras, vamos con el punto de Kitaro: drones con osciladores desafinados
y pads de ataque lento.

### 5. Composición estilo Kitaro

> Vamos por Kitaro

Voy a escribirlo y probarlo.

Aquí tienes `kitaro.py` y `kitaro.mp3` (3 min 10 s, estéreo). El script tarda
cerca de un minuto en generarlo y escribe el MP3 con `lameenc`, como antes. No
puedo oírlo: lo que comprobé es que el archivo es válido, que no hay saturación
ni valores corruptos, y que la intensidad crece a lo largo de la pieza como se
pretendía.

#### **Cómo está hecho**

- **Drone:** Re2 – La2 – Re3 durante toda la pieza, con entrada de 10 s. Cada
nota son tres osciladores de diente de sierra desafinados (−9, 0 y +8 cents)
repartidos de izquierda a derecha. Un LFO muy lento (periodo de 11 a 25 s) abre
y cierra el brillo, y esa lenta respiración es lo que da la sensación de
movimiento sin cambiar de nota.
- **Pads:** Dm9 – Bbmaj7 – Fmaj7 – Cadd9, 12 s por acorde y 3 vueltas. Tienen
ataque lento de 3,5 s, y como cada pad dura más que su acorde, cada uno se funde
con el siguiente sin cortes.
- **Flauta:** tipo shakuhachi, en Re pentatónica menor (Re, Fa, Sol, La, Do),
con una frase por acorde de 2 o 3 notas largas con silencios. Lleva vibrato que
aparece tras medio segundo y un soplo de ruido filtrado. Usé la pentatónica
porque funciona sobre los cuatro acordes sin choques.
- **Pulso:** pizzicatos suaves sobre las notas de cada acorde, con eco ping-pong
(alterna derecha e izquierda). La flauta tiene su propio eco, más lento.
- **Reverb:** cola de 5 s, más oscura y cálida que la de las otras piezas.

**Forma:** el drone entra solo; la primera vuelta añade los pads; en la segunda
aparecen la flauta (centrada en La4) y el pulso; en la tercera suben el volumen
y la tesitura (centro en Re5); termina con un Dm9 largo, dos notas de flauta y
desvanecimiento.

#### **Para ajustar**

- `CH` cambia la duración de cada acorde, y `CICLOS` la longitud total.
- En el pad, `brillo=(0.3, 0.8)` controla cuánto se abre el timbre. Valores más
bajos dan algo más oscuro y más cercano a Kitaro de *Oasis*.
- La reverb (`rt60`) y la mezcla seco/húmedo (`0.62 / 0.38`) son lo que más
cambia el carácter. Si lo quieres más espacial, sube la parte húmeda.
- Cambiando la semilla en `componer(semilla=...)` salen otras frases de flauta.

Con esto quedan hechas las cinco propuestas. Lo único pendiente es la que tú
mismo aplazaste: episodios con secuencias y modulación para la fuga, cuando
quieras retomarlo.

### 4. Composición estilo Yanni

> Ya estoy de vuelta...
>
> Y mientras descansaba hoy, me di cuenta que sin querer me/nos saltamos a Yanni
> ayer.
>
> Podríamos hacer Yanni antes del  episodio modulante de la fuga, que dejamos pendiente para hoy?

Voy a construir primero la pieza al estilo Yanni y a probarla.

Ya quedó afinado el crescendo hacia el final; ahora copio los archivos y te los
entrego.

Bienvenido de vuelta, JP, y buena observación: Yanni se nos quedó fuera, así que
lo hicimos antes del episodio de la fuga. Te dejo `yanni.py` y `yanni.mp3`
(2 min 21 s, estéreo). El script tarda unos 40 s en generarlo y escribe el MP3
con `lameenc`. Como siempre, no puedo oírlo: comprobé que las melodías cumplen
las reglas, que el archivo es válido, que no hay saturación y que la intensidad
sube hacia el final como se pretendía.

**La forma** (4/4, 84 negras por minuto)

- **Introducción (4 compases):** piano solo, con bajo en octavas y un ostinato
de corcheas sobre Dm – Bb – F – C.
- **A (8):** la melodía la toca el piano, con notas largas y espaciadas, y a
mitad entra el violonchelo.
- **B (8):** el violín solista toma la melodía, con cuerdas y timbales suaves.
- **Puente (8):** una secuencia ascendente (el mismo dibujo melódico sube un
grado sobre cada acorde) por Bb – C – Dm – Gm – Bb – C – Am. Acaba en Si mayor,
que es el dominante de Mi menor.
- **Final (8):** cambio de tonalidad un tono arriba, de Re menor a Mi menor,
como en los finales típicos de Yanni. Entran todos los instrumentos, el violín
repite la melodía de B, el piano la dobla una octava abajo, y hay timbales y un
platillo. Antes de este momento hay un redoble de timbales que crece durante un
compás y un platillo que crece durante 6 tiempos hasta el golpe.
- **Coda (4):** notas largas del violín, ritardando y un acorde final de Mi
menor arpegiado.

#### **Cómo se genera la melodía**

Cada frase de 4 compases es: motivo, respuesta, el motivo repetido sobre el
tercer acorde (una secuencia, como hacía Bach) y una cadencia que termina en una
nota del acorde. Los tiempos fuertes caen siempre sobre notas del acorde y los
débiles pueden ser notas de paso. La segunda mitad de A y de B repite los tres
primeros compases y cambia solo la cadencia. Probé 8 semillas, y en todas hubo
0 fallos en los tiempos fuertes. Elegí la semilla 1 porque tiene un perfil
melódico claro: sin notas repetidas y con un puente que sube limpiamente. La
semilla 7, mi primera opción, tenía el mismo ritmo `[3,1]` en casi todos los
compases y sonaba monótona.

#### **Qué suena a qué**

El piano es el mismo del estilo Winston. Las cuerdas, el violín y el violonchelo
son osciladores en conjunto (3 voces desafinadas ±6 cents), con vibrato que
aparece tras 0,4 s en el violín. Los timbales tienen un barrido de afinación y
un golpe de ruido, y el platillo es ruido filtrado con un crescendo. Hay dos
reverbs: una más corta para el piano y otra de sala grande para la orquesta.

#### **Para ajustar**

- `BPM` cambia el tempo, y `partitura(semilla=...)` da melodías distintas.
- `PROG_A`, `PROG_P` y `PROG_C` son las progresiones. Si quieres otro cambio de
tonalidad, cambia la `trans` de las secciones `final` y `coda` (2 = un tono;
3 = tercera menor).
- Las velocidades de cada sección están en `vel_arp` y en los diccionarios de
`cuerdas` y `timbal`. Ahí se regula cuánto crece el final.

Con esto quedan hechos Winston, Kitaro y Yanni. 

El siguiente paso es el episodio modulante de la fuga, con secuencias y modulación, que dejaste pendiente. Dime si empezamos hoy con él.

### 1. (cont) El episodio modulante de la fuga, con secuencias y modulación

> Ahora si, vamos por 'el episodio modulante de la fuga, con secuencias y
> modulación, que dejaste pendiente.'

*Voy a ampliar `contrapunto()` para aceptar otras tonalidades (el acorde final ya
no será siempre el de Re menor) y a construir los episodios, probándolo todo
antes de darte nada.*

*Ya hay una versión válida, con cadencias Do→Fa y La→Re en el bajo; estoy
puliendo la salida del script y verificando el resultado antes de entregarlo.*

Aquí está el episodio modulante: `fuga_episodios.py` y el
audio `fuga_episodios.mp3` (1 min 14 s). Los otros dos scripts, `fuga.py` y
`fuga_larga.py`, van actualizados y deben estar en la misma carpeta. Como
siempre, no puedo oírlo. Lo que comprobé es el contrapunto de toda la pieza
(0 disonancias en tiempo y 0 quintas u octavas paralelas), la estructura de las
secuencias y las cadencias.

#### **La forma completa**

1. **Exposición** en Re menor (tiempos 0–24), igual que antes.
2. **Episodio I** (24–34), de Re a Fa mayor.
3. **Entradas en Fa mayor** (34–50): el sujeto en el alto y su inversión en el
bajo.
4. **Episodio II** (50–60), de Fa de vuelta a Re.
5. **Entradas finales en Re menor** (60–84): el sujeto en aumentación en el
alto, el sujeto en el bajo y el acorde final de Re menor.

#### **Cómo funciona cada episodio**

- **Soprano:** repite el motivo (los 2 primeros tiempos del sujeto) tres veces,
cada vez un grado más grave. Es una secuencia descendente.
- **Alto:** lleva un contramotivo en corcheas que se genera **una sola vez** y
es válido en las tres repeticiones a la vez. Comprobé que los intervalos son
idénticos en las tres, así que es una secuencia real y no tres frases parecidas.
- **Cadencia:** los últimos 4 tiempos son 2 de dominante y 2 de tónica de
llegada. El bajo hace Do→Fa en el episodio I y La→Re en el II (en este caso,
dominante→tónica de Re menor).

#### **Sobre la modulación**

Fa mayor es la relativa de Re menor y usa exactamente las mismas siete notas,
así que no hay alteraciones que la delaten. La tonalidad se afirma por la
cadencia en el bajo, por las entradas del sujeto sobre Fa y por los acordes de
llegada. Sonará como un cambio de centro tonal, pero más suave que una
modulación con accidentales.

Si quieres una modulación más marcada, por ejemplo a La menor (la dominante),
haría falta introducir alteraciones (Sol♯ y Si natural). Hoy todo se calcula con
los grados de Re menor natural, así que eso exigiría extender el sistema.

#### **Dos cosas que descubrí al probarlo**

- La primera versión del episodio pedía la cadencia en solo 2 tiempos, y no
tenía solución: el bajo no puede estar en el dominante a la vez que el soprano
ya llega a la tónica. Por eso cada episodio dura 10 tiempos y no 8.
- El script reintenta con otras semillas hasta que toda la pieza verifica sin
fallos. Con la semilla actual lo logró en la variante 30, en unos 6 segundos.

#### **Para ajustar**

- `paso` y `k` en `episodio()` cambian la longitud y la dirección de la
secuencia (por ejemplo, ascendente con `paso=-1`).
- `plan` en `fuga_completa()` permite reordenar o añadir entradas (por
ejemplo, otra en la subdominante).
- `base_s` cambia la altura inicial del soprano en cada episodio.

Con esto cerramos todo lo pendiente de ayer y de hoy. ¿Quieres que sigamos con
alguna extensión (stretto, modulación a la dominante) o lo dejamos aquí?

---

## Generar MIDI

> Que tan difícil es grabar el resultado de estos programas en MIDI, además del
> `wav`y `mp3`?

*Es bastante fácil, porque todas las piezas ya son listas de notas (altura,
inicio, duración). Voy a escribir y probar un módulo de exportación para que lo
veas funcionando.*

Es fácil, porque todas las piezas ya son listas de notas (altura, inicio,
duración) y eso es justo lo que contiene un archivo MIDI. Escribí
`midi_export.py` y exporté tres piezas: `fuga_episodios.mid`, `winston.mid` y
`yanni.mid`.

### **Cómo funciona**

La función central es `guardar_midi()`. Recibe una pista por instrumento, con
programa General MIDI (órgano 19, piano 0, cuerdas 48, violín 40, violonchelo
42, timbales 47) y las notas en tiempos musicales. Usa la biblioteca `mido`:

```sh
pip install mido
python midi_export.py
```

Cada pieza necesita un adaptador pequeño:

- **Fuga:** convierte los grados de Re menor a altura MIDI con la misma función
`midi()` y pone una pista por voz (soprano, alto y bajo).
- **Winston:** una pista de piano.
- **Yanni:** cinco pistas (piano, cuerdas, violín, violonchelo y timbales).

### **Los ritardandos**

Winston y Yanni terminan frenando. Eso se exporta como un mapa de tempo, con un
cambio de tempo cada negra durante el ritardando: Winston baja de 66 a 39 BPM, y
Yanni de 84 a 47.

### **Comprobación**

Releí los tres archivos con `mido`. Los conteos de notas coinciden con los
eventos de cada pieza (Winston: 296; fuga: 119 + 101 + 74) y las duraciones
concuerdan con las del audio, sin contar la cola de reverb. Pero no puedo oír el
resultado en un sintetizador.

### **Lo que se pierde al pasar a MIDI**

- **Los timbres:** el sonido lo pone el sintetizador que abra el archivo, no mi
síntesis. Con un buen SoundFont de piano, Winston puede sonar incluso mejor.
- **La humanización** (pequeñas variaciones aleatorias de tiempo y volumen), el panorama estéreo y la reverb.
- **El platillo de Yanni:** es ruido filtrado, no una nota, así que se omite.

### **Qué no exporté**

Kitaro: sus pads y el drone se generan dentro de `componer()` con tiempos en
segundos, y no se recogen en una lista de eventos. Se podría refactorizar, pero
su carácter depende sobre todo de la síntesis (osciladores desafinados y filtros
que respiran), que MIDI no guarda.

### **Para qué sirve**

- Abrir el `.mid` en MuseScore para ver la partitura y revisar las secuencias y cadencias de la fuga.
- Cargarlo en un DAW (Reaper, Ableton, LMMS) y probar otros instrumentos.
- Convertirlo a audio con FluidSynth y un SoundFont:
`fluidsynth -ni fuente.sf2 fuga_episodios.mid -F salida.wav`.

Con MuseScore vas a ver la fuga con claridad, porque cada voz queda en su propia
pista. Que disfrutes estudiando el código.

---

## Por dónde empezar a estudiar el código

> voy a necesitar tu ayuda con el código...
>
>Por dónde sugieres que empiece?

Te sugiero ir de lo simple a lo denso, con una idea: casi todo el código sigue
el mismo patrón (generar eventos → sintetizar → mezclar), así que conviene
entenderlo primero en un archivo pequeño.

1. **`winston.py` (el mejor punto de partida).** Tiene el esqueleto completo:
`partitura()` produce una lista de eventos
`(nota, inicio, duración, velocidad)`, `render()` la convierte en audio y
`wav_a_mp3()` la exporta. Fíjate en `piano()` (síntesis aditiva), en la melodía
como paseo aleatorio ponderado (`elegir_nota`) y en `segundos()`, que
implementa el ritardando.
2. **`kitaro.py`.** Es DSP puro: osciladores desafinados, LFO que abre y cierra
el brillo, eco ping-pong y reverb por convolución. Si te interesa el lado de
señal, aquí está lo más didáctico.
3. **`yanni.py`.** Añade estructura: secciones, transposición (el cambio de
tonalidad es un solo parámetro `trans`) y `secuenciar()`, que repite un dibujo
melódico sobre otro acorde.
4. **`fuga.py`.** Es el corazón intelectual, y conviene leerlo en este orden:
`midi()`, `muestrear_midi()` y `paralelos()` (las piezas básicas);
`sujeto()` (generar y filtrar); y `contrapunto()`, que es el núcleo. Esta última
es un problema de satisfacción de restricciones resuelto por
**búsqueda con retroceso**: `nota_ok()` poda y `dfs()` explora. Con tu
formación en bases de datos, puede ayudarte verlo como una consulta con
predicados de poda, solo que las condiciones son reglas de armonía.
5. **`fuga_larga.py` y `fuga_episodios.py`.** Reutilizan `contrapunto()` de
formas nuevas. Lo más interesante es el parámetro `escenarios`: permite exigir
que una misma voz cumpla las reglas en varias situaciones a la vez, que es lo
que da el contrapunto invertible y las secuencias reales.
6. **`midi_export.py`.** Es corto y sirve de repaso del formato de eventos.

Mientras lees, te recomiendo hacer un experimento por archivo: cambiar una
constante y volver a escuchar. Por ejemplo, `BPM` y `PROG` en Winston, el `rt60`
de la reverb en Kitaro, o `paso` y `k` en `episodio()`.

Para cualquiera de ellos puedo escribirte un recorrido comentado línea por
línea, explicar una función concreta, o preparar pruebas pequeñas que muestren
qué hace cada regla del contrapunto. ¿Por cuál quieres empezar? Mi sugerencia es `winston.py`.

## Variaciones de instrumentos en la fuga

### Vientos

> para la 'fuga_episodios'que 3 instrumentos de vientos debería usar para
> reemplazar las voces de organo?

Te recomiendo **flauta (soprano), clarinete en Si♭ (alto) y fagot (bajo)**. Esa
elección sale de los registros reales de la pieza que generamos:

- **Soprano:** La4 a Re6. Es el registro cómodo y brillante de la flauta.
- **Alto:** Sol3 a Mi5. El clarinete lo cubre entero, del registro grave (chalumeau) al medio (clarín).
- **Bajo:** Sol2 a Re4. Está en la zona central del fagot, que llega hasta el
Si♭1.

Además, los tres timbres son muy distintos entre sí (brillante, hueco y cálido,
y aterciopelado). En una fuga eso ayuda mucho a seguir cada entrada del sujeto,
porque cada voz se distingue por su color además de por su altura.

#### **Alternativas y por qué las descarté**

- **Oboe, corno inglés y fagot.** Es un trío de lengüeta doble, más pastoral y
de aire barroco. Los registros también encajan (el corno inglés baja hasta el Mi3, así que cubre el alto). El inconveniente es que las tres voces suenan más
parecidas y cuesta más distinguirlas.
- **Oboe en el alto.** No sirve, porque su nota más grave es el Si♭3 y esa voz
baja hasta el Sol3.
- **Clarinete en el bajo.** Tampoco, porque su nota más grave suena en Re3 y el
bajo baja hasta el Sol2.

#### **Qué cambiaría en el código**

- **Para el MIDI** es inmediato, porque en `exportar_fuga()` ahora todas las
voces usan el programa 19 (órgano). Bastaría un programa por voz con los números
de General MIDI: flauta 73, clarinete 71, fagot 70 (oboe 68 y corno inglés 69
por si pruebas la alternativa). El archivo guarda alturas reales, así que la
transposición del clarinete en Si♭ la resuelve el programa que abra el MIDI.
- **Para el audio** habría que sustituir `tono()` por tres timbres nuevos. La
flauta ya la tienes casi hecha en `kitaro.py`, con vibrato y soplo. El clarinete
se aproxima con armónicos impares, y el fagot con armónicos ricos pasados por un
filtro paso bajo.

¿Quieres que escriba las dos cosas, el mapeo MIDI y los tres timbres sintetizados, para que puedas comparar la fuga con órgano y con vientos?

### Cuerdas

> Estoy usando MuseScore Studio, como recomendaste, para oir los MIDI... y
> quería ver de cambiar los instrumentos.
>
> Si ahora quisiera cambiar a cuerdas, que opinas de violín, viola, y chelo?

Violín, viola y chelo es una elección excelente para esta fuga, probablemente
mejor que los vientos. Los registros reales de la pieza encajan sin forzar nada:

- **Soprano (La4 a Re6) en violín.** Cae en el registro medio-agudo, que es el
más cómodo del violín.
- **Alto (Sol3 a Mi5) en viola.** Su nota más grave es el Do3, así que la voz
entra entera, con holgura.
- **Bajo (Sol2 a Re4) en chelo.** Llega hasta el Do2, así que queda en la zona
media del instrumento.

Las cuerdas tienen una ventaja adicional: pueden ligar y sostener como lo hace
un órgano, y el contrapunto se oye con mucha claridad. El inconveniente es que
los tres timbres se parecen más que en un trío de vientos. Aun así, cada voz
queda en un registro distinto, y a cambio se gana en fusión.

Voy a hacer que el exportador acepte un conjunto de instrumentos y generar los
MIDI de cuerdas y de vientos, para que los compares directamente en MuseScore.

Ya tienes tres versiones de la fuga, con las mismas notas y distintos
instrumentos: `fuga_cuerdas.mid` (violín, viola, violonchelo),
`fuga_vientos.mid` (flauta, clarinete, fagot) y `fuga_organo.mid` (el original).
Releí los tres archivos: cada pista tiene su instrumento
(programas General MIDI 40-41-42, 73-71-70 y 19) y el mismo número de notas que
antes. `fuga_episodios.mid` se sustituyó por `fuga_organo.mid`.

#### **Cambiar instrumentos en MuseScore Studio**

Hay dos caminos:

1. **Desde el código (el más fiable).** Como MuseScore asigna el instrumento según el programa MIDI, basta con exportar con otro conjunto. Para uno propio:

   ```python
   exportar_fuga(voces, "mi_fuga.mid",
                 conjunto=[('Oboe', 68), ('Corno inglés', 69), ('Fagot', 70)])
   ```

   Al abrirlo, MuseScore pondrá cada pista con su instrumento y su clave
   (la viola, por ejemplo, en clave de do).
2. **Desde MuseScore.** En el panel de instrumentos (tecla `I`) debería haber
una opción para sustituir un instrumento por otro dentro de la partitura. No
conozco con certeza el nombre exacto del botón en tu versión, así que si no lo
encuentras, usa el primer camino.

#### **Para comparar**

Abre las tres versiones y escucha sobre todo los episodios (compases hacia los
tiempos 24-34 y 50-60). Allí la secuencia del soprano y el contramotivo del alto
se oyen mejor con timbres que ligan, así que mi apuesta es que las cuerdas
brillan ahí. Con los vientos, en cambio, las entradas del sujeto se distinguen
más fácilmente.

Una observación para tu estudio: el MIDI lleva todas las notas con la misma
velocidad (0,7), y las cuerdas de MuseScore sonarán algo planas por eso. Si
quieres, puedo hacer que las frases tengan un perfil dinámico (crescendo hacia
los puntos culminantes del sujeto y en las secuencias), lo que marcaría mucho la
diferencia en un trío de cuerdas.

---

## Preguntas sin investigar

- **Generación de sonidos tranquilizantes**:
  - **Ruido rosa**: se genera en el dominio de la frecuencia, escalando el
espectro por 1/√f con `np.fft`.
  - **Música generativa**: caminatas aleatorias sobre una escala pentatónica,
con notas largas y mucha reverberación.
    - **Hecho**: `kitaro.py` PENTA define la escala, melodia() hace la caminata
    (pasos de ±1 o ±2 grados, notas de 2, 3 o 4 s con silencios de 0,3 a 1,5 s)
    y reverb() usa rt60=5.
  - **Sonidos binaurales**: dos senos con frecuencias ligeramente distintas
en cada oído.
  - **Síntesis de drones**: varios osciladores sinusoidales desafinados apenas
    - **Hecho, con un matiz**: `kitaro.py` el drone es pad([38, 45, 50], ...), es decir Re2, La2 y Re3, con tres voces a −9, 0 y +8 cents por nota.
entre sí.
  - ¿Te interesa más la parte de ruido (fractal), la música generativa o algo en tiempo real?
    - ruido (fractal)
    - algo en tiempo real

- **Generación de MIDI, Cuerdas**: ¿Quieres que escriba las dos cosas, el mapeo
MIDI y los tres timbres sintetizados, para que puedas comparar la fuga con
órgano y con vientos?
- **1. (cont) El episodio modulante de la fuga, con secuencias y modulación**: ¿Quieres que sigamos con alguna extensión (stretto, modulación a la
dominante) o lo dejamos aquí?
  - stretto
  - modulación a la dominante

### Revisando los pendientes

> Hay algunas preguntas tuyas que quedaron abiertas o sin investigar, las estoy
> resaltando en el 'journal'

Buena idea dejar la conversación completa como diario: el README explica qué
hay, y el journal explica por qué está así. Para que puedas cruzarlo con lo que
tú has resaltado, estas son las cosas abiertas o sin comprobar que recuerdo yo.

#### **Código que escribí y nunca ejecuté**

- Los fragmentos del principio de la conversación: Mandelbrot, copo de Koch,
olas con ruido marrón y el primer canon.
- El canon por movimiento contrario y por aumentación (variantes A, B y C). Lo
que dije de cómo sonaría, por ejemplo que en B la pieza dura 64 tiempos, lo
deduje del código, no lo medí.

#### **Afirmaciones que no pude comprobar**

- Todo lo que dije sobre cómo suena algo: que las cuerdas brillarán en los
episodios, que la modulación a Fa sonará como un cambio de centro tonal
"más suave", y que con vientos las entradas se distinguen mejor. Son
predicciones, porque no puedo oír el audio.
- Los registros que di para elegir instrumentos
(La4–Re6, Sol3–Mi5, Sol2–Re4) son de la fuga con `semilla=1`. Con otras
semillas pueden variar, y no lo comprobé.
- En MuseScore te dije que debería haber una opción para sustituir
instrumentos en el panel `I`, pero admití que no sabía el nombre exacto del
botón.
- El comando de FluidSynth que te di
(`fluidsynth -ni fuente.sf2 fuga.mid -F salida.wav`) tampoco lo probé.

#### **Ofertas que dejé sin cumplir**

- Perfil dinámico en el MIDI (velocidades según las frases), que haría sonar
mucho mejor el trío de cuerdas.
- Sintetizar flauta, clarinete y fagot en el audio, para comparar con el órgano.
- Exportar Kitaro a MIDI, que exigiría refactorizarlo.
- Stretto, respuesta tonal y modulación a la dominante (esta última necesita
alteraciones, algo que hoy el sistema no soporta).
- Extraer el código repetido a un módulo común y escribir pruebas formales.

Antes de hacer público el journal, revisa que no contenga nada que no quieras
publicar.

Si me pegas aquí lo que resaltaste, lo cruzo con esta lista y vemos qué falta.
Lo más barato de cerrar es lo primero: puedo ejecutar y verificar ahora los
fragmentos iniciales (el canon y las demás variantes, el Mandelbrot y las olas)
y decirte con certeza cuáles funcionan. ¿Empiezo por ahí?

Gracias, JP. Cruzado con mi lista, quedan cinco pendientes. Uno no estaba en mi
lista: **el ruido fractal y el tiempo real**, que vienen del paso de los
sonidos tranquilizantes. Cuando elegiste la música generativa, esas dos opciones
quedaron sin hacer y las perdí de vista.

| Pendiente | Qué implicaría | Qué puedo y qué no puedo comprobar |
| --- | --- | --- |
| **Ruido fractal** | Generar ruido rosa (1/f) y marrón (1/f²) en el dominio de la frecuencia, con el exponente espectral variando lentamente y un perfil de olas. Conecta con el origen fractal del proyecto: para un movimiento browniano fraccionario, el espectro es 1/f^(2H+1) y la dimensión de su gráfica es 2 − H. | Puedo medir la pendiente del espectro generado y comprobar que coincide con la teórica. |
| **Tiempo real** | Reproducir con `sounddevice` mediante un callback, empezando por ruido y luego por una pieza sencilla. La síntesis aditiva actual es demasiado pesada para hacerla al vuelo, así que habría que precalcular las notas. | **No puedo probar la reproducción**: mi entorno no tiene tarjeta de sonido. Solo podría verificar los bloques de audio que genera el callback, y la prueba real sería en tu equipo. |
| **Timbres sintetizados para la fuga** | Flauta, clarinete y fagot (y, ya que `yanni.py` tiene `cuerda()`, también cuerdas), para comparar con el órgano, con perfil dinámico por frase. | Solo puedo comprobar propiedades del espectro y de las envolventes. Si suena bien, lo juzgas tú. |
| **Stretto** | Entradas del sujeto solapadas. Hay que investigar qué retardos admite este sujeto: la búsqueda probaría varios y reportaría cuáles cumplen las reglas, quizá con una selección de sujetos que lo permitan. | `verificar()` comprueba las reglas con total fiabilidad. |
| **Modulación a la dominante** | Pasar a La menor, que exige alteraciones (Sol♯ y Si natural, mientras que Re menor natural tiene Si♭). Es la tarea más grande: hay que sustituir la escala fija de `midi(g)` por una escala por sección y ajustar `contrapunto()`. | Las reglas se pueden verificar, pero requiere el refactor y puede introducir fallos en lo que ya funciona. |

Sigue además en pie lo que te propuse al final del mensaje anterior: ejecutar
los fragmentos iniciales (canon, Mandelbrot, Koch y olas) para confirmar cuáles
funcionan. Es lo más corto y lo único donde yo afirmé algo que no había
ejecutado.

### Plan de trabajo para los pendientes

Mi orden sugerido sería:

1. Verificar los fragmentos iniciales (poco trabajo, y limpia lo que afirmé sin
probar).
2. Timbres sintetizados para la fuga.
3. Ruido fractal.
4. Stretto.
5. Tiempo real.
6. Modulación a la dominante, por ser la tarea mayor.

¿Empezamos por el primero, o prefieres otro orden?

> Donde quedaron:

```text
- **Música generativa**: caminatas aleatorias sobre una escala pentatónica,
con notas largas y mucha reverberación.
- **Sonidos binaurales**: dos senos con frecuencias ligeramente distintas
en cada oído.
- **Síntesis de drones**: varios osciladores sinusoidales desafinados apenas
entre sí.

```

Los tres quedaron así:

| Tu cita | Estado | Dónde |
| --- | --- | --- |
| **Música generativa** (caminata sobre la pentatónica, notas largas, mucha reverb) | Hecho | `kitaro.py`: `PENTA` define la escala, `melodia()` hace la caminata (pasos de ±1 o ±2 grados, notas de 2, 3 o 4 s con silencios de 0,3 a 1,5 s) y `reverb()` usa `rt60=5`. |
| **Síntesis de drones** (osciladores desafinados apenas entre sí) | Hecho, con un matiz | `kitaro.py`: el drone es `pad([38, 45, 50], ...)`, es decir Re2, La2 y Re3, con tres voces a −9, 0 y +8 cents por nota. |
| **Sonidos binaurales** (un seno distinto en cada oído) | **No se hizo** | No está en ningún archivo. |

**El matiz del drone.** La idea original hablaba de osciladores *sinusoidales*.
Lo que escribí usa ondas tipo diente de sierra construidas con hasta
8 armónicos, filtradas hacia lo grave con un brillo bajo (0,1 a 0,4). Cumple
la parte de "desafinados apenas", pero no es literalmente un drone de senos
puros.

**Por qué el drone de Kitaro no es binaural.** Se parece, pero es otra cosa.
Las tres voces desafinadas se reparten en el estéreo con panoramas distintos,
pero cada voz llega a **los dos oídos** en distinta proporción. Las voces se
mezclan en el aire y producen *batidos acústicos*: en el Re2, con 73 Hz, los 17
cents entre la voz más grave y la más aguda son unos 0,7 Hz. Un batido binaural
exige que cada oído reciba **solo** su tono por separado, con auriculares, y que
el cerebro construya el batido.

Binaural fue un hueco en mi lista: era una de las viñetas y no la incluí entre
los pendientes. Con ello son seis, y hay una buena razón para hacerlo junto con
el ruido fractal: ambos son audio para escuchar con auriculares y comparten
estructura. Serían dos senos (por ejemplo, 220 Hz en el izquierdo y 226 Hz en el
derecho para un batido de 6 Hz) sobre un colchón de ruido rosa. Puedo verificar
con una FFT que cada canal contiene la frecuencia que debe. La evidencia de que
los batidos binaurales relajen o ayuden a concentrarse es mixta, así que lo
presentaría como un experimento sonoro y no como una técnica de relajación.

¿Lo añado a la lista y lo hago en el mismo paso que el ruido fractal?

> Añádelo a la lista!
>
> Pero hagamos la generación de sonidos algo más amplio.
>
>Lo primero que mostraste es 'generación de olas' y eso me puso a pensar en
>otros sonidos naturales:
>
> - agua de río
> - agua de arroyo
> - viento en el bosque
> - lluvia suave
> - lluvia intensa que se va acercando y luego pasa por encima hasta irse
> - (yo se que no es de la naturaleza) ... perdón por el anglicismo...
> 'wind-chimes' de metal y madera
> - otros que se te ocurran

Ya pasan 9 de 10 pruebas; la que falla (la lluvia) probablemente mide mal por los fundidos de entrada y salida, y lo estoy comprobando.

Los trece sonidos están hechos y probados. Los archivos son `sonidos_naturales.py`, `verificar_sonidos.py` y una muestra en MP3 de cada sonido (45 s; 100 s la tormenta; 75 s el bosque nocturno). No puedo oírlos, así que lo que sigue son mediciones y no juicios de sonido.

| Sonido | Cómo está hecho | Lo que medí |
|---|---|---|
| **Olas** | Rumor grave que crece 5 s, cresta y decae; la espuma llega con la cresta y se apaga antes | 12 olas en 120 s, separación mediana de 10 s (generada: 6,5–11 s) |
| **Río, arroyo, cascada** | Turbulencia más burbujas con el modelo de Minnaert: el radio fija el tono y las grandes suenan graves | Brillo medio de 2349, 3336 y 4775 Hz; el arroyo es más brillante que el río |
| **Viento en el bosque** | Ráfagas lentas: cuanto más fuertes, más agudos, con hojas y un silbido entre ramas | Correlación 0,45 entre nivel y brillo; rango de 26,6 dB |
| **Lluvia suave** | Miles de microimpactos por segundo, gotas medianas, goteo de hojas y charcos | Nivel estable, con variación de 0,23 dB |
| **Tormenta que pasa** | La cercanía sigue una curva con máximo al 48 %. De lejos solo se oyen los graves, y al pasar el sonido se abre a todo el estéreo, con truenos que suenan más fuerte cuanto más cerca está | Máximo en el segundo 48, sube 35 dB, el timbre se aclara en el pico, y la tormenta cruza de izquierda a derecha (relación L/R de 8,3 al inicio y 0,16 al final) |
| **Campanas de metal** | Síntesis modal: parciales de una barra libre (1; 2,756; 5,404; 8,933) y tuberías de re mayor pentatónica | Los parciales caen donde deben y caen 30 dB en 2,4 s |
| **Campanas de madera** | Parciales que se extinguen rápido más un golpe seco | Caen 30 dB en 0,86 s, frente a los 2,4 s del metal |
| **Fuego** | Rugido grave, siseo y chasquidos en racimos con estallidos | Curtosis 58, es decir, muy impulsivo |
| **Goteo en cueva** | Burbujas con reverb de 6,5 s | Sin NaN, nivel audible |
| **Grillos** | Ocho individuos con pulsos de 12 ms | Portadora a 4501 Hz y pulsos a 36,6 Hz (generado: 35,7 Hz) |
| **Bosque nocturno** | Mezcla de arroyo, viento suave y grillos | Sin NaN, nivel audible |

`verificar_sonidos.py` hace estas comprobaciones (10 de 10 superadas) y comprueba además que el ruido de color tiene la pendiente espectral teórica (−1,00 y −2,00).

**Lo que probablemente tendrás que ajustar al oído**
- **La lluvia suave** tiene el brillo medio en 6,3 kHz, que es bastante alto: puede sonar áspera. Se puede suavizar bajando los 9000 Hz de `banda(...)` en `lluvia_suave`.
- **El viento** varía 26 dB entre calma y racha, que puede ser mucho para fondo. Se regula con `fuerza` y con el `sesgo` de `rafaga`.
- **Los timbres de campana, fuego y burbujas** son modelos físicos simplificados; no puedo asegurar que suenen reales.

**Una corrección mía:** la prueba de la lluvia falló al principio porque medía también los fundidos de entrada y salida, y yo lo interpreté como lluvia poco estable. Retoqué la lluvia sin necesidad (menos cola pesada en las gotas); el cambio es menor, pero queda en el código.

Se usa así: `python sonidos_naturales.py rio tormenta --dur 120 --semilla 3`. La tormenta tiene `t_pico`, `wa` y `wd` para cambiar cuándo pasa y cuánto tarda en acercarse y alejarse. Para apreciar el movimiento de la tormenta usa auriculares. Los 13 MP3 pesan 13 MB en total, por si no quieres subirlos todos al repositorio.

**Lo que no hice:** pájaros, ranas, cuencos tibetanos y mar profundo, que serían los siguientes candidatos. Quedan además pendientes ruido fractal, binaural, tiempo real, timbres de vientos y cuerdas para la fuga, stretto y modulación a la dominante. No toqué tu README, porque tienes tu propia copia editada.

¿Quieres que ajustemos alguno de estos sonidos según cómo te suene, o seguimos con otro pendiente de la lista?

> 1) hagamos, para terminar el capítulo de generación de sonidos (más adelante volveré con comentarios de algunos de los sonidos para ajustar, pero por ahora no vale la pena):
>
> - cuencos tibetanos
> - mar profundo
> - ruido fractal
> - binaural
>
> 2) Que de sonidos se puede generar en tiempo real
>
> 3) stretto y modulación a la dominante
>
> Y con eso terminaríamos por ahora

Terminé los cuatro sonidos (más uno extra) y medí la velocidad de todos para responder lo del tiempo real. No puedo oír los resultados, así que todo lo que sigue son mediciones.

## 1) Sonidos nuevos (`sonidos_meditativos.py`)

| Sonido | Cómo está hecho | Lo que medí |
|---|---|---|
| **Cuencos tibetanos** | Golpeados (se apagan solos) y frotados (cantan). Cada modo se desdobla en dos frecuencias muy próximas, y de ahí sale el latido lento | Modos a 1; 2,71; 5,15 veces la fundamental (0, −18 y −30 dB); pulsación de 0,98 Hz; decaen 60 dB en unos 29 s; el frotado alcanza el 90 % de su nivel a los 8 s |
| **Mar profundo** | Presión grave, oleaje lejano amortiguado de ~10 s, burbujas grandes y llamadas de ballena opcionales, con reverb de 7 s | 99,8 % de la energía por debajo de 800 Hz (medido sin ballenas); variación de nivel por el oleaje de 4,3 dB; una llamada de ballena tiene el centroide en 257 Hz |
| **Ruido fractal** | La pendiente espectral β pasa de 0,2 a 2,2 y vuelve (de blanco a marrón y de regreso) en 90 s | β medida frente a la esperada: error máximo de 0,09. Para β = 2,2: H = 0,60 y D = 1,40 |
| **Binaural** | Portadora de 200 Hz, ±beat/2 en cada oído, con el batido bajando de 10 Hz (alfa) a 4 Hz (theta), sobre un lecho de ruido rosa | La diferencia entre oídos sigue el plan (8,50, 7,00 y 5,51 Hz en tres puntos); el tono del otro oído se cuela a −37 dB |
| **Isocrónico** (extra) | Tono pulsado al ritmo del batido; funciona en altavoces | Pulsos a 9,2 Hz (esperado 9,3) |

Las pruebas de `verificar_sonidos.py` pasan 15 de 15.

Algunas salvedades:
- **Cuencos:** las proporciones de los modos son valores típicos de la literatura que usé de memoria. No las medí en un cuenco real.
- **Ballenas:** son sintéticas y podrían sonar artificiales. Se desactivan con `ballenas=False`.
- **Mar profundo y binaural:** necesitan auriculares. Los altavoces de portátil no reproducen por debajo de ~100 Hz, y el binaural solo funciona con un tono distinto en cada oído. Úsalo a volumen bajo; la evidencia de que ayude a relajarse o concentrarse es mixta, así que lo tomaría como un experimento sonoro.

## 2) ¿Qué se puede generar en tiempo real?

Casi todo. Medí cuánto tarda cada generador en producir 30 s de audio:

| Sonidos | Velocidad frente al tiempo real |
|---|---|
| Fractal, isocrónico, binaural, lluvia suave, campanas de madera, fuego, grillos, goteo | 69 a 126 veces más rápido |
| Olas, mar profundo, viento, tormenta, cuencos | 23 a 33 veces |
| Río, arroyo, cascada, campanas de metal, bosque nocturno | 10 a 17 veces |
| Winston (128 s de audio en 6,5 s) | 20 veces |
| Yanni y Kitaro (medidos antes) | unas 3 veces |
| Fuga completa (70 s de audio, incluidos los reintentos) | unas 11 veces |

Estas cifras no son una prueba de tiempo real, porque hoy cada sonido se calcula entero de una vez. Para emitir en directo habría que reescribirlos por bloques con estado entre bloques (filtros, fase de los osciladores). Lo que cuenta entonces es el peor caso por bloque: con 1024 muestras hay 23 ms para cada uno.

- **Se reescriben sin gran dificultad:** binaural, isocrónico, lluvia, fuego, grillos, goteo, viento, olas, campanas, cuencos y agua. Casi todo son filtros con estado, osciladores y gotas al azar. Hay que cambiar el ruido `1/f` (hoy sale de una FFT sobre toda la señal) por filtros recursivos o por bloques solapados, y la reverb por convolución (3–7 s) por una algorítmica o por convolución por particiones.
- **Se puede, pero no tal como están:** Winston, Yanni y Kitaro. Habría que precalcular las notas y secuenciarlas al vuelo. La fuga se generaría por secciones, calculando la siguiente mientras suena la actual.
- **Lo que gana el tiempo real:** controlar parámetros en vivo (intensidad de la lluvia, fuerza del viento, posición de la tormenta, batido del binaural) o disparar cuencos y campanas desde un teclado.

La reproducción en vivo la haría con `sounddevice`. No puedo probarla aquí, porque mi entorno no tiene tarjeta de sonido: solo podría medir el tiempo por bloque con un callback simulado, y la prueba real sería en tu equipo. Si te interesa, puedo escribir un prototipo con cuatro o cinco sonidos y controles en vivo.

## 3) Stretto y modulación a la dominante

Sigue la fuga, y son dos tareas de tamaño distinto. Mi propuesta es empezar por el **stretto**, que es más acotado: probaría varios retardos para las entradas solapadas y reportaría cuáles cumplen las reglas con este sujeto. La **modulación a la dominante** requiere un refactor mayor, porque hay que pasar de una escala fija a una por sección (con Sol♯ y Si natural).

Cuando cerremos el punto 3, puedo escribirte las secciones de README y de guía de estudio de los módulos de sonido y de la fuga ampliada. ¿Sigo con el stretto?

> Si, sigue con el stretto

Empiezo explorando qué retardos admite este sujeto, antes de construir nada.

Sigo con el stretto: ya sé qué sujetos lo admiten y cómo encadenar las entradas; ahora escribo el módulo que lo integra en la fuga.

Todo verificado, incluso con una revisión más estricta que la habitual; incorporo esa revisión al módulo y entrego los archivos.

El stretto está hecho: `fuga_stretto.py`, `fuga_stretto.mp3` (unos 85 s) y tres versiones MIDI (`fuga_stretto_organo.mid`, `fuga_stretto_cuerdas.mid` y `fuga_stretto_vientos.mid`). Como siempre, no puedo oír el resultado.

**Qué admite el sujeto**

Un stretto no se puede aplicar a cualquier sujeto, así que el programa comprueba cada caso con las reglas del contrapunto.

- **El sujeto que usábamos** (semilla 2) solo admite entradas a 4 tiempos, y solo a la octava. Eso es casi un canon, con el solapamiento justo de la mitad del sujeto.
- **En 300 sujetos candidatos**, solo 19 admiten un retardo de 3 tiempos o menos, y solo 7 de ellos permiten además componer la exposición.
- **Mi elección** fue el sujeto de la semilla 5, `[0, 3, 5, 3, 0, −1, −2, −1, −2, 1, 0]`, con retardo de 3 tiempos. Entran el alto, luego el soprano una octava arriba, y luego el bajo una octava abajo, cada uno 3 tiempos después del anterior, así que se solapan 5 de los 8 tiempos del sujeto. Ocupa los tiempos 84 a 98, tras todas las secciones anteriores.
- El **sujeto de la semilla 71** es el más flexible que encontré: admite retardos de 1, 2, 2,5, 3, 4... tiempos. Se puede usar con `python fuga_stretto.py --dmin 0.5 --dmax 1`. Ese stretto de 1 tiempo mezcla respuesta y sujeto (alto con la respuesta, luego bajo y soprano con el sujeto). No lo elegí como principal porque un retardo tan corto suena casi como movimiento paralelo.

**Una limitación importante:** todos los encadenamientos válidos que encontré, salvo el de la semilla 71 con 1 tiempo, usan sujeto con sujeto (o respuesta con respuesta), siempre a la octava. Lo habitual en Bach es alternar el sujeto en la tónica con la respuesta en la dominante, y con las reglas estrictas que uso no apareció ninguno así. Habría que ver si se debe a las reglas o a que la transposición por grados cambia la calidad de los intervalos.

**Verificación:** `verificar()` da 0 disonancias en tiempo y 0 paralelas en toda la obra. Además añadí `diagnostico_estricto()`, que también cuenta cruzamientos entre voces y disonancias débiles sin grado conjunto, y da 0 en las 472 posiciones comparadas entre las tres voces.

**Cambios en lo anterior:** `fuga_episodios.py` ahora acepta secciones propias (`'custom'`) y un `plan_extra`. Los demás archivos no cambiaron. El README tendrá que reflejar `fuga_stretto.py` y este cambio.

Solo queda la **modulación a la dominante**. Es la tarea más grande: hay que pasar de una escala fija a una escala por sección (con Sol♯ y Si natural), y eso toca `midi()`, `contrapunto()` y varias comprobaciones. Mi propuesta es hacerlo en archivos nuevos, copiando los existentes, para no poner en riesgo lo que ya funciona. ¿Empiezo así?

---

> empieza modulación a la dominante, como lo sugieres: "propuesta es hacerlo en archivos nuevos, copiando los existentes, para no poner en riesgo lo que ya funciona"

Empiezo por la modulación a la dominante, en archivos nuevos y sin tocar los que ya funcionan. Antes de escribir nada reviso el código que voy a adaptar.

Los criterios tonales ya se cumplen en todas las secciones; falta comprobar los archivos generados y entregártelos.
La modulación a la dominante está hecha, en archivos nuevos y sin tocar los que ya funcionaban. Te dejo `fuga_tonal.py`, `fuga_tonal.mp3` (unos 75 s) y tres versiones MIDI (`fuga_tonal_organo.mid`, `fuga_tonal_cuerdas.mid` y `fuga_tonal_vientos.mid`). No puedo oírlo; lo que sigue son mediciones.

**La forma (en tiempos)**

- **0–24:** exposición en Re menor, la de siempre.
- **24–34:** episodio I, de Re a La. La secuencia desciende un grado por repetición, y la última repetición ya está en La menor. Termina con una cadencia Mi mayor → La menor, con Sol♯ como sensible.
- **34–50:** entradas en La menor, con el sujeto en el alto y su inversión en el bajo.
- **50–60:** episodio II, de La a Re, con cadencia La mayor → Re menor, con Do♯ como sensible.
- **60–84:** entradas en Re menor, con el sujeto en aumentación y el sujeto en el bajo.
- **84–90:** cadencia final La mayor → Re menor. Las cadencias de esta versión son auténticas, con sensible, y no modales (VII–i) como en las anteriores.

**Qué cambió por dentro**

- **Notas como alturas MIDI:** antes eran grados de Re menor natural, que no admiten Sol♯ ni Do♯. Ahora cada sección tiene su `Escala` (Re menor, La menor y sus versiones con sensible). `contrapunto_tonal()` acepta una escala distinta en cada escenario, y por eso una secuencia puede cruzar de una tonalidad a otra.
- **Transposición real:** el sujeto en La menor es el de Re menor subido 7 semitonos. Conserva todos los intervalos y solo sustituye Si♭ por Si natural. El paso a Fa mayor de `fuga_episodios.py` transponía por grados (mismas notas, otros intervalos).
- **Regla nueva:** sin segundas aumentadas en las melodías (Fa → Sol♯).

**Lo que medí**

`verificar_midi()` da 0 disonancias en tiempo y 0 paralelas en toda la obra, y la revisión estricta (cruzamientos, disonancias débiles sin grado conjunto, paralelas) da 0 en 460 posiciones. Además estimé la tonalidad de cada tramo con el algoritmo de Krumhansl-Schmuckler, que compara cuánto suena cada nota con el perfil de cada tonalidad (r es la correlación):

| Tramo | Tonalidad estimada | Alteraciones |
|---|---|---|
| Exposición | Re menor (0,83) | Si♭ |
| Episodio I, secuencia | Do mayor (0,70) | transición |
| Episodio I, cadencia | **La menor (0,80)** | Sol♯ |
| Entradas en La menor | **La menor (0,85 y 0,82)** | Si natural y ningún Si♭ |
| Episodio II, cadencia | Re menor (0,81) | Do♯ |
| Entradas en Re menor | Re menor (0,69 y 0,81) | Si♭ y ningún Si natural |
| Cadencia final | Re menor (0,88) | Do♯ |

Para comparar, el paso a Fa mayor de la versión anterior se detecta como Fa mayor con r = 0,91, así que ambas modulaciones se distinguen bien.

**Cautelas**

- **Parte del resultado es por construcción.** Hice que la tonalidad estimada de cada sección fuera un criterio de aceptación, así que el programa descartó variantes hasta encontrar una (la 8, entre 200 posibles) que lo cumple. Las cifras no prueban cómo suena, solo que las notas encajan.
- **La aumentación en Re menor es el tramo más débil:** Re menor 0,69 frente a Sol mayor 0,68.
- **Las secuencias** salen ambiguas (Do mayor, Sol mayor), como corresponde a un pasaje que está modulando.
- **Primer intento fallido:** el acorde final de las cadencias llevaba solo fundamental y quinta, sin tercera. El detector lo leyó como Re mayor (0,79) y ahora se exige la tercera.
- **La inversión en La menor es diatónica** (por grados de la escala), no cromática.
- **Sujeto y escalas:** se usa el sujeto de la semilla 2, y las entradas en La menor emplean la menor natural; Sol♯ solo aparece en las cadencias.
- **No integré el stretto** en esta versión, ni la sección en Fa mayor. Son combinables, porque el stretto se escribe sobre notas MIDI.

Con esto cerramos lo que tenías pendiente en la fuga. Lo que queda es poner al día el README y la guía de estudio con los módulos nuevos (`fuga_stretto.py`, `fuga_tonal.py`, `sonidos_naturales.py`, `sonidos_meditativos.py` y `verificar_sonidos.py`), los cambios en `fuga_episodios.py` y las limitaciones que antes figuraban como pendientes. ¿Lo escribo ahora, como sección nueva que puedas pegar en tu copia del README?

---

> Si, escribe ahora las seeciones nuevas del README

Antes de escribirlas, reviso los archivos nuevos para que cada nombre, cifra y tiempo que cite sea exacto.

Reviso tres afirmaciones del texto contra el código antes de darlo por bueno: el número de MP3, un experimento que cité y los retardos del sujeto 71.

Te dejo `README_secciones_nuevas.md`, con lo que hay que **añadir o sustituir** en tu copia del README. Como no tengo tu versión editada, cada bloque indica a qué sección corresponde.

**Contenido**

- **A. Autoría y verificación:** fechas actualizadas (24 al 29 de octubre) y la tabla de verificación ampliada. Incluye lo **no** verificado: los fragmentos iniciales del chat (que nunca se ejecutaron), el comando de FluidSynth, el botón de MuseScore y el tiempo real.
- **B. Contenido, dependencias y ejecución:** tabla de archivos con las líneas actuales, diagrama de dependencias y comandos con los tiempos que medí (de 5 a 58 s).
- **C. Qué hace cada pieza:** cuatro viñetas nuevas.
- **D. Guía de estudio:** secciones 8 a 12 (`sonidos_naturales.py`, `sonidos_meditativos.py`, `verificar_sonidos.py`, `fuga_stretto.py` y `fuga_tonal.py`), cada una con conceptos, orden de lectura, experimentos y preguntas. También el orden de lectura ampliado, los cambios en archivos que ya existían y los formatos de datos nuevos.
- **E. Parámetros, lecciones, limitaciones y glosario:** filas nuevas, las lecciones de la 8 a la 14, qué limitaciones quitar y cuáles añadir, y términos nuevos.
- **F. Estado de lo pendiente:** tabla de hecho y pendiente.

**Dos puntos del contenido**

- **Seed 71:** antes de entregarlo corregí el texto del sujeto de la semilla 71. Admite muchos retardos **entre dos entradas** (1; 2; 2,5; 3; 4...), pero al encadenar **tres** solo admite 1 tiempo. En mi mensaje del stretto lo describí de forma que podía leerse como que los admite todos en cadena, y eso no es así.
- **Parte "por construcción":** en `fuga_tonal.py` dejé explícito que la tonalidad esperada es un criterio de selección, para que quien lea el repositorio no interprete esas cifras como una prueba de cómo suena.

Corregí también tres errores del primer borrador: el número de MP3 de sonidos (son 18, no 15), un experimento que citaba una constante que no existe en `ruido_color`, y la redacción de otro. Los números de líneas y los tiempos son los del entorno de pruebas, y cada nombre de función, parámetro y constante lo comprobé contra el código.

Queda pendiente lo que figura en la sección F: timbres sintetizados de vientos y cuerdas para el audio de la fuga, perfil dinámico en el MIDI, ejecutar los fragmentos iniciales, exportar Kitaro a MIDI y el prototipo de tiempo real. Con esto cerramos lo que acordamos para hoy. Cuando quieras, dime cuál de esos retomamos.

---

> No supe dónde, ni cómo, poner el siguiente texto de las secciones nuevas

```md
## Cambios en archivos que ya existían

- **`fuga.py`**: `contrapunto()` acepta `triada=None` para quitar la regla de la nota final (o una tríada distinta).
- **`fuga_larga.py`**: `seccion()` acepta `triada` y `rangos` propios, necesarios para escribir en otra tonalidad.
- **`fuga_episodios.py`**: `fuga_completa(semilla, intentos, plan_extra=())` acepta secciones de tipo `'custom'` con una función propia `fn(voces, t0, S, sem) -> (voces, duración)`. Así se enganchó el stretto sin tocar el resto.

## Formatos de datos: lo nuevo

- **`fuga_tonal.py` usa alturas MIDI**, no grados de Re menor. Una nota es `(altura_midi, inicio, duración)`. La conversión desde las voces de `fuga.py` es `a_midi()`.
- **`Escala(tonica, modo)`**: el índice 0 es la tónica; `esc.midi(i)` da la altura del grado `i`. Re menor es `Escala(62)` y La menor `Escala(69)`; el modo `'armonica'` sube el séptimo grado (la sensible).
- **La voz que genera `contrapunto_tonal()`** son índices relativos de escala. La altura final es `esc.midi(g + despl)`, y cada *escenario* puede traer su propia escala.
- **`triada`** en `contrapunto_tonal()` son clases de altura (módulo 12), no grados: `{9, 0, 4}` es el acorde de La menor.

```

> Adjunto el `README.md` como está hasta ahora.

Ya apliqué las inserciones en una copia de tu README; te la entrego y te explico dónde fue cada cosa.

Esas dos secciones no iban como bloques aparte: mi fallo fue presentarlas como si lo fueran. Las repartí por tu README, que ya tenía bien integrado todo lo demás (secciones 8 a 12, orden de lectura, parámetros, lecciones, limitaciones y glosario). Te dejo `README_es.md` con los cambios aplicados sobre tu archivo y nada más tocado. El diff muestra solo estas líneas.

**"Formatos de datos: lo nuevo"** va dentro de tu sección **"Formatos de datos (la clave de todo)"**, en tres sitios:
- Una viñeta nueva en **Altura**, detrás de la de Winston, Yanni y Kitaro: `fuga_tonal.py` usa alturas MIDI porque necesita Sol♯ y Do♯.
- Una viñeta nueva en **Nota y evento**, detrás de la de la fuga: `(altura_midi, inicio, duración)`.
- Un párrafo nuevo, **"Escalas y grados en `fuga_tonal.py`"**, detrás de la convención de posición en el contrapunto, con `Escala`, los índices relativos y `triada` como clases de altura.

**"Cambios en archivos que ya existían"** va repartido en las secciones de cada archivo, que es donde alguien lo buscaría:
- **Sección 4 (`fuga.py`):** sustituí la última viñeta de "Reglas de `contrapunto`" para aclarar que `triada` tiene un valor por defecto, que `triada=None` quita la regla y qué le pasan otras secciones.
- **Sección 5 (`fuga_larga.py`):** viñeta nueva después de `PLAN` sobre `seccion()` con `triada` y `rangos`.
- **Sección 6 (`fuga_episodios.py`):** viñeta nueva después de `fuga_completa()` sobre `plan_extra` y las secciones `'custom'`, con la mención al stretto.

Si prefieres un solo bloque, ponlo como `## Cambios en archivos que ya existían` justo antes de `## Parámetros para experimentar (resumen)`; el texto original de esa sección te sirve tal cual. Pero repartido queda más fácil de encontrar, y por eso hice esto.

**Dos retoques extra** que vi al leerlo, también ya aplicados:
- El encabezado `## F. Estado de lo pendiente (sección nueva)` conservaba etiquetas de mis bloques, y ahora es `## Estado de lo pendiente`.
- La tabla de verificación decía "MP3 de 192 kbps", pero los `sonido_*.mp3` salen a 160 kbps, y ahora dice "160 o 192 kbps".

Como la copia parte del archivo que subiste, si has cambiado el tuyo desde entonces, conviene aplicar estos cambios sobre el tuyo en lugar de reemplazarlo; con `diff` verás el cambio exacto.

---

> Puedes traducir el `Readme_es.md` al inglés?
>
>Me gustaría que otros lectores lo pudieran leer.

Primero leo tu README completo, por tramos, para traducir lo que realmente contiene y no una versión anterior.

Ya está traducido por completo; antes de entregarlo comparo las cifras con el original para descartar erratas.

Te dejo la traducción completa al inglés como `README.md` (635 líneas, toda la guía de estudio incluida). Sustituye al primer borrador en español que ocupaba ese nombre en la misma carpeta; si prefieres `README_en.md`, basta con renombrarlo.

**Cómo la hice**
- Los identificadores del código (`contrapunto`, `seccion_tonal`...), los nombres de archivo y los comandos se quedan tal cual, porque el código está en español.
- Añadí tres cosas que no estaban en tu versión, pensadas para quien lea en inglés:
  - Una nota al principio que avisa de que el código, sus comentarios y sus mensajes están en español.
  - Una tabla final, **"Spanish terms in the code"**, con el significado de unos 35 identificadores (`sujeto`, `corchea`, `semilla`, `rafaga`...).
  - Junto al enlace al diario, la aclaración de que la conversación está en español. El título del diario lo traduje yo, y el enlace sigue apuntando al archivo original.

**Comprobaciones:** los encabezados coinciden (33 en español y 34 en inglés, por la sección nueva), los bloques de código están balanceados, y todas las cifras coinciden con el original salvo las diferencias que explico abajo. No quedan palabras en español en la prosa.

**Cuatro correcciones que hice solo en el inglés** y que conviene aplicar también a tu `README_es.md`. Dos son errores míos de las primeras versiones del texto:

1. **La respuesta de `fuga.py` no es una "respuesta real (transposición exacta)".** Es el sujeto desplazado +4 grados dentro de Re menor natural, es decir, una transposición diatónica, y por eso los intervalos pueden cambiar en un semitono. Sustituye en Limitaciones la viñeta *"La fuga usa **respuesta real**…"* por: *"En `fuga.py` la respuesta es el sujeto desplazado **+4 grados dentro de Re menor natural** (transposición diatónica: mismas notas, intervalos que pueden cambiar en un semitono); no es una transposición exacta ni la *respuesta tonal* de Bach."*
2. **En la sección 6, "los intervalos son idénticos en cada repetición" solo es cierto en grados de la escala**, no necesariamente en semitonos. Añade: *"(en semitonos pueden diferir en uno, porque los desplazamientos son diatónicos)"*.
3. **La viñeta "Código duplicado" aparece dos veces** en Limitaciones. En el inglés las fusioné en una, así que borra la primera (la que menciona `hz` y `piano`) o únelas.
4. **Dos ideas ya hechas seguían como pendientes.** Cambia *"Stretto (entradas solapadas) y entrada del sujeto en la subdominante"* por *"Entrada del sujeto en la subdominante"*, y *"Respuesta tonal y alteraciones para modular a la dominante"* por *"Respuesta tonal (como en Bach) en lugar de la transposición diatónica a la quinta"*.

Falta una revisión que no he podido hacer: que el inglés suene natural a un lector nativo. He cuidado los términos técnicos (por ejemplo *bar* y *beat* para compás y tiempo), pero conviene una lectura rápida por alguien que conozca el vocabulario musical.