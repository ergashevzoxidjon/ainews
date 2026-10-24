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
    for e in fetch.new_entries():
        if posted >= config.MAX_POSTS:
            break
        if db.is_seen(c, e["url"]):
            continue
        art = fetch.get_article(e["url"])
        if not art:
            db.mark(c, e["url"], False)
            continue
        try:
            r = llm.process(e["title"], art["text"])
        except Exception as ex:
            log.warning("LLM xato: %s", ex)
            continue
        if r["score"] < config.MIN_SCORE:
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


if __name__ == "__main__":
    run()
