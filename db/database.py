import sqlite3
import os
from pathlib import Path
from datetime import datetime


DB_DIR = Path.home() / ".local" / "share" / "english-tutor"
DB_PATH = DB_DIR / "tutor.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                level TEXT DEFAULT 'beginner',
                total_messages INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                positive TEXT,
                correction TEXT,
                tip TEXT,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            );

            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                session_id INTEGER NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                session_id INTEGER NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                accuracy_pct REAL DEFAULT 0.0,
                words_learned INTEGER DEFAULT 0,
                corrections_count INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)


def create_session(level: str = "beginner") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (created_at, level, total_messages) VALUES (?, ?, 0)",
            (datetime.utcnow().isoformat(),  level),
        )
        session_id = cur.lastrowid
        conn.execute(
            "INSERT INTO stats (session_id, accuracy_pct, words_learned, corrections_count) VALUES (?, 0, 0, 0)",
            (session_id,),
        )
        return session_id


def get_last_session() -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()


def save_message(session_id: int, role: str, content: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.execute(
            "UPDATE sessions SET total_messages = total_messages + 1 WHERE id = ?",
            (session_id,),
        )
        return cur.lastrowid


def save_feedback(message_id: int, positive: str, correction: str | None, tip: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO feedback (message_id, positive, correction, tip) VALUES (?, ?, ?, ?)",
            (message_id, positive, correction, tip),
        )


def save_vocabulary(words: list[str], session_id: int) -> None:
    if not words:
        return
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO vocabulary (word, first_seen, session_id) VALUES (?, ?, ?)",
            [(w, now, session_id) for w in words],
        )


def save_goals(goals: list[str], session_id: int) -> None:
    if not goals:
        return
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM goals WHERE session_id = ?", (session_id,))
        conn.executemany(
            "INSERT INTO goals (goal_text, created_at, session_id) VALUES (?, ?, ?)",
            [(g, now, session_id) for g in goals],
        )


def get_goals(session_id: int) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT goal_text FROM goals WHERE session_id = ?", (session_id,)
        ).fetchall()
        return [r["goal_text"] for r in rows]


def add_goal(goal_text: str, session_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO goals (goal_text, created_at, session_id) VALUES (?, ?, ?)",
            (goal_text, datetime.utcnow().isoformat(), session_id),
        )


def delete_goal(goal_text: str, session_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM goals WHERE goal_text = ? AND session_id = ?",
            (goal_text, session_id),
        )


def get_messages(session_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()


def update_stats(session_id: int, accuracy_pct: float, words_learned: int, corrections_count: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE stats SET accuracy_pct = ?, words_learned = ?, corrections_count = ?
               WHERE session_id = ?""",
            (accuracy_pct, words_learned, corrections_count, session_id),
        )
        conn.execute(
            "UPDATE sessions SET level = (SELECT level FROM sessions WHERE id = ?) WHERE id = ?",
            (session_id, session_id),
        )


def get_stats(session_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM stats WHERE session_id = ?", (session_id,)
        ).fetchone()


def get_cumulative_stats() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT AVG(accuracy_pct) as avg_acc, SUM(words_learned) as total_words, SUM(corrections_count) as total_corrections FROM stats"
        ).fetchone()
        sessions = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
        return {
            "avg_accuracy": row["avg_acc"] or 0.0,
            "total_words": row["total_words"] or 0,
            "total_corrections": row["total_corrections"] or 0,
            "total_sessions": sessions["cnt"] or 0,
        }


def update_session_level(session_id: int, level: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET level = ? WHERE id = ?",
            (level, session_id),
        )
