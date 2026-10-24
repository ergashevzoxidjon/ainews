import html
import json
import requests
from .config import BOT_TOKEN, CHANNEL


def post(title, summary, image, page_url):
    caption = f"<b>{html.escape(title)}</b>\n\n{html.escape(summary)}"[:1024]
    markup = json.dumps({"inline_keyboard": [[{"text": "Barchasini ko'rish", "url": page_url}]]})
    base = f"https://api.telegram.org/bot{BOT_TOKEN}"
    if image:
        r = requests.post(f"{base}/sendPhoto", data={
            "chat_id": CHANNEL, "photo": image, "caption": caption,
            "parse_mode": "HTML", "reply_markup": markup}, timeout=30)
        if r.ok:
            return
    r = requests.post(f"{base}/sendMessage", data={
        "chat_id": CHANNEL, "text": caption, "parse_mode": "HTML",
        "reply_markup": markup}, timeout=30)
    r.raise_for_status()
