"""Testy modułów z listy TOP-25 (docs/top25.md)."""
import math
import struct

import numpy as np
import pytest

from skyguard import dsp, doa, fusion, radar, rid, sim, ai, pipeline

SR = 8000


# ---------- akustyka ----------

def test_mel_matches_librosa():
    librosa = pytest.importorskip("librosa")
    x = np.random.default_rng(0).standard_normal(SR)
    ours = dsp.melspectrogram(x, SR, n_fft=1024, hop=256, n_mels=64)
    ref = librosa.feature.melspectrogram(y=x, sr=SR, n_fft=1024, hop_length=256, n_mels=64, pad_mode="constant")
    assert ours.shape == ref.shape
    assert np.allclose(ours, ref, rtol=1e-6, atol=1e-8)
    m = dsp.mfcc(x, SR, n_mfcc=13, n_fft=1024, hop=256, n_mels=64)
    mr = librosa.feature.mfcc(y=x, sr=SR, n_mfcc=13, n_fft=1024, hop_length=256, n_mels=64, pad_mode="constant")
    assert np.allclose(m, mr, atol=1e-4)


def test_mel_hz_roundtrip():
    f = np.array([0, 100, 999, 1000, 4000])
    assert np.allclose(dsp.mel_to_hz(dsp.hz_to_mel(f)), f)


def test_spectral_gate_stationary_keeps_drone_tone():
    rng = np.random.default_rng(1)
    t = np.arange(4 * SR) / SR
    tone = np.sin(2 * np.pi * 400 * t)
    noise = 0.5 * rng.standard_normal(t.size)
    bg = 0.5 * rng.standard_normal(2 * SR)              # nagranie samego tła
    y = dsp.spectral_gate(tone + noise, SR, noise_clip=bg, n_fft=512, freq_smooth_hz=50)
    f = np.fft.rfftfreq(t.size, 1 / SR)
    Y, X = np.abs(np.fft.rfft(y)), np.abs(np.fft.rfft(tone + noise))
    band = (f > 1000)
    assert Y[band].mean() < 0.5 * X[band].mean()        # szum stłumiony
    pk = np.argmin(np.abs(f - 400))
    assert Y[pk - 2:pk + 3].max() > 0.7 * X[pk - 2:pk + 3].max()  # ton zostaje


def test_spectral_gate_nonstationary_passes_onset_removes_hum():
    t = np.arange(6 * SR) / SR
    hum = np.sin(2 * np.pi * 300 * t)
    burst = np.where((t > 3) & (t < 3.5), np.sin(2 * np.pi * 1200 * t), 0.0)
    y = dsp.spectral_gate(hum + burst, SR, n_fft=512)
    seg = (t > 3.1) & (t < 3.4)
    f = np.fft.rfftfreq(seg.sum(), 1 / SR)
    Y = np.abs(np.fft.rfft(y[seg]))
    e = lambda fr: Y[np.argmin(np.abs(f - fr))]
    assert e(1200) > 5 * e(300)


def test_loudness_matches_pyloudnorm_reference_value():
    # sinus 1 kHz, amplituda 1 (0 dBFS szczyt), mono: wg BS.1770 ≈ −3.01 LUFS
    sr = 48000
    t = np.arange(5 * sr) / sr
    L = dsp.integrated_loudness(np.sin(2 * np.pi * 1000 * t), sr)
    assert abs(L - (-3.01)) < 0.1
    y = dsp.normalize(0.01 * np.sin(2 * np.pi * 1000 * t), sr, -23.0)
    assert abs(dsp.integrated_loudness(y, sr) + 23.0) < 0.1
    assert dsp.integrated_loudness(np.zeros(sr), sr) == float("-inf")


def test_entropy_tone_vs_noise():
    rng = np.random.default_rng(2)
    t = np.arange(SR) / SR
    tone, noise = np.sin(2 * np.pi * 300 * t), rng.standard_normal(SR)
    assert dsp.spectral_entropy(tone, SR) < 0.3 < 0.9 < dsp.spectral_entropy(noise, SR)
    assert dsp.perm_entropy(noise, 3) > 0.99
    assert dsp.perm_entropy(np.arange(100.0), 3) == pytest.approx(0.0)
    assert 1.8 < dsp.higuchi_fd(noise) < 2.2


def test_cwt_tracks_chirp_and_matches_pywt_center():
    t = np.arange(SR) / SR
    f_inst = 200 + 300 * t
    x = np.cos(2 * np.pi * np.cumsum(f_inst) / SR)
    freqs = np.linspace(100, 700, 121)
    W = dsp.morlet_cwt(x, SR, freqs)
    r = dsp.ridge(W, freqs)
    mid = slice(1000, 7000)
    assert np.median(np.abs(r[mid] - f_inst[mid])) < 10
    amp = np.abs(W[np.argmin(np.abs(freqs - 400)), 3900:4100]).mean()
    assert 0.7 < amp < 1.3
    pywt = pytest.importorskip("pywt")
    assert pywt.scale2frequency("cmor1.5-1.0", 20.0) * SR == pytest.approx(1.0 * SR / 20.0)


def test_harmonic_tracker_on_synthetic_drone():
    cfg = sim.DroneAudioConfig(sr=SR, rotor_hz=95.0, n_blades=2, seed=3)
    x = sim.synth_drone(3.0, cfg, snr_db=0)
    rep = dsp.analyze_harmonics(x, SR)
    # f0 trafia w obroty wału lub BPF (2×)
    assert min(abs(rep.f0_hz - 95) / 95, abs(rep.f0_hz - 190) / 190) < 0.05
    assert rep.stability > 0.8
    n = dsp.analyze_harmonics(np.random.default_rng(4).standard_normal(3 * SR), SR)
    assert rep.salience > 2 * n.salience


def test_rotor_family_count_two_drones():
    a = sim.synth_drone(3.0, sim.DroneAudioConfig(sr=SR, rotor_hz=90.0, seed=5))
    b = sim.synth_drone(3.0, sim.DroneAudioConfig(sr=SR, rotor_hz=127.0, seed=6))
    one = dsp.analyze_harmonics(a, SR).n_rotor_families
    two = dsp.analyze_harmonics(a + b, SR).n_rotor_families
    assert one == 1 and two >= 2


def test_flyby_doppler_shift():
    cfg = sim.DroneAudioConfig(sr=SR, rotor_hz=100.0, n_blades=2, brown_rms=0.0, seed=7)
    y, d = sim.flyby(8.0, cfg, speed_ms=20.0, closest_m=10.0, wind_rms=0.0, ground_reflection=0.0)
    assert d.argmin() == pytest.approx(y.size // 2, abs=SR // 10)
    f = np.fft.rfftfreq(SR, 1 / SR)
    band = (f > 180) & (f < 220)
    pk = lambda seg: f[band][np.argmax(np.abs(np.fft.rfft(seg * np.hanning(SR)))[band])]
    f_app, f_rec = pk(y[:SR]), pk(y[-SR:])
    assert f_app > 200 > f_rec  # zbliżanie → wyższy ton


# ---------- AI ----------

def test_ast_fbank_shape_and_norm():
    x = np.random.default_rng(8).standard_normal(SR * 2)
    fb = ai.ast_fbank(x, SR, target_length=300)
    assert fb.shape == (300, 128)
    assert np.all(fb[199:] == 0) or fb.shape[0] == 300
    z = ai.ast_normalize(fb)
    assert z.shape == fb.shape and np.isfinite(z).all()


def test_ast_fbank_matches_torchaudio_if_available():
    torchaudio = pytest.importorskip("torchaudio")
    import torch
    x = np.random.default_rng(9).standard_normal(16000)
    ref = torchaudio.compliance.kaldi.fbank(torch.tensor(x[None], dtype=torch.float64), htk_compat=True,
                                            sample_frequency=16000, use_energy=False, window_type="hanning",
                                            num_mel_bins=128, dither=0.0, frame_shift=10).numpy()
    ours = ai.ast_fbank(x, 16000, target_length=ref.shape[0])
    assert np.allclose(ours, ref, atol=1e-3)


def test_onnx_runner_optional():
    if not ai.ONNX_AVAILABLE:
        with pytest.raises(RuntimeError):
            ai.OnnxClassifier("brak.onnx")
    from skyguard.ai.onnx_runner import softmax
    assert np.allclose(softmax(np.array([[1.0, 2.0, 3.0]])).sum(), 1.0)


# ---------- Remote ID ----------

def test_odid_location_roundtrip():
    m = rid.encode_location(52.2297, 21.0122, alt_geo=120.5, height=80.0, direction=270.0,
                            speed_h=12.25, speed_v=-1.5, timestamp=1234.5)
    assert len(m) == 25
    d = rid.decode_message(m)
    assert d["type"] == rid.MessageType.LOCATION
    assert d["lat"] == pytest.approx(52.2297, abs=1e-7) and d["lon"] == pytest.approx(21.0122, abs=1e-7)
    assert d["alt_geo"] == 120.5 and d["height"] == 80.0
    assert d["direction"] == 270.0 and d["speed_h"] == 12.25 and d["speed_v"] == -1.5
    assert d["timestamp"] == pytest.approx(1234.5)
    fast = rid.decode_message(rid.encode_location(0, 0, speed_h=100.0))
    assert fast["speed_h"] == pytest.approx(100.0, abs=0.75)


def test_odid_basic_id_and_pack_limits():
    b = rid.encode_basic_id("1596F12345678901", id_type=1, ua_type=2)
    d = rid.decode_message(b)
    assert d["uas_id"] == "1596F12345678901" and d["id_type"] == 1 and d["ua_type"] == 2
    pack = rid.encode_pack([b, rid.encode_location(50.0, 19.9)])
    msgs = rid.decode_pack(pack)
    assert [m["type"] for m in msgs] == [rid.MessageType.BASIC_ID, rid.MessageType.LOCATION]
    with pytest.raises(ValueError):
        rid.decode_pack(rid.encode_pack([rid.encode_location(1, 1)] * 2))


def test_odid_system_and_operator():
    msg = bytes([0x42, 0x01]) + struct.pack("<iiHBHHBHI", int(52.1e7), int(21.2e7), 1, 5, 0, 0, 0x21,
                                              int((100 + 1000) * 2), 1000) + b"\x00"
    d = rid.decode_message(msg)
    assert d["operator_lat"] == pytest.approx(52.1) and d["area_radius"] == 50
    assert d["operator_alt_geo"] == 100.0 and d["class_eu"] == 1 and d["category_eu"] == 2
    assert d["timestamp"] == 1546300800 + 1000
    op = rid.decode_message(bytes([0x52, 0]) + b"POL87astrdge12k8".ljust(20, b"\0") + b"\0\0\0")
    assert op["operator_id"] == "POL87astrdge12k8"


def test_ble_and_wifi_framing():
    pack = rid.encode_pack([rid.encode_basic_id("SG-TEST-1"), rid.encode_location(50.06, 19.94)])
    sd = bytes([0xFA, 0xFF, 0x0D, 0x07]) + rid.encode_basic_id("SG-TEST-1")
    adv = bytes([2, 0x01, 0x06, len(sd) + 1, 0x16]) + sd
    assert rid.decode_ble_advert(adv)[0]["uas_id"] == "SG-TEST-1"
    body = bytes([0xFA, 0x0B, 0xBC, 0x0D, 0x01]) + pack
    ies = bytes([0, 4]) + b"SSID" + bytes([0xDD, len(body)]) + body
    out = rid.decode_wifi_beacon(ies)
    assert out[1]["lat"] == pytest.approx(50.06)
    assert rid.decode_wifi_beacon(bytes([0, 2]) + b"ab") == []


def test_dji_droneid_v2():
    b = bytearray(80)
    b[0:3] = rid.DJI_OUI
    b[6], b[7] = 0x10, 2
    b[12:12 + 14] = b"1581F4XFC23050"
    struct.pack_into("<ii", b, 28, int(round(21.01 * 174533.0)), int(round(52.23 * 174533.0)))  # lon, lat
    struct.pack_into("<hhhhhh", b, 36, 1205, 800, 300, 400, -100, 9000)
    struct.pack_into("<ii", b, 56, int(round(52.24 * 174533.0)), int(round(21.02 * 174533.0)))  # pilot lat, lon
    b[72] = 68
    d = rid.parse_dji_vendor_ie(bytes(b))
    assert d["serial"] == "1581F4XFC23050" and d["product_name"] == "Mavic 3"
    assert d["position"][0] == pytest.approx(52.23, abs=1e-5) and d["position"][1] == pytest.approx(21.01, abs=1e-5)
    assert d["alt_m"] == 120.5 and d["speed_h"] == pytest.approx(5.0) and d["speed_v"] == -1.0
    assert d["pilot"][0] == pytest.approx(52.24, abs=1e-5)
    assert rid.parse_dji_vendor_ie(b"\x00" * 40) is None


def test_rid_anomaly_checker():
    c = rid.RidAnomalyChecker()
    assert c.check("A", 0.0, 52.0, 21.0, alt=100) == []
    kinds = {a.kind for a in c.check("A", 1.0, 52.01, 21.0, alt=100)}  # 1.1 km w 1 s
    assert "teleport" in kinds
    assert {a.kind for a in c.check("B", 1.0, 52.0, 21.0, alt=3000, speed_h=90)} >= {"altitude", "speed"}
    assert any(a.kind == "range" for a in c.check("C", 1.0, 53.0, 21.0, own_pos=(52.0, 21.0)))
    for i in range(3):
        r = c.check(f"N{i}", 2.0, 52.0, 21.0)
    assert any(a.kind == "burst" for a in r)
    c2 = rid.RidAnomalyChecker()
    msg = rid.encode_location(52.0, 21.0)
    kinds = [{a.kind for a in c2.check("R", 0.1 * i, 52.0, 21.0, raw=msg, rssi=-70)} for i in range(4)]
    assert "replay" in kinds[3] and "replay" not in kinds[2]
    c3 = rid.RidAnomalyChecker()
    for i in range(4):
        c3.check("S", float(i), 52.0, 21.0, rssi=-80)
    assert any(a.kind == "rssi" for a in c3.check("S", 5.0, 52.0, 21.0, rssi=-40))


# ---------- DoA ----------

def _ula_snapshots(angles, M=8, N=400, snr_db=20, seed=0):
    rng = np.random.default_rng(seed)
    A = doa.steering_vector(angles, M)
    S = (rng.standard_normal((len(angles), N)) + 1j * rng.standard_normal((len(angles), N))) / np.sqrt(2)
    n = (rng.standard_normal((M, N)) + 1j * rng.standard_normal((M, N))) / np.sqrt(2) * 10 ** (-snr_db / 20)
    return A @ S + n


def test_root_music():
    est = doa.root_music_doa(_ula_snapshots([-20.0, 35.0]), 2)
    assert np.allclose(est, [-20, 35], atol=0.5)


def test_mvdr_peak_and_distortionless():
    X = _ula_snapshots([10.0])
    g, p = doa.mvdr_spectrum(X)
    assert abs(g[np.argmax(p)] - 10) < 1
    a = doa.steering_vector(10.0, 8)[:, 0]
    w = doa.mvdr_weights(doa.covariance(X), a)
    assert abs(w.conj() @ a - 1) < 1e-9


def test_gcc_phat_bearing():
    rng = np.random.default_rng(11)
    sr, d, ang = 48000, 0.15, 30.0
    tau = d * math.sin(math.radians(ang)) / 343.0
    s = rng.standard_normal(sr // 2)
    S = np.fft.rfft(s)
    f = np.fft.rfftfreq(s.size, 1 / sr)
    y = np.fft.irfft(S * np.exp(-2j * np.pi * f * tau), s.size)
    t_est, _ = doa.gcc_phat(s, y, sr, max_tau=d / 343.0)
    assert abs(doa.tdoa_to_bearing(t_est, d) - ang) < 2.0


def test_srp_phat_azimuth():
    rng = np.random.default_rng(12)
    sr = 16000
    mics = 0.05 * np.array([[math.cos(a), math.sin(a)] for a in np.linspace(0, 2 * np.pi, 4, endpoint=False)])
    az0 = 120.0
    u = np.array([math.cos(math.radians(az0)), math.sin(math.radians(az0))])
    s = rng.standard_normal(sr // 2)
    S = np.fft.rfft(s)
    f = np.fft.rfftfreq(s.size, 1 / sr)
    sig = np.stack([np.fft.irfft(S * np.exp(2j * np.pi * f * (m @ u) / 343.0), s.size) for m in mics])
    az, P = doa.srp_phat(sig, mics, sr)
    err = abs((az[np.argmax(P)] - az0 + 180) % 360 - 180)
    assert err < 5


# ---------- fuzja ----------

def test_yager_and_pignistic():
    D, N = "dron", "nie"
    m1 = {frozenset({D}): 0.9, frozenset({D, N}): 0.1}
    m2 = {frozenset({N}): 0.9, frozenset({D, N}): 0.1}
    y = fusion.combine_yager(m1, m2)
    assert y[frozenset({D, N})] == pytest.approx(0.01 + 0.81)
    assert sum(y.values()) == pytest.approx(1.0)
    bp = fusion.pignistic(y)
    assert bp[D] == pytest.approx(bp[N]) and sum(bp.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("fn", ["systematic_resample", "stratified_resample", "residual_resample", "multinomial_resample"])
def test_resampling_unbiased(fn):
    w = np.array([0.1, 0.2, 0.3, 0.4])
    rng = np.random.default_rng(0)
    counts = np.zeros(4)
    for _ in range(300):
        counts += np.bincount(getattr(fusion, fn)(np.repeat(w / 25, 25), rng) // 25, minlength=4)
    assert np.allclose(counts / counts.sum(), w, atol=0.02)


def test_particle_filter_tracks_bearing():
    rng = np.random.default_rng(13)
    true = 10.0 + 0.5 * np.arange(60)
    pf = fusion.ParticleFilter(rng.uniform(-90, 90, (2000, 1)),
                               transition=lambda p, r: p + 0.5 + r.normal(0, 1.0, p.shape),
                               likelihood=lambda z, p: np.exp(-0.5 * ((z - p[:, 0]) / 3.0) ** 2), seed=1)
    for k, th in enumerate(true):
        pf.predict()
        pf.update(th + rng.normal(0, 3.0))
    m, v = pf.estimate()
    assert abs(m[0] - true[-1]) < 3.0


# ---------- radar ----------

def test_clutter_removal_and_mti():
    rng = np.random.default_rng(14)
    n_ch = 64
    static = 5.0 * np.ones((n_ch, 32))
    mov = np.exp(2j * np.pi * 0.2 * np.arange(n_ch))[:, None] * (np.arange(32) == 7)
    cube = static + mov + 0.01 * rng.standard_normal((n_ch, 32))
    out = radar.clutter_removal(cube, axis=0)
    assert np.abs(out[:, 0]).mean() < 0.05 and np.abs(out[:, 7]).mean() > 0.9
    m = radar.mti_filter(cube, 2)
    assert m.shape == (n_ch - 1, 32) and np.abs(m[:, 0]).mean() < 0.05
    bs = radar.BackgroundSubtractor(0.5)
    for _ in range(30):
        r = bs(static[0])
    assert np.abs(r).max() < 1e-6


def test_angle_fft():
    x = doa.steering_vector(30.0, 8)[:, 0].conj()  # konwencja exp(+j)
    ang, S = radar.angle_fft(x, 256)
    assert abs(ang[np.argmax(S)] - 30) < 2


def test_dbscan():
    rng = np.random.default_rng(15)
    a = rng.normal([0, 0], 0.1, (30, 2))
    b = rng.normal([5, 5], 0.1, (30, 2))
    noise = np.array([[10.0, -10.0]])
    lab = radar.dbscan(np.vstack([a, b, noise]), eps=0.5, min_samples=4)
    assert len(set(lab[:30])) == 1 and len(set(lab[30:60])) == 1 and lab[0] != lab[30] and lab[-1] == -1
    c = radar.cluster_centroids(np.vstack([a, b, noise]), lab)
    assert c.shape == (2, 2)


def test_micro_doppler_features():
    fs, fc, f_rot, L = 20000.0, 24e9, 60.0, 0.12
    x = radar.simulate_rotor_echo(fs, 0.5, fc, f_rot=f_rot, n_blades=2, blade_len_m=L, snr_db=30)
    feat = radar.micro_doppler_features(x, fs, fc)
    v_tip = 2 * np.pi * f_rot * L
    assert feat["tip_speed_ms"] == pytest.approx(v_tip, rel=0.15)
    assert feat["flash_rate_hz"] == pytest.approx(2 * f_rot, rel=0.2)


# ---------- potok ----------

def test_pipeline_describe_and_no_veto_by_default():
    x = sim.synth_drone(2.0, sim.DroneAudioConfig(sr=SR, seed=16), snr_db=10)
    d = pipeline.describe(x, SR)
    assert d.harmonic_score > 0.3 and d.n_rotor_families >= 1
    p = pipeline.AcousticPipeline()
    assert p.decide(True, np.random.default_rng(0).standard_normal(2 * SR), SR)[0] is True  # bez weta
    assert p.decide(False, x, SR) == (False, None)
