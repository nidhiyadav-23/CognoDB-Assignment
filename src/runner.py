from __future__ import annotations

import concurrent.futures
import random
import time
from typing import Any

from .adapters.base import GraphAdapter
from .config import PlatformConfig
from .loader import SamplePool, load_all
from .metrics import LatencySamples, timer
from .workloads import MIXED_WRITE_QUERIES, WORKLOADS, dialect_for


def run_read_workloads(
    adapter: GraphAdapter, dialect: str, pool: SamplePool, iterations: int, warmup_iterations: int
) -> dict[str, Any]:
    """Runs every workload from workloads.WORKLOADS: warmup_iterations
    unmeasured calls followed by `iterations` measured calls, returning
    p50/p95/p99 per workload. This is the core of section 5.2's traversal/
    lookup/aggregation rows.
    """
    results: dict[str, Any] = {}
    key = dialect_for(dialect)
    for wl in WORKLOADS:
        query = wl.queries[key]
        samples = LatencySamples()

        for _ in range(warmup_iterations):
            adapter.run_query(query, wl.param_fn(pool))

        for _ in range(iterations):
            params = wl.param_fn(pool)
            with timer() as t:
                adapter.run_query(query, params)
            samples.add(t.ms)

        results[wl.name] = {
            "category": wl.category,
            "description": wl.description,
            **samples.summary(),
        }
    return results


def _mixed_worker(adapter_factory, dialect: str, pool: SamplePool, read_ratio: float,
                   duration_seconds: float, stop_time: float) -> dict[str, Any]:
    """Runs on its own adapter connection (most drivers aren't safe to share
    across threads) issuing a read/write mix until stop_time, returning the
    count and latency samples it produced. read_ratio=0.8 means ~80% reads.
    """
    adapter = adapter_factory()
    adapter.connect()
    key = dialect_for(dialect)
    read_query = WORKLOADS[3].queries[key]  # point_lookup
    write_query = MIXED_WRITE_QUERIES[key]
    rng = random.Random()
    samples = LatencySamples()
    ops = 0
    try:
        while time.perf_counter() < stop_time:
            is_read = rng.random() < read_ratio
            movie_id = pool.random_movie_id()
            with timer() as t:
                if is_read:
                    adapter.run_query(read_query, {"movie_id": movie_id})
                else:
                    adapter.run_query(write_query, {"movie_id": movie_id})
            samples.add(t.ms)
            ops += 1
    finally:
        adapter.close()
    return {"ops": ops, "samples": samples}


def run_mixed_workload(
    adapter_factory, dialect: str, pool: SamplePool, concurrency_levels: list[int],
    duration_seconds: float = 15.0, read_ratio: float = 0.8,
) -> dict[str, Any]:
    """Sweeps client concurrency (e.g. 1/10/40) as required by assignment
    section 5.2's 'Mixed workload' row, reporting sustained throughput at
    each level with a stated read/write mix.
    """
    sweep: dict[str, Any] = {}
    for concurrency in concurrency_levels:
        stop_time = time.perf_counter() + duration_seconds
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = [
                ex.submit(_mixed_worker, adapter_factory, dialect, pool, read_ratio, duration_seconds, stop_time)
                for _ in range(concurrency)
            ]
            worker_results = [f.result() for f in futures]

        total_ops = sum(r["ops"] for r in worker_results)
        all_samples = LatencySamples()
        for r in worker_results:
            all_samples.values_ms.extend(r["samples"].values_ms)

        sweep[str(concurrency)] = {
            "concurrency": concurrency,
            "read_write_mix": f"{int(read_ratio * 100)}/{int((1 - read_ratio) * 100)}",
            "duration_seconds": duration_seconds,
            "total_ops": total_ops,
            "throughput_qps": round(total_ops / duration_seconds, 2),
            **all_samples.summary(),
        }
    return sweep


def run_platform_benchmark(
    platform: PlatformConfig, adapter_factory, settings: dict[str, Any]
) -> dict[str, Any]:
    """Full benchmark for one platform: load -> read workloads -> mixed
    workload concurrency sweep -> footprint. Returns everything needed to
    populate the README results matrix for this platform.
    """
    adapter = adapter_factory()
    result: dict[str, Any] = {"platform": platform.id, "display_name": platform.display_name,
                               "advertised_specs": platform.advertised_specs, "query_dialect": platform.query_dialect}
    try:
        adapter.connect()
        result["load"] = load_all(adapter)
        pool = SamplePool()
        result["reads"] = run_read_workloads(
            adapter, platform.query_dialect, pool,
            iterations=settings["read_iterations"], warmup_iterations=settings["warmup_iterations"],
        )
        result["footprint"] = adapter.footprint()
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        return result
    finally:
        adapter.close()

    # Mixed workload needs its own connections per thread, so it uses the
    # factory directly rather than the adapter opened above.
    try:
        pool = SamplePool()
        result["mixed_workload"] = run_mixed_workload(
            adapter_factory, platform.query_dialect, pool, settings["concurrency_levels"],
        )
    except Exception as e:
        result["mixed_workload_error"] = f"{type(e).__name__}: {e}"

    return result
