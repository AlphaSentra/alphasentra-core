from __future__ import annotations

from typing import Any

from pymongo import ReplaceOne
from pymongo.collection import Collection

from helpers import DatabaseManager


class InvestorRepository:
    """MongoDB persistence layer for eToro Pro Investor records."""

    def __init__(self, db_name: str = "alphasentra-core") -> None:
        self.db_name = db_name
        self._collection: Collection | None = None

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            client = DatabaseManager().get_client()
            self._collection = client[self.db_name]["etoro_pi"]
            try:
                self._collection.create_index("userName", unique=True)
            except Exception:
                pass
        return self._collection

    def bulk_upsert(self, investors: list[dict[str, Any]], batch_size: int = 500) -> None:
        operations: list[ReplaceOne] = []
        skipped = 0
        for inv in investors:
            uname = inv.get("userName")
            if not uname:
                skipped += 1
                continue
            doc = dict(inv)
            doc["_id"] = uname
            operations.append(ReplaceOne({"_id": uname}, doc, upsert=True))

        if not operations:
            return

        chunks = [
            operations[i : i + batch_size]
            for i in range(0, len(operations), batch_size)
        ]

        for chunk in chunks:
            self.collection.bulk_write(chunk, ordered=False)
