"""Bufor pierścieniowy SPSC (jeden producent, jeden konsument) bez blokad.

Bezpieczny przy dokładnie jednym wątku piszącym i jednym czytającym: tylko
producent zmienia `head`, tylko konsument zmienia `tail`. Dane w numpy, więc
kopiowanie ramek zwalnia GIL wewnątrz numpy. Opcjonalnie na SharedMemory
(międzyprocesowo, `name=`)."""
from __future__ import annotations

import numpy as np


class SPSCRingBuffer:
    def __init__(self, n_slots: int, frame_len: int, dtype=np.complex64, name: str | None = None,
                 create: bool = True):
        if n_slots < 2 or n_slots & (n_slots - 1):
            raise ValueError("n_slots musi być potęgą 2 i >= 2")
        self.n, self.mask, self.frame_len = n_slots, n_slots - 1, frame_len
        self.dtype = np.dtype(dtype)
        self._shm = None
        data_bytes = n_slots * frame_len * self.dtype.itemsize
        if name is not None:
            from multiprocessing import shared_memory
            self._shm = shared_memory.SharedMemory(name=name, create=create, size=16 + data_bytes)
            buf = self._shm.buf
            self._idx = np.ndarray((2,), np.int64, buf, 0)
            if create:
                self._idx[:] = 0
            self._data = np.ndarray((n_slots, frame_len), self.dtype, buf, 16)
        else:
            self._idx = np.zeros(2, np.int64)
            self._data = np.zeros((n_slots, frame_len), self.dtype)

    # head = _idx[0] (zapis), tail = _idx[1] (odczyt)
    def __len__(self):
        return int(self._idx[0] - self._idx[1])

    def push(self, frame) -> bool:
        h, t = int(self._idx[0]), int(self._idx[1])
        if h - t >= self.n:
            return False  # pełny — ramka odrzucona (nie blokujemy akwizycji)
        self._data[h & self.mask, :] = frame
        self._idx[0] = h + 1
        return True

    def pop(self):
        h, t = int(self._idx[0]), int(self._idx[1])
        if h == t:
            return None
        out = self._data[t & self.mask].copy()
        self._idx[1] = t + 1
        return out

    def close(self, unlink: bool = False):
        if self._shm is not None:
            self._idx = self._data = None
            self._shm.close()
            if unlink:
                self._shm.unlink()
            self._shm = None
