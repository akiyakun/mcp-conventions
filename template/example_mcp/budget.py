"""Persistent atomic call reservation. Failures still count; no automatic retry."""
import sqlite3
import time
from contextlib import closing
from datetime import datetime

from .config import Settings


class BudgetError(ValueError):
    pass


def reserve(settings: Settings) -> None:
    now = time.time()
    day = datetime.fromtimestamp(now, settings.timezone).date().isoformat()
    with closing(sqlite3.connect(settings.usage_db, timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS calls (started REAL NOT NULL, day TEXT NOT NULL)")
        db.execute("BEGIN IMMEDIATE")
        recent = db.execute("SELECT count(*) FROM calls WHERE started > ?",
                            (now - settings.window_seconds,)).fetchone()[0]
        today = db.execute("SELECT count(*) FROM calls WHERE day = ?", (day,)).fetchone()[0]
        if recent >= settings.calls_per_window or today >= settings.calls_per_day:
            raise BudgetError("API呼び出し回数の上限です。この依頼で再試行しないでください。")
        db.execute("INSERT INTO calls VALUES (?, ?)", (now, day))
