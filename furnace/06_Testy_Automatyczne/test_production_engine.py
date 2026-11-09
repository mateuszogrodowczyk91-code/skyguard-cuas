"""Original Furnace production-engine unit tests (portfolio packaging)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _cand in (
    _ROOT / "00_Master_Launcher",
    _ROOT / "02_Blackbox_PS4_Linux",
):
    s = str(_cand)
    if s not in sys.path:
        sys.path.insert(0, s)

from skyguard_production_engine_v7 import (  # noqa: E402
    ARUKFFilter,
    C4ISRFusionEngine,
    PassiveAcousticProcessor,
    PclSignalProcessor,
    SwarmTarget,
    audit_eu_ai_act_titan_m2,
)


class TestSkyGuardProductionEngineV8(unittest.TestCase):
    def test_pcl_eca_b(self) -> None:
        fs = 10e6
        n_samples = 5000
        pcl = PclSignalProcessor(fs=fs, f_carrier=600e6, n_samples=n_samples, max_delay_chips=20)
        t = np.arange(n_samples) / fs
        s_ref = np.exp(1j * 2 * np.pi * 1e6 * t).astype(np.complex64)
        s_surv = (
            0.5 * s_ref + 0.05 * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
        ).astype(np.complex64)
        s_clean = pcl.extensive_cancellation_algorithm_ecab(s_ref, s_surv)
        self.assertEqual(len(s_clean), n_samples)
        self.assertLess(np.mean(np.abs(s_clean) ** 2), np.mean(np.abs(s_surv) ** 2))

    def test_acoustic_tdoa_bpf(self) -> None:
        fs = 44100
        n_samples = 4410
        acoustic = PassiveAcousticProcessor(fs=fs, mic_distance=0.15)
        t = np.arange(n_samples) / fs
        sig1 = np.sin(2 * np.pi * 350 * t).astype(np.float32)
        sig2 = np.roll(sig1, 5)
        _tdoa, az = acoustic.gcc_phat_tdoa(sig1, sig2)
        bpf = acoustic.estimate_bpf_harmonic(sig1)
        self.assertIsInstance(az, float)
        self.assertGreater(bpf, 0)

    def test_arukf_filter(self) -> None:
        ukf = ARUKFFilter()
        ukf.predict()
        z = np.array([10.0, 50.0, 10.0])
        x_up, mahalanobis = ukf.update_adaptive(z)
        self.assertEqual(len(x_up), 6)
        self.assertGreaterEqual(mahalanobis, 0.0)

    def test_c4isr_cot_and_titan_m2(self) -> None:
        c4isr = C4ISRFusionEngine()
        target = SwarmTarget(
            target_id="UAV-TEST-01",
            position_enu=np.array([50.0, 100.0, 20.0]),
            velocity_enu=np.array([-30.0, -20.0, -10.0]),
            rf_signature="FPV_5.8GHz_ANALOG",
            acoustics_bpf=350.0,
            snr_db=25.0,
        )
        threat, intent, _rec = c4isr.evaluate_threat_score(target)
        self.assertGreaterEqual(threat, 50.0)
        self.assertIn(
            intent,
            [
                "KINETIC_ATTACK_KAMIKAZE",
                "RECONNAISSANCE_HOVERING",
                "AUTONOMOUS_DARK_DRONE_PENETRATION",
            ],
        )
        cot_xml = c4isr.generate_cot_xml(target, threat, intent)
        self.assertIn("<event", cot_xml)
        self.assertIn("UAV-TEST-01", cot_xml)
        pelco_hex = c4isr.generate_pelco_d_hex(pan_deg=15.0, tilt_deg=10.0)
        self.assertTrue(pelco_hex.startswith("FF01"))
        titan_hash = audit_eu_ai_act_titan_m2(cot_xml)
        self.assertEqual(len(titan_hash), 64)


if __name__ == "__main__":
    unittest.main()
