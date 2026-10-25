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
    "https://blog.google/technology/ai/rss/",
    "https://www.microsoft.com/en-us/ai/blog/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://the-decoder.com/feed/",
    "https://www.marktechpost.com/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
]

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN", "")
MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "2"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "5"))
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).resolve().parent.parent / "news_live.db"))
