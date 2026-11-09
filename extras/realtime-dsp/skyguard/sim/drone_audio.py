"""Syntetyczny dźwięk multikoptera do testów (bez nagrań, bez zbiorów danych).

Model zaadaptowany z PhaseResponse/drone-acoustic-analysis (MIT, © 2026
Sharon Urieli): harmoniczne BPF (N_b·f0, 2·N_b·f0, …) dominujące, harmoniczne
nie-BPF tłumione wykładniczo, lekkie różnice obrotów silników (dudnienie),
losowa faza na silnik, szum 1/f² (silnik + aerodynamika), przelot z efektem
Dopplera, odbiciem od ziemi (źródło lustrzane) i szumem wiatru 1/f².
Implementacja SKYGUARD napisana od nowa (oryginał to notatniki Jupyter)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

C_SOUND = 343.0


@dataclass
class DroneAudioConfig:
    sr: int = 8000
    rotor_hz: float = 90.0        # obroty wału [Hz]
    n_blades: int = 2
    n_motors: int = 4
    rpm_spread: float = 0.015     # względny rozrzut obrotów silników
    n_harm: int = 12
    non_bpf_decay: float = 1.5
    brown_rms: float = 0.05
    seed: int | None = 0


def brown_noise(n, rng):
    w = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(w.size)
    w[1:] /= f[1:]
    w[0] = 0
    y = np.fft.irfft(w, n)
    return y / (np.std(y) + 1e-12)


def _source(t_emit, cfg: DroneAudioConfig, rng):
    y = np.zeros_like(t_emit)
    for m in range(cfg.n_motors):
        fr = cfg.rotor_hz * (1 + cfg.rpm_spread * rng.uniform(-1, 1))
        for h in range(1, cfg.n_harm + 1):
            fh = h * fr
            if fh >= cfg.sr / 2 * 0.95:
                break
            amp = 1.0 / h if h % cfg.n_blades == 0 else np.exp(-cfg.non_bpf_decay * h) / h
            y += amp * np.sin(2 * np.pi * fh * t_emit + rng.uniform(0, 2 * np.pi))
    return y / cfg.n_motors


def synth_drone(duration_s: float, cfg: DroneAudioConfig | None = None, snr_db: float | None = None):
    """Nieruchomy dron; opcjonalnie dodany biały szum o danym SNR."""
    cfg = cfg or DroneAudioConfig()
    rng = np.random.default_rng(cfg.seed)
    n = int(duration_s * cfg.sr)
    t = np.arange(n) / cfg.sr
    y = _source(t, cfg, rng) + cfg.brown_rms * brown_noise(n, rng)
    y /= np.std(y) + 1e-12
    if snr_db is not None:
        y = y + rng.standard_normal(n) * 10 ** (-snr_db / 20)
    return y


def flyby(duration_s: float, cfg: DroneAudioConfig | None = None, height_m: float = 20.0,
          speed_ms: float = 10.0, closest_m: float = 30.0, mic_xyz=(0.0, 0.0, 1.5),
          ground_reflection: float = 0.5, wind_rms: float = 0.1):
    """Przelot po linii prostej; zwraca (sygnał, odległość[m] w czasie)."""
    cfg = cfg or DroneAudioConfig()
    rng = np.random.default_rng(cfg.seed)
    n = int(duration_s * cfg.sr)
    t = np.arange(n) / cfg.sr
    x = speed_ms * (t - duration_s / 2)
    mic = np.asarray(mic_xyz, float)
    out = np.zeros(n)
    rng_state = rng.bit_generator.state
    dist_direct = None
    for z, gain in ((height_m, 1.0), (-height_m, ground_reflection)):
        d = np.sqrt((x - mic[0]) ** 2 + (closest_m - mic[1]) ** 2 + (z - mic[2]) ** 2)
        rng.bit_generator.state = rng_state  # ta sama faza dla źródła lustrzanego
        out += gain * _source(t - d / C_SOUND, cfg, rng) / np.maximum(d, 1.0)
        if dist_direct is None:
            dist_direct = d
    out /= np.std(out) + 1e-12
    out += wind_rms * brown_noise(n, rng)
    return out, dist_direct
