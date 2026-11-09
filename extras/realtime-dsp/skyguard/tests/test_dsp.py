import numpy as np
import pytest
from scipy import signal

from skyguard import dsp


@pytest.mark.parametrize("name,ref", [("hann", "hann"), ("hamming", "hamming"),
                                      ("blackman", "blackman"), ("blackmanharris", "blackmanharris")])
@pytest.mark.parametrize("sym", [True, False])
def test_windows_match_scipy(name, ref, sym):
    np.testing.assert_allclose(dsp.get_window(name, 64, sym), signal.get_window(ref, 64, fftbins=not sym), atol=1e-12)


def test_kaiser_matches_scipy():
    np.testing.assert_allclose(dsp.kaiser(51, 6.0, sym=True), signal.windows.kaiser(51, 6.0, sym=True), atol=1e-12)


def test_unwrap_matches_numpy():
    rng = np.random.default_rng(0)
    ph = np.cumsum(rng.normal(0, 1.2, 500))
    w = np.angle(np.exp(1j * ph))
    np.testing.assert_allclose(dsp.unwrap_phase(w), np.unwrap(w), atol=1e-9)


@pytest.mark.parametrize("n", [255, 256])
def test_hilbert_matches_scipy(n):
    x = np.random.default_rng(1).normal(size=n)
    np.testing.assert_allclose(dsp.analytic_signal(x), signal.hilbert(x), atol=1e-10)


def test_hilbert_envelope_of_am():
    t = np.arange(8000) / 8000
    env = 1 + 0.5 * np.sin(2 * np.pi * 3 * t)
    x = env * np.cos(2 * np.pi * 1000 * t)
    np.testing.assert_allclose(dsp.hilbert_envelope(x)[200:-200], env[200:-200], atol=0.02)


def test_teager_kaiser_sine():
    A, w = 0.7, 0.3
    x = A * np.sin(w * np.arange(1000))
    np.testing.assert_allclose(dsp.teager_kaiser(x)[1:-1], A**2 * np.sin(w) ** 2, atol=1e-12)


def test_hjorth_sine_mobility():
    w = 0.05
    act, mob, comp = dsp.hjorth(np.sin(w * np.arange(20000)))
    assert act == pytest.approx(0.5, rel=1e-3)
    assert mob == pytest.approx(2 * np.sin(w / 2), rel=1e-2)
    assert comp == pytest.approx(1.0, abs=0.02)


def test_spectral_subtraction_improves_snr():
    rng = np.random.default_rng(2)
    sr = 16000
    t = np.arange(sr) / sr
    clean = np.sin(2 * np.pi * 440 * t)
    noise = rng.normal(0, 0.5, sr)
    y = dsp.spectral_subtraction(clean + noise, rng.normal(0, 0.5, sr))
    assert np.mean((y - clean) ** 2) < 0.5 * np.mean(noise**2)
    assert y.shape == clean.shape


def test_tsa_recovers_periodic():
    rng = np.random.default_rng(3)
    period = 100.0
    base = np.sin(2 * np.pi * np.arange(100) / period) + 0.3 * np.sin(6 * np.pi * np.arange(100) / period)
    x = np.tile(base, 200) + rng.normal(0, 1, 20000)
    avg = dsp.tsa(x, period)
    assert np.corrcoef(avg, base)[0, 1] > 0.98


def test_lfcc_shape_and_finite():
    x = np.random.default_rng(4).normal(size=16000)
    c = dsp.lfcc(x, 16000, n_coeffs=20)
    assert c.shape == (30, 20) and np.isfinite(c).all()


def test_gammatone_peak_band():
    sr = 16000
    x = np.sin(2 * np.pi * 1000 * np.arange(sr) / sr)
    cf, y = dsp.gammatone_filterbank(x, sr, n_bands=24)
    best = cf[np.argmax(np.sum(y**2, axis=1))]
    assert abs(best - 1000) / 1000 < 0.15


def test_numba_energy_and_peak():
    n = 1024
    iq = np.exp(2j * np.pi * 100 * np.arange(n) / n).astype(np.complex64)
    spec, e, k = dsp.frame_spectrum_energy(iq)
    assert e == pytest.approx(1.0, rel=1e-5)
    assert k == n // 2 + 100
