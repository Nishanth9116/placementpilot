"""SQLite connection management for PlacementPilot.

Configures connection pragmas (WAL mode, foreign keys, row factory)
for local transactional consistency and concurrency.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from config.settings import settings


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection.

    Args:
        db_path: Path to SQLite database file. Defaults to settings.DATABASE_PATH.

    Returns:
        Configured sqlite3.Connection instance with Row factory and pragmas enabled.
    """
    target_path = db_path or settings.DATABASE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(target_path),
        timeout=10.0,
    )
    conn.row_factory = sqlite3.Row

    # Enable foreign keys and Write-Ahead Logging (WAL) for better local concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a transactional SQLite database connection.

    Automatically commits on normal exit and rolls back on unhandled exceptions.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

