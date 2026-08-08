import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.metrics import LatencySamples


def test_empty_samples():
    s = LatencySamples()
    summary = s.summary()
    assert summary["n"] == 0


def test_single_sample():
    s = LatencySamples()
    s.add(10.0)
    summary = s.summary()
    assert summary["n"] == 1
    assert summary["p50_ms"] == 10.0
    assert summary["p95_ms"] == 10.0


def test_percentiles_known_distribution():
    s = LatencySamples()
    for v in range(1, 101):  # 1..100
        s.add(float(v))
    summary = s.summary()
    assert summary["n"] == 100
    # p50 of 1..100 should be close to 50
    assert 49 <= summary["p50_ms"] <= 52
    # p95 should be close to 95
    assert 93 <= summary["p95_ms"] <= 97


def test_min_max_mean():
    s = LatencySamples()
    for v in [5.0, 10.0, 15.0]:
        s.add(v)
    summary = s.summary()
    assert summary["min_ms"] == 5.0
    assert summary["max_ms"] == 15.0
    assert summary["mean_ms"] == 10.0
