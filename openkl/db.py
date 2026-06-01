"""
Database layer using LadybugDB for graph storage and vector search.
"""

import logging
from pathlib import Path

import ladybug as graphdb

logger = logging.getLogger(__name__)

# Default database path
DB_PATH = Path.home() / ".ok" / "ladybug"
LEGACY_KUZU_DB_PATH = Path.home() / ".ok" / "kuzu"

# LadybugDB schema definitions
SCHEMA = [
    # Memory nodes
    "CREATE NODE TABLE IF NOT EXISTS MemoryNote(id STRING PRIMARY KEY, text STRING, ts STRING, tags STRING[], vec FLOAT[384]);",
    # Grounding Store nodes
    "CREATE NODE TABLE IF NOT EXISTS Doc(id STRING PRIMARY KEY, path STRING, sha256 STRING);",
    "CREATE NODE TABLE IF NOT EXISTS Chunk(id STRING PRIMARY KEY, text STRING, span STRING, vec FLOAT[384]);",
    # Entity and topic nodes
    "CREATE NODE TABLE IF NOT EXISTS Entity(id STRING PRIMARY KEY, name STRING, type STRING);",
    "CREATE NODE TABLE IF NOT EXISTS Topic(id STRING PRIMARY KEY, name STRING);",
    # Relationships
    "CREATE REL TABLE IF NOT EXISTS HAS_CHUNK(FROM Doc TO Chunk);",
    "CREATE REL TABLE IF NOT EXISTS Mentions(FROM Chunk TO Entity);",
    "CREATE REL TABLE IF NOT EXISTS MemMentions(FROM MemoryNote TO Entity);",
    "CREATE REL TABLE IF NOT EXISTS DerivedFrom(FROM MemoryNote TO Chunk);",
    "CREATE REL TABLE IF NOT EXISTS HasTopic(FROM MemoryNote TO Topic);",
]

# Global connection
_connection: graphdb.Connection | None = None


def init_db(db_path: Path | None = None) -> graphdb.Connection:
    """Initialize the LadybugDB database with schema."""
    global _connection

    if db_path is None:
        db_path = DB_PATH
        if LEGACY_KUZU_DB_PATH.exists() and not DB_PATH.exists():
            logger.warning(
                "Found legacy Kuzu database at %s. OpenKL now uses LadybugDB at %s. "
                "Rebuild or migrate the derived graph before relying on old graph data.",
                LEGACY_KUZU_DB_PATH,
                DB_PATH,
            )

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create database and connection
    db = graphdb.Database(str(db_path))
    conn = graphdb.Connection(db)

    # Install and load vector extension
    try:
        conn.execute("INSTALL VECTOR;")
        conn.execute("LOAD VECTOR;")
        logger.info("Vector extension installed and loaded")
    except Exception as e:
        logger.error("Failed to install vector extension: %s", e)
        raise RuntimeError("Vector extension is required for OpenKL") from e

    # Create schema
    for stmt in SCHEMA:
        conn.execute(stmt)
        logger.debug(f"Executed schema statement: {stmt[:50]}...")

    _connection = conn
    logger.info(f"Database initialized at {db_path}")
    return conn


def get_connection() -> graphdb.Connection:
    """Get the database connection, initializing if needed."""
    global _connection

    if _connection is None:
        _connection = init_db()

    return _connection


def close_connection() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")
