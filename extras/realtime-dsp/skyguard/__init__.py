"""SKYGUARD — zunifikowany pakiet Python (DSP, Remote ID, DoA, fuzja, radar, AI, realtime).

Kod jest nasz: część algorytmów to własne implementacje, część to kod
zaadaptowany z projektów na licencjach MIT/BSD/Apache/ISC z zachowaniem
nagłówków i informacji o licencji (zob. THIRD_PARTY_LICENSES.md, docs/top25.md).
Z repozytoriów bez licencji nie kopiowano kodu — metody napisano od nowa.
"""
__version__ = "0.3.0"

from . import dsp, radar, doa, fusion, realtime, rid, sim, ai  # noqa: E402,F401
from . import pipeline  # noqa: E402,F401

__all__ = ["dsp", "radar", "doa", "fusion", "realtime", "rid", "sim", "ai", "pipeline", "cuas", "__version__"]
