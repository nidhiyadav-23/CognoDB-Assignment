"""Small stats helpers. Kept separate from runner.py so they're independently
unit-testable (see tests/test_metrics.py) - percentile math is exactly the
kind of thing that's easy to get subtly wrong (off-by-one in the index,
mean vs. median confusion) and silently produce a misleading benchmark.
"""
from __future__ import annotations

import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class LatencySamples:
    values_ms: list[float] = field(default_factory=list)

    def add(self, ms: float) -> None:
        self.values_ms.append(ms)

    def percentile(self, pct: float) -> float:
        if not self.values_ms:
            return float("nan")
        return statistics.quantiles(self.values_ms, n=100, method="inclusive")[int(pct) - 1] \
            if len(self.values_ms) >= 2 else self.values_ms[0]

    def summary(self) -> dict[str, float]:
        if not self.values_ms:
            return {"n": 0, "p50_ms": float("nan"), "p95_ms": float("nan"), "p99_ms": float("nan"),
                    "mean_ms": float("nan"), "min_ms": float("nan"), "max_ms": float("nan")}
        return {
            "n": len(self.values_ms),
            "p50_ms": round(self.percentile(50), 3),
            "p95_ms": round(self.percentile(95), 3),
            "p99_ms": round(self.percentile(99), 3),
            "mean_ms": round(statistics.mean(self.values_ms), 3),
            "min_ms": round(min(self.values_ms), 3),
            "max_ms": round(max(self.values_ms), 3),
        }


@contextmanager
def timer():
    """Usage: with timer() as t: ...  then t.ms holds elapsed milliseconds."""
    class _T:
        ms: float = 0.0
    t = _T()
    start = time.perf_counter()
    try:
        yield t
    finally:
        t.ms = (time.perf_counter() - start) * 1000.0
