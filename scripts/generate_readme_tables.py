#!/usr/bin/env python3
"""Reads results/results.json and prints markdown tables matching the
structure of assignment section 5.2, ready to paste into README.md. Keeping
table generation scripted (rather than hand-typed) is what prevents the
results matrix from silently drifting from the raw JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tabulate import tabulate

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_results() -> list[dict]:
    with open(ROOT / "results" / "results.json") as f:
        return json.load(f)


def table_loading(results: list[dict]) -> str:
    rows = []
    for r in results:
        if r.get("skipped") or r.get("error"):
            rows.append([r["display_name"], "N/A", "N/A", "N/A", r.get("reason") or r.get("error")])
            continue
        load = r["load"]
        rows.append([r["display_name"], load["nodes_per_second"], load["edges_per_second"],
                     f"{load['total_load_seconds']}s", ""])
    return tabulate(rows, headers=["Platform", "Nodes/sec", "Rels/sec", "Total load time", "Notes"],
                     tablefmt="github")


def table_reads(results: list[dict], workload_name: str) -> str:
    rows = []
    for r in results:
        if r.get("skipped") or r.get("error"):
            rows.append([r["display_name"], "N/A", "N/A", r.get("reason") or r.get("error")])
            continue
        wl = r.get("reads", {}).get(workload_name)
        if not wl:
            rows.append([r["display_name"], "N/A", "N/A", "workload not run"])
            continue
        rows.append([r["display_name"], f"{wl['p50_ms']} ms", f"{wl['p95_ms']} ms", f"n={wl['n']}"])
    return tabulate(rows, headers=["Platform", "p50", "p95", "Notes"], tablefmt="github")


def table_mixed(results: list[dict]) -> str:
    rows = []
    for r in results:
        if r.get("skipped") or r.get("error") or "mixed_workload" not in r:
            rows.append([r["display_name"], "N/A", "N/A", "N/A", r.get("reason") or r.get("error") or r.get("mixed_workload_error", "")])
            continue
        for level, stats in r["mixed_workload"].items():
            rows.append([r["display_name"], stats["concurrency"], stats["read_write_mix"],
                         f"{stats['throughput_qps']} qps", f"p95={stats['p95_ms']}ms"])
    return tabulate(rows, headers=["Platform", "Concurrency", "R/W mix", "Throughput", "Latency"], tablefmt="github")


def table_footprint(results: list[dict]) -> str:
    rows = []
    for r in results:
        if r.get("skipped") or r.get("error"):
            continue
        fp = r.get("footprint", {})
        if fp.get("observable"):
            rows.append([r["display_name"], fp.get("nodeCount", "?"), fp.get("relCount", "?"), fp.get("note", "")])
        else:
            rows.append([r["display_name"], "not observable", "not observable", fp.get("reason", "")])
    return tabulate(rows, headers=["Platform", "Node count", "Rel count", "Notes"], tablefmt="github")


def main():
    results = load_results()
    print("## Data loading\n")
    print(table_loading(results))
    print("\n## Traversals\n")
    for wl in ["traversal_1hop", "traversal_2hop", "traversal_3hop"]:
        print(f"\n### {wl}\n")
        print(table_reads(results, wl))
    print("\n## Lookups\n")
    for wl in ["point_lookup", "indexed_filtered_lookup"]:
        print(f"\n### {wl}\n")
        print(table_reads(results, wl))
    print("\n## Aggregations\n")
    print(table_reads(results, "aggregation_by_category"))
    print("\n## Mixed workload (concurrency sweep)\n")
    print(table_mixed(results))
    print("\n## Footprint\n")
    print(table_footprint(results))


if __name__ == "__main__":
    main()
