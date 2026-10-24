import sqlite3
from .config import DB_PATH


def conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS seen (url TEXT PRIMARY KEY, posted INTEGER DEFAULT 0, ts DEFAULT CURRENT_TIMESTAMP)")
    return c


def is_seen(c, url):
    return c.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone() is not None


def mark(c, url, posted):
    c.execute("INSERT OR REPLACE INTO seen(url, posted) VALUES (?,?)", (url, int(posted)))
    c.commit()


def count(c):
    return c.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
