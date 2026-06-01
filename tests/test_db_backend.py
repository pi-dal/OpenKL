import logging

import openkl.db as db_module
from openkl.db import close_connection, init_db


def test_init_db_creates_core_schema(tmp_path):
    conn = init_db(tmp_path / "ladybug")
    try:
        result = conn.execute("MATCH (m:MemoryNote) RETURN count(m)")
        assert list(result)[0][0] == 0
    finally:
        close_connection()


def test_init_db_warns_when_legacy_kuzu_path_exists(tmp_path, monkeypatch, caplog):
    legacy_path = tmp_path / "kuzu"
    ladybug_path = tmp_path / "ladybug"
    legacy_path.mkdir()

    monkeypatch.setattr(db_module, "LEGACY_KUZU_DB_PATH", legacy_path)
    monkeypatch.setattr(db_module, "DB_PATH", ladybug_path)

    caplog.set_level(logging.WARNING, logger="openkl.db")
    init_db()
    try:
        assert "Found legacy Kuzu database" in caplog.text
        assert "OpenKL now uses LadybugDB" in caplog.text
        assert ladybug_path.exists()
    finally:
        close_connection()
