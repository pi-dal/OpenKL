from openkl.db import close_connection, init_db
from openkl.vector_search import create_vector_indexes, search_memory_vectors


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
        assert results[0]["id"] == "m-test"
    finally:
        close_connection()
