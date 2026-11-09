"""Ciągła transformata falkowa (CWT) z zespoloną falką Morleta.

Własna implementacja (splot w dziedzinie częstotliwości); konwencja skal jak
PyWavelets/pywt (MIT) `cmor{B}-{C}`: psi(t) = (πB)^-1/2 · exp(-t²/B) · exp(j2πCt),
częstotliwość skali f = C·fs/scale. Służy do śledzenia zmian obrotów wirnika
podczas manewrów (ton BPF zmienia się szybciej niż okno FFT)."""
from __future__ import annotations

import numpy as np


def morlet_cwt(x, sr: int, freqs, bandwidth: float = 1.5, center: float = 1.0) -> np.ndarray:
    """Zwraca macierz zespoloną (len(freqs), len(x))."""
    x = np.asarray(x, float)
    n = x.size
    freqs = np.asarray(freqs, float)
    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    X = np.fft.fft(x, nfft)
    w = np.fft.fftfreq(nfft, d=1.0 / sr)
    out = np.empty((freqs.size, n), complex)
    for i, f in enumerate(freqs):
        scale = center * sr / f
        # FT falki cmor w skali `scale` (próbki): Gauss wokół f, szerokość ~ 1/(scale*sqrt(B))
        psi_hat = np.exp(-(np.pi ** 2) * bandwidth * (w / sr * scale - center) ** 2)
        out[i] = 2.0 * np.fft.ifft(X * psi_hat)[:n]  # ×2: amplituda sinusoidy
    return out


def ridge(cwt_mag: np.ndarray, freqs) -> np.ndarray:
    """Częstotliwość chwilowa = maksimum |CWT| w każdej chwili."""
    return np.asarray(freqs)[np.argmax(np.abs(cwt_mag), axis=0)]
