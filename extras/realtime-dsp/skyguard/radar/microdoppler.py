"""Mikro-Doppler wirników: symulacja echa, spektrogram, cechy klasyfikacyjne.

Metody: Keerthi2134/doppler-radar (bez licencji — własna implementacja)
i ZhongliangGuo/MathWorks-Radar-Drone-Project (MIT — przepisane z MATLAB
na numpy, bez kopiowania kodu): model łopat jako punktów rozpraszających
obracających się z f_rot, echo z fazą 4π·r(t)/λ, STFT, cechy: szerokość
pasma mikro-Dopplera, okres „błysków” łopat (cepstrum/autokorelacja)."""
from __future__ import annotations

import numpy as np


def simulate_rotor_echo(fs: float, duration_s: float, fc_hz: float = 24e9, f_rot: float = 80.0,
                        n_blades: int = 2, blade_len_m: float = 0.12, body_v_ms: float = 0.0,
                        body_rcs: float = 1.0, blade_rcs: float = 0.3, n_scat: int = 10, snr_db: float = 20.0,
                        seed: int | None = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    lam = 3e8 / fc_hz
    t = np.arange(int(fs * duration_s)) / fs
    s = body_rcs * np.exp(1j * 4 * np.pi * body_v_ms * t / lam)
    for b in range(n_blades):
        ph = 2 * np.pi * b / n_blades
        for r in np.linspace(blade_len_m / n_scat, blade_len_m, n_scat):
            radial = r * np.cos(2 * np.pi * f_rot * t + ph)
            s = s + blade_rcs / n_scat * np.exp(1j * 4 * np.pi * (body_v_ms * t + radial) / lam)
    p = np.mean(np.abs(s) ** 2)
    noise = (rng.standard_normal(t.size) + 1j * rng.standard_normal(t.size)) * np.sqrt(p / 2 * 10 ** (-snr_db / 10))
    return s + noise


def micro_doppler_spectrogram(x: np.ndarray, fs: float, n_fft: int = 256, hop: int = 32):
    win = np.hanning(n_fft)
    k = 1 + (len(x) - n_fft) // hop
    S = np.stack([np.fft.fftshift(np.fft.fft(x[i * hop:i * hop + n_fft] * win)) for i in range(k)], 1)
    f = np.fft.fftshift(np.fft.fftfreq(n_fft, 1 / fs))
    return f, np.arange(k) * hop / fs, np.abs(S) ** 2


def micro_doppler_features(x: np.ndarray, fs: float, fc_hz: float = 24e9, n_fft: int = 256, hop: int = 32,
                           thr_db: float = 6.0) -> dict:
    """Szerokość mikro-Dopplera (→ prędkość końcówki łopaty), częstotliwość błysków (→ n_blades·f_rot).

    Szerokość = zakres widma uśrednionego w czasie powyżej (dno szumu + thr_db);
    dno szumu = 5. percentyl. Wymaga przyzwoitego SNR echa łopat (≳ 25 dB całkowitego)."""
    f, t, S = micro_doppler_spectrogram(x, fs, n_fft, hop)
    m = 10 * np.log10(S.mean(axis=1) + 1e-15)
    occ = m > np.percentile(m, 5) + thr_db
    bw = float(f[occ].max() - f[occ].min()) if occ.any() else 0.0
    lam = 3e8 / fc_hz
    body = np.abs(f) < max(0.05 * bw, 2 * fs / n_fft)
    flash = S[~body].sum(axis=0)
    flash = flash - flash.mean()
    ac = np.correlate(flash, flash, "full")[flash.size - 1:]
    frame_rate = fs / hop
    lag_min = 2
    half = ac.size // 2
    lag = lag_min + int(np.argmax(ac[lag_min:half])) if half > lag_min else 0
    return {"doppler_bandwidth_hz": bw, "tip_speed_ms": bw / 2 * lam / 2,
            "flash_rate_hz": float(frame_rate / lag) if lag else 0.0,
            "doppler_centroid_hz": float(np.sum(f[:, None] * S) / S.sum())}
