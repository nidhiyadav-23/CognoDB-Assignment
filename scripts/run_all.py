#!/usr/bin/env python3
"""One-command benchmark runner.

Usage:
    python scripts/run_all.py                       # all platforms in config/platforms.yaml
    python scripts/run_all.py --only cognodb memgraph_cloud
    python scripts/run_all.py --skip-load            # re-run reads/mixed only, skip re-ingesting data

Writes results/results_<platform_id>.json per platform and results/results.json
combined. Run scripts/generate_readme_tables.py afterward to produce the
markdown tables for the README.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.adapters import build_adapter
from src.config import load_benchmark_settings, load_platforms
from src.runner import run_platform_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None, help="Subset of platform ids to run")
    args = parser.parse_args()

    settings = load_benchmark_settings()
    platforms = load_platforms(only=args.only)
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    all_results = []
    for platform in platforms:
        print(f"\n=== {platform.display_name} ({platform.id}) ===")
        if not platform.is_configured():
            print(f"  SKIPPED: missing credentials in .env for {platform.id} "
                  f"(set {platform.id.upper()}_* vars - see .env.example)")
            all_results.append({"platform": platform.id, "display_name": platform.display_name,
                                 "skipped": True, "reason": "not configured"})
            continue

        def adapter_factory(p=platform):
            return build_adapter(p)

        try:
            result = run_platform_benchmark(platform, adapter_factory, settings)
        except Exception as e:
            print(f"  FAILED: {e}")
            traceback.print_exc()
            result = {"platform": platform.id, "display_name": platform.display_name,
                      "error": f"{type(e).__name__}: {e}"}

        out_path = results_dir / f"results_{platform.id}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  -> wrote {out_path}")
        all_results.append(result)

    with open(results_dir / "results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nCombined results written to {results_dir / 'results.json'}")
    print("Run: python scripts/generate_readme_tables.py")


if __name__ == "__main__":
    main()
