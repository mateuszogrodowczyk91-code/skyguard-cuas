"""Extra coverage for config loader and production-engine helpers."""
from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "00_Master_Launcher"))

from lib.skyguard_config import SkyguardSettings, load_env_file  # noqa: E402
from skyguard_production_engine_v7 import (  # noqa: E402
    ARUKFFilter,
    C4ISRFusionEngine,
    PassiveAcousticProcessor,
    PclSignalProcessor,
    SwarmTarget,
    audit_eu_ai_act_titan_m2,
)


class TestConfig(unittest.TestCase):
    def test_load_env_does_not_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skyguard.env"
            path.write_text("BLACKBOX_PORT=1111\nREF_LAT=50.0\n", encoding="utf-8")
            env = {"BLACKBOX_PORT": "2222"}
            load_env_file(path, env)
            self.assertEqual(env["BLACKBOX_PORT"], "2222")
            self.assertEqual(env["REF_LAT"], "50.0")

    def test_settings_from_environ(self) -> None:
        settings = SkyguardSettings.from_environ(
            {
                "SKYGUARD_EMULATION": "true",
                "BLACKBOX_PORT": "19090",
                "REF_LAT": "51.98",
                "REF_LON": "5.90",
                "ENABLE_PIXEL_TRACKER": "false",
                "PTZ_CAMERA_PASSWORD": "",
                "GEMINI_API_KEY": "",
            }
        )
        self.assertTrue(settings.emulation)
        self.assertEqual(settings.blackbox_port, 19090)
        self.assertFalse(settings.enable_pixel)
        self.assertEqual(settings.gemini_api_key, "")


class TestEngineExtras(unittest.TestCase):
    def test_caf_shape(self) -> None:
        pcl = PclSignalProcessor(fs=1e6, f_carrier=600e6, n_samples=2048, max_delay_chips=16)
        t = np.arange(2048) / 1e6
        s_ref = np.exp(1j * 2 * np.pi * 1e5 * t).astype(np.complex64)
        s_surv = (0.4 * s_ref).astype(np.complex64)
        clean = pcl.extensive_cancellation_algorithm_ecab(s_ref, s_surv)
        delays = np.arange(0, 8, dtype=int)
        dopplers = np.array([-100.0, 0.0, 100.0])
        caf = pcl.compute_fast_fft_caf(s_ref, clean, delays, dopplers)
        self.assertEqual(caf.shape, (len(dopplers), len(delays)))

    def test_pelco_and_threat_bounds(self) -> None:
        c4isr = C4ISRFusionEngine()
        hex_cmd = c4isr.generate_pelco_d_hex(pan_deg=0.0, tilt_deg=0.0)
        self.assertTrue(hex_cmd.startswith("FF01"))
        target = SwarmTarget(
            target_id="T-1",
            position_enu=np.array([10.0, 10.0, 5.0]),
            velocity_enu=np.array([1.0, 0.0, 0.0]),
            rf_signature="UNKNOWN",
            acoustics_bpf=200.0,
            snr_db=5.0,
        )
        threat, intent, _rec = c4isr.evaluate_threat_score(target)
        self.assertGreaterEqual(threat, 0.0)
        self.assertLessEqual(threat, 100.0)
        self.assertIsInstance(intent, str)
        digest = audit_eu_ai_act_titan_m2("sample")
        self.assertEqual(len(digest), 64)

    def test_ukf_predict_update_stable(self) -> None:
        ukf = ARUKFFilter()
        for _ in range(5):
            ukf.predict()
            x_up, m = ukf.update_adaptive(np.array([1.0, 2.0, 3.0]))
            self.assertEqual(len(x_up), 6)
            self.assertTrue(math.isfinite(float(m)))

    def test_acoustic_zero_energy_safe(self) -> None:
        acoustic = PassiveAcousticProcessor(fs=44100, mic_distance=0.15)
        zeros = np.zeros(2048, dtype=np.float32)
        bpf = acoustic.estimate_bpf_harmonic(zeros)
        self.assertTrue(isinstance(bpf, (int, float, np.floating)))


if __name__ == "__main__":
    unittest.main()
