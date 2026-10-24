"""Sozlamalarni tekshiradi: bot, kanal, admin huquqi, Claude kaliti, Telegraph."""
import requests
from ainews import config

base = f"https://api.telegram.org/bot{config.BOT_TOKEN}"
me = requests.get(f"{base}/getMe", timeout=20).json()
print("Bot:", me.get("result", {}).get("username") if me.get("ok") else f"XATO {me}")
ch = requests.get(f"{base}/getChat", params={"chat_id": config.CHANNEL}, timeout=20).json()
print("Kanal:", ch.get("result", {}).get("title") if ch.get("ok") else f"XATO {ch}")
if me.get("ok") and ch.get("ok"):
    m = requests.get(f"{base}/getChatMember", params={"chat_id": config.CHANNEL, "user_id": me["result"]["id"]}, timeout=20).json()
    print("Botning kanaldagi holati:", m.get("result", {}).get("status"))
import os
print("ANTHROPIC_API_KEY:", "bor" if os.getenv("ANTHROPIC_API_KEY") else "YO'Q - .env ga yozing")
