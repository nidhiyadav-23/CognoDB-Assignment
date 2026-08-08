from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Workload:
    name: str
    category: str
    description: str
    queries: dict[str, str]
    param_fn: Callable[[Any], dict[str, Any]]


def _pick_person_id(sample_pool) -> dict[str, Any]:
    return {"person_id": sample_pool.random_person_id()}


def _pick_movie_id(sample_pool) -> dict[str, Any]:
    return {"movie_id": sample_pool.random_movie_id()}


def _pick_year(sample_pool) -> dict[str, Any]:
    return {"year": sample_pool.random_year()}


WORKLOADS: list[Workload] = [

    Workload(
        name="traversal_1hop",
        category="Traversals",
        description="From a random Person, return the Movies they acted in (1 hop).",
        queries={
            "cypher":
                """
                MATCH (p:Person {person_id: $person_id})-[:ACTED_IN]->(m:Movie)
                RETURN m.movie_id AS id
                """,

            "aql":
                """
                WITH Person, Movie
                FOR v, e IN 1..1 OUTBOUND CONCAT('Person/', @person_id) ACTED_IN
                RETURN v._key
                """
        },
        param_fn=_pick_person_id,
    ),

    Workload(
        name="traversal_2hop",
        category="Traversals",
        description="From a random Person, return co-stars.",
        queries={
            "cypher":
                """
                MATCH (p:Person {person_id: $person_id})
                      -[:ACTED_IN]->(:Movie)
                      <-[:ACTED_IN]-(costar:Person)
                RETURN DISTINCT costar.person_id AS id
                """,

            "aql":
                """
                WITH Person, Movie
                FOR v, e, p IN 2..2 ANY CONCAT('Person/', @person_id) ACTED_IN
                FILTER IS_SAME_COLLECTION('Person', v)
                RETURN DISTINCT v._key
                """
        },
        param_fn=_pick_person_id,
    ),

    Workload(
        name="traversal_3hop",
        category="Traversals",
        description="From a random Person, return co-stars' other movies.",
        queries={
            "cypher":
                """
                MATCH (p:Person {person_id: $person_id})
                      -[:ACTED_IN]->(:Movie)
                      <-[:ACTED_IN]-(:Person)
                      -[:ACTED_IN]->(m2:Movie)
                RETURN DISTINCT m2.movie_id AS id
                """,

            "aql":
                """
                WITH Person, Movie
                FOR v, e, p IN 3..3 ANY CONCAT('Person/', @person_id) ACTED_IN
                FILTER IS_SAME_COLLECTION('Movie', v)
                RETURN DISTINCT v._key
                """
        },
        param_fn=_pick_person_id,
    ),

    Workload(
        name="point_lookup",
        category="Lookups",
        description="Exact-match lookup of a single Movie by movie_id.",
        queries={
            "cypher":
                """
                MATCH (m:Movie {movie_id: $movie_id})
                RETURN m.title AS title, m.year AS year
                """,

            "aql":
                """
                FOR m IN Movie
                    FILTER m.movie_id == @movie_id
                    RETURN {
                        title: m.title,
                        year: m.year
                    }
                """
        },
        param_fn=_pick_movie_id,
    ),

    Workload(
        name="indexed_filtered_lookup",
        category="Lookups",
        description="Movies released in a given year.",
        queries={
            "cypher":
                """
                MATCH (m:Movie {year: $year})
                RETURN m.movie_id AS id, m.title AS title
                """,

            "aql":
                """
                FOR m IN Movie
                    FILTER m.year == @year
                    RETURN {
                        id: m.movie_id,
                        title: m.title
                    }
                """
        },
        param_fn=_pick_year,
    ),

    Workload(
        name="aggregation_by_category",
        category="Aggregations",
        description="Count ACTED_IN edges grouped by category.",
        queries={
            "cypher":
                """
                MATCH ()-[r:ACTED_IN]->()
                RETURN r.category AS category,
                       count(*) AS cnt
                ORDER BY category
                """,

            "aql":
                """
                FOR e IN ACTED_IN
                    COLLECT category = e.category
                    WITH COUNT INTO cnt
                    RETURN {
                        category,
                        cnt
                    }
                """
        },
        param_fn=lambda pool: {},
    ),
]


MIXED_WRITE_QUERIES = {
    "cypher":
        """
        MATCH (m:Movie {movie_id: $movie_id})
        SET m.bench_writes = coalesce(m.bench_writes, 0) + 1
        """,

    "aql":
        """
        FOR m IN Movie
            FILTER m.movie_id == @movie_id
            UPDATE m
            WITH {
                bench_writes:
                    (HAS(m, 'bench_writes')
                        ? m.bench_writes
                        : 0) + 1
            }
            IN Movie
        """
}


def dialect_for(query_dialect: str) -> str:
    return "cypher" if query_dialect in ("cypher", "opencypher") else query_dialect