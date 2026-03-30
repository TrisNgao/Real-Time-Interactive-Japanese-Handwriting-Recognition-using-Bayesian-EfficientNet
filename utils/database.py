import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "progress.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            char        TEXT PRIMARY KEY,
            attempts    INTEGER DEFAULT 0,
            correct     INTEGER DEFAULT 0,
            streak      INTEGER DEFAULT 0,
            last_score  REAL    DEFAULT 0,
            next_review REAL    DEFAULT 0,
            last_seen   TEXT    DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def get_progress(char):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT * FROM progress WHERE char=?", (char,))
    row  = c.fetchone()
    conn.close()
    if row:
        return {
            'char': row[0], 'attempts': row[1], 'correct': row[2],
            'streak': row[3], 'last_score': row[4],
            'next_review': row[5], 'last_seen': row[6]
        }
    return {
        'char': char, 'attempts': 0, 'correct': 0,
        'streak': 0, 'last_score': 0,
        'next_review': 0, 'last_seen': ''
    }


def update_progress(char, score):
    conn   = sqlite3.connect(DB_PATH)
    c      = conn.cursor()
    prog   = get_progress(char)
    is_ok  = score >= 0.7

    attempts = prog['attempts'] + 1
    correct  = prog['correct'] + (1 if is_ok else 0)
    streak   = prog['streak'] + 1 if is_ok else 0

    interval = prog.get('next_review', 0)
    if is_ok:
        interval = max(1, interval * (1.5 + streak * 0.1))
    else:
        interval = 1

    next_review = time.time() + interval * 3600
    last_seen   = datetime.now().strftime('%Y-%m-%d %H:%M')

    c.execute("""
        INSERT OR REPLACE INTO progress
        (char, attempts, correct, streak, last_score, next_review, last_seen)
        VALUES (?,?,?,?,?,?,?)
    """, (char, attempts, correct, streak, score, next_review, last_seen))
    conn.commit()
    conn.close()


def get_all_stats():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT char, attempts, correct, streak, last_score FROM progress")
    rows = c.fetchall()
    conn.close()
    return rows
