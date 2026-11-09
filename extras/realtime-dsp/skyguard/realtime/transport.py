"""Transport ramek I/Q przez ZeroMQ (pyzmq), zero-copy, nagłówek z czasem wysłania."""
from __future__ import annotations

import struct
import time

import numpy as np

_HDR = struct.Struct("<QdI")  # seq, t_send (perf_counter_ns->s), n_samples


def pack_frame(seq: int, iq: np.ndarray, t_send: float | None = None):
    iq = np.ascontiguousarray(iq, dtype=np.complex64)
    return [_HDR.pack(seq, time.perf_counter() if t_send is None else t_send, iq.size), iq]


def unpack_frame(parts):
    hdr, body = (getattr(p, "buffer", p) for p in parts[:2])
    seq, t_send, n = _HDR.unpack(bytes(hdr))
    iq = np.frombuffer(body, dtype=np.complex64, count=n)
    return seq, t_send, iq


class IQPublisher:
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5557", hwm: int = 64, ctx=None):
        import zmq
        self._zmq = zmq
        self.ctx = ctx or zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.PUSH)
        self.sock.setsockopt(zmq.SNDHWM, hwm)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.bind(endpoint)

    def send(self, seq, iq) -> bool:
        try:
            self.sock.send_multipart(pack_frame(seq, iq), flags=self._zmq.NOBLOCK, copy=False)
            return True
        except self._zmq.Again:
            return False

    def close(self):
        self.sock.close()


class IQSubscriber:
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5557", hwm: int = 64, ctx=None):
        import zmq
        self._zmq = zmq
        self.ctx = ctx or zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.PULL)
        self.sock.setsockopt(zmq.RCVHWM, hwm)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.connect(endpoint)

    def recv(self, timeout_ms: int = 1000):
        if not self.sock.poll(timeout_ms):
            return None
        return unpack_frame(self.sock.recv_multipart(copy=False))

    def close(self):
        self.sock.close()
