"""Sun'iy intellekt chaqiruvlari.

Tartib: avval bepul Gemini modellari (ro'yxat bo'yicha), limit tugasa yoki ishlamasa —
Claude Haiku (zaxira). Ish ikki bosqichda: 1) sarlavhalar bitta so'rovda arzon baholanadi,
2) faqat tanlanganlari to'liq tarjima qilinadi.
"""
import json
import logging
import re
import time
from collections import Counter

import requests

from . import config

log = logging.getLogger("ainews")

SCORE_PROMPT = """Sen sun'iy intellekt yangiliklari bo'yicha o'zbek tilidagi Telegram kanal muharririsan.
Quyidagi ingliz tilidagi yangiliklarni sarlavha va qisqa tavsifi bo'yicha bahola.
Har biriga 1-10 ball qo'y: sun'iy intellekt sohasi uchun qanchalik muhim va qiziqarli
(yirik model/mahsulot chiqishi, muhim tadqiqot, katta kompaniya yangiligi = yuqori;
reklama, vebinar, qo'llanma/tutorial, kichik yangilanish, past sifat = past).
Bir xil voqea haqida bir nechta yangilik bo'lsa, faqat eng yaxshisiga yuqori ball ber, qolganlariga 1.
"Yaqinda e'lon qilingan" ro'yxatidagi voqea haqidagi yangiliklarga ham 1 ber.

Yaqinda e'lon qilingan:
{recent}

Baholanadigan yangiliklar:
{items}

Faqat JSON qaytar, boshqa hech narsa yozma:
{{"scores": [{{"id": 1, "score": 7}}, ...]}}
"""

TRANSLATE_PROMPT = """Sen sun'iy intellekt yangiliklari bo'yicha o'zbek tilidagi kanal muharririsan.
Quyidagi ingliz tilidagi maqolani o'qib, JSON qaytar (boshqa hech narsa yozma):
{{
 "title_uz": "qisqa, jozibali sarlavha",
 "summary_uz": "2-3 gapli qisqa xulosa (jami 400 belgidan oshmasin)",
 "body_uz": ["to'liq matn abzatslari ro'yxati"]
}}
Qoidalar: matnni so'zma-so'z ko'chirma, o'z so'zlaring bilan sodda va ravon o'zbek tilida (lotin yozuvi) qayta aytib ber.
Faktlar, raqamlar va nomlarni aniq saqla, o'zingdan hech narsa qo'shma. Mahsulot/kompaniya nomlarini asl holida qoldir.
Ommabop atamalar: model, agent, token, chip, ochiq manbali (open source).

Sarlavha: {title}
Matn:
{text}
"""


class Unavailable(Exception):
    """Hech bir provayder javob bermadi (limit, tarmoq, kalit). Keyingi ishga tushishda qayta urinish kerak."""


class BadOutput(Exception):
    """Provayder javob berdi, lekin natija yaroqsiz. Bu maqolani qayta urinish pul/limit isrofi."""


class _Skip(Exception):
    """Bu provayder hozir ishlamaydi; keyingisiga o'tiladi. disable=True — shu ishga tushish davomida qaytib urinilmaydi."""

    def __init__(self, msg, disable=False):
        super().__init__(msg)
        self.disable = disable


_disabled = set()        # shu ishga tushishda limiti tugagan / ishlamaydigan provayderlar
usage = Counter()        # qaysi provayder necha marta ishlatildi (log uchun)
_claude = None


# ---------------- Gemini (bepul) ----------------
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _gemini(model, prompt, max_tokens, thinking=True, retry=True):
    gen = {"responseMimeType": "application/json", "maxOutputTokens": max_tokens}
    if thinking:
        gen["thinkingConfig"] = {"thinkingLevel": "low"}
    try:
        r = requests.post(
            GEMINI_URL.format(model=model),
            headers={"x-goog-api-key": config.GEMINI_API_KEY, "Content-Type": "application/json"},
            json={"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen},
            timeout=90,
        )
    except requests.RequestException as e:
        # Javob kelmadi (band server). Shu ishga tushishda qayta kutib o'tirmaymiz.
        raise _Skip(f"tarmoq xatosi: {e}", disable=True)
    if r.status_code == 429:
        raise _Skip("bepul limit tugadi (429)", disable=True)
    if r.status_code >= 500:
        if retry:  # vaqtinchalik band (503): 5 soniyadan keyin bir marta qayta urinamiz
            time.sleep(5)
            return _gemini(model, prompt, max_tokens, thinking, retry=False)
        raise _Skip(f"server xatosi {r.status_code}", disable=True)
    if r.status_code == 400 and thinking and "thinking" in r.text.lower():
        # Model thinkingLevel ni qo'llamasa — usiz qayta so'raymiz.
        return _gemini(model, prompt, max_tokens, thinking=False)
    if r.status_code in (401, 403) or (r.status_code == 400 and "api key" in r.text.lower()):
        raise _Skip(f"kalit xato yoki ruxsat yo'q ({r.status_code}): {r.text[:200]}", disable=True)
    if r.status_code == 404:
        raise _Skip("model topilmadi (nomini tekshiring)", disable=True)
    if not r.ok:
        raise _Skip(f"xato {r.status_code}: {r.text[:300]}", disable=True)
    data = r.json()
    cands = data.get("candidates") or []
    if not cands:
        raise BadOutput(f"bo'sh javob: {str(data.get('promptFeedback', ''))[:200]}")
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if cands[0].get("finishReason") == "MAX_TOKENS":
        raise BadOutput("javob uzunlik chegarasida kesildi")
    return text


# ---------------- Claude (zaxira, pullik) ----------------
def _claude_call(model, prompt, max_tokens):
    import anthropic
    global _claude
    _claude = _claude or anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        r = _claude.messages.create(model=model, max_tokens=max_tokens,
                                    messages=[{"role": "user", "content": prompt}])
    except anthropic.RateLimitError:
        raise _Skip("limit (429)", disable=True)
    except anthropic.APIConnectionError as e:  # timeout ham shu yerga kiradi
        raise _Skip(f"tarmoq xatosi: {e}")
    except anthropic.InternalServerError as e:
        raise _Skip(f"server xatosi: {e}")
    except anthropic.APIStatusError as e:  # kalit xato, balans tugagan, model topilmadi va h.k.
        raise _Skip(f"xato {e.status_code}: {str(e)[:300]}", disable=True)
    if r.stop_reason == "max_tokens":
        raise BadOutput("javob uzunlik chegarasida kesildi")
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


# ---------------- Umumiy zanjir ----------------
def _chain(first_gemini=None):
    out = []
    if config.GEMINI_API_KEY:
        models = ([first_gemini] if first_gemini else []) + config.GEMINI_MODELS
        for m in dict.fromkeys(models):
            out.append(("gemini", m))
    if config.ANTHROPIC_API_KEY:
        out.append(("claude", config.CLAUDE_FALLBACK_MODEL))
    return out


def _parse(raw):
    raw = re.sub(r"^```(?:json)?|```$", "", (raw or "").strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise BadOutput("JSON topilmadi")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise BadOutput(f"JSON buzuq: {e}")


def _ask(prompt, validate, gemini_tokens, claude_tokens, first_gemini=None):
    chain = [p for p in _chain(first_gemini) if p not in _disabled]
    if not chain:
        raise Unavailable("ishlaydigan provayder yo'q (kalitlar yoki limitlar)")
    got_answer = False
    for prov in chain:
        kind, model = prov
        for _ in range(2 if kind == "gemini" else 1):  # yaroqsiz javobda bepul modelda bir marta qayta urinish
            try:
                raw = (_gemini(model, prompt, gemini_tokens) if kind == "gemini"
                       else _claude_call(model, prompt, claude_tokens))
                got_answer = True
                result = validate(_parse(raw))
                usage[model] += 1
                return result
            except _Skip as e:
                log.warning("%s: %s — keyingisiga o'tilmoqda", model, e)
                if e.disable:
                    _disabled.add(prov)
                break
            except (BadOutput, ValueError, KeyError, TypeError) as e:
                got_answer = True
                log.warning("%s: yaroqsiz javob (%s)", model, e)
    if got_answer:
        raise BadOutput("hech bir provayder yaroqli javob bermadi")
    raise Unavailable("barcha provayderlar ishlamadi (limit/tarmoq)")


# ---------------- 1-bosqich: baholash ----------------
def score(entries, recent_titles=()):
    """entries: [{"title", "summary", "url"}] -> {index: ball}. Bitta so'rovda 40 tagacha."""
    out = {}
    for start in range(0, len(entries), 40):
        chunk = entries[start:start + 40]
        items = "\n".join(
            f"{i}. [{_domain(e['url'])}] {e['title']}" + (f" — {e['summary']}" if e.get("summary") else "")
            for i, e in enumerate(chunk, 1))
        recent = "\n".join(f"- {t}" for t in recent_titles) or "(yo'q)"
        prompt = SCORE_PROMPT.format(recent=recent, items=items)

        def validate(d, n=len(chunk)):
            res = {}
            for s in d["scores"]:
                i = int(s["id"])
                if 1 <= i <= n:
                    res[i] = max(1, min(10, int(float(s["score"]))))
            if not res:
                raise ValueError("ballar bo'sh")
            return res

        try:
            res = _ask(prompt, validate, gemini_tokens=4096, claude_tokens=2000,
                       first_gemini=config.GEMINI_SCORE_MODEL)
        except (Unavailable, BadOutput) as e:
            if not out:
                raise
            # Oldingi bo'laklar allaqachon baholangan: ularni yo'qotmaymiz, qolganlari keyingi safar.
            log.warning("Baholash qisman: %d/%d ta baholandi, qolganlari keyingi safar (%s)", len(out), len(entries), e)
            break
        for i, sc in res.items():
            out[start + i - 1] = sc
    return out


# ---------------- 2-bosqich: tarjima ----------------
def translate(title, text):
    def validate(d):
        for k in ("title_uz", "summary_uz", "body_uz"):
            if not d.get(k):
                raise ValueError(f"'{k}' yo'q")
        if isinstance(d["body_uz"], str):
            d["body_uz"] = [p for p in d["body_uz"].split("\n") if p.strip()]
        d["body_uz"] = [str(p) for p in d["body_uz"] if str(p).strip()]
        return {k: d[k] for k in ("title_uz", "summary_uz", "body_uz")}

    return _ask(TRANSLATE_PROMPT.format(title=title, text=text), validate,
                gemini_tokens=16384, claude_tokens=8000)


def _domain(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else ""
