"""SQLite schema for document-level joking extraction."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DDL = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS document (
  doc_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  region TEXT NOT NULL,
  ethnography_group_name TEXT NOT NULL,
  pdf_path TEXT NOT NULL,
  md_raw_path TEXT,
  md_clean_path TEXT,
  char_count INTEGER,
  truncated INTEGER DEFAULT 0,
  converted_at TEXT,
  extracted_at TEXT,
  extract_model TEXT,
  extract_warnings TEXT
);

CREATE TABLE IF NOT EXISTS joking_relationship (
  relationship_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT NOT NULL,
  region TEXT NOT NULL,
  ethnography_group_name TEXT NOT NULL,
  entity_a_raw TEXT NOT NULL,
  entity_a_type TEXT NOT NULL,
  entity_b_raw TEXT NOT NULL,
  entity_b_type TEXT NOT NULL,
  scope_coded TEXT NOT NULL,
  reasoning TEXT,
  supporting_quote_raw TEXT,
  relation_label_raw TEXT,
  local_term_raw TEXT,
  symmetry_coded TEXT,
  relation_type_coded TEXT,
  confidence REAL,
  notes TEXT,
  extracted_at TEXT,
  FOREIGN KEY (doc_id) REFERENCES document(doc_id)
);

CREATE INDEX IF NOT EXISTS idx_jr_doc ON joking_relationship(doc_id);
CREATE INDEX IF NOT EXISTS idx_jr_scope ON joking_relationship(scope_coded);
"""


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    return con
