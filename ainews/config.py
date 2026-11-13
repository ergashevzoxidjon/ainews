import os
from dotenv import load_dotenv

import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://venturebeat.com/category/ai/feed/",
    "https://blog.google/technology/ai/rss/",
    "https://www.microsoft.com/en-us/ai/blog/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://the-decoder.com/feed/",
    "https://www.marktechpost.com/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
]


def _list(name, default):
    return [m.strip() for m in os.getenv(name, default).split(",") if m.strip()]


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN", "")

# --- Sun'iy intellekt provayderlari ---
# 1) Asosiy: Google Gemini (bepul tarif). Har bir modelning o'z kunlik limiti bor,
#    shuning uchun bittasining limiti tugasa, ro'yxatdagi keyingisi ishlatiladi.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELS = _list("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite")
# Sarlavhalarni baholash uchun yengil (tez) model — tarjima limitini tejaydi.
GEMINI_SCORE_MODEL = os.getenv("GEMINI_SCORE_MODEL", "gemini-3.5-flash-lite")
# 2) Zaxira: barcha Gemini limitlari tugasa — Claude Haiku (arzon, pullik).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_FALLBACK_MODEL = os.getenv("CLAUDE_FALLBACK_MODEL", "claude-haiku-5-5")

MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "2"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "5"))
# Navbatdagi (yaxshi baholangan, lekin hali chiqmagan) yangilik necha soatgacha kutadi.
QUEUE_MAX_AGE_H = int(os.getenv("QUEUE_MAX_AGE_H", "24"))
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
# Sinov (DRY_RUN) alohida bazadan foydalanadi, jonli bazaga tegmaydi.
DB_PATH = os.getenv("DB_PATH", str(ROOT / ("news_dry.db" if DRY_RUN else "news_live.db")))
