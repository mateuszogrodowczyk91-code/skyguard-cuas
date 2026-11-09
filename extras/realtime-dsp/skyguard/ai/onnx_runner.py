"""Uruchamianie modelu klasyfikatora ONNX (microsoft/onnxruntime, MIT — tylko zależność).

onnxruntime jest opcjonalny: jeśli go nie ma, `OnnxClassifier` zgłasza czytelny
błąd, a reszta pakietu działa. Wyjście: prawdopodobieństwa (softmax, jeśli
model zwraca logity)."""
from __future__ import annotations

import numpy as np

try:  # pragma: no cover - zależy od środowiska
    import onnxruntime as _ort
    ONNX_AVAILABLE = True
except Exception:  # pragma: no cover
    _ort = None
    ONNX_AVAILABLE = False


def softmax(z, axis=-1):
    z = np.asarray(z, float)
    e = np.exp(z - z.max(axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)


class OnnxClassifier:
    def __init__(self, model_path: str, labels: list[str] | None = None, threads: int = 1):
        if not ONNX_AVAILABLE:
            raise RuntimeError("Brak onnxruntime: pip install onnxruntime")
        so = _ort.SessionOptions()
        so.intra_op_num_threads = threads
        self.sess = _ort.InferenceSession(model_path, so, providers=["CPUExecutionProvider"])
        self.input = self.sess.get_inputs()[0].name
        self.labels = labels

    def predict(self, x: np.ndarray) -> np.ndarray:
        y = self.sess.run(None, {self.input: np.asarray(x, np.float32)})[0]
        y = np.asarray(y, float)
        if y.min() < 0 or not np.allclose(y.sum(-1), 1, atol=1e-3):
            y = softmax(y)
        return y
