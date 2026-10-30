import json
import os
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(os.getenv('EPIVIBE_DB_PATH', str(Path(__file__).resolve().parents[2] / 'data' / 'epivibe.sqlite3')))


class PostgresConnection:
    """SQLite-style execute/transaction interface over psycopg 3."""
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.conn.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self.conn.__exit__(exc_type, exc, tb)

    def execute(self, query, params=None):
        # All existing application queries use positional SQLite placeholders.
        query = query.replace('?', '%s')
        return self.conn.execute(query, params)


def has_table(db, name):
    if isinstance(db, PostgresConnection):
        return bool(db.execute('SELECT 1 FROM information_schema.tables WHERE table_schema=current_schema() AND table_name=?', (name,)).fetchone())
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def project_scoped_tables(db):
    """Discover project_id tables for complete project deletion."""
    if isinstance(db, PostgresConnection):
        rows = db.execute("""SELECT table_name FROM information_schema.columns
            WHERE table_schema=current_schema() AND column_name='project_id' """).fetchall()
        return [row['table_name'] for row in rows]
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return [row['name'] for row in rows if 'project_id' in {
        col['name'] for col in db.execute('PRAGMA table_info("' + row['name'].replace('"', '""') + '")')
    }]

def connect():
    url = os.getenv('DATABASE_URL', '').strip()
    if url:
        import psycopg
        from psycopg.rows import dict_row
        return PostgresConnection(psycopg.connect(url, row_factory=dict_row, connect_timeout=15))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH), timeout=15)
    db.row_factory = sqlite3.Row
    return db

def initialize():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Draft',
            brief_json TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )''')

# Research state is separate from project brief to preserve previous project data.
_old_initialize = initialize
def initialize():
    _old_initialize()
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS research_runs (project_id TEXT PRIMARY KEY, status TEXT NOT NULL, step INTEGER NOT NULL DEFAULT 0, percent INTEGER NOT NULL DEFAULT 0, error TEXT, evidence_json TEXT, updated_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id))""")
