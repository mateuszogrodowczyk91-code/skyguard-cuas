import threading

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from skyguard import fusion, realtime

D, B, N = "dron", "ptak", "nic"


def test_dempster_classic():
    m1 = {frozenset([D]): 0.6, frozenset([D, B, N]): 0.4}
    m2 = {frozenset([D]): 0.5, frozenset([B]): 0.3, frozenset([D, B, N]): 0.2}
    m = fusion.combine(m1, m2)
    assert sum(m.values()) == pytest.approx(1.0)
    k = 0.6 * 0.3
    assert m[frozenset([D])] == pytest.approx((0.6 * 0.5 + 0.6 * 0.2 + 0.4 * 0.5) / (1 - k))
    assert fusion.belief(m, [D]) <= fusion.plausibility(m, [D])


def test_dempster_total_conflict():
    with pytest.raises(ValueError):
        fusion.combine({frozenset([D]): 1.0}, {frozenset([B]): 1.0})


@pytest.mark.parametrize("shape", [(6, 6), (4, 7), (7, 4)])
def test_hungarian_matches_scipy(shape):
    C = np.random.default_rng(sum(shape)).random(shape)
    r, c = linear_sum_assignment(C)
    pairs = fusion.hungarian(C)
    assert sum(C[i, j] for i, j in pairs) == pytest.approx(C[r, c].sum())


def test_tracker_two_crossing_targets():
    trk = fusion.MultiTargetTracker(dt=0.1, q=0.5, r=0.05)
    rng = np.random.default_rng(0)
    for k in range(60):
        t = k * 0.1
        z = [np.array([t * 2, 0.0]), np.array([10 - t * 2, 3.0])]
        out = trk.step([zz + rng.normal(0, 0.05, 2) for zz in z])
    assert len(out) == 2
    v = sorted(x[2] for _, x in out)
    assert v[0] == pytest.approx(-2, abs=0.3) and v[1] == pytest.approx(2, abs=0.3)


def test_ringbuffer_basic_and_full():
    rb = realtime.SPSCRingBuffer(4, 8)
    for i in range(4):
        assert rb.push(np.full(8, i))
    assert not rb.push(np.zeros(8))
    assert rb.pop()[0] == 0 and len(rb) == 3
    with pytest.raises(ValueError):
        realtime.SPSCRingBuffer(3, 8)


def test_ringbuffer_threads_order():
    rb = realtime.SPSCRingBuffer(64, 16, dtype=np.float64)
    total = 20000
    got = []

    def prod():
        i = 0
        while i < total:
            if rb.push(np.full(16, i)):
                i += 1

    th = threading.Thread(target=prod)
    th.start()
    while len(got) < total:
        f = rb.pop()
        if f is not None:
            got.append(int(f[0]))
    th.join()
    assert got == list(range(total))


def test_ringbuffer_shared_memory():
    import uuid
    name = "sg_" + uuid.uuid4().hex[:8]
    a = realtime.SPSCRingBuffer(8, 4, name=name, create=True)
    b = realtime.SPSCRingBuffer(8, 4, name=name, create=False)
    a.push(np.arange(4) + 1j)
    np.testing.assert_allclose(b.pop(), np.arange(4) + 1j)
    b.close(); a.close(unlink=True)


def test_zmq_roundtrip():
    pytest.importorskip("zmq")
    ep = "tcp://127.0.0.1:5591"
    pub = realtime.IQPublisher(ep)
    sub = realtime.IQSubscriber(ep)
    iq = (np.arange(256) * (1 + 1j)).astype(np.complex64)
    import time
    time.sleep(0.1)
    assert pub.send(7, iq)
    seq, t_send, got = sub.recv(2000)
    assert seq == 7 and np.array_equal(got, iq)
    pub.close(); sub.close()


def test_priority_never_raises():
    assert isinstance(realtime.set_realtime_priority(10), str)
