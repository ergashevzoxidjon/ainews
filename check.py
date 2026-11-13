"""Sozlamalarni tekshiradi: bot, kanal, admin huquqi, Gemini va Claude kalitlari."""
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

print()
if config.GEMINI_API_KEY:
    # Modellar ro'yxatini olish limitdan sarflanmaydi.
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                     headers={"x-goog-api-key": config.GEMINI_API_KEY}, params={"pageSize": 1000}, timeout=20)
    if r.ok:
        have = {m["name"].split("/", 1)[-1] for m in r.json().get("models", [])}
        print("GEMINI_API_KEY: ishlayapti (bepul, asosiy)")
        for m in dict.fromkeys([config.GEMINI_SCORE_MODEL] + config.GEMINI_MODELS):
            print(f"  {m}:", "bor" if m in have else "TOPILMADI - .env dagi nomni tekshiring")
    else:
        print(f"GEMINI_API_KEY: XATO {r.status_code} {r.text[:200]}")
else:
    print("GEMINI_API_KEY: YO'Q - aistudio.google.com/apikey dan olib .env ga yozing")

print("ANTHROPIC_API_KEY:", f"bor (zaxira: {config.CLAUDE_FALLBACK_MODEL})" if config.ANTHROPIC_API_KEY
      else "yo'q (zaxira o'chiq - Gemini limiti tugasa, bot keyingi safargacha kutadi)")
