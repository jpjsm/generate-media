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
