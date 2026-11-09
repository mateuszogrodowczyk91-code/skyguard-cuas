"""Tests for cuas_reference.py (run: python -m pytest -q test_cuas_reference.py; needs numpy + scipy)."""
import glob, json, os, re
from dataclasses import asdict

import numpy as np
import pytest

import cuas_reference as C

HERE = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.environ.get("SKYGUARD_EVIDENCE", "/workspace/evidence")


def as_json(rep):
    return json.loads(json.dumps(asdict(rep), allow_nan=False, ensure_ascii=False))  # NaN -> ValueError


def quadcopter(sr, bpf=150.0, dur=12.0, snr_noise=0.05, seed=0):
    """4 rotors, 2 blades: shaft 75 Hz + BPF 150 Hz harmonics, small per-rotor RPM spread, light noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(sr * dur)) / sr
    x = np.zeros_like(t)
    for m, d in enumerate([-1.2, 0.8, -0.4, 0.6]):
        f = bpf + d
        x += 0.05 * np.sin(2 * np.pi * f / 2 * t + m)
        for k in range(1, 12):
            if k * f < sr / 2 - 100:
                x += 0.08 * k ** -0.5 * np.sin(2 * np.pi * k * f * t + 0.3 * m * k)
    return x + snr_noise * rng.standard_normal(len(t))


def test_no_paste_garbage_in_source():
    src = open(os.path.join(HERE, "cuas_reference.py"), encoding="utf-8").read()
    assert not re.search(r"\[span_\d+\]|start_span|end_span", src)


@pytest.mark.parametrize("sr", [48000, 8000])
def test_synthetic_quadcopter_150hz_detected(sr):
    rep = C.UAVAcousticOrchestrator(sr=sr).analyze_stream(quadcopter(sr), flyby_window_s=None)
    j = as_json(rep)
    assert j["uav_detected"] is True
    assert j["propulsion_category"] == "multirotor_electric"
    assert abs(j["kinematics_doppler"]["Intrinsic_BPF0_Hz"] - 150.0) < 3.0
    assert j["propulsion_physics"]["estimated_blades_nb"] == 2
    assert abs(j["kinematics_doppler"]["Cruise_Rotor_RPM"] - 4500.0) < 100.0


def test_builtin_benchmark_flyby():
    x = C.synthesize_field_recording_benchmark(sr=48000, duration=12.0)
    j = as_json(C.UAVAcousticOrchestrator(sr=48000).analyze_stream(x))
    k = j["kinematics_doppler"]
    assert j["uav_detected"] is True
    assert j["identified_model"] == "DJI Phantom 4 Pro"
    assert abs(k["Flight_Velocity_m_s"] - 14.5) < 2.0       # generator: 14.5 m/s
    assert abs(k["CPA_Time_s"] - 6.5) < 0.5                 # generator: CPA at 6.5 s
    assert abs(k["CPA_Distance_m"] - 12.0) < 4.0            # generator: 12 m


@pytest.mark.parametrize("sr", [48000, 8000])
def test_white_noise_not_detected(sr):
    x = 0.1 * np.random.default_rng(1).standard_normal(sr * 12)
    j = as_json(C.UAVAcousticOrchestrator(sr=sr).analyze_stream(x))
    assert j["uav_detected"] is False
    assert j["detection_confidence"] == 0.0 and j["identified_model"] == "none"


def test_short_clip_and_digital_silence_do_not_crash():
    o = C.UAVAcousticOrchestrator(sr=8000)
    as_json(o.analyze_stream(quadcopter(8000, dur=2.0)))            # was IndexError (flyby window 2.8-9.2 s)
    x = np.concatenate([quadcopter(8000, dur=3.0), np.zeros(8000 * 3)])
    as_json(o.analyze_stream(x))                                     # was math domain error
    as_json(o.analyze_stream((quadcopter(8000) * 20000).astype(np.int16)))  # int16 PCM accepted
    with pytest.raises(ValueError):
        o.analyze_stream(np.zeros(1000))


def test_mvdr_kalman_finds_plane_wave_direction():
    sr, f, theta = 8000, 600.0, 30.0
    pos = np.arange(4) * 0.25                                        # 4-mic ULA, 25 cm
    t = np.arange(sr * 3) / sr
    rng = np.random.default_rng(2)
    tau = pos * np.sin(np.deg2rad(theta)) / 343.0
    multi = np.stack([np.sin(2 * np.pi * f * (t - d)) + 0.05 * rng.standard_normal(len(t)) for d in tau])
    res = C.KinematicAndSpatialSolver().mvdr_beamform_and_kalman_track(multi, sr, pos, f)
    assert abs(np.median(res["raw_azimuth_track_deg"]) - theta) <= 3.0
    assert abs(res["kalman_smoothed_azimuth_deg"][-1] - theta) <= 5.0


EVIDENCE_FILES = sorted(glob.glob(os.path.join(EVIDENCE, "*", "SG_*.wav")))


@pytest.mark.skipif(not EVIDENCE_FILES, reason="no camera recordings in " + EVIDENCE)
@pytest.mark.parametrize("name,start", [("SG_2026-10-29_23-00-02.wav", 529.0),           # 'kropka' 23:09 event
                                        ("SG_2026-10-29_22-50-19_snapshot.wav", 204.0)])  # 22:53:49 event
def test_runs_on_camera_evidence(name, start):
    paths = [p for p in EVIDENCE_FILES if os.path.basename(p) == name]
    if not paths:
        pytest.skip(name + " missing")
    j = as_json(C.analyze_wav(paths[0], start, 12.0))
    assert isinstance(j["uav_detected"], bool)
    assert 70.0 <= j["kinematics_doppler"]["Intrinsic_BPF0_Hz"] <= 360.0 * 1.3
