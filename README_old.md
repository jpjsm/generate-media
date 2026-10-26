# generate-media

Learning about how to generate fractal images and generate sounds

## Notas de estudio

e sugiero ir de lo simple a lo denso, con una idea: casi todo el código sigue el mismo patrón (generar eventos → sintetizar → mezclar), así que conviene entenderlo primero en un archivo pequeño.

winston.py (el mejor punto de partida). Tiene el esqueleto completo: partitura() produce una lista de eventos (nota, inicio, duración, velocidad), render() la convierte en audio y wav_a_mp3() la exporta. Fíjate en piano() (síntesis aditiva), en la melodía como paseo aleatorio ponderado (elegir_nota) y en segundos(), que implementa el ritardando.
kitaro.py. Es DSP puro: osciladores desafinados, LFO que abre y cierra el brillo, eco ping-pong y reverb por convolución. Si te interesa el lado de señal, aquí está lo más didáctico.
yanni.py. Añade estructura: secciones, transposición (el cambio de tonalidad es un solo parámetro trans) y secuenciar(), que repite un dibujo melódico sobre otro acorde.
fuga.py. Es el corazón intelectual, y conviene leerlo en este orden: midi(), muestrear_midi() y paralelos() (las piezas básicas); sujeto() (generar y filtrar); y contrapunto(), que es el núcleo. Esta última es un problema de satisfacción de restricciones resuelto por búsqueda con retroceso: nota_ok() poda y dfs() explora. Con tu formación en bases de datos, puede ayudarte verlo como una consulta con predicados de poda, solo que las condiciones son reglas de armonía.
fuga_larga.py y fuga_episodios.py. Reutilizan contrapunto() de formas nuevas. Lo más interesante es el parámetro escenarios: permite exigir que una misma voz cumpla las reglas en varias situaciones a la vez, que es lo que da el contrapunto invertible y las secuencias reales.
midi_export.py. Es corto y sirve de repaso del formato de eventos.

Mientras lees, te recomiendo hacer un experimento por archivo: cambiar una constante y volver a escuchar. Por ejemplo, BPM y PROG en Winston, el rt60 de la reverb en Kitaro, o paso y k en episodio().

Para cualquiera de ellos puedo escribirte un recorrido comentado línea por línea, explicar una función concreta, o preparar pruebas pequeñas que muestren qué hace cada regla del contrapunto. ¿Por cuál quieres empezar? Mi sugerencia es winston.py
