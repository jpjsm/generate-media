import io
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import lameenc


def generar_ruido_blanco(num_muestras):
    """Base aleatoria gaussian para todos los ruidos espectrales"""
    return np.random.normal(0, 1, num_muestras)


def generar_ruido_frecuencia(num_muestras, fs, exponente):
    """
    Genera ruidos aplicando una pendiente matemática en el dominio de la frecuencia.
    Marrón: exponente = -1.0
    Rosa:   exponente = -0.5
    Azul:   exponente =  0.5
    Violeta:exponente =  1.0
    """
    blanco = generar_ruido_blanco(num_muestras)
    espectro = np.fft.rfft(blanco)
    frecuencias = np.fft.rfftfreq(num_muestras, d=1 / fs)

    # Copiamos para modificar la componente continua (DC) y evitar división por cero
    frecuencias_ajustadas = np.copy(frecuencias)
    frecuencias_ajustadas[0] = frecuencias_ajustadas[
        1
    ]  # Evita 0 o infinito en la frecuencia 0

    # Aplicar la pendiente del espectro según el color
    espectro_coloreado = espectro * (frecuencias_ajustadas**exponente)

    # Forzar que la componente continua sea 0 si la pendiente es negativa (evita desfases DC)
    if exponente < 0:
        espectro_coloreado[0] = 0

    ruido = np.fft.irfft(espectro_coloreado, n=num_muestras)
    return normalizar(ruido)


def generar_ruido_gris(num_muestras, fs):
    """Ruido blanco filtrado con la inversa de la curva de ponderación A"""
    blanco = generar_ruido_blanco(num_muestras)
    espectro = np.fft.rfft(blanco)
    frecuencias = np.fft.rfftfreq(num_muestras, d=1 / fs)

    f = np.copy(frecuencias)
    f[0] = 1e-6  # Evitar ceros en la fórmula

    # Fórmula estándar para la curva de ponderación A (psicoacústica humana)
    f2 = f**2
    num = (12194**2) * (f**4)
    den = (f2 + 20.6**2) * np.sqrt((f2 + 107.7**2) * (f2 + 737.9**2)) * (f2 + 12194**2)
    ponderacion_a = num / den

    # Invertimos el peso para obtener el ruido gris
    espectro_gris = espectro / (ponderacion_a + 1e-6)
    espectro_gris[0] = 0

    ruido = np.fft.irfft(espectro_gris, n=num_muestras)
    return normalizar(ruido)


def generar_ruido_verde(num_muestras, fs):
    """Filtro paso de banda (500Hz - 2000Hz) aplicado sobre ruido blanco"""
    blanco = generar_ruido_blanco(num_muestras)
    # Diseñar filtro Butterworth paso de banda de orden 4
    sos = signal.butter(4, [500, 2000], btype="bandpass", fs=fs, output="sos")
    ruido = signal.sosfilt(sos, blanco)
    return normalizar(ruido)


def normalizar(audio):
    """Normaliza el audio al rango dinámico [-1.0, 1.0]"""
    return audio / np.max(np.abs(audio))


# --- Configuración de Parámetros ---
fs = 44100  # Frecuencia de muestreo estándar (44.1 kHz)
duracion = 30.0  # Duración en segundos
num_muestras = int(fs * duracion)

# # --- Generación de todos los Colores ---
# ruido_marron = generar_ruido_frecuencia(num_muestras, fs, exponente=-1.0)
# ruido_rosa = generar_ruido_frecuencia(num_muestras, fs, exponente=-0.5)
# ruido_azul = generar_ruido_frecuencia(num_muestras, fs, exponente=0.5)
# ruido_violeta = generar_ruido_frecuencia(num_muestras, fs, exponente=1.0)
# ruido_gris = generar_ruido_gris(num_muestras, fs)
# ruido_verde = generar_ruido_verde(num_muestras, fs)

# # --- Guardar en archivos .WAV usando scipy.io.wavfile ---
# colores = {
#     "marron": ruido_marron,
#     "rosa": ruido_rosa,
#     "azul": ruido_azul,
#     "violeta": ruido_violeta,
#     "gris": ruido_gris,
#     "verde": ruido_verde,
# }

# --- Generación y Exportación en Estéreo ---
colores_nombres = ["marron", "rosa", "azul", "violeta", "gris", "verde"]

for nombre in colores_nombres:
    ###----------------------------------
    # CORRECCIÓN 1: Generar dos señales de ruido independientes (Izquierda y Derecha)
    if nombre == "marron":
        ch_izq = generar_ruido_frecuencia(num_muestras, fs, exponente=-1.0)
        ch_der = generar_ruido_frecuencia(num_muestras, fs, exponente=-1.0)
    elif nombre == "rosa":
        ch_izq = generar_ruido_frecuencia(num_muestras, fs, exponente=-0.5)
        ch_der = generar_ruido_frecuencia(num_muestras, fs, exponente=-0.5)
    elif nombre == "azul":
        ch_izq = generar_ruido_frecuencia(num_muestras, fs, exponente=0.5)
        ch_der = generar_ruido_frecuencia(num_muestras, fs, exponente=0.5)
    elif nombre == "violeta":
        ch_izq = generar_ruido_frecuencia(num_muestras, fs, exponente=1.0)
        ch_der = generar_ruido_frecuencia(num_muestras, fs, exponente=1.0)
    elif nombre == "gris":
        ch_izq = generar_ruido_gris(num_muestras, fs)
        ch_der = generar_ruido_gris(num_muestras, fs)
    elif nombre == "verde":
        ch_izq = generar_ruido_verde(num_muestras, fs)
        ch_der = generar_ruido_verde(num_muestras, fs)

    # CORRECCIÓN 2: Intercalar los canales en una matriz 2D (Muestras, Canales)
    audio_estereo = np.stack((ch_izq, ch_der), axis=-1)

    # CORRECCIÓN 3: Convertir el audio flotante a enteros de 16 bits (int16) para lameenc
    datos_int16 = (audio_estereo * 32767).astype(np.int16)

    # --- STEP 2: Escribir el WAV en el archivo en memoria ---
    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, fs, datos_int16)

    # --- STEP 3: Leer los datos DESDE el archivo en memoria ---
    wav_buffer.seek(0)

    # Saltamos los 44 bytes de la cabecera estándar de SciPy
    wav_buffer.seek(44)

    # Leemos los bytes puros (que ahora están intercalados L, R, L, R... gracias a np.stack)
    pcm_bytes = wav_buffer.read()

    # --- STEP 4: Codificar a MP3 vía lameenc ---
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(192)
    encoder.set_in_sample_rate(fs)

    # CORRECCIÓN 4: Ahora sí configuramos 2 canales (Estéreo)
    encoder.set_channels(2)

    encoder.set_quality(2)
    encoder.silence()

    mp3_data = encoder.encode(pcm_bytes)
    mp3_data += encoder.flush()

    # --- STEP 5: Guardar el MP3 final ---
    archivo_mp3 = f"ruido_{nombre}_estereo.mp3"

    with open(archivo_mp3, "wb") as mp3_file:
        mp3_file.write(mp3_data)

    ###----------------------------------
    print(f"Archivo '{archivo_mp3}' generado correctamente en estéreo envolvente.")

print("\n¡Todos los archivos de audio se han exportado con éxito en formato Estéreo!")
