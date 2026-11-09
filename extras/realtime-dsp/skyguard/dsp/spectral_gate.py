"""Bramka widmowa (redukcja szumu tła: wiatr, ruch uliczny, buczenie).

Zaadaptowane z timsainb/noisereduce (MIT, © 2019 Tim Sainburg), pliki
noisereduce/spectralgate/stationary.py i nonstationary.py:
- tryb stacjonarny: próg na pasmo = średnia + n_std·odchylenie (dB) z próbki
  samego tła (`noise_clip`), maska binarna, wygładzanie maski;
- tryb niestacjonarny: wygładzanie widma w czasie filtrem IIR o stałej czasowej,
  maska sigmoidalna względem tła — przepuszcza ZMIANY (np. nadlatujący dron),
  tłumi wszystko, co stałe (także stały ton!), więc do ciągłego tonu drona
  używaj trybu stacjonarnego z nagraniem tła.
Zmiany SKYGUARD: jedna funkcja bez klas, mono, parametry pod 8–16 kHz.
Licencja MIT: zob. THIRD_PARTY_LICENSES.md."""
from __future__ import annotations

import numpy as np
from scipy.signal import filtfilt, fftconvolve, istft, stft


def _time_smooth(spec, sr, hop, time_constant_s):
    t_frames = time_constant_s * sr / float(hop)
    b = (np.sqrt(1 + 4 * t_frames ** 2) - 1) / (2 * t_frames ** 2)
    return filtfilt([b], [1, b - 1], spec, axis=-1, padtype=None)


def _sigmoid(x, shift, mult):
    return 1 / (1 + np.exp(-(x + shift) * mult))


def _amp_to_db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-10))


def _smoothing_kernel(nf, nt):
    a = np.concatenate([np.linspace(0, 1, nf + 1, endpoint=False), np.linspace(1, 0, nf + 2)])[1:-1]
    b = np.concatenate([np.linspace(0, 1, nt + 1, endpoint=False), np.linspace(1, 0, nt + 2)])[1:-1]
    k = np.outer(a, b)
    return k / k.sum()


def spectral_gate(x, sr: int, noise_clip=None, n_fft: int = 1024, hop: int | None = None,
                  n_std_thresh: float = 1.5, time_constant_s: float = 2.0, thresh_n_mult: float = 2.0,
                  sigmoid_slope: float = 10.0, prop_decrease: float = 1.0,
                  freq_smooth_hz: float = 500.0, time_smooth_ms: float = 50.0) -> np.ndarray:
    """`noise_clip` podany → tryb stacjonarny; brak → niestacjonarny."""
    x = np.asarray(x, dtype=float)
    hop = hop or n_fft // 4
    kw = dict(nperseg=n_fft, noverlap=n_fft - hop, nfft=n_fft)
    _, _, Z = stft(x, padded=False, **kw)
    if noise_clip is not None:
        _, _, N = stft(np.asarray(noise_clip, float), padded=False, **kw)
        nd = _amp_to_db(N)
        thr = nd.mean(axis=1) + n_std_thresh * nd.std(axis=1)
        mask = (_amp_to_db(Z) > thr[:, None]).astype(float)
    else:
        A = np.abs(Z)
        smooth = _time_smooth(A, sr, hop, time_constant_s)
        mask = _sigmoid((A - smooth) / np.maximum(smooth, 1e-12), -thresh_n_mult, sigmoid_slope)
    nf = max(1, int(freq_smooth_hz / (sr / n_fft)))
    nt = max(1, int(time_smooth_ms / (hop / sr * 1000)))
    if nf > 1 or nt > 1:
        mask = fftconvolve(mask, _smoothing_kernel(nf, nt), mode="same")
    mask = mask * prop_decrease + (1.0 - prop_decrease)
    _, y = istft(Z * mask, **kw)
    out = np.zeros_like(x)
    n = min(x.size, y.size)
    out[:n] = y[:n]
    return out
