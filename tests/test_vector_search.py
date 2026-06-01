import pytest

import openkl.vector_search as vector_search
from openkl.db import close_connection, init_db
from openkl.vector_search import (
    create_vector_indexes,
    search_chunk_vectors,
    search_memory_vectors,
)


def test_memory_vector_search_round_trip(tmp_path):
    conn = init_db(tmp_path / "ladybug")
    try:
        conn.execute(
            "CREATE (m:MemoryNote {id: $id, text: $text, ts: $ts, tags: $tags, vec: $vec})",
            {
                "id": "m-test",
                "text": "ladybug migration",
                "ts": "2026-05-31T00:00:00",
                "tags": ["test"],
                "vec": [0.1] * 384,
            },
        )

        create_vector_indexes()

        results = search_memory_vectors([0.1] * 384, k=1)
        assert results, "Expected at least one vector-search result"
        assert results[0]["id"] == "m-test"
    finally:
        close_connection()


def test_vector_search_rejects_non_numeric_vectors_before_db_access(monkeypatch):
    def fail_get_connection():
        raise AssertionError("database should not be touched for invalid vectors")

    monkeypatch.setattr(vector_search, "get_connection", fail_get_connection)

    with pytest.raises(ValueError, match="query_vector must contain only numeric"):
        search_memory_vectors(["not-a-number"], k=1)


def test_vector_search_rejects_invalid_k_before_db_access(monkeypatch):
    def fail_get_connection():
        raise AssertionError("database should not be touched for invalid k")

    monkeypatch.setattr(vector_search, "get_connection", fail_get_connection)

    with pytest.raises(ValueError, match="k must be between"):
        search_chunk_vectors([0.1] * 384, k=0)
