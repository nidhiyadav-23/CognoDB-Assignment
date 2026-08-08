"""Amazon Neptune adapter. Neptune has no native Bolt endpoint, but it does
support the openCypher query language over its HTTPS data API
(POST {endpoint}/openCypher), which lets us reuse the same Cypher query
templates from workloads.py almost unchanged - this is what "same logical
queries" means in practice for a platform with a different wire protocol.

Auth: SigV4-signs requests when AWS credentials are supplied; falls back to
unsigned requests for setups behind an SSH tunnel / VPC-internal test client
where IAM auth is disabled on the cluster. Document whichever mode you use
in the README - it affects network overhead and is a real fairness caveat.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

import requests

from .base import GraphAdapter

try:
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    from botocore.credentials import Credentials
    _HAS_BOTOCORE = True
except ImportError:
    _HAS_BOTOCORE = False


class NeptuneOpenCypherAdapter(GraphAdapter):
    def __init__(self, credentials: dict[str, str]):
        super().__init__(credentials)
        self.endpoint = credentials["endpoint"].rstrip("/")
        self._session = requests.Session()

    def connect(self) -> None:
        # Neptune's openCypher endpoint has no explicit "connect" call - do a
        # cheap status check so connection failures surface early, not on
        # the first timed query.
        resp = self._post_cypher("RETURN 1 AS ok")
        assert resp, "Neptune openCypher endpoint did not respond as expected"

    def close(self) -> None:
        self._session.close()

    def _post_cypher(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        url = f"{self.endpoint}/openCypher"
        body = {"query": query}
        if params:
            body["parameters"] = json.dumps(params)
        data = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in body.items())

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if _HAS_BOTOCORE and self.credentials.get("aws_access_key_id"):
            request = AWSRequest(method="POST", url=url, data=data, headers=headers)
            creds = Credentials(
                self.credentials["aws_access_key_id"],
                self.credentials["aws_secret_access_key"],
            )
            SigV4Auth(creds, "neptune-db", self.credentials.get("aws_region", "us-east-1")).add_auth(request)
            headers = dict(request.headers)

        resp = self._session.post(url, data=data, headers=headers, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("results", [])

    def wipe_database(self) -> None:
        while True:
            self._post_cypher("MATCH (n) WITH n LIMIT 10000 DETACH DELETE n")
            remaining = self._post_cypher("MATCH (n) RETURN count(n) AS c")
            if remaining[0]["c"] == 0:
                break

    def create_indexes(self) -> None:
        # Neptune does not support explicit index DDL via openCypher the way
        # Neo4j-family databases do - it auto-indexes properties used in
        # equality lookups. Documented here rather than silently omitted.
        pass

    def load_nodes(self, label: str, rows: Iterable[dict[str, Any]], batch_size: int = 1000) -> int:
        batch: list[dict[str, Any]] = []
        total = 0
        for row in rows:
            batch.append(row)
            if len(batch) >= batch_size:
                total += self._flush_nodes(label, batch)
                batch = []
        if batch:
            total += self._flush_nodes(label, batch)
        return total

    def _flush_nodes(self, label: str, batch: list[dict[str, Any]]) -> int:
        query = f"UNWIND $rows AS row CREATE (n:{label}) SET n = row"
        self._post_cypher(query, {"rows": batch})
        return len(batch)

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
        batch: list[dict[str, Any]] = []
        total = 0
        query = (
            f"UNWIND $rows AS row "
            f"MATCH (a:{from_label} {{{from_key}: row.from_id}}) "
            f"MATCH (b:{to_label} {{{to_key}: row.to_id}}) "
            f"CREATE (a)-[r:{rel_type}]->(b) SET r += row.props"
        )
        for row in rows:
            batch.append(row)
            if len(batch) >= batch_size:
                self._post_cypher(query, {"rows": batch})
                total += len(batch)
                batch = []
        if batch:
            self._post_cypher(query, {"rows": batch})
            total += len(batch)
        return total

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._post_cypher(query, params)

    def footprint(self) -> dict[str, Any]:
        try:
            nodes = self._post_cypher("MATCH (n) RETURN count(n) AS c")[0]["c"]
            rels = self._post_cypher("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
            return {
                "observable": True,
                "nodeCount": nodes,
                "relCount": rels,
                "note": "Storage/NCU memory usage not exposed via openCypher - "
                        "pull from CloudWatch (NeptuneDB metrics) manually for the README.",
            }
        except Exception as e:
            return {"observable": False, "reason": str(e)}
