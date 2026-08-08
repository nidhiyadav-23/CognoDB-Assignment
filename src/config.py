"""Loads platform registry (config/platforms.yaml) and merges in credentials
from environment variables (.env). Keeping these separate is what lets us
commit platforms.yaml (specs, dialects) while keeping secrets out of git.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass
class PlatformConfig:
    id: str
    display_name: str
    adapter: str
    query_dialect: str
    advertised_specs: dict[str, Any]
    credentials: dict[str, str] = field(default_factory=dict)

    def is_configured(self) -> bool:
        """A platform is runnable if its required credentials are non-empty.
        Different adapters need different credential sets, so we just check
        that nothing is blank among what was loaded.
        """
        return all(v for v in self.credentials.values() if v is not None) and len(self.credentials) > 0


def _load_credentials(env_prefix: str, adapter: str) -> dict[str, str]:
    if adapter == "bolt_cypher":
        return {
            "uri": os.getenv(f"{env_prefix}_URI", ""),
            "user": os.getenv(f"{env_prefix}_USER", ""),
            "password": os.getenv(f"{env_prefix}_PASSWORD", ""),
        }
    if adapter == "neptune_opencypher":
        return {
            "endpoint": os.getenv(f"{env_prefix}_ENDPOINT", ""),
            "aws_access_key_id": os.getenv(f"{env_prefix}_AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": os.getenv(f"{env_prefix}_AWS_SECRET_ACCESS_KEY", ""),
            "aws_region": os.getenv(f"{env_prefix}_AWS_REGION", "us-east-1"),
        }
    if adapter == "arango_aql":
        return {
            "url": os.getenv(f"{env_prefix}_URL", ""),
            "db": os.getenv(f"{env_prefix}_DB", "benchmark"),
            "user": os.getenv(f"{env_prefix}_USER", ""),
            "password": os.getenv(f"{env_prefix}_PASSWORD", ""),
        }
    raise ValueError(f"Unknown adapter type: {adapter}")


def load_platforms(only: list[str] | None = None) -> list[PlatformConfig]:
    """Load all platforms from config/platforms.yaml, attaching credentials
    from the environment. Pass `only=["cognodb", "memgraph_cloud"]` to filter
    to a subset (handy for iterating on one platform's adapter at a time).
    """
    with open(ROOT / "config" / "platforms.yaml") as f:
        raw = yaml.safe_load(f)

    platforms = []
    for p in raw["platforms"]:
        if only and p["id"] not in only:
            continue
        creds = _load_credentials(p["env_prefix"], p["adapter"])
        platforms.append(
            PlatformConfig(
                id=p["id"],
                display_name=p["display_name"],
                adapter=p["adapter"],
                query_dialect=p["query_dialect"],
                advertised_specs=p["advertised_specs"],
                credentials=creds,
            )
        )
    return platforms


def load_benchmark_settings() -> dict[str, Any]:
    with open(ROOT / "config" / "platforms.yaml") as f:
        raw = yaml.safe_load(f)
    settings = dict(raw["benchmark"])
    # env overrides, since these are the knobs you tweak most often between runs
    if os.getenv("BENCH_ITERATIONS"):
        settings["read_iterations"] = int(os.getenv("BENCH_ITERATIONS"))
    if os.getenv("BENCH_WARMUP_ITERATIONS"):
        settings["warmup_iterations"] = int(os.getenv("BENCH_WARMUP_ITERATIONS"))
    if os.getenv("BENCH_CONCURRENCY_LEVELS"):
        settings["concurrency_levels"] = [int(x) for x in os.getenv("BENCH_CONCURRENCY_LEVELS").split(",")]
    return settings
