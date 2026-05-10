"""Postgres helpers — insert into pg.statements and pg.scrape_errors.

Connection comes from $POSTGRES_URL (sourced from k8s secret pg-creds).
Per kickoff: write failures HALT the run — do not retry-and-pray.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg import sql

log = logging.getLogger(__name__)


def _conn_str() -> str:
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL is not set in the environment")
    return url


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(_conn_str(), autocommit=False)
    try:
        yield conn
    finally:
        conn.close()


def insert_statement(conn: psycopg.Connection, row: dict[str, Any]) -> str | None:
    """Insert a row into `statements`. Idempotent via ON CONFLICT DO NOTHING.

    Returns the new row's id (uuid as str) on insert; None if duplicate.
    """
    q = sql.SQL(
        """
        INSERT INTO statements
            (politician, statement_or_decision, source_url, published_date,
             kind, confidence, raw_html)
        VALUES
            (%(politician)s, %(statement_or_decision)s, %(source_url)s,
             %(published_date)s, %(kind)s, %(confidence)s, %(raw_html)s)
        ON CONFLICT ON CONSTRAINT statements_dedup_key DO NOTHING
        RETURNING id;
        """
    )
    with conn.cursor() as cur:
        cur.execute(q, row)
        result = cur.fetchone()
    return str(result[0]) if result else None


def insert_scrape_error(
    conn: psycopg.Connection,
    *,
    source_url: str,
    politician: str | None,
    fetcher: str,
    http_status: int | None,
    kind: str,
    detail: str | None = None,
) -> str:
    q = sql.SQL(
        """
        INSERT INTO scrape_errors (source_url, politician, fetcher, http_status, kind, detail)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
    )
    with conn.cursor() as cur:
        cur.execute(q, (source_url, politician, fetcher, http_status, kind, detail))
        result = cur.fetchone()
    return str(result[0])


def count_statements(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM statements;")
        return int(cur.fetchone()[0])


def fetch_review_queue(conn: psycopg.Connection, *, limit: int = 5) -> list[dict[str, Any]]:
    """Top-confidence query per kickoff §5.1."""
    q = """
        SELECT id, politician, kind, published_date, confidence,
               statement_or_decision, source_url
        FROM statements
        ORDER BY confidence DESC NULLS LAST, scraped_at DESC
        LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(q, (limit,))
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
