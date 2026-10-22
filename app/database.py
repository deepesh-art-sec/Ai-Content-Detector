"""
SQLite database management for analysis history conforming to VeritasDoc Specification.
Uses standard library sqlite3 without any ORM.
Implements retry logic for database lock resilience and automatic schema migration.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional
from app.config import DATABASE_PATH

logger = logging.getLogger("ai_detector.database")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analyses (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  verdict TEXT NOT NULL,
  verdict_zone TEXT DEFAULT 'GREEN',
  ai_percentage REAL NOT NULL,
  total_sentences INTEGER NOT NULL,
  ai_sentences INTEGER NOT NULL,
  total_words INTEGER DEFAULT 0,
  sha256_hash TEXT DEFAULT '',
  sensitivity_mode TEXT DEFAULT 'balanced',
  model_used TEXT NOT NULL,
  sentences TEXT NOT NULL,        -- JSON string
  sections TEXT DEFAULT '[]',     -- JSON string
  attribution TEXT DEFAULT '{}',  -- JSON string
  evasion TEXT DEFAULT '{}',      -- JSON string
  plagiarism TEXT DEFAULT '{}',   -- JSON string
  ensemble TEXT DEFAULT '{}',     -- JSON string
  forensic_metrics TEXT DEFAULT '{}', -- JSON string
  esl_guardrail TEXT DEFAULT '{}',    -- JSON string
  created_at TEXT NOT NULL        -- ISO 8601
);
CREATE INDEX IF NOT EXISTS idx_created ON analyses(created_at DESC);
"""


def get_connection(db_path: Path | str = DATABASE_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with timeout and dictionary row factory."""
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def _execute_with_retry(fn, max_retries: int = 1, delay: float = 0.2) -> Any:
    """Execute a database function, retrying once if database is locked."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries:
                logger.warning("Database locked, retrying operation in %ss...", delay)
                time.sleep(delay)
                continue
            logger.error("Database operational error: %s", e)
            raise


def init_db(db_path: Path | str = DATABASE_PATH) -> None:
    """Initialize SQLite database with schema, WAL mode, and migrations."""
    def _init():
        with get_connection(db_path) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.executescript(SCHEMA_SQL)

            # Safe column migrations for existing databases
            existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(analyses);").fetchall()}
            migrations = [
                ("total_words", "INTEGER DEFAULT 0"),
                ("verdict_zone", "TEXT DEFAULT 'GREEN'"),
                ("sha256_hash", "TEXT DEFAULT ''"),
                ("sensitivity_mode", "TEXT DEFAULT 'balanced'"),
                ("sections", "TEXT DEFAULT '[]'"),
                ("attribution", "TEXT DEFAULT '{}'"),
                ("evasion", "TEXT DEFAULT '{}'"),
                ("plagiarism", "TEXT DEFAULT '{}'"),
                ("ensemble", "TEXT DEFAULT '{}'"),
                ("forensic_metrics", "TEXT DEFAULT '{}'"),
                ("esl_guardrail", "TEXT DEFAULT '{}'"),
            ]
            for col_name, col_type in migrations:
                if col_name not in existing_cols:
                    try:
                        conn.execute(f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type};")
                        logger.info("Migrated database: added column %s", col_name)
                    except Exception as e:
                        logger.warning("Could not add column %s: %s", col_name, e)

            conn.commit()

    _execute_with_retry(_init)
    logger.info("Database initialized successfully at %s", db_path)


def insert_analysis(record: dict[str, Any], db_path: Path | str = DATABASE_PATH) -> None:
    """
    Insert a complete analysis record including sections, attribution, evasion, plagiarism, and ensemble.
    """
    def _to_json(val, default):
        if val is None:
            return json.dumps(default)
        if isinstance(val, str):
            return val
        return json.dumps(val, ensure_ascii=False)

    sentences_str = _to_json(record.get("sentences"), [])
    sections_str = _to_json(record.get("sections"), [])
    attribution_str = _to_json(record.get("attribution"), {})
    evasion_str = _to_json(record.get("evasion"), {})
    plagiarism_str = _to_json(record.get("plagiarism"), {})
    ensemble_str = _to_json(record.get("ensemble"), {})
    forensic_str = _to_json(record.get("forensic_metrics"), {})
    esl_str = _to_json(record.get("esl_guardrail"), {})

    query = """
    INSERT INTO analyses (
      id, filename, file_path, verdict, verdict_zone, ai_percentage,
      total_sentences, ai_sentences, total_words, sha256_hash, sensitivity_mode, model_used,
      sentences, sections, attribution, evasion, plagiarism, ensemble, forensic_metrics, esl_guardrail, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    params = (
        record["id"],
        record["filename"],
        record["file_path"],
        record["verdict"],
        record.get("verdict_zone", "GREEN"),
        float(record["ai_percentage"]),
        int(record["total_sentences"]),
        int(record["ai_sentences"]),
        int(record.get("total_words", 0)),
        record.get("sha256_hash", ""),
        record.get("sensitivity_mode", "balanced"),
        record["model_used"],
        sentences_str,
        sections_str,
        attribution_str,
        evasion_str,
        plagiarism_str,
        ensemble_str,
        forensic_str,
        esl_str,
        record["created_at"],
    )

    def _insert():
        with get_connection(db_path) as conn:
            conn.execute(query, params)
            conn.commit()

    _execute_with_retry(_insert)


def list_analyses(db_path: Path | str = DATABASE_PATH) -> list[dict[str, Any]]:
    """List summary of past analyses ordered by created_at DESC."""
    query = """
    SELECT id, filename, file_path, verdict, verdict_zone, ai_percentage,
           total_sentences, ai_sentences, total_words, sha256_hash, sensitivity_mode, model_used,
           attribution, ensemble, created_at
    FROM analyses
    ORDER BY created_at DESC;
    """

    def _list():
        with get_connection(db_path) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                for f in ["attribution", "ensemble"]:
                    try:
                        item[f] = json.loads(item[f]) if item.get(f) else {}
                    except Exception:
                        item[f] = {}
                results.append(item)
            return results

    return _execute_with_retry(_list)


def get_analysis(analysis_id: str, db_path: Path | str = DATABASE_PATH) -> Optional[dict[str, Any]]:
    """Get full analysis details including parsed sentences, sections, ensemble, and forensic audits."""
    query = """
    SELECT id, filename, file_path, verdict, verdict_zone, ai_percentage,
           total_sentences, ai_sentences, total_words, sha256_hash, sensitivity_mode, model_used,
           sentences, sections, attribution, evasion, plagiarism, ensemble, forensic_metrics, esl_guardrail, created_at
    FROM analyses
    WHERE id = ?;
    """

    def _get():
        with get_connection(db_path) as conn:
            cursor = conn.execute(query, (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            for json_field in ["sentences", "sections", "attribution", "evasion", "plagiarism", "ensemble", "forensic_metrics", "esl_guardrail"]:
                try:
                    data[json_field] = json.loads(data[json_field]) if data.get(json_field) else ([] if json_field in ["sentences", "sections"] else {})
                except Exception:
                    data[json_field] = [] if json_field in ["sentences", "sections"] else {}
            return data

    return _execute_with_retry(_get)


def delete_analysis(analysis_id: str, db_path: Path | str = DATABASE_PATH) -> Optional[dict[str, Any]]:
    """Delete an analysis row by ID. Returns the deleted record metadata or None."""
    def _delete():
        with get_connection(db_path) as conn:
            cursor = conn.execute("SELECT id, file_path FROM analyses WHERE id = ?;", (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            record = dict(row)
            conn.execute("DELETE FROM analyses WHERE id = ?;", (analysis_id,))
            conn.commit()
            return record

    return _execute_with_retry(_delete)
