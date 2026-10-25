import logging
import time
from ainews import config, db, fetch, llm, telegraph, telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ainews")


def run():
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY topilmadi. .env fayl main.py bilan bir papkada va nomi aynan .env bo'lishi kerak.")
    c = db.conn()
    posted = 0
    entries = fetch.new_entries()
    if db.count(c) == 0 and not config.DRY_RUN:
        # BASELINE: birinchi jonli ishga tushirishda mavjud yangiliklarni "ko'rilgan" deb belgilaymiz,
        # shunda eski yangiliklar qayta e'lon qilinmaydi. Faqat keyin chiqqanlari yuboriladi.
        for e in entries:
            db.mark(c, e["url"], False)
        log.info("BASELINE: %d ta mavjud yangilik belgilandi, e'lon qilinmadi", len(entries))
        return
    stats = {"yangi": 0, "matn_yoq": 0, "past_ball": 0, "xato": 0}
    log.info("ISHGA TUSHDI: %d ta yozuv o'qildi", len(entries))
    for e in entries:
        if posted >= config.MAX_POSTS:
            break
        if db.is_seen(c, e["url"]):
            continue
        stats["yangi"] += 1
        art = fetch.get_article(e["url"])
        if not art:
            stats["matn_yoq"] += 1
            db.mark(c, e["url"], False)
            continue
        try:
            r = llm.process(e["title"], art["text"])
        except Exception as ex:
            stats["xato"] += 1
            log.warning("LLM xato: %s", ex)
            continue
        if r["score"] < config.MIN_SCORE:
            stats["past_ball"] += 1
            log.info("o'tkazildi (%s): %s", r["score"], e["title"])
            db.mark(c, e["url"], False)
            continue
        if config.DRY_RUN:
            log.info("DRY_RUN:\n%s\n%s\n%s", r["title_uz"], r["summary_uz"], "\n".join(r["body_uz"])[:500])
            posted += 1
            continue
        else:
            try:
                page = telegraph.create_page(r["title_uz"], r["body_uz"], art["image"], e["url"])
                telegram.post(r["title_uz"], r["summary_uz"], art["image"], page)
            except Exception as ex:
                log.error("Nashr xatosi: %s", ex)
                continue
            log.info("e'lon qilindi: %s", page)
        db.mark(c, e["url"], True)
        posted += 1
        time.sleep(5)
    log.info("XULOSA: e'lon qilindi=%d, %s", posted, stats)


if __name__ == "__main__":
    run()
