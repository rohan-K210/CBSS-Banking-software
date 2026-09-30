"""
Database connection management for the CBSS backend.

Provides:
- Pooled connections via mysql.connector.pooling
- SQLAlchemy engine factory for pandas read_sql
- Context managers for safe connection lifecycle
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator

import mysql.connector
from mysql.connector import pooling
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool

from shared.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection pool (one pool per process)
# ---------------------------------------------------------------------------
_pool: pooling.MySQLConnectionPool | None = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """Return (or create) the mysql.connector connection pool."""
    global _pool
    if _pool is None:
        cfg = get_settings().database
        _pool = pooling.MySQLConnectionPool(
            pool_name="cbss_pool",
            pool_size=min(cfg.pool_size, 32),  # mysql.connector max is 32
            pool_reset_session=True,
            **cfg.mysql_connector_kwargs,
        )
        logger.info(
            "Database pool created: host=%s db=%s pool_size=%d",
            cfg.host,
            cfg.database,
            cfg.pool_size,
        )
    return _pool


@contextmanager
def get_connection() -> Generator:
    """
    Context manager that yields a mysql.connector connection.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = None
    try:
        conn = _get_pool().get_connection()
        yield conn
    except mysql.connector.Error as exc:
        logger.error("Database connection error: %s", exc)
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@contextmanager
def get_cursor(dictionary: bool = False) -> Generator:
    """
    Context manager that yields a mysql.connector cursor.

    Automatically closes cursor and commits/rollbacks the connection.

    Usage:
        with get_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ...")
            rows = cursor.fetchall()
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# SQLAlchemy engine (for pandas read_sql)
# ---------------------------------------------------------------------------
_engine: Engine | None = None


def get_sqlalchemy_engine() -> Engine:
    """Return a shared SQLAlchemy engine (created once per process)."""
    global _engine
    if _engine is None:
        url = get_settings().database.sqlalchemy_url
        _engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # verify connections before reuse
        )
        logger.info("SQLAlchemy engine created: host=%s", get_settings().database.host)
    return _engine


def close_resources() -> None:
    """Clean up database resources (call on process shutdown)."""
    global _pool, _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("SQLAlchemy engine disposed.")
    # mysql.connector pool doesn't have an explicit close; GC handles it.
    _pool = None
