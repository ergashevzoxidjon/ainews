import json
import re
import anthropic
from .config import CLAUDE_MODEL

PROMPT = """Sen sun'iy intellekt yangiliklari bo'yicha o'zbek tilidagi kanal muharririsan.
Quyidagi ingliz tilidagi maqolani o'qib, JSON qaytar (boshqa hech narsa yozma):
{{
 "score": 1-10 (sun'iy intellekt sohasi uchun qanchalik muhim va qiziqarli; reklama/past sifat = past),
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

_client = None


def _call(title, text):
    r = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT.format(title=title, text=text)}],
    )
    raw = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError("JSON topilmadi")
    d = json.loads(m.group(0))
    for k in ("score", "title_uz", "summary_uz", "body_uz"):
        if k not in d:
            raise ValueError(f"'{k}' yo'q")
    if isinstance(d["body_uz"], str):
        d["body_uz"] = [p for p in d["body_uz"].split("\n") if p.strip()]
    return d


def process(title, text):
    global _client
    _client = _client or anthropic.Anthropic()
    last = None
    for _ in range(2):
        try:
            return _call(title, text)
        except anthropic.AuthenticationError:
            raise SystemExit("ANTHROPIC_API_KEY noto'g'ri yoki bo'sh. .env faylni tekshiring.")
        except (ValueError, json.JSONDecodeError) as e:
            last = e
    raise last
