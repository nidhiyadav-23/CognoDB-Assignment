"""Every platform adapter implements this interface so loader.py, workloads.py
and runner.py never need to know which database they're talking to. This is
the thing that makes "same logical queries, same client machine" enforceable
in code rather than just asserted in the README.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


class GraphAdapter(ABC):
    """Minimal surface area: connect, load nodes/edges in batches, run a
    parameterized query and return records, close. Workload queries themselves
    live in workloads.py as per-dialect string templates (Cypher / openCypher /
    AQL) so the *logical* query is identical even when syntax differs.
    """

    def __init__(self, credentials: dict[str, str]):
        self.credentials = credentials

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def wipe_database(self) -> None:
        """Clear all nodes/edges/indexes before a fresh load. Required so
        repeated runs don't silently accumulate duplicate data.
        """

    @abstractmethod
    def create_indexes(self) -> None:
        """Create the indexes documented in the README's 'which properties
        are indexed' column. Must be called once, after wipe, before load.
        """

    @abstractmethod
    def load_nodes(self, label: str, rows: Iterable[dict[str, Any]], batch_size: int = 1000) -> int:
        """Load nodes of a given label from an iterable of property dicts.
        Returns count loaded. Must be idempotent-safe within a single run
        (call wipe_database first).
        """

    @abstractmethod
    def load_edges(
        self,
        rel_type: str,
        rows: Iterable[dict[str, Any]],
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        batch_size: int = 1000,
    ) -> int:
        """Load edges of rel_type. Each row must contain from_key and to_key
        values used to match existing nodes (created via load_nodes first).
        """

    @abstractmethod
    def run_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute one query/statement in this platform's native dialect and
        return result rows as plain dicts. Timing is measured by the caller
        (runner.py), not here, so adapters stay dumb and comparable.
        """

    @abstractmethod
    def footprint(self) -> dict[str, Any]:
        """Best-effort resource footprint: stored data size, memory usage,
        etc. Return {'observable': False, 'reason': '...'} for whatever a
        platform doesn't expose rather than guessing.
        """
