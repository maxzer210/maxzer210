from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class User:
    tg_id: int
    full_name: str
    qr_code: str
    created_at: str


class Storage:
    def __init__(self, db_path: str = "tea_kitsune.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    qr_code TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tea_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER NOT NULL,
                    tea_name TEXT NOT NULL,
                    taste TEXT NOT NULL,
                    impression TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tg_id) REFERENCES users (tg_id)
                );

                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tg_id) REFERENCES users (tg_id)
                );
                """
            )

    def get_or_create_user(self, tg_id: int, full_name: str) -> User:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
            if row:
                return User(**dict(row))

            qr_code = f"KITSUNE-{uuid.uuid4().hex[:12].upper()}"
            created_at = datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO users (tg_id, full_name, qr_code, created_at) VALUES (?, ?, ?, ?)",
                (tg_id, full_name, qr_code, created_at),
            )
            return User(tg_id=tg_id, full_name=full_name, qr_code=qr_code, created_at=created_at)

    def add_note(self, tg_id: int, tea_name: str, taste: str, impression: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tea_notes (tg_id, tea_name, taste, impression, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tg_id, tea_name, taste, impression, datetime.utcnow().isoformat()),
            )

    def get_notes(self, tg_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM tea_notes WHERE tg_id = ? ORDER BY created_at DESC LIMIT ?",
                (tg_id, limit),
            ).fetchall()

    def add_visit_by_code(self, qr_code: str, source: str = "admin_scan") -> int | None:
        with self._connect() as conn:
            row = conn.execute("SELECT tg_id FROM users WHERE qr_code = ?", (qr_code.strip(),)).fetchone()
            if not row:
                return None
            tg_id = int(row["tg_id"])
            conn.execute(
                "INSERT INTO visits (tg_id, source, created_at) VALUES (?, ?, ?)",
                (tg_id, source, datetime.utcnow().isoformat()),
            )
            return tg_id

    def visits_count(self, tg_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM visits WHERE tg_id = ?", (tg_id,)).fetchone()
            return int(row["cnt"])

    def find_user_by_tg_id(self, tg_id: int) -> User | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
            if not row:
                return None
            return User(**dict(row))
