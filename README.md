# AI yangiliklari kanali (o'zbekcha)

1. `pip install -r requirements.txt`
2. `.env.example` -> `.env`, kalitlarni to'ldiring.
3. Telegraph token: `python -c "from ainews import telegraph; print(telegraph.create_account())"`
4. Sinov: `DRY_RUN=1 python main.py` (hech narsa yuborilmaydi)
5. Jonli: `.env` da `DRY_RUN=0`.
6. Cron (har soat): `0 * * * * cd /yo'l/ai-news-bot && python main.py >> bot.log 2>&1`
