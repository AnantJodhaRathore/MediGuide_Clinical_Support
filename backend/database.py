from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from backend.config import DATABASE_PATH

_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class Database:
    def __init__(self, path: Path | str = DATABASE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with _LOCK:
            conn = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            full_name TEXT NOT NULL DEFAULT '',
            age INTEGER,
            sex TEXT NOT NULL DEFAULT 'Prefer not to say',
            blood_group TEXT NOT NULL DEFAULT 'Unknown',
            conditions TEXT NOT NULL DEFAULT '',
            allergies TEXT NOT NULL DEFAULT '',
            emergency_contact TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            schedule TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms_json TEXT NOT NULL,
            severity_json TEXT NOT NULL,
            duration TEXT NOT NULL,
            probable_condition TEXT NOT NULL,
            confidence REAL NOT NULL,
            alternatives_json TEXT NOT NULL,
            urgency TEXT NOT NULL,
            red_flags_json TEXT NOT NULL,
            guidance_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
        );
        """
        with self.connection() as conn:
            conn.executescript(schema)
            conn.execute(
                "INSERT OR IGNORE INTO profiles (id, updated_at) VALUES (1, ?)",
                (utc_now(),),
            )

    def get_profile(self) -> dict[str, Any]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = 1").fetchone()
        return _row_to_dict(row) or {}

    def save_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE profiles
                SET full_name=?, age=?, sex=?, blood_group=?, conditions=?, allergies=?,
                    emergency_contact=?, updated_at=?
                WHERE id=1
                """,
                (
                    profile.get("full_name", ""),
                    profile.get("age"),
                    profile.get("sex", "Prefer not to say"),
                    profile.get("blood_group", "Unknown"),
                    profile.get("conditions", ""),
                    profile.get("allergies", ""),
                    profile.get("emergency_contact", ""),
                    utc_now(),
                ),
            )
        return self.get_profile()

    def list_medications(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM medications ORDER BY active DESC, created_at DESC"
            ).fetchall()
        return [dict(row) | {"active": bool(row["active"])} for row in rows]

    def add_medication(self, medication: dict[str, Any]) -> dict[str, Any]:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO medications (name, dosage, schedule, notes, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    medication["name"].strip(),
                    medication["dosage"].strip(),
                    medication["schedule"].strip(),
                    medication.get("notes", "").strip(),
                    int(medication.get("active", True)),
                    utc_now(),
                ),
            )
            row = conn.execute("SELECT * FROM medications WHERE id=?", (cursor.lastrowid,)).fetchone()
        result = dict(row)
        result["active"] = bool(result["active"])
        return result

    def delete_medication(self, medication_id: int) -> bool:
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM medications WHERE id=?", (medication_id,))
        return cursor.rowcount > 0

    def create_assessment(self, result: dict[str, Any]) -> dict[str, Any]:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO assessments (
                    symptoms_json, severity_json, duration, probable_condition, confidence,
                    alternatives_json, urgency, red_flags_json, guidance_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(result["symptoms"]),
                    json.dumps(result["severity"]),
                    result["duration"],
                    result["probable_condition"],
                    result["confidence"],
                    json.dumps(result["alternatives"]),
                    result["urgency"],
                    json.dumps(result["red_flags"]),
                    json.dumps(result["guidance"]),
                    result.get("created_at", utc_now()),
                ),
            )
            assessment_id = int(cursor.lastrowid)
        return self.get_assessment(assessment_id) or {}

    @staticmethod
    def _decode_assessment(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        for source, target in (
            ("symptoms_json", "symptoms"),
            ("severity_json", "severity"),
            ("alternatives_json", "alternatives"),
            ("red_flags_json", "red_flags"),
            ("guidance_json", "guidance"),
        ):
            item[target] = json.loads(item.pop(source))
        return item

    def get_assessment(self, assessment_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
        return self._decode_assessment(row) if row else None

    def list_assessments(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM assessments ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._decode_assessment(row) for row in rows]

    def delete_assessment(self, assessment_id: int) -> bool:
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM assessments WHERE id=?", (assessment_id,))
        return cursor.rowcount > 0

    def add_chat_message(self, assessment_id: int, role: str, content: str) -> dict[str, Any]:
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_messages (assessment_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (assessment_id, role, content, utc_now()),
            )
            row = conn.execute("SELECT * FROM chat_messages WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def list_chat_messages(self, assessment_id: int) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE assessment_id=? ORDER BY id", (assessment_id,)
            ).fetchall()
        return [dict(row) for row in rows]
