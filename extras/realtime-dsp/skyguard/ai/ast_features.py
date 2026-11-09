"""Przygotowanie wejścia dla Audio Spectrogram Transformer (AST).

Zaadaptowane z YuanGongND/ast (BSD-3-Clause, © 2021 Yuan Gong): fbank w stylu
Kaldi — 16 kHz, 128 pasm mel, okno 25 ms, krok 10 ms, Hanning, odjęcie DC,
preemfaza 0.97, log, potem dopełnienie/obcięcie do target_length ramek
i normalizacja (x − mean) / (2·std) z wartościami AudioSet
(mean −4.2677393, std 4.5689974). Zmiany SKYGUARD: czysty numpy (bez
torchaudio), resampling scipy z dowolnego sr."""
from __future__ import annotations

import numpy as np
from scipy.signal import resample_poly

AST_MEAN = -4.2677393
AST_STD = 4.5689974


def _kaldi_mel_banks(n_mels, n_fft, sr, low=20.0, high=0.0):
    high = sr / 2 + high if high <= 0 else high
    mel = lambda f: 1127.0 * np.log(1 + f / 700.0)
    m_lo, m_hi = mel(low), mel(high)
    d = (m_hi - m_lo) / (n_mels + 1)
    fft_mel = mel(np.arange(n_fft // 2) * sr / n_fft)
    W = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        l, c, r = m_lo + i * d, m_lo + (i + 1) * d, m_lo + (i + 2) * d
        up = (fft_mel - l) / (c - l)
        dn = (r - fft_mel) / (r - c)
        W[i, :-1] = np.maximum(0, np.minimum(up, dn))
    return W


def ast_fbank(x, sr: int, n_mels: int = 128, target_length: int = 1024) -> np.ndarray:
    """Zwraca (target_length, n_mels) log-mel fbank jak `torchaudio.compliance.kaldi.fbank`."""
    x = np.asarray(x, float)
    if sr != 16000:
        g = np.gcd(int(sr), 16000)
        x = resample_poly(x, 16000 // g, int(sr) // g)
    sr = 16000
    x = x - x.mean()
    wl, sh, n_fft = 400, 160, 512
    if x.size < wl:
        x = np.pad(x, (0, wl - x.size))
    k = 1 + (x.size - wl) // sh
    fr = x[np.arange(wl)[None, :] + sh * np.arange(k)[:, None]].copy()
    fr -= fr.mean(axis=1, keepdims=True)
    fr = np.concatenate([fr[:, :1] - 0.97 * fr[:, :1], fr[:, 1:] - 0.97 * fr[:, :-1]], axis=1)
    win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(wl) / (wl - 1)))
    P = np.abs(np.fft.rfft(fr * win, n_fft, axis=1)) ** 2
    fb = np.log(np.maximum(P @ _kaldi_mel_banks(n_mels, n_fft, sr).T, np.finfo(float).eps))
    if fb.shape[0] < target_length:
        fb = np.pad(fb, ((0, target_length - fb.shape[0]), (0, 0)))
    return fb[:target_length]


def ast_normalize(fb: np.ndarray, mean: float = AST_MEAN, std: float = AST_STD) -> np.ndarray:
    return (fb - mean) / (2 * std)
