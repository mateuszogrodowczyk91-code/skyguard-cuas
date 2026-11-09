"""Techniki z raportu C-UAS (Niemcy/NATO) wdrożone w SKYGUARD — patrz docs/cuas-report-extraction.md.

- profiles     — profile sygnatur maszyn (BPF/RPM), klasa wielkości z f0 (wyuczone na naszych nagraniach)
- uncertainty  — Uncertainty Wrapper (styl Fraunhofer IESE) dla decyzji SG-FUZJA
- payload      — skok BPF → możliwy zrzut ładunku
- threat       — poziom zagrożenia 1–5 (CPA, opadanie, klasa, brak RID) + kolor alarmu (reguła 3 sensorów)
- sapient      — węzeł SAPIENT BSI Flex 335 v2.0 (protobuf zgodny bajt-w-bajt, ramka LE, maszyna stanów)
- asterix      — eksport torów CAT062 (binarnie + JSON), poprawny dekoder CAT048 I048/120
- forensic     — łańcuch dowodowy SHA-256
Fuzja torów CI/ICI oraz UKF: skyguard.fusion.
Żaden moduł nie zależy od Remote ID i żaden nie zmienia decyzji SG-FUZJA ani progu nagrywania 88%.
"""
from __future__ import annotations

from .profiles import estimate_size, bpf_hz, rpm_from_bpf, SignatureModel, SIZE_CLASSES
from .uncertainty import UncertaintyWrapper, clopper_pearson_upper, default_wrapper
from .payload import detect_bpf_steps, PayloadEvent
from .threat import score as threat_score, ThreatInput, alarm_colour, cpa


def assess(x, sr: int, fz: bool | None = None, fz_max: float | None = None, u_max: float = 0.20) -> dict:
    """Pełna ocena klipu: cechy akustyczne, klasa wielkości, wiarygodność alarmu
    SG-FUZJA (jeśli podany), możliwy zrzut. Nie zmienia decyzji SG-FUZJA."""
    from ..pipeline import describe
    from ..dsp.harmonic import analyze_harmonics
    import numpy as np
    from scipy.signal import resample_poly
    x = np.asarray(x, float)
    if sr != 8000:
        from math import gcd
        g = gcd(int(sr), 8000); x = resample_poly(x, 8000 // g, int(sr) // g); sr = 8000
    d = describe(x, sr).to_dict()
    out = {"acoustic": d, "size": estimate_size(d["f0_hz"]).to_dict() if d["f0_hz"] > 0 else None}
    h = analyze_harmonics(x, sr)
    out["payload_events"] = [e.to_dict() for e in detect_bpf_steps(h.track_hz, hop_s=1024 / sr)]
    if fz is not None and fz_max is not None:
        row = dict(d, fz_max=float(fz_max))
        w = default_wrapper()
        out["sgfuzja"] = {"alarm": bool(fz), "uncertainty_u95": w.uncertainty(row) if fz else None,
                          "grade": w.gate(bool(fz), row, u_max)}
    return out


__all__ = ["estimate_size", "bpf_hz", "rpm_from_bpf", "SignatureModel", "SIZE_CLASSES", "UncertaintyWrapper",
           "clopper_pearson_upper", "default_wrapper", "detect_bpf_steps", "PayloadEvent", "threat_score",
           "ThreatInput", "alarm_colour", "cpa", "assess"]
