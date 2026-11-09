import numpy as np
import pytest

from skyguard import radar, doa


@pytest.mark.parametrize("method", ["ca", "go", "so", "caso", "os"])
def test_cfar_1d_finds_targets_low_fa(method):
    rng = np.random.default_rng(0)
    p = rng.exponential(1.0, 4000)
    targets = [500, 1500, 3000]
    p[targets] = 200.0
    det, thr = radar.cfar_1d(p, guard=2, train=16, pfa=1e-4, method=method)
    assert det[targets].all()
    assert det.sum() - len(targets) < 10


def test_cfar_bad_method():
    with pytest.raises(ValueError):
        radar.cfar_1d(np.ones(100), method="xx")


def test_range_doppler_and_cfar_2d():
    rng = np.random.default_rng(1)
    nc, ns = 64, 128
    n, m = np.arange(ns), np.arange(nc)[:, None]
    chirps = np.exp(2j * np.pi * (20 * n / ns + 8 * m / nc)) + 0.1 * (rng.normal(size=(nc, ns)) + 1j * rng.normal(size=(nc, ns)))
    rd = radar.range_doppler_map(chirps)
    d, r = np.unravel_index(np.argmax(rd), rd.shape)
    assert (r, d - nc // 2) == (20, 8)
    mask = radar.cfar_2d(rd, pfa=1e-6)
    assert mask[d, r]
    assert mask.sum() < 30


def test_axes():
    ra = radar.range_axis(256, 10e6, 30e12)
    assert ra[0] == 0 and ra[1] == pytest.approx(10e6 / 256 * 3e8 / 60e12, rel=1e-3)
    assert radar.velocity_axis(64, 100e-6, 77e9).shape == (64,)


def _snapshots(angles, n_elem=8, n_snap=400, snr_db=20, seed=0):
    rng = np.random.default_rng(seed)
    A = doa.steering_vector(angles, n_elem)
    S = (rng.normal(size=(len(angles), n_snap)) + 1j * rng.normal(size=(len(angles), n_snap))) / np.sqrt(2)
    s = 10 ** (-snr_db / 20)
    N = s * (rng.normal(size=(n_elem, n_snap)) + 1j * rng.normal(size=(n_elem, n_snap))) / np.sqrt(2)
    return A @ S + N


def test_music_two_sources():
    est = doa.music_doa(_snapshots([-20, 35]), 2)
    np.testing.assert_allclose(est, [-20, 35], atol=1.0)


def test_esprit_two_sources():
    est = doa.esprit_doa(_snapshots([-20, 35]), 2)
    np.testing.assert_allclose(est, [-20, 35], atol=1.0)
