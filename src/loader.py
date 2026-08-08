from __future__ import annotations

import random
import time
from pathlib import Path

import pandas as pd

from .adapters.base import GraphAdapter

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"


class SamplePool:
    """Holds a small in-memory sample of real ids/years from the loaded
    dataset so workload queries hit real data (not random misses), which is
    what makes p50/p95 latencies meaningful rather than an artifact of
    querying nonexistent nodes.
    """

    def __init__(self, seed: int = 7, pool_size: int = 5000):
        rng = random.Random(seed)
        movies = pd.read_csv(PROCESSED_DIR / "movies.csv")
        persons = pd.read_csv(PROCESSED_DIR / "persons.csv")
        self._movie_ids = movies.movie_id.sample(min(pool_size, len(movies)), random_state=seed).tolist()
        self._person_ids = persons.person_id.sample(min(pool_size, len(persons)), random_state=seed).tolist()
        self._years = movies.year.dropna().unique().tolist()
        self._rng = rng

    def random_movie_id(self) -> str:
        return self._rng.choice(self._movie_ids)

    def random_person_id(self) -> str:
        return self._rng.choice(self._person_ids)

    def random_year(self) -> int:
        return int(self._rng.choice(self._years))


def load_all(adapter: GraphAdapter, batch_size: int = 500) -> dict[str, float]:
    movies = pd.read_csv(PROCESSED_DIR / "movies.csv").to_dict("records")
    persons = pd.read_csv(PROCESSED_DIR / "persons.csv").to_dict("records")
    edges = pd.read_csv(PROCESSED_DIR / "acted_in.csv")

    print(f"\nMovies: {len(movies)}")
    print(f"Persons: {len(persons)}")
    print(f"Relationships: {len(edges)}")

    print("\nCleaning database...")
    adapter.wipe_database()

    print("Creating indexes...")
    adapter.create_indexes()

    print("\nLoading Movie nodes...")
    start = time.perf_counter()

    n_movies = adapter.load_nodes(
        "Movie",
        movies,
        batch_size=batch_size,
    )

    print(f"✓ Loaded {n_movies} Movie nodes")

    print("\nLoading Person nodes...")

    n_persons = adapter.load_nodes(
        "Person",
        persons,
        batch_size=batch_size,
    )

    print(f"✓ Loaded {n_persons} Person nodes")

    node_elapsed = time.perf_counter() - start

    print("\nLoading ACTED_IN relationships...")

    edge_rows = (
        {
            "from_id": r["from_id"],
            "to_id": r["to_id"],
            "props": {
                "ordering": r["ordering"],
                "category": r["category"],
            },
        }
        for r in edges.to_dict("records")
    )

    start = time.perf_counter()

    n_edges = adapter.load_edges(
        "ACTED_IN",
        edge_rows,
        from_label="Person",
        from_key="person_id",
        to_label="Movie",
        to_key="movie_id",
        batch_size=batch_size,
    )

    print(f"✓ Loaded {n_edges} Relationships")

    # ==========================================
    # VERIFY DATABASE CONTENTS
    # ==========================================
     # ==========================================
    # VERIFY DATABASE CONTENTS
    # ==========================================
    print("\nVERIFYING DATABASE...")

    try:

        if adapter.__class__.__name__ == "ArangoAdapter":

            movies_count = adapter.run_query(
                "RETURN LENGTH(Movie)"
            )[0]

            persons_count = adapter.run_query(
                "RETURN LENGTH(Person)"
            )[0]

            rels_count = adapter.run_query(
                "RETURN LENGTH(ACTED_IN)"
            )[0]

        else:

            movies_count = adapter.run_query(
                "MATCH (m:Movie) RETURN count(m) AS c"
            )[0]["c"]

            persons_count = adapter.run_query(
                "MATCH (p:Person) RETURN count(p) AS c"
            )[0]["c"]

            rels_count = adapter.run_query(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            )[0]["c"]

        print(f"Movies in DB: {movies_count}")
        print(f"Persons in DB: {persons_count}")
        print(f"Relationships in DB: {rels_count}")

    except Exception as e:
        print(f"Verification failed: {e}")

    edge_elapsed = time.perf_counter() - start

    total_elapsed = node_elapsed + edge_elapsed

    print("\nBenchmark loading completed.\n")

    return {
        "nodes_loaded": n_movies + n_persons,
        "edges_loaded": n_edges,
        "node_load_seconds": round(node_elapsed, 3),
        "edge_load_seconds": round(edge_elapsed, 3),
        "total_load_seconds": round(total_elapsed, 3),
        "nodes_per_second": round(
            (n_movies + n_persons) / node_elapsed, 1
        ) if node_elapsed > 0 else None,
        "edges_per_second": round(
            n_edges / edge_elapsed, 1
        ) if edge_elapsed > 0 else None,
    }