"""Testy technik z raportu C-UAS (skyguard.cuas + CI/ICI/UKF)."""
import json
import math
import struct

import numpy as np
import pytest

from skyguard.cuas import (estimate_size, bpf_hz, rpm_from_bpf, UncertaintyWrapper, clopper_pearson_upper,
                           default_wrapper, detect_bpf_steps, threat_score, ThreatInput, alarm_colour, cpa, assess)
from skyguard.cuas import sapient as S, asterix as A, forensic as FR
from skyguard.cuas.profiles import default_model, size_class_of_diameter
from skyguard.fusion import covariance_intersection, inverse_covariance_intersection, naive_kalman_fusion, UKF
from skyguard.sim.drone_audio import synth_drone, DroneAudioConfig
from skyguard.dsp.harmonic import analyze_harmonics


# ------------------------------------------------------------------ profile
def test_bpf_formula():
    assert bpf_hz(6000, 2) == 200.0 and rpm_from_bpf(200.0, 2) == 6000.0


def test_profiles_fitted_on_real_data():
    m = default_model()
    assert -1.2 < m.b < -0.4                      # BPF maleje z rozmiarem śmigła
    names = {p.model for p in m.profiles}
    assert {"DJI Matrice 300 RTK", "DJI Mini 2", "DJI Phantom 4", "DJI S900"} <= names
    assert estimate_size(98).size_class == "heavy"      # Matrice 300
    assert estimate_size(315).size_class == "micro"     # Mini 2
    assert estimate_size(201).size_class == "consumer"  # Mavic 2 Enterprise
    e = estimate_size(150)
    assert abs(sum(e.class_probs.values()) - 1) < 1e-3 and e.nearest_models


def test_size_class_boundaries():
    assert size_class_of_diameter(5) == "micro" and size_class_of_diameter(21) == "heavy"


# ------------------------------------------------------------------ uncertainty wrapper
def test_clopper_pearson():
    assert clopper_pearson_upper(0, 0) == 1.0
    u = clopper_pearson_upper(0, 118, 0.95)
    assert abs(u - (1 - 0.05 ** (1 / 118))) < 1e-9   # przypadek k=0 ma postać zamkniętą
    assert clopper_pearson_upper(5, 40) > 5 / 40


def test_wrapper_learns_and_never_deletes_alarm():
    rng = np.random.default_rng(0)
    rows, wrong = [], []
    for _ in range(600):
        h = rng.uniform(0, 1)
        rows.append(dict(fz_max=rng.uniform(0.9, 1), harmonic_score=h, salience=rng.uniform(1, 4),
                         stability=rng.uniform(0, 1), spectral_entropy=rng.uniform(0.5, 1),
                         n_rotor_families=int(rng.integers(1, 6))))
        wrong.append(rng.uniform() < (0.6 if h < 0.5 else 0.02))
    w = UncertaintyWrapper().fit(rows, wrong)
    good = dict(rows[0], harmonic_score=0.9); bad = dict(rows[0], harmonic_score=0.1)
    assert w.uncertainty(good) < 0.1 < w.uncertainty(bad)
    assert w.gate(True, bad) == "DO_WERYFIKACJI" and w.gate(True, good) == "PEWNA"
    assert w.gate(False, good) == "BRAK"
    oos = dict(good, salience=1e6)  # poza zakresem danych uczących → nie ufamy
    assert w.uncertainty(oos) == 1.0
    w2 = UncertaintyWrapper.from_dict(json.loads(json.dumps(w.to_dict())))
    assert w2.uncertainty(good) == w.uncertainty(good)


def test_default_wrapper_shipped():
    w = default_wrapper()
    assert "loudness_lufs" not in w.factors and w.tree is not None


# ------------------------------------------------------------------ zrzut ładunku
def _two_level(f1, f2, seed=0, dur=6.0):
    a = synth_drone(dur, DroneAudioConfig(rotor_hz=f1, seed=seed), snr_db=0)
    b = synth_drone(dur, DroneAudioConfig(rotor_hz=f2, seed=seed + 1), snr_db=0)
    return analyze_harmonics(np.r_[a, b], 8000).track_hz


def test_payload_drop_detected():
    ev = detect_bpf_steps(_two_level(100, 80))
    assert ev and ev[0].kind == "spadek_bpf" and 5.0 < ev[0].t_s < 7.5


def test_payload_no_event_on_steady_and_octave_jump():
    assert detect_bpf_steps(_two_level(100, 100)) == []
    tr = np.r_[np.full(60, 100.0), np.full(60, 200.0)]   # skok toru wał→BPF (×2)
    assert detect_bpf_steps(tr) == []


# ------------------------------------------------------------------ zagrożenie i kolor
def test_cpa():
    d, t = cpa((1000, 0, 0), (-10, 0, 0))
    assert d == pytest.approx(0) and t == pytest.approx(100)
    d, t = cpa((100, 100, 0), (10, 0, 0))          # oddala się
    assert t == 0 and d == pytest.approx(math.hypot(100, 100))


def test_threat_levels():
    lo = threat_score(ThreatInput(size_class="micro", remote_id_seen=True))
    assert lo.level == 1
    hi = threat_score(ThreatInput(size_class="heavy", rel_pos_m=(500, 0, 50), rel_vel_ms=(-10, 0, 0),
                                  vz_ms=-4, protect_radius_m=150))
    assert hi.level == 5 and len(hi.reasons) == 5


def test_alarm_colour_three_sensor_rule():
    assert alarm_colour(3) == "CZERWONY"
    assert alarm_colour(2) == "ZOLTY_DO_WERYFIKACJI"
    assert alarm_colour(1) == "BRAK"
    assert alarm_colour(3, "DO_WERYFIKACJI") == "ZOLTY_DO_WERYFIKACJI"   # wątpliwa akustyka nie daje czerwieni


# ------------------------------------------------------------------ SAPIENT
def test_ulid():
    u = S.new_ulid(ts_ms=1762000000000)
    assert S.is_ulid(u) and S.new_ulid() != S.new_ulid()


def test_sapient_session_order_and_wire():
    n = S.SapientNode()
    with pytest.raises(S.SapientSequenceError):
        n.detection_report(object_id=S.new_ulid(), confidence=0.5, azimuth_deg=10)
    reg = S.to_wire(n.registration())
    (ln,) = struct.unpack("<I", reg[:4]); assert ln == len(reg) - 4
    assert S.from_payload(reg[4:])["registration"]["icd_version"] == S.ICD_VERSION
    assert n.state == "AWAITING_ACK"
    with pytest.raises(S.SapientSequenceError):   # rejestracja wysłana, ale bez ACK
        n.detection_report(object_id=S.new_ulid(), confidence=0.5, azimuth_deg=10)
    n.handle({"registration_ack": {"acceptance": True}})
    m = n.detection_report(object_id=S.new_ulid(), confidence=0.8, azimuth_deg=370.0, azimuth_err_deg=8,
                           classification=[{"type": "UAV", "confidence": 0.8}])
    w = S.to_wire(m)
    acc = S.FrameAccumulator()
    frames = acc.feed(w[:3]) + acc.feed(w[3:10]) + acc.feed(w[10:] + reg)
    assert len(frames) == 2
    d = S.from_payload(frames[0])["detection_report"]
    assert d["range_bearing"]["azimuth"] == pytest.approx(10.0)
    assert d["range_bearing"]["datum"] == S.RB_DATUM_TRUE
    assert d["classification"][0]["type"] == "UAV"


def test_sapient_semantic_checks():
    n = S.SapientNode(); n.registration(); n.handle({"registration_ack": {"acceptance": True}})
    with pytest.raises(S.SapientProtocolError):
        n.detection_report(object_id="nie-ulid", confidence=0.5, azimuth_deg=1)
    with pytest.raises(S.SapientProtocolError):
        n.detection_report(object_id=S.new_ulid(), confidence=1.5, azimuth_deg=1)
    with pytest.raises(S.SapientProtocolError):
        n.detection_report(object_id=S.new_ulid(), confidence=0.5)   # brak lokalizacji
    with pytest.raises(S.SapientProtocolError):
        S.FrameAccumulator(max_len=10).feed(struct.pack("<I", 1000))
    rej = S.SapientNode(); rej.registration()
    assert rej.handle({"registration_ack": {"acceptance": False, "ack_response_reason": ["x"]}}) == "REJECTED"


def test_sapient_golden_bytes():
    # wzorzec wygenerowany oficjalną biblioteką protobuf ze schematu dstl (tools/cuas-report/verify_sapient_protoc.py)
    m = {"timestamp": {"seconds": 1, "nanos": 0}, "node_id": "a",
         "detection_report": {"report_id": "r", "object_id": "o", "detection_confidence": 0.5,
                              "range_bearing": {"azimuth": 90.0, "coordinate_system": 1, "datum": 1}}}
    b = S.encode(m, S.SAPIENT_MESSAGE)
    assert b.hex() == "0a0208011201613a1a0a017212016f2a0d110000000000805640380140013d0000003f"


# ------------------------------------------------------------------ ASTERIX
def test_cat062_roundtrip_and_json():
    tr = dict(track_number=77, t=1762000123.5, lat=50.0612, lon=19.9376, alt_m=80.0, vx_e=-3.25, vy_n=7.5, vz=-2.0)
    blk = A.encode_cat062([tr, dict(tr, track_number=78)], sac=7, sic=9)
    assert blk[0] == 62 and struct.unpack(">H", blk[1:3])[0] == len(blk)
    r = A.decode_cat062(blk)
    assert len(r) == 2 and r[0]["track_number"] == 77 and r[1]["track_number"] == 78
    assert abs(r[0]["lat"] - 50.0612) < 1e-5 and r[0]["vx_e"] == -3.25 and abs(r[0]["alt_m"] - 80) < 2
    assert abs(r[0]["vz"] + 2.0) < 0.05
    j = A.cat062_json(tr, extra={"klasa": "consumer"})
    assert j["I062/040"] == 77 and j["SP"]["klasa"] == "consumer" and "I062/105" in j


def test_cat048_doppler_fixed_decoder():
    blk = A.encode_cat048_test_record(1, 2, 100.0, 5.0, 45.0, -12)
    r = A.decode_cat048(blk)[0]
    assert r["doppler_cal_ms"] == -12 and r["track_number"] == 123 and abs(r["theta_deg"] - 45) < 0.01
    # bit 0x40 drugiego oktetu FSPEC to I240 (FRN 9), nie I048/120 — błąd z raportu
    fspec = A._fspec({20})
    assert fspec[1] & 0x40 == 0 and fspec[2] & 0x04


# ------------------------------------------------------------------ łańcuch dowodowy
def test_forensic_chain(tmp_path):
    p = str(tmp_path / "log.jsonl")
    c = FR.ChainLog(p)
    for i in range(3):
        c.append({"n": i, "alarm": "ZOLTY"}, t=float(i))
    assert FR.verify(p) == (True, 3, "OK")
    lines = open(p).read().splitlines()
    lines[1] = lines[1].replace('"n": 1', '"n": 9')
    open(p, "w").write("\n".join(lines) + "\n")
    ok, n, msg = FR.verify(p)
    assert not ok and n == 1


# ------------------------------------------------------------------ fuzja CI / ICI / UKF
def test_ci_ici_consistent_under_correlation():
    rng = np.random.default_rng(1)
    Pa = np.diag([4.0, 1.0]); Pb = np.diag([1.0, 4.0])
    common = 0.8
    errs = {"ci": [], "ici": [], "naive": []}
    Ps = {}
    for _ in range(4000):
        c = rng.multivariate_normal([0, 0], common * np.eye(2))      # wspólny (skorelowany) błąd
        xa = c + rng.multivariate_normal([0, 0], Pa - common * np.eye(2))
        xb = c + rng.multivariate_normal([0, 0], Pb - common * np.eye(2))
        for k, f in (("ci", covariance_intersection), ("ici", inverse_covariance_intersection),
                     ("naive", naive_kalman_fusion)):
            out = f(xa, Pa, xb, Pb)
            errs[k].append(out[0]); Ps[k] = out[1]
    nees = {k: float(np.mean([e @ np.linalg.solve(Ps[k], e) for e in v])) for k, v in errs.items()}
    assert nees["ci"] <= 2.2 and nees["ici"] <= 2.2      # spójne (NEES ≤ wymiar)
    assert nees["naive"] > 2.2                          # naiwna fuzja zaniża niepewność
    assert np.trace(Ps["ici"]) <= np.trace(Ps["ci"]) + 1e-9   # ICI mniej zachowawcze


def test_ukf_range_bearing():
    dt = 1.0
    F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]])
    f = lambda x, dt: F @ x
    h = lambda x: np.array([math.hypot(x[0], x[1]), math.atan2(x[1], x[0])])
    def res(a, b):
        y = a - b; y[1] = (y[1] + math.pi) % (2 * math.pi) - math.pi; return y
    rng = np.random.default_rng(2)
    truth = np.array([300.0, -200.0, -4.0, 6.0])
    ukf = UKF([280, -180, 0, 0], np.diag([400, 400, 25, 25]), f, h, np.diag([0.1, 0.1, 0.05, 0.05]),
              np.diag([25.0, 0.02 ** 2]), residual_z=res)
    for _ in range(40):
        truth = F @ truth
        z = h(truth) + rng.normal(0, [5.0, 0.02])
        ukf.predict(dt); ukf.update(z)
    assert np.linalg.norm(ukf.x[:2] - truth[:2]) < 15 and np.linalg.norm(ukf.x[2:] - truth[2:]) < 1.5


# ------------------------------------------------------------------ całość
def test_assess_end_to_end():
    x = synth_drone(5.0, DroneAudioConfig(rotor_hz=100.0, seed=3), snr_db=10)
    r = assess(x, 8000, fz=True, fz_max=0.97)
    assert r["size"] is not None and r["sgfuzja"]["grade"] in ("PEWNA", "DO_WERYFIKACJI")
    assert isinstance(r["payload_events"], list)
