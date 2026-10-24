import os
from dotenv import load_dotenv

import pathlib
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://venturebeat.com/category/ai/feed/",
]

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN", "")
MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "2"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "6"))
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
DB_PATH = os.getenv("DB_PATH", "news_live.db")
