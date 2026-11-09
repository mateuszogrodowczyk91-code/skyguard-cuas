#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wzorcowy Moduł Referencyjny dla orkiestratorów C2 C-UAS:
Akustyczna Detekcja, Dekonstrukcja Fizyczna, Lokalizacja (MVDR + Doppler CPA)
oraz Hybrydowa Klasyfikacja Bezzałogowych Statków Powietrznych (BSP / UAV).

Architektura:
1. SignalConditioner: Cubic Declipping -> Zero-Phase Butterworth HPF -> STFT HPSS -> MMSE Noise Subtraction.
2. PhysicsFeatureExtractor: HPS Fundamental Tracker -> Sub-Harmonic Blade Discriminator ->
   Real Cepstrum Quefrency -> Hilbert Envelope Modulation Spectrum (PID Beats vs Piston ICE).
3. KinematicAndSpatialSolver: Non-linear Doppler CPA Trajectory Solver + Multi-Mic MVDR Beamformer + Kalman Tracker.
4. DeepAudioBackboneAdapter: Pluggable interface for PANNs (CNN14) / Audio Spectrogram Transformer (AST).
5. UAVAcousticOrchestrator: Orchestrator entrypoint returning schema-validated JSON telemetry for C2/EO-IR cueing.

SKYGUARD notes (tools/acoustic/cuas/README.md): reference / research module, NOT wired into the app yet.
Fixes vs the supplied file are marked "# FIX:". Known limitations kept as-is (logic unchanged):
- snr_post_dsp_db is always snr_raw_est_db + 9.21 dB (fixed 0.12 factor), so snr_gain_db is a constant, not a measurement.
- uav_detected = snr_post_dsp_db > 5 and median SFM < 0.65 is a heuristic gate, not a trained detector.
- flight phases use fixed 0-2.5 / 2.5-9.5 / 9.5-end s windows from the 12 s synthetic benchmark.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import scipy.fft as fft
import scipy.signal as signal
from scipy.ndimage import median_filter
from scipy.optimize import curve_fit


# ============================================================================
# 1. STRUKTURY DANYCH I KATALOG SYGNATUR FIZYCZNYCH BSP (DLA ORKIESTRATORÓW)
# ============================================================================

@dataclass
class UAVPlatformSignature:
    """Wzorcowa sygnatura fizyczna i widmowa platformy BSP."""
    model_name: str
    category: str                  # "multirotor_electric" | "fixed_wing_piston" | "turboprop_male"
    n_rotors: int
    n_blades: int
    rpm_range: Tuple[float, float]
    bpf_range_hz: Tuple[float, float]
    nominal_cruise_bpf_hz: float
    characteristic_peaks_hz: List[float]
    mass_kg: float
    frame_diagonal_mm: float
    prop_diameter_mm: float
    source_level_db: float


UAV_SIGNATURE_CATALOG: List[UAVPlatformSignature] = [
    UAVPlatformSignature(
        model_name="DJI Phantom 4 Pro",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(3000.0, 6000.0),
        bpf_range_hz=(100.0, 200.0),
        nominal_cruise_bpf_hz=195.2,
        characteristic_peaks_hz=[95.0, 195.2, 293.0, 395.0, 495.0],
        mass_kg=1.38,
        frame_diagonal_mm=350.0,
        prop_diameter_mm=240.0,
        source_level_db=82.0,
    ),
    UAVPlatformSignature(
        model_name="DJI Mavic 2 Pro / Zoom",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(4500.0, 6600.0),
        bpf_range_hz=(150.0, 220.0),
        nominal_cruise_bpf_hz=183.0,
        characteristic_peaks_hz=[90.0, 108.0, 183.0, 219.0],
        mass_kg=0.905,
        frame_diagonal_mm=354.0,
        prop_diameter_mm=0.0,
        source_level_db=75.0,
    ),
    UAVPlatformSignature(
        model_name="DJI Mavic 3",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(4000.0, 7000.0),
        bpf_range_hz=(133.0, 233.0),
        nominal_cruise_bpf_hz=153.0,
        characteristic_peaks_hz=[76.5, 153.0, 306.0, 459.0],
        mass_kg=0.895,
        frame_diagonal_mm=380.0,
        prop_diameter_mm=239.0,
        source_level_db=75.0,
    ),
    UAVPlatformSignature(
        model_name="Autel EVO / EVO II",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(3240.0, 6240.0),
        bpf_range_hz=(108.0, 208.0),
        nominal_cruise_bpf_hz=177.0,
        characteristic_peaks_hz=[108.0, 177.0, 208.0, 312.0, 419.0],
        mass_kg=1.191,
        frame_diagonal_mm=397.0,
        prop_diameter_mm=230.0,
        source_level_db=77.0,
    ),
    UAVPlatformSignature(
        model_name="DJI Mini / Mini 2",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(5370.0, 10620.0),
        bpf_range_hz=(179.0, 354.0),
        nominal_cruise_bpf_hz=223.0,
        characteristic_peaks_hz=[111.5, 223.0, 354.0, 446.0],
        mass_kg=0.242,
        frame_diagonal_mm=213.0,
        prop_diameter_mm=119.0,
        source_level_db=68.0,
    ),
    UAVPlatformSignature(
        model_name="DJI Inspire 2",
        category="multirotor_electric",
        n_rotors=4,
        n_blades=2,
        rpm_range=(3500.0, 5600.0),
        bpf_range_hz=(116.0, 187.0),
        nominal_cruise_bpf_hz=152.0,
        characteristic_peaks_hz=[76.0, 152.0, 304.0, 456.0],
        mass_kg=3.40,
        frame_diagonal_mm=605.0,
        prop_diameter_mm=0.0,
        source_level_db=82.0,
    ),
    UAVPlatformSignature(
        model_name="Shahed-136 / Geran-2 (MADO MD-550)",
        category="fixed_wing_piston",
        n_rotors=1,
        n_blades=2,
        rpm_range=(4000.0, 7500.0),
        bpf_range_hz=(133.0, 250.0),
        nominal_cruise_bpf_hz=183.0,
        characteristic_peaks_hz=[73.5, 92.5, 107.0, 183.0, 193.3, 1070.0],
        mass_kg=200.0,
        frame_diagonal_mm=2500.0,
        prop_diameter_mm=0.0,
        source_level_db=110.0,
    ),
    UAVPlatformSignature(
        model_name="Bayraktar TB2 (Rotax 912S)",
        category="fixed_wing_piston",
        n_rotors=1,
        n_blades=2,
        rpm_range=(4500.0, 5800.0),
        bpf_range_hz=(65.0, 85.0),
        nominal_cruise_bpf_hz=71.0,
        characteristic_peaks_hz=[71.0, 142.0, 173.0, 346.0],
        mass_kg=0.0,
        frame_diagonal_mm=0.0,
        prop_diameter_mm=0.0,
        source_level_db=108.0,
    ),
]


@dataclass
class UAVTelemetryReport:
    """Ustrukturyzowany meldunek wyjściowy dla orkiestratora C-UAS (JSON Schema)."""
    uav_detected: bool
    detection_confidence: float
    identified_model: str
    propulsion_category: str
    candidate_ranking: List[Dict[str, Any]]
    signal_quality: Dict[str, float]
    propulsion_physics: Dict[str, Any]
    kinematics_doppler: Dict[str, float]
    flight_phases: List[Dict[str, Any]]
    spatial_doa_tracking: Optional[Dict[str, Any]] = None
    deep_embedding_status: Dict[str, Any] = field(default_factory=dict)
    catalog_match_confidence: float = 0.0


# ============================================================================
# 2. KONDYCJONOWANIE SYGNAŁU POLOWEGO (DECLIPPING, HPF, HPSS, MMSE)
# ============================================================================

class SignalConditioner:
    """Czterostopniowe kondycjonowanie surowych nagrań polowych."""

    def __init__(
        self,
        sr: int = 48000,
        clip_threshold: float = 0.98,
        highpass_cutoff_hz: float = 85.0,
        stft_nperseg: int = 8192,
        stft_noverlap: int = 6144,
        hpss_kernel_harm: int = 15,
        hpss_kernel_perc: int = 15,
        hpss_margin: float = 1.2,
        mmse_noise_percentile: float = 15.0,
        mmse_over_subtraction: float = 1.4,
        mmse_spectral_floor: float = 0.04,
    ) -> None:
        self.sr = sr
        self.clip_threshold = clip_threshold
        self.highpass_cutoff_hz = highpass_cutoff_hz
        self.stft_nperseg = stft_nperseg
        self.stft_noverlap = stft_noverlap
        self.hpss_kernel_harm = hpss_kernel_harm
        self.hpss_kernel_perc = hpss_kernel_perc
        self.hpss_margin = hpss_margin
        self.mmse_noise_percentile = mmse_noise_percentile
        self.mmse_over_subtraction = mmse_over_subtraction
        self.mmse_spectral_floor = mmse_spectral_floor

    def cubic_declip(self, x: np.ndarray) -> Tuple[np.ndarray, float]:
        """Rekonstruuje przesterowane wierzchołki sygnału metodą interpolacji lokalnej."""
        y = x.astype(np.float64, copy=True)
        clipped = np.abs(y) >= self.clip_threshold
        if not np.any(clipped):
            return y, 0.0

        clip_ratio = float(np.mean(clipped))
        diff = np.diff(clipped.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1
        if clipped[0]:
            starts = np.insert(starts, 0, 0)
        if clipped[-1]:
            ends = np.append(ends, len(y))

        for s, e in zip(starts, ends):
            if (e - s) > 256:
                continue
            left = max(0, s - 6)
            right = min(len(y), e + 6)
            idx_window = np.arange(left, right)
            valid_mask = ~clipped[left:right]
            if np.sum(valid_mask) >= 4:
                y[s:e] = np.interp(
                    np.arange(s, e),
                    idx_window[valid_mask],
                    y[left:right][valid_mask],
                )
        return y, clip_ratio

    def zero_phase_highpass(self, x: np.ndarray) -> np.ndarray:
        """Eliminuje subsoniczne uderzenia wiatru (<85 Hz) bez zniekształceń fazowych."""
        sos = signal.butter(
            4, self.highpass_cutoff_hz, btype="highpass", fs=self.sr, output="sos"
        )
        return signal.sosfiltfilt(sos, x)

    def hpss_separation(
        self, zxx: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Rozdziela składową harmoniczną (dron) od perkusyjnej (trzaski mikrofonu)."""
        power_spec = np.abs(zxx) ** 2.0
        harm_median = median_filter(power_spec, size=(1, self.hpss_kernel_harm))
        perc_median = median_filter(power_spec, size=(self.hpss_kernel_perc, 1))
        eps = 1e-12
        mask_harm = (harm_median ** 2) / (
            (harm_median ** 2) + (self.hpss_margin * perc_median) ** 2 + eps
        )
        mask_perc = (perc_median ** 2) / (
            (perc_median ** 2) + (self.hpss_margin * harm_median) ** 2 + eps
        )
        return zxx * mask_harm, zxx * mask_perc, mask_harm

    def spectral_subtraction_mmse(
        self, zxx_harm: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Tłumi szerokopasmowy szum komunikacyjny metodą subtrakcji widmowej."""
        mag = np.abs(zxx_harm)
        phase = np.angle(zxx_harm)
        psd = mag ** 2
        noise_psd = np.percentile(
            psd, self.mmse_noise_percentile, axis=1, keepdims=True
        )
        clean_psd = np.maximum(
            psd - self.mmse_over_subtraction * noise_psd,
            self.mmse_spectral_floor * noise_psd,
        )
        gain = np.sqrt(clean_psd / (psd + 1e-12))
        return mag * gain * np.exp(1j * phase), noise_psd.squeeze()

    def process(self, raw_audio: np.ndarray) -> Dict[str, Any]:
        """Uruchamia pełną kaskadę kondycjonowania i zwraca oczyszczony sygnał oraz STFT."""
        y_declip, clip_ratio = self.cubic_declip(raw_audio)
        y_hp = self.zero_phase_highpass(y_declip)

        freqs, times, zxx = signal.stft(
            y_hp,
            fs=self.sr,
            window="hann",
            nperseg=self.stft_nperseg,
            noverlap=self.stft_noverlap,
        )
        z_harm, z_perc, _ = self.hpss_separation(zxx)
        z_clean, noise_floor = self.spectral_subtraction_mmse(z_harm)

        _, y_clean = signal.istft(
            z_clean,
            fs=self.sr,
            window="hann",
            nperseg=self.stft_nperseg,
            noverlap=self.stft_noverlap,
        )
        y_clean = y_clean[: len(raw_audio)]

        # Estymacja SNR przed i po kondycjonowaniu
        noise_est_var = float(np.var(y_hp - y_clean)) + 1e-12
        clean_var = float(np.var(y_clean))
        snr_post_db = float(10.0 * np.log10(clean_var / (0.12 * noise_est_var)))
        snr_raw_db = float(10.0 * np.log10(clean_var / noise_est_var))

        return {
            "y_clean": y_clean,
            "freqs": freqs,
            "times": times,
            "z_clean": z_clean,
            "noise_floor_psd": noise_floor,
            "clip_ratio": clip_ratio,
            "snr_raw_est_db": round(snr_raw_db, 2),
            "snr_post_dsp_db": round(snr_post_db, 2),
            "snr_gain_db": round(snr_post_db - snr_raw_db, 2),
        }


# ============================================================================
# 3. EKSTRAKCJA CECH FIZYCZNYCH (HPS, SUBHARMONICZNE, CEPSTRUM, MODULACJA)
# ============================================================================

class PhysicsFeatureExtractor:
    """Ekstraktor parametrów fizycznych napędu bezzałogowca."""

    def __init__(self, sr: int = 48000, nperseg: int = 8192) -> None:
        self.sr = sr
        self.nperseg = nperseg

    def track_bpf_hps(
        self,
        freqs: np.ndarray,
        z_clean: np.ndarray,
        bpf_min_hz: float = 70.0,
        bpf_max_hz: float = 360.0,
        n_harmonics: int = 6,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Śledzi chwilową częstotliwość BPF(t) metodą HPS z interpolacją paraboliczną."""
        valid_bins = np.where((freqs >= bpf_min_hz) & (freqs <= bpf_max_hz))[0]
        n_frames = z_clean.shape[1]
        bpf_track = np.zeros(n_frames, dtype=np.float64)
        spectral_flatness = np.zeros(n_frames, dtype=np.float64)

        df = self.sr / float(self.nperseg)

        for t_idx in range(n_frames):
            spec_col = np.abs(z_clean[:, t_idx]) + 1e-12
            # Płaskość widmowa (SFM) w paśmie 100 - 3000 Hz
            band_mask = (freqs >= 100.0) & (freqs <= 3000.0)
            band_power = spec_col[band_mask] ** 2
            geo_mean = np.exp(np.mean(np.log(band_power + 1e-15)))
            arith_mean = np.mean(band_power) + 1e-15
            spectral_flatness[t_idx] = float(geo_mean / arith_mean)

            hps = np.ones(len(valid_bins), dtype=np.float64)
            for k in range(1, n_harmonics + 1):
                k_bins = np.minimum(valid_bins * k, len(spec_col) - 1)
                hps *= spec_col[k_bins]

            best_bin = valid_bins[int(np.argmax(hps))]
            # Interpolacja paraboliczna wokół 4. harmonicznej dla 4x wyższej precyzji
            k_ref = 4
            ref_bin = min(best_bin * k_ref, len(spec_col) - 2)
            if ref_bin > 1:
                y0 = math.log(spec_col[ref_bin - 1])
                y1 = math.log(spec_col[ref_bin])
                y2 = math.log(spec_col[ref_bin + 1])
                denom = y0 - 2.0 * y1 + y2
                delta = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-10 else 0.0
                delta = float(np.clip(delta, -0.5, 0.5))
                bpf_track[t_idx] = ((ref_bin + delta) * df) / float(k_ref)
            else:
                bpf_track[t_idx] = freqs[best_bin]

        return bpf_track, spectral_flatness

    def analyze_blade_count_and_harmonics(
        self, y_clean: np.ndarray, bpf_ref_hz: float
    ) -> Dict[str, Any]:
        """Wyznacza liczbę łopat śmigła (Nb = 2 vs 3) oraz główne piki widma mocy."""
        n_welch = min(len(y_clean), 32768)
        f_psd, pxx = signal.welch(
            y_clean, fs=self.sr, window="hann", nperseg=n_welch, noverlap=n_welch // 2
        )

        def peak_in_window(f_center: float, tol_hz: float = 5.5) -> float:
            mask = (f_psd >= f_center - tol_hz) & (f_psd <= f_center + tol_hz)
            return float(np.max(pxx[mask])) if np.any(mask) else 1e-15

        bg_median = float(
            np.median(pxx[(f_psd >= 50.0) & (f_psd <= 500.0)]) + 1e-15
        )
        e_half = peak_in_window(bpf_ref_hz / 2.0)
        e_third = peak_in_window(bpf_ref_hz / 3.0)

        # FIX: digital silence (zero-padded / dropout audio) gave e = 0 -> math domain error in log10
        snr_half_db = 10.0 * math.log10((e_half + 1e-30) / bg_median)
        snr_third_db = 10.0 * math.log10((e_third + 1e-30) / bg_median)
        n_blades = 2 if snr_half_db >= snr_third_db else 3

        # Ekstrakcja dominujących pików w paśmie 70 - 600 Hz
        band_idx = np.where((f_psd >= 70.0) & (f_psd <= 600.0))[0]
        pxx_db = 10.0 * np.log10(pxx[band_idx] / (np.max(pxx[band_idx]) + 1e-15) + 1e-15)
        # FIX: distance must be >= 1 bin (short clips / coarse Welch grid raised ValueError)
        peaks, props = signal.find_peaks(
            pxx_db, distance=max(1, int(15.0 / (f_psd[1] - f_psd[0]))), prominence=3.0
        )
        # FIX: "dominant" peaks = the 6 most prominent ones (original took the 6 lowest in frequency)
        order = np.argsort(props["prominences"])[::-1][:6]
        top_peaks_hz = sorted(round(float(f_psd[band_idx[peaks[i]]]), 1) for i in order)

        return {
            "estimated_blades_nb": n_blades,
            "subharmonic_half_snr_db": round(snr_half_db, 2),
            "subharmonic_third_snr_db": round(snr_third_db, 2),
            "dominant_low_freq_peaks_hz": top_peaks_hz,
        }

    def compute_real_cepstrum_f0(
        self, y_clean: np.ndarray, f_min: float = 70.0, f_max: float = 350.0
    ) -> float:
        """Oblicza cepstrum rzeczywiste do niezależnej weryfikacji okresu podstawowego."""
        spectrum = fft.rfft(y_clean * np.hanning(len(y_clean)))
        log_spec = np.log(np.abs(spectrum) + 1e-12)
        cepstrum = np.abs(fft.irfft(log_spec))
        quefrencies = np.arange(len(cepstrum)) / float(self.sr)

        q_min, q_max = 1.0 / f_max, 1.0 / f_min
        mask = (quefrencies >= q_min) & (quefrencies <= q_max)
        if not np.any(mask):
            return 0.0
        best_q = quefrencies[mask][int(np.argmax(cepstrum[mask]))]
        return round(1.0 / float(best_q), 2)

    def analyze_envelope_modulation(self, y_clean: np.ndarray) -> Dict[str, Any]:
        """
        Analizuje widmo modulacji obwiedni Hilberta w paśmie 600-2500 Hz.
        Rozróżnia dudnienia międzywirnikowe PID (1.5-18 Hz) od silnika 2-suwowego (45-125 Hz).
        """
        # FIX: keep the 600-2500 Hz band below Nyquist (sr < 5 kHz raised ValueError)
        sos_bp = signal.butter(
            4, [600.0, min(2500.0, 0.45 * self.sr)], btype="bandpass", fs=self.sr, output="sos"
        )
        y_bp = signal.sosfiltfilt(sos_bp, y_clean)
        envelope = np.abs(signal.hilbert(y_bp))
        env_zero = envelope - np.mean(envelope)

        decim_factor = max(1, self.sr // 1000)
        env_ds = signal.decimate(env_zero, decim_factor, ftype="fir")
        sr_env = self.sr / float(decim_factor)

        n_mod = min(len(env_ds), 4096)
        f_mod, p_mod = signal.welch(env_ds, fs=sr_env, window="hann", nperseg=n_mod)

        total_mod_energy = float(
            np.sum(p_mod[(f_mod >= 0.5) & (f_mod <= 200.0)]) + 1e-15
        )
        beat_mask = (f_mod >= 1.5) & (f_mod <= 18.0)
        piston_mask = (f_mod >= 45.0) & (f_mod <= 125.0)

        beat_ratio = float(np.sum(p_mod[beat_mask]) / total_mod_energy)
        piston_ratio = float(np.sum(p_mod[piston_mask]) / total_mod_energy)
        peak_beat_hz = float(f_mod[beat_mask][int(np.argmax(p_mod[beat_mask]))])

        propulsion_type = (
            "fixed_wing_piston"
            if piston_ratio > 0.15
            else "multirotor_electric"
        )

        return {
            "propulsion_type_inferred": propulsion_type,
            "peak_inter_rotor_beat_hz": round(peak_beat_hz, 2),
            "multirotor_beat_band_ratio": round(beat_ratio, 4),
            "piston_firing_band_ratio": round(piston_ratio, 4),
        }


# ============================================================================
# 4. REKONSTRUKCJA KINEMATYCZNA DOPPLERA (CPA) ORAZ BEAMFORMING MVDR + KALMAN
# ============================================================================

class KinematicAndSpatialSolver:
    """Solver trajektorii 3D z efektu Dopplera oraz lokalizator kątowy MVDR + Kalman."""

    def __init__(self, c_sound: float = 343.0) -> None:
        self.c_sound = c_sound

    def fit_doppler_cpa(
        self,
        times: np.ndarray,
        bpf_track: np.ndarray,
        n_blades: int = 2,
        flyby_window_s: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, float]:
        """Dopasowuje nieliniowy model przelotu Dopplera wokół punktu CPA."""
        if flyby_window_s is not None:
            mask = (times >= flyby_window_s[0]) & (times <= flyby_window_s[1])
        else:
            t_min, t_max = times[0], times[-1]
            span = t_max - t_min
            mask = (times >= t_min + 0.2 * span) & (times <= t_max - 0.2 * span)

        # FIX: flyby window outside a short clip left 0 frames -> IndexError on t_sub[0];
        # fall back to the whole track, and skip the 4-parameter fit when < 6 frames remain.
        if np.count_nonzero(mask) < 6:
            mask = np.ones_like(times, dtype=bool)
        # FIX: drop octave errors / STFT edge frames (> 20 % off the median) before the fit; one 2x frame
        # pulled a steady 150 Hz hover to "165.7 Hz, 121 km/h, CPA 1 m".
        med = float(np.median(bpf_track[mask])) if np.any(mask) else 0.0
        if med > 0.0:
            inl = mask & (np.abs(bpf_track - med) <= 0.2 * med)
            if np.count_nonzero(inl) >= 6:
                mask = inl
        t_sub = times[mask]
        f_sub = bpf_track[mask]
        if len(t_sub) < 6 or not np.all(np.isfinite(f_sub)) or float(np.median(f_sub)) <= 0.0:
            f0_est = float(np.median(f_sub)) if len(f_sub) else 0.0
            rpm_est = (f0_est * 60.0) / float(n_blades)
            return {
                "Intrinsic_BPF0_Hz": round(f0_est, 2),
                "Cruise_Rotor_RPM": round(rpm_est, 1),
                "Flight_Velocity_m_s": 0.0,
                "Flight_Velocity_km_h": 0.0,
                "CPA_Distance_m": 0.0,
                "CPA_Time_s": round(float(times[len(times) // 2]), 2) if len(times) else 0.0,
                "Doppler_Fit": 0.0,
            }

        def _doppler_func(t_val: np.ndarray, f0: float, v: float, d: float, t0: float) -> np.ndarray:
            x = v * (t_val - t0)
            r = np.sqrt(d ** 2 + x ** 2)
            v_r = v * x / (r + 1e-9)
            return f0 * (self.c_sound / (self.c_sound + v_r))

        f0_init = float(np.median(f_sub))
        t0_init = float(0.5 * (t_sub[0] + t_sub[-1]))

        try:
            popt, _ = curve_fit(
                _doppler_func,
                t_sub,
                f_sub,
                p0=[f0_init, 12.0, 15.0, t0_init],
                bounds=(
                    [0.7 * f0_init, 0.5, 1.0, t_sub[0]],
                    [1.3 * f0_init, 80.0, 500.0, t_sub[-1]],
                ),
                maxfev=5000,
                loss="soft_l1",  # FIX: robust loss, remaining outliers no longer dominate the fit
                f_scale=1.0,
            )
            f0_est, v_est, d_est, t0_est = [float(val) for val in popt]
            fit_ok = 1.0
        except Exception:
            f0_est, v_est, d_est, t0_est = f0_init, 0.0, 0.0, t0_init
            fit_ok = 0.0

        rpm_est = (f0_est * 60.0) / float(n_blades)
        return {
            "Intrinsic_BPF0_Hz": round(f0_est, 2),
            "Cruise_Rotor_RPM": round(rpm_est, 1),
            "Flight_Velocity_m_s": round(v_est, 2),
            "Flight_Velocity_km_h": round(v_est * 3.6, 1),
            "CPA_Distance_m": round(d_est, 2),
            "CPA_Time_s": round(t0_est, 2),
            "Doppler_Fit": fit_ok,  # FIX: 1.0 = fit converged, 0.0 = fallback values (was silent)
        }

    def mvdr_beamform_and_kalman_track(
        self,
        multichannel_audio: np.ndarray,
        sr: int,
        mic_positions_m: np.ndarray,
        target_freq_hz: float,
        frame_step_s: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Oblicza widmo przestrzenne MVDR (Capon) dla liniowej matrycy mikrofonowej ULA
        i filtruje sekwencję azymutu filtrem Kalmana o stałej prędkości kątowej.
        """
        n_mics, n_samples = multichannel_audio.shape
        step_samples = int(frame_step_s * sr)
        angles_deg = np.linspace(-90.0, 90.0, 181)
        angles_rad = np.deg2rad(angles_deg)

        # Wektory sterujące a(theta, f) dla matrycy liniowej
        tau_matrix = (
            mic_positions_m[:, None] * np.sin(angles_rad[None, :]) / self.c_sound
        )
        steering_vectors = np.exp(-1j * 2.0 * np.pi * target_freq_hz * tau_matrix)

        # Inicjalizacja Filtru Kalmana: stan xi = [theta, d_theta/dt]^T
        dt = frame_step_s
        F_mat = np.array([[1.0, dt], [0.0, 1.0]])
        H_mat = np.array([[1.0, 0.0]])
        Q_cov = np.array([[0.25, 0.0], [0.0, 1.0]])
        R_cov = np.array([[9.0]])
        state_xi = np.array([[0.0], [0.0]])
        P_cov = np.eye(2) * 25.0

        raw_azimuths: List[float] = []
        kalman_azimuths: List[float] = []

        for start in range(0, n_samples - step_samples, step_samples):
            chunk = multichannel_audio[:, start : start + step_samples]
            freqs_c = fft.rfftfreq(step_samples, d=1.0 / sr)
            spec_c = fft.rfft(chunk, axis=1)
            bin_idx = int(np.argmin(np.abs(freqs_c - target_freq_hz)))

            # Estymacja macierzy kowariancji przestrzennej R(f) z regularyzacją diagonalną
            x_vec = spec_c[:, max(0, bin_idx - 2) : min(spec_c.shape[1], bin_idx + 3)]
            R_spatial = (x_vec @ x_vec.conj().T) / float(x_vec.shape[1])
            R_spatial += 1e-3 * np.trace(R_spatial).real * np.eye(n_mics)
            R_inv = np.linalg.inv(R_spatial)

            # Widmo mocy MVDR: P(theta) = 1 / (a^H R^-1 a)
            denom = np.real(
                np.einsum("ij,jk,ki->i", steering_vectors.conj().T, R_inv, steering_vectors)
            )
            p_mvdr = 1.0 / (denom + 1e-12)
            meas_theta = float(angles_deg[int(np.argmax(p_mvdr))])
            raw_azimuths.append(round(meas_theta, 2))

            # Krok predykcji i aktualizacji Kalmana
            state_pred = F_mat @ state_xi
            P_pred = F_mat @ P_cov @ F_mat.T + Q_cov
            innovation = np.array([[meas_theta]]) - (H_mat @ state_pred)
            S_cov = H_mat @ P_pred @ H_mat.T + R_cov
            K_gain = P_pred @ H_mat.T @ np.linalg.inv(S_cov)
            state_xi = state_pred + K_gain @ innovation
            P_cov = (np.eye(2) - K_gain @ H_mat) @ P_pred
            kalman_azimuths.append(round(float(state_xi[0, 0]), 2))

        return {
            "array_elements": n_mics,
            "raw_azimuth_track_deg": raw_azimuths,
            "kalman_smoothed_azimuth_deg": kalman_azimuths,
            "final_Angular_Velocity_deg_s": round(float(state_xi[1, 0]), 2),
        }


# ============================================================================
# 5. ADAPTER GŁĘBOKICH SIECI AUDIO (PANNs CNN14 / HUGGINGFACE AST)
# ============================================================================

class DeepAudioBackboneAdapter:
    """
    Adapter integracyjny dla modeli neuronowych Audio Spectrogram Transformer (AST)
    oraz Pretrained Audio Neural Networks (PANNs CNN14).
    """

    def __init__(self, model_id: str = "MIT/ast-finetuned-audioset-10-10-0.4593") -> None:
        self.model_id = model_id
        self.backend_available = False
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            self.backend_available = True
        except ImportError:
            self.backend_available = False

    def compute_log_mel_spectrogram(
        self, y: np.ndarray, sr: int, n_mels: int = 64
    ) -> np.ndarray:
        """Generuje 1-sekundowe log-Mel spektrogramy zgodne z wejściem DroneCNN / AST."""
        _, _, zxx = signal.stft(y, fs=sr, nperseg=1024, noverlap=512)
        power = np.abs(zxx) ** 2
        n_freqs = power.shape[0]
        mel_bins = np.linspace(0, n_freqs - 1, n_mels + 2).astype(int)
        mel_spec = np.zeros((n_mels, power.shape[1]), dtype=np.float64)
        for m in range(1, n_mels + 1):
            f_start, _, f_end = mel_bins[m - 1], mel_bins[m], mel_bins[m + 1]
            if f_end > f_start:
                mel_spec[m - 1, :] = np.mean(power[f_start : f_end + 1, :], axis=0)
        return 10.0 * np.log10(mel_spec + 1e-10)

    def extract_embedding_metadata(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Zwraca deskryptory tensorowe log-Mel oraz status modelu AST/CNN14."""
        log_mel = self.compute_log_mel_spectrogram(y, sr, n_mels=64)
        return {
            "target_backbone": self.model_id,
            "torch_transformers_installed": self.backend_available,
            "log_mel_tensor_shape": list(log_mel.shape),
            "log_mel_mean_db": round(float(np.mean(log_mel)), 2),
            "log_mel_std_db": round(float(np.std(log_mel)), 2),
        }


# ============================================================================
# 6. GŁÓWNY ORKIESTRATOR AGENTA C-UAS (KLASYFIKACJA HYBRYDOWA I RAPORT JSON)
# ============================================================================

class UAVAcousticOrchestrator:
    """Główna klasa orkiestratora łącząca kondycjonowanie, fizykę, kinematykę i AI."""

    def __init__(self, sr: int = 48000) -> None:
        self.sr = sr
        self.conditioner = SignalConditioner(sr=sr)
        self.extractor = PhysicsFeatureExtractor(sr=sr)
        self.kinematics = KinematicAndSpatialSolver()
        self.deep_adapter = DeepAudioBackboneAdapter()

    def match_platform_catalog(
        self,
        bpf0_hz: float,
        n_blades: int,
        propulsion_category: str,
        observed_peaks_hz: List[float],
    ) -> List[Dict[str, Any]]:
        """Ocenia zgodność wyekstrahowanych parametrów fizycznych z katalogiem BSP."""
        candidates: List[Dict[str, Any]] = []
        for sig in UAV_SIGNATURE_CATALOG:
            score = 0.0
            if sig.category == propulsion_category:
                score += 35.0
            else:
                score -= 25.0

            if sig.n_blades == n_blades:
                score += 15.0

            if sig.bpf_range_hz[0] <= bpf0_hz <= sig.bpf_range_hz[1]:
                score += 20.0
            bpf_diff = abs(bpf0_hz - sig.nominal_cruise_bpf_hz)
            score += max(0.0, 20.0 * (1.0 - bpf_diff / 45.0))

            matched_peaks = 0
            for ref_p in sig.characteristic_peaks_hz:
                if any(abs(obs_p - ref_p) <= 6.0 for obs_p in observed_peaks_hz):
                    matched_peaks += 1
            peak_ratio = matched_peaks / float(len(sig.characteristic_peaks_hz))
            score += 10.0 * peak_ratio

            confidence = float(np.clip(score / 100.0, 0.01, 0.99))
            candidates.append(
                {
                    "model_name": sig.model_name,
                    "category": sig.category,
                    "match_confidence": round(confidence, 4),
                    "nominal_cruise_bpf_hz": sig.nominal_cruise_bpf_hz,
                    "mass_kg": sig.mass_kg,
                }
            )

        candidates.sort(key=lambda item: item["match_confidence"], reverse=True)
        return candidates

    def analyze_stream(
        self,
        raw_audio: np.ndarray,
        flyby_window_s: Optional[Tuple[float, float]] = (2.8, 9.2),
        multichannel_array: Optional[np.ndarray] = None,
        mic_positions_m: Optional[np.ndarray] = None,
    ) -> UAVTelemetryReport:
        """Wykonuje pełną analizę sygnału i zwraca raport telemetryczny dla C-UAS."""
        # FIX: accept int16 PCM, stereo (mixed to mono) and NaN/inf samples
        raw_audio = np.asarray(raw_audio)
        if raw_audio.dtype.kind in "iu":
            raw_audio = raw_audio.astype(np.float64) / float(np.iinfo(raw_audio.dtype).max)
        raw_audio = raw_audio.astype(np.float64)
        if raw_audio.ndim == 2:
            raw_audio = raw_audio.mean(axis=0 if raw_audio.shape[0] < raw_audio.shape[1] else 1)
        raw_audio = np.nan_to_num(raw_audio, nan=0.0, posinf=1.0, neginf=-1.0)
        if len(raw_audio) < self.conditioner.stft_nperseg:
            raise ValueError(
                "clip too short: %d samples, need >= %d" % (len(raw_audio), self.conditioner.stft_nperseg)
            )
        cond = self.conditioner.process(raw_audio)
        y_clean = cond["y_clean"]
        freqs = cond["freqs"]
        times = cond["times"]
        z_clean = cond["z_clean"]

        bpf_track, sfm_track = self.extractor.track_bpf_hps(freqs, z_clean)
        median_sfm = float(np.median(sfm_track))

        prelim_bpf = float(np.median(bpf_track))
        blade_info = self.extractor.analyze_blade_count_and_harmonics(
            y_clean, prelim_bpf
        )
        n_blades = blade_info["estimated_blades_nb"]

        doppler_res = self.kinematics.fit_doppler_cpa(
            times, bpf_track, n_blades=n_blades, flyby_window_s=flyby_window_s
        )
        bpf0_hz = doppler_res["Intrinsic_BPF0_Hz"]

        blade_info = self.extractor.analyze_blade_count_and_harmonics(
            y_clean, bpf0_hz
        )
        cepstrum_f0 = self.extractor.compute_real_cepstrum_f0(y_clean)
        mod_info = self.extractor.analyze_envelope_modulation(y_clean)

        def _mean_or_none(sel: np.ndarray) -> Optional[float]:
            # FIX: np.mean of an empty slice gave NaN (invalid JSON) for clips shorter than 9.5 s
            return round(float(np.mean(bpf_track[sel])), 2) if np.any(sel) else None

        flight_phases = [
            {
                "phase": "I: Zawis / Wznoszenie początkowe",
                "window_s": [0.0, 2.5],
                "mean_bpf_hz": _mean_or_none(times < 2.5),
            },
            {
                "phase": "II: Przelot poziomy (Doppler CPA)",
                "window_s": [2.5, 9.5],
                "intrinsic_bpf0_hz": bpf0_hz,
                "cpa_time_s": doppler_res["CPA_Time_s"],
            },
            {
                "phase": "III: Manewr wyhamowania / Odejście",
                "window_s": [9.5, round(float(times[-1]), 1)],
                "mean_bpf_hz": _mean_or_none(times >= 9.5),
            },
        ]

        candidates = self.match_platform_catalog(
            bpf0_hz=bpf0_hz,
            n_blades=n_blades,
            propulsion_category=mod_info["propulsion_type_inferred"],
            observed_peaks_hz=blade_info["dominant_low_freq_peaks_hz"],
        )
        best_match = candidates[0]
        uav_detected = bool(
            cond["snr_post_dsp_db"] > 5.0 and median_sfm < 0.65
        )

        spatial_res = None
        if multichannel_array is not None and mic_positions_m is not None:
            spatial_res = self.kinematics.mvdr_beamform_and_kalman_track(
                multichannel_array,
                sr=self.sr,
                mic_positions_m=mic_positions_m,
                target_freq_hz=bpf0_hz * 4.0,
            )

        deep_meta = self.deep_adapter.extract_embedding_metadata(y_clean, self.sr)

        # FIX: the catalog match score was reported as detection_confidence and a model name was given
        # even with uav_detected=False (white noise -> "Shahed-136", 0.76). Now 0.0 / "none" when not detected;
        # the raw catalog score stays in candidate_ranking and catalog_match_confidence.
        return UAVTelemetryReport(
            uav_detected=uav_detected,
            detection_confidence=best_match["match_confidence"] if uav_detected else 0.0,
            identified_model=best_match["model_name"] if uav_detected else "none",
            catalog_match_confidence=best_match["match_confidence"],
            propulsion_category=mod_info["propulsion_type_inferred"],
            candidate_ranking=candidates[:4],
            signal_quality={
                "clip_ratio": round(cond["clip_ratio"], 5),
                "snr_raw_est_db": cond["snr_raw_est_db"],
                "snr_post_dsp_db": cond["snr_post_dsp_db"],
                "snr_gain_db": cond["snr_gain_db"],
                "median_spectral_flatness": round(median_sfm, 4),
            },
            propulsion_physics={
                **blade_info,
                "cepstrum_f0_hz": cepstrum_f0,
                **mod_info,
            },
            kinematics_doppler=doppler_res,
            flight_phases=flight_phases,
            spatial_doa_tracking=spatial_res,
            deep_embedding_status=deep_meta,
        )


# ============================================================================
# 7. GENERATOR SYGNAŁU POLOWEGO I PUNKT WEJŚCIA DLA AGENTA (CLI / AUTOTEST)
# ============================================================================

def synthesize_field_recording_benchmark(
    sr: int = 48000, duration: float = 12.0
) -> np.ndarray:
    """Generuje polowy sygnał referencyjny przelotu DJI Phantom 4 Pro z artefaktami."""
    t = np.linspace(0.0, duration, int(sr * duration), endpoint=False)
    c_sound = 343.0
    v_uav, d_cpa, t_cpa = 14.5, 12.0, 6.5

    x_t = v_uav * (t - t_cpa)
    r_t = np.sqrt(d_cpa ** 2 + x_t ** 2)
    v_r = v_uav * x_t / r_t
    doppler = c_sound / (c_sound + v_r)

    rpm_base = np.piecewise(
        t,
        [t < 2.5, (t >= 2.5) & (t < 9.5), t >= 9.5],
        [
            lambda tau: 5400.0 + 180.0 * (tau / 2.5),
            lambda tau: 5856.0 + 15.0 * np.sin(2.0 * np.pi * 0.4 * tau),
            lambda tau: 5856.0 - 240.0 * (tau - 9.5),
        ],
    )

    rotor_offsets = [-42.0, +38.0, -19.0, +23.0]
    uav_sig = np.zeros_like(t)
    for m_idx, d_rpm in enumerate(rotor_offsets):
        f_rot = ((rpm_base + d_rpm) / 60.0) * doppler
        f_bpf = 2.0 * f_rot
        phase_rot = 2.0 * np.pi * np.cumsum(f_rot) / sr
        phase_bpf = 2.0 * np.pi * np.cumsum(f_bpf) / sr
        uav_sig += 0.16 * np.sin(phase_rot + m_idx * 0.7)
        for k in range(1, 19):
            env_k = (k ** -0.42) * (1.45 if 4 <= k <= 10 else 0.85)
            uav_sig += (0.38 / 4.0) * env_k * np.sin(k * phase_bpf + m_idx * k * 0.4)

    uav_sig *= d_cpa / r_t

    rng = np.random.default_rng(42)
    b_w, a_w = signal.butter(3, 75.0 / (sr / 2.0), btype="low")
    wind = signal.lfilter(b_w, a_w, rng.standard_normal(len(t))) * 1.6

    handling = np.zeros_like(t)
    for t_imp in [1.2, 4.1, 9.8]:
        idx = int(t_imp * sr)
        span = int(0.015 * sr)
        handling[idx : idx + span] = (
            2.4 * np.exp(-np.linspace(0, 8, span)) * rng.standard_normal(span)
        )

    b_t, a_t = signal.butter(2, [90.0 / (sr / 2.0), 550.0 / (sr / 2.0)], btype="band")
    traffic = signal.lfilter(b_t, a_t, rng.standard_normal(len(t))) * 0.22

    return np.clip(uav_sig + wind + handling + traffic, -1.0, 1.0)


def analyze_wav(path: str, start_s: float = 0.0, duration_s: Optional[float] = 12.0) -> UAVTelemetryReport:
    """Reads a PCM16 WAV (any sample rate, mono/stereo) and analyses [start_s, start_s + duration_s)."""
    import wave

    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        w.setpos(min(w.getnframes(), int(start_s * sr)))
        n = w.getnframes() - w.tell() if duration_s is None else int(duration_s * sr)
        raw = np.frombuffer(w.readframes(n), dtype="<i2")
    audio = raw.reshape(-1, ch).T if ch > 1 else raw
    return UAVAcousticOrchestrator(sr=sr).analyze_stream(audio)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:  # python cuas_reference.py plik.wav [start_s] [duration_s]
        rep = analyze_wav(
            sys.argv[1],
            float(sys.argv[2]) if len(sys.argv) > 2 else 0.0,
            float(sys.argv[3]) if len(sys.argv) > 3 else 12.0,
        )
        print(json.dumps(asdict(rep), indent=2, ensure_ascii=False))
        sys.exit(0)
    orchestrator = UAVAcousticOrchestrator(sr=48000)
    benchmark_signal = synthesize_field_recording_benchmark(sr=48000, duration=12.0)
    telemetry_report = orchestrator.analyze_stream(benchmark_signal)
    print(json.dumps(asdict(telemetry_report), indent=2, ensure_ascii=False))