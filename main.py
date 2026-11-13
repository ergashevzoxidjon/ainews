import logging
import time
from ainews import config, db, fetch, llm, telegraph, telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ainews")

MAX_PUBLISH_TRIES = 3


def run():
    if not (config.GEMINI_API_KEY or config.ANTHROPIC_API_KEY):
        raise SystemExit("GEMINI_API_KEY ham, ANTHROPIC_API_KEY ham topilmadi. .env fayl main.py bilan bir papkada va nomi aynan .env bo'lishi kerak.")
    if not config.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY yo'q — faqat pullik Claude ishlatiladi")
    c = db.conn()

    entries, urls = [], set()
    for e in fetch.new_entries():
        if e["url"] not in urls:
            urls.add(e["url"])
            entries.append(e)

    if db.count(c) == 0 and not config.DRY_RUN:
        # BASELINE: birinchi jonli ishga tushirishda mavjud yangiliklarni "ko'rilgan" deb belgilaymiz,
        # shunda eski yangiliklar qayta e'lon qilinmaydi. Faqat keyin chiqqanlari yuboriladi.
        for e in entries:
            db.mark(c, e["url"], False, e["title"])
        log.info("BASELINE: %d ta mavjud yangilik belgilandi, e'lon qilinmadi", len(entries))
        return

    stats = {"yangi": 0, "past_ball": 0, "navbatga": 0, "matn_yoq": 0, "xato": 0,
             "eskirdi": db.expire_queue(c, config.QUEUE_MAX_AGE_H)}
    new = [e for e in entries if not db.is_seen(c, e["url"]) and not db.in_queue(c, e["url"])]
    stats["yangi"] = len(new)
    log.info("ISHGA TUSHDI: %d ta yozuv o'qildi, %d tasi yangi", len(entries), len(new))

    # 1-bosqich: yangi sarlavhalarni bitta so'rovda arzon baholash.
    if new:
        try:
            scores = llm.score(new, db.recent_titles(c))
        except (llm.Unavailable, llm.BadOutput) as ex:
            log.error("Baholab bo'lmadi: %s — keyingi safar qayta uriniladi", ex)
            scores = {}
        for i, e in enumerate(new):
            if i not in scores:
                continue  # baholanmadi — keyingi safar qayta baholanadi
            if scores[i] < config.MIN_SCORE:
                stats["past_ball"] += 1
                log.info("o'tkazildi (%s): %s", scores[i], e["title"])
                db.mark(c, e["url"], False, e["title"])
            else:
                stats["navbatga"] += 1
                db.enqueue(c, e["url"], e["title"], scores[i])

    # 2-bosqich: eng yuqori baholilarni tarjima qilib e'lon qilish.
    posted = failures = 0
    for q in db.queue_items(c):
        if posted >= config.MAX_POSTS:
            break
        r = q["data"]  # oldingi safar tarjima qilingan, lekin nashrda xato bo'lgan bo'lsa — tayyor
        if r is None:
            art = fetch.get_article(q["url"])
            if not art:
                stats["matn_yoq"] += 1
                db.mark(c, q["url"], False, q["title"])
                continue
            try:
                r = llm.translate(q["title"], art["text"])
            except llm.Unavailable as ex:
                log.error("Tarjima qilib bo'lmadi: %s — navbatdagilar keyingi safar", ex)
                break
            except llm.BadOutput as ex:
                # Qayta urinish faqat limit/pul isrofi — bu maqolani o'tkazib yuboramiz.
                stats["xato"] += 1
                log.warning("Tarjima yaroqsiz, o'tkazildi: %s (%s)", q["title"], ex)
                db.mark(c, q["url"], False, q["title"])
                continue
            r["image"] = art["image"]
            if not config.DRY_RUN:
                db.save_translation(c, q["url"], r)

        if config.DRY_RUN:
            log.info("DRY_RUN (%s ball):\n%s\n%s\n%s", q["score"], r["title_uz"], r["summary_uz"],
                     "\n".join(r["body_uz"])[:500])
            posted += 1
            continue
        try:
            page = telegraph.create_page(r["title_uz"], r["body_uz"], r.get("image"), q["url"])
            telegram.post(r["title_uz"], r["summary_uz"], r.get("image"), page)
        except Exception as ex:
            n = db.add_try(c, q["url"])
            log.error("Nashr xatosi (%d/%d): %s", n, MAX_PUBLISH_TRIES, ex)
            if n >= MAX_PUBLISH_TRIES:
                db.mark(c, q["url"], False, q["title"])
            failures += 1
            if failures >= 2:
                break  # Telegram/Telegraph ishlamayapti — boshqalarini behuda tarjima qilmaymiz
            continue
        log.info("e'lon qilindi (%s ball): %s", q["score"], page)
        db.mark(c, q["url"], True, q["title"])
        posted += 1
        time.sleep(5)

    log.info("XULOSA: e'lon qilindi=%d, %s, ishlatilgan modellar=%s", posted, stats, dict(llm.usage) or "-")


if __name__ == "__main__":
    run()
