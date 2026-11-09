"""Spektrogram melowy, log-mel i MFCC (Slaney mel, jak librosa).

Własna implementacja tych samych wzorów co librosa/librosa (ISC) — wyniki
zgodne z `librosa.feature.melspectrogram` / `mfcc` (test porównawczy, gdy
librosa jest zainstalowana). librosa nie jest wymagana."""
from __future__ import annotations

import numpy as np

from .windows import hann


def hz_to_mel(f):
    f = np.asanyarray(f, dtype=float)
    f_sp, min_log_hz = 200.0 / 3, 1000.0
    min_log_mel, logstep = min_log_hz / f_sp, np.log(6.4) / 27.0
    m = f / f_sp
    return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-10) / min_log_hz) / logstep, m)


def mel_to_hz(m):
    m = np.asanyarray(m, dtype=float)
    f_sp, min_log_hz = 200.0 / 3, 1000.0
    min_log_mel, logstep = min_log_hz / f_sp, np.log(6.4) / 27.0
    return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), f_sp * m)


def mel_filterbank(sr: int, n_fft: int, n_mels: int = 128, fmin: float = 0.0, fmax: float | None = None) -> np.ndarray:
    fmax = fmax or sr / 2
    fft_f = np.linspace(0, sr / 2, 1 + n_fft // 2)
    mel_f = mel_to_hz(np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), n_mels + 2))
    fdiff = np.diff(mel_f)
    ramps = mel_f[:, None] - fft_f[None, :]
    lower = -ramps[:-2] / fdiff[:-1, None]
    upper = ramps[2:] / fdiff[1:, None]
    w = np.maximum(0, np.minimum(lower, upper))
    enorm = 2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels])
    return w * enorm[:, None]


def stft_power(x, n_fft: int = 2048, hop: int = 512, center: bool = True) -> np.ndarray:
    """|STFT|^2, kształt (1 + n_fft/2, ramki); okno Hann, centrowanie z odbiciem jak librosa ≥0.10 (pad 'constant')."""
    x = np.asarray(x, dtype=float)
    if center:
        x = np.pad(x, n_fft // 2, mode="constant")
    if x.size < n_fft:
        x = np.pad(x, (0, n_fft - x.size))
    k = 1 + (x.size - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(k)[:, None]
    return (np.abs(np.fft.rfft(x[idx] * hann(n_fft), axis=1)) ** 2).T


def melspectrogram(x, sr: int, n_fft: int = 2048, hop: int = 512, n_mels: int = 128,
                   fmin: float = 0.0, fmax: float | None = None) -> np.ndarray:
    return mel_filterbank(sr, n_fft, n_mels, fmin, fmax) @ stft_power(x, n_fft, hop)


def power_to_db(S, ref: float = 1.0, amin: float = 1e-10, top_db: float | None = 80.0) -> np.ndarray:
    S = np.asarray(S, dtype=float)
    d = 10.0 * np.log10(np.maximum(amin, S)) - 10.0 * np.log10(max(amin, ref))
    if top_db is not None:
        d = np.maximum(d, d.max() - top_db)
    return d


def mfcc(x, sr: int, n_mfcc: int = 20, **kw) -> np.ndarray:
    """MFCC (DCT-II ortho z log-mel w dB), kształt (n_mfcc, ramki)."""
    from scipy.fft import dct
    return dct(power_to_db(melspectrogram(x, sr, **kw)), axis=0, type=2, norm="ortho")[:n_mfcc]
