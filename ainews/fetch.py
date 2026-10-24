import feedparser
import requests
import trafilatura
from .config import FEEDS

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


def new_entries():
    out = []
    for f in FEEDS:
        try:
            d = feedparser.parse(f, request_headers=UA)
        except Exception:
            continue
        for e in d.entries[:10]:
            if getattr(e, "link", None):
                out.append({"url": e.link, "title": getattr(e, "title", "")})
    return out


def get_article(url):
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        html = r.text
    except Exception:
        return None
    text = trafilatura.extract(html, include_comments=False)
    meta = trafilatura.extract_metadata(html)
    if not text or len(text) < 600:
        return None
    return {"text": text[:12000], "image": getattr(meta, "image", None)}
