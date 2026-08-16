"""Deterministic relevance filtering for durable memory."""

from __future__ import annotations

import re
from collections.abc import Iterable

from roberta.memory.contracts import DurableMemoryStore, MemoryRecord

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "you",
    }
)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(str(value or "").casefold())
        if token not in _STOPWORDS and len(token) > 1
    }


def memory_relevance_score(record: MemoryRecord, query: str) -> int:
    """Return a deterministic lexical relevance score for one memory record."""

    query_tokens = _tokens(query)
    if not query_tokens:
        return 0

    topic_tokens = set()
    for topic in record.topics:
        topic_tokens.update(_tokens(topic))
    key_tokens = _tokens(record.key.replace(":", " ").replace("/", " "))
    category_tokens = _tokens(record.category.replace("_", " "))
    content_tokens = _tokens(record.content)
    rationale_tokens = _tokens(record.rationale or "")

    score = 0
    score += 6 * len(query_tokens & topic_tokens)
    score += 4 * len(query_tokens & key_tokens)
    score += 3 * len(query_tokens & category_tokens)
    score += 2 * len(query_tokens & content_tokens)
    score += len(query_tokens & rationale_tokens)
    return score


def select_relevant_memory(
    records: Iterable[MemoryRecord],
    query: str,
    *,
    limit: int = 6,
) -> list[MemoryRecord]:
    """Keep only query-relevant records in stable score/key order."""

    if limit <= 0:
        return []
    scored = [
        (memory_relevance_score(record, query), record)
        for record in records
    ]
    relevant = [(score, record) for score, record in scored if score > 0]
    relevant.sort(key=lambda item: (-item[0], item[1].key))
    return [record for _, record in relevant[:limit]]


def retrieve_relevant_memory(
    store: DurableMemoryStore,
    query: str,
    *,
    limit: int = 6,
) -> list[MemoryRecord]:
    """Search a provider and deterministically re-filter the returned candidates."""

    if limit <= 0 or not str(query or "").strip():
        return []
    candidates = store.search(query, limit=max(limit * 3, limit))
    return select_relevant_memory(candidates, query, limit=limit)
