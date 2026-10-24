import json
import pathlib
import re
import requests
from . import config

API = "https://api.telegra.ph"
ENV = pathlib.Path(__file__).resolve().parent.parent / ".env"
_token = config.TELEGRAPH_TOKEN


def _new_token():
    global _token
    r = requests.post(f"{API}/createAccount", data={"short_name": "AINews", "author_name": "AI Yangiliklari"}, timeout=30).json()
    _token = r["result"]["access_token"]
    txt = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    if re.search(r"^TELEGRAPH_TOKEN=.*$", txt, re.M):
        txt = re.sub(r"^TELEGRAPH_TOKEN=.*$", "TELEGRAPH_TOKEN=" + _token, txt, flags=re.M)
    else:
        txt += "\nTELEGRAPH_TOKEN=" + _token + "\n"
    ENV.write_text(txt, encoding="utf-8")


def ensure_token():
    if not _token:
        _new_token()


def create_page(title, paragraphs, image, source_url):
    nodes = []
    if image:
        nodes.append({"tag": "img", "attrs": {"src": image}})
    for p in paragraphs:
        nodes.append({"tag": "p", "children": [p]})
    nodes.append({"tag": "p", "children": [
        "Manba: ", {"tag": "a", "attrs": {"href": source_url}, "children": [source_url]}]})
    for attempt in range(2):
        j = requests.post(f"{API}/createPage", data={
            "access_token": _token, "title": title[:256],
            "content": json.dumps(nodes), "return_content": "false"}, timeout=30).json()
        if j.get("ok"):
            return j["result"]["url"]
        if j.get("error") == "ACCESS_TOKEN_INVALID" and attempt == 0:
            _new_token()
            continue
        raise RuntimeError(j)
