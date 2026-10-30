import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv('EPIVIBE_DB_PATH', str(Path(__file__).resolve().parents[2] / 'data' / 'epivibe.sqlite3')))

def connect():
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
