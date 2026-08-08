from __future__ import annotations

from typing import Any, Iterable

import pandas as pd
from arango import ArangoClient

from .base import GraphAdapter


class ArangoAdapter(GraphAdapter):
    def __init__(self, credentials: dict[str, str]):
        super().__init__(credentials)
        self._client = None
        self._db = None

    def connect(self) -> None:
        self._client = ArangoClient(hosts=self.credentials["url"])

        sys_db = self._client.db(
            "_system",
            username=self.credentials["user"],
            password=self.credentials["password"],
        )

        db_name = self.credentials["db"]

        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)

        self._db = self._client.db(
            db_name,
            username=self.credentials["user"],
            password=self.credentials["password"],
        )

    def close(self) -> None:
        pass

    def wipe_database(self) -> None:
        for coll_name in ("Movie", "Person", "ACTED_IN"):
            if self._db.has_collection(coll_name):
                self._db.delete_collection(coll_name)

        self._db.create_collection("Movie")
        self._db.create_collection("Person")
        self._db.create_collection("ACTED_IN", edge=True)

    def create_indexes(self) -> None:
        self._db.collection("Movie").add_persistent_index(
            fields=["movie_id"],
            unique=True,
        )

        self._db.collection("Person").add_persistent_index(
            fields=["person_id"],
            unique=True,
        )

        self._db.collection("Movie").add_persistent_index(
            fields=["year"]
        )

    def load_nodes(
        self,
        label: str,
        rows: Iterable[dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:

        coll = self._db.collection(label)

        batch = []
        total = 0

        key_field = "movie_id" if label == "Movie" else "person_id"

        for row in rows:

            doc = {}

            for k, v in row.items():

                if pd.isna(v):
                    doc[k] = None
                else:
                    doc[k] = v

            raw_id = str(doc[key_field])

            raw_id = raw_id.replace("tt", "")
            raw_id = raw_id.replace("nm", "")

            doc["_key"] = raw_id

            batch.append(doc)

            if len(batch) >= batch_size:
                try:
                    coll.insert_many(batch, overwrite=True)
                except Exception as e:
                    print("\n====================")
                    print("FAILED DOCUMENT")
                    print("====================")
                    print(batch[0])
                    print("\nERROR:")
                    print(e)
                    print("====================\n")
                    raise

                total += len(batch)
                batch = []

        if batch:
            try:
                coll.insert_many(batch, overwrite=True)
            except Exception as e:
                print("\n====================")
                print("FAILED DOCUMENT")
                print("====================")
                print(batch[0])
                print("\nERROR:")
                print(e)
                print("====================\n")
                raise

            total += len(batch)

        return total

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

        coll = self._db.collection(rel_type)

        batch = []
        total = 0

        for row in rows:

            doc = {}

            props = row.get("props", {})

            for k, v in props.items():
                if pd.isna(v):
                    doc[k] = None
                else:
                    doc[k] = v

            from_id = str(row["from_id"])
            to_id = str(row["to_id"])

            from_id = from_id.replace("nm", "")
            to_id = to_id.replace("tt", "")

            doc["_from"] = f"{from_label}/{from_id}"
            doc["_to"] = f"{to_label}/{to_id}"

            batch.append(doc)

            if len(batch) >= batch_size:
                coll.insert_many(batch)
                total += len(batch)
                batch = []

        if batch:
            coll.insert_many(batch)
            total += len(batch)

        return total

    def run_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        cursor = self._db.aql.execute(
            query,
            bind_vars=params or {},
        )

        return list(cursor)

    def footprint(self) -> dict[str, Any]:
        try:
            movie_count = self._db.collection("Movie").count()
            person_count = self._db.collection("Person").count()
            edge_count = self._db.collection("ACTED_IN").count()

            return {
                "observable": True,
                "nodeCount": movie_count + person_count,
                "relCount": edge_count,
            }

        except Exception as e:
            return {
                "observable": False,
                "reason": str(e),
            }