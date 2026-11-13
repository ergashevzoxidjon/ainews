# AI yangiliklari kanali (o'zbekcha)

1. `pip install -r requirements.txt`
2. `.env.example` -> `.env`, kalitlarni to'ldiring.
   - `GEMINI_API_KEY` — asosiy, **bepul**: https://aistudio.google.com/apikey
   - `ANTHROPIC_API_KEY` — zaxira (ixtiyoriy, pullik): faqat Gemini limiti tugasa Claude Haiku ishlaydi.
3. Telegraph token (bo'sh bo'lsa birinchi postda o'zi yaratiladi): `python -c "from ainews import telegraph; telegraph.ensure_token()"`
4. Tekshiruv: `python check.py`
5. Sinov: `DRY_RUN=1 python main.py` (hech narsa yuborilmaydi, alohida `news_dry.db` ishlatiladi)
6. Jonli: `.env` da `DRY_RUN=0`.
7. Cron (har soat): `0 * * * * cd /yo'l/ai-news-bot && python main.py >> bot.log 2>&1`

## Qanday ishlaydi (xarajatni tejash)

1. **Baholash** — yangi sarlavhalar (va RSS tavsifi) bitta so'rovda baholanadi (yengil Gemini modeli).
   Past ballilar to'liq tarjima qilinmaydi.
2. **Navbat** — `MIN_SCORE` dan yuqorilari navbatga tushadi, eng yuqori ballilari birinchi chiqadi.
   `QUEUE_MAX_AGE_H` soatdan eskirganlari o'chadi.
3. **Tarjima** — faqat e'lon qilinadiganlari tarjima qilinadi. Tarjima saqlanadi: nashrda xato bo'lsa,
   qayta tarjima qilinmaydi (3 urinishdan keyin o'tkaziladi). Yaroqsiz tarjima qayta urinilmaydi.
4. **Provayderlar zanjiri** — `GEMINI_MODELS` dagi modellar ketma-ket (har birining o'z bepul limiti bor),
   hammasi tugasa `CLAUDE_FALLBACK_MODEL`. Logdagi `XULOSA` qatorida qaysi model necha marta ishlatilgani ko'rinadi.
