# RISKCORE Database Connection
# On-premises PostgreSQL - NO CLOUD STORAGE

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Generator
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Connection pool (initialized lazily)
_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def get_connection_pool() -> pool.ThreadedConnectionPool:
    """
    Get or create the database connection pool.

    Uses ThreadedConnectionPool for thread-safe connection management.
    Pool is created lazily on first use.
    """
    global _connection_pool

    if _connection_pool is None:
        settings = get_settings()

        logger.info(f"Creating database connection pool to {settings.database_url[:50]}...")

        _connection_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=settings.database_url,
        )

        logger.info("Database connection pool created")

    return _connection_pool


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager for database connections.

    Automatically returns connection to pool when done.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM positions")
                results = cur.fetchall()
    """
    connection_pool = get_connection_pool()
    conn = connection_pool.getconn()

    try:
        yield conn
    finally:
        connection_pool.putconn(conn)


@contextmanager
def get_db_cursor(dict_cursor: bool = True) -> Generator[psycopg2.extensions.cursor, None, None]:
    """
    Context manager for database cursor with automatic commit/rollback.

    Args:
        dict_cursor: If True, returns RealDictCursor (rows as dicts)

    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM positions WHERE id = %s", (position_id,))
            position = cur.fetchone()
    """
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)

        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def get_db() -> psycopg2.extensions.connection:
    """
    FastAPI dependency for database access.

    Note: This returns a connection from the pool. The caller is responsible
    for returning it. For most cases, use get_db_connection() context manager instead.

    Usage:
        @app.get("/items")
        def get_items(conn = Depends(get_db)):
            # Use connection
            # Connection is returned to pool after request
    """
    connection_pool = get_connection_pool()
    return connection_pool.getconn()


def release_db(conn: psycopg2.extensions.connection):
    """Return a connection to the pool."""
    connection_pool = get_connection_pool()
    connection_pool.putconn(conn)


def close_all_connections():
    """
    Close all connections in the pool.
    Call this on application shutdown.
    """
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("All database connections closed")


# Health check
def check_database_connection() -> dict:
    """
    Check database connectivity.

    Returns:
        dict with status and optional error
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "connected", "error": None}
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {"status": "error", "error": str(e)}
