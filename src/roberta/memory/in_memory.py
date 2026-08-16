"""Deterministic in-memory implementation of Roberta's durable-memory contract."""

from __future__ import annotations

from collections.abc import Iterable

from roberta.memory.contracts import MemoryRecord
from roberta.memory.retrieval import select_relevant_memory


class InMemoryDurableMemoryStore:
    """Simple deterministic store for tests and local development."""

    def __init__(self, records: Iterable[MemoryRecord] = ()) -> None:
        self._records: dict[str, MemoryRecord] = {}
        for record in records:
            self.upsert(record)

    def get(self, key: str) -> MemoryRecord | None:
        return self._records.get(key)

    def upsert(self, record: MemoryRecord) -> None:
        self._records[record.key] = record

    def search(self, query: str, *, limit: int = 12) -> list[MemoryRecord]:
        return select_relevant_memory(self._records.values(), query, limit=limit)

    def all_records(self) -> list[MemoryRecord]:
        """Return records in stable key order for deterministic tests/inspection."""

        return [self._records[key] for key in sorted(self._records)]
