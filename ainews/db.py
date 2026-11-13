import json
import sqlite3
from .config import DB_PATH


def conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS seen (url TEXT PRIMARY KEY, posted INTEGER DEFAULT 0, ts DEFAULT CURRENT_TIMESTAMP)")
    if "title" not in [r[1] for r in c.execute("PRAGMA table_info(seen)")]:
        c.execute("ALTER TABLE seen ADD COLUMN title TEXT DEFAULT ''")
    # Navbat: yaxshi baholangan, lekin hali e'lon qilinmagan yangiliklar.
    # data — tayyor tarjima (nashrda xato bo'lsa, qayta tarjima qilib pul/limit sarflamaslik uchun).
    c.execute("""CREATE TABLE IF NOT EXISTS queue (
        url TEXT PRIMARY KEY, title TEXT, score INTEGER, data TEXT,
        tries INTEGER DEFAULT 0, ts DEFAULT CURRENT_TIMESTAMP)""")
    c.commit()
    return c


def is_seen(c, url):
    return c.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone() is not None


def mark(c, url, posted, title=""):
    """Yakuniy holat: e'lon qilindi yoki o'tkazib yuborildi. Navbatdan ham olib tashlanadi."""
    c.execute("INSERT OR REPLACE INTO seen(url, posted, title) VALUES (?,?,?)", (url, int(posted), title))
    c.execute("DELETE FROM queue WHERE url=?", (url,))
    c.commit()


def count(c):
    return c.execute("SELECT COUNT(*) FROM seen").fetchone()[0]


def in_queue(c, url):
    return c.execute("SELECT 1 FROM queue WHERE url=?", (url,)).fetchone() is not None


def enqueue(c, url, title, score):
    c.execute("INSERT OR IGNORE INTO queue(url, title, score) VALUES (?,?,?)", (url, title, score))
    c.commit()


def expire_queue(c, max_age_h):
    """Juda eskirgan navbatdagi yangiliklarni o'tkazib yuborilgan deb belgilaydi."""
    old = c.execute("SELECT url, title FROM queue WHERE ts < datetime('now', ?)", (f"-{max_age_h} hours",)).fetchall()
    for url, title in old:
        mark(c, url, False, title)
    return len(old)


def queue_items(c):
    rows = c.execute("SELECT url, title, score, data, tries FROM queue ORDER BY score DESC, ts DESC").fetchall()
    return [{"url": u, "title": t, "score": s, "data": json.loads(d) if d else None, "tries": n}
            for u, t, s, d, n in rows]


def save_translation(c, url, data):
    c.execute("UPDATE queue SET data=? WHERE url=?", (json.dumps(data, ensure_ascii=False), url))
    c.commit()


def add_try(c, url):
    c.execute("UPDATE queue SET tries = tries + 1 WHERE url=?", (url,))
    c.commit()
    row = c.execute("SELECT tries FROM queue WHERE url=?", (url,)).fetchone()
    return row[0] if row else 0


def recent_titles(c, limit=20):
    rows = c.execute("""SELECT title FROM seen WHERE posted=1 AND title != ''
                        AND ts > datetime('now', '-3 days') ORDER BY ts DESC LIMIT ?""", (limit,)).fetchall()
    return [r[0] for r in rows]
