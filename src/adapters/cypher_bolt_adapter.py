"""
Single adapter for every platform that speaks Cypher over the Bolt
protocol via the official neo4j Python driver: CognoDB, Neo4j Aura,
Neo4j+ (self-managed), and Memgraph Cloud.
"""

from __future__ import annotations

import time
from typing import Any, Iterable

from neo4j import GraphDatabase

from .base import GraphAdapter


class CypherBoltAdapter(GraphAdapter):
    def __init__(self, credentials: dict[str, str]):
        super().__init__(credentials)
        self._driver = None

    def connect(self) -> None:
        self._driver = GraphDatabase.driver(
            self.credentials["uri"],
            auth=(
                self.credentials["user"],
                self.credentials["password"],
            ),
            connection_timeout=120,
            max_connection_lifetime=3600,
        )
        self._driver.verify_connectivity()

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def wipe_database(self) -> None:
        with self._driver.session() as session:

            print("\nCleaning existing database...")

            while True:
                result = session.run("""
                    MATCH (n)
                    WITH n LIMIT 10000
                    DETACH DELETE n
                    RETURN count(*) AS deleted
                """).single()

                deleted = result["deleted"]

                print(f"Deleted {deleted} nodes")

                if deleted == 0:
                    break

            try:
                indexes = session.run("SHOW INDEXES YIELD name")

                for rec in indexes:
                    try:
                        session.run(
                            f"DROP INDEX {rec['name']}"
                        ).consume()
                    except Exception:
                        pass
            except Exception:
                pass

            print("Database cleaned successfully.\n")

    def create_indexes(self) -> None:
        with self._driver.session() as session:
            session.run(
                "CREATE INDEX movie_id_idx IF NOT EXISTS FOR (m:Movie) ON (m.movie_id)"
            ).consume()

            session.run(
                "CREATE INDEX person_id_idx IF NOT EXISTS FOR (p:Person) ON (p.person_id)"
            ).consume()

            session.run(
                "CREATE INDEX movie_year_idx IF NOT EXISTS FOR (m:Movie) ON (m.year)"
            ).consume()

    def load_nodes(
        self,
        label: str,
        rows: Iterable[dict[str, Any]],
        batch_size: int = 500,
    ) -> int:

        batch = []
        total = 0

        with self._driver.session() as session:
            for row in rows:
                batch.append(row)

                if len(batch) >= batch_size:
                    total += self._flush_nodes(session, label, batch)
                    print(f"{label}: {total} loaded")
                    batch = []

            if batch:
                total += self._flush_nodes(session, label, batch)
                print(f"{label}: {total} loaded")

        return total

    def _flush_nodes(
        self,
        session,
        label: str,
        batch: list[dict[str, Any]],
    ) -> int:

        query = f"""
        UNWIND $rows AS row
        CREATE (n:{label})
        SET n = row
        """

        session.run(query, rows=batch).consume()
        time.sleep(0.05) 

        return len(batch)

    def load_edges(
        self,
        rel_type: str,
        rows: Iterable[dict[str, Any]],
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        batch_size: int = 500,
    ) -> int:

        batch = []
        total = 0

        query = (
            f"UNWIND $rows AS row "
            f"MATCH (a:{from_label} {{{from_key}: row.from_id}}) "
            f"MATCH (b:{to_label} {{{to_key}: row.to_id}}) "
            f"CREATE (a)-[r:{rel_type}]->(b) "
            f"SET r += row.props"
        )

        with self._driver.session() as session:
            for row in rows:
                batch.append(row)

                if len(batch) >= batch_size:
                    session.run(query, rows=batch).consume()
                    time.sleep(0.05) 
                    total += len(batch)
                    print(f"Relationships: {total} loaded")
                    batch = []

            if batch:
                session.run(query, rows=batch).consume()
                time.sleep(0.05) 
                total += len(batch)
                print(f"Relationships: {total} loaded")

        return total

    def run_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [dict(r) for r in result]

    def footprint(self) -> dict[str, Any]:
        try:
            with self._driver.session() as session:
                rec = session.run(
                    """
                    CALL apoc.meta.stats()
                    YIELD nodeCount, relCount
                    RETURN nodeCount, relCount
                    """
                ).single()

                return {
                    "observable": True,
                    "nodeCount": rec["nodeCount"],
                    "relCount": rec["relCount"],
                    "note": "APOC statistics",
                }

        except Exception:

            try:
                with self._driver.session() as session:

                    nodes = session.run(
                        "MATCH (n) RETURN count(n) AS c"
                    ).single()["c"]

                    rels = session.run(
                        "MATCH ()-[r]->() RETURN count(r) AS c"
                    ).single()["c"]

                    return {
                        "observable": True,
                        "nodeCount": nodes,
                        "relCount": rels,
                        "note": "Fallback count() queries",
                    }

            except Exception as e:
                return {
                    "observable": False,
                    "reason": str(e),
                }