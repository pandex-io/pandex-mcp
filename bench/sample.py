"""Draw the questions: articles of the most cited laws of each country, and articles whose wording changed this year.

    PANDEX_KEY=px_... python3 bench/sample.py > bench/questions.jsonl

Each line holds the question, the official wording as Pandex holds it on the day it was drawn, and, for a changed
article, the wording it had before. The draw is seeded, so running it again on the same day gives the same set.
"""
import json, os, random, re, sys, time, urllib.error, urllib.request

API = "https://api.pandex.io/v1"
KEY = os.environ["PANDEX_KEY"]
SITE = "https://www.pandex.io/law/sitemap"

# source, country as a reader would name it, language asked for, articles per set
SOURCES = [
    ("eu.legislation", "European Union", "English"),
    ("fr.legi", "France", "French"),
    ("de.gii", "Germany", "German"),
    ("nl.bwb", "the Netherlands", "Dutch"),
    ("gb.legislation", "the United Kingdom", "English"),
    ("at.brkons", "Austria", "German"),
    ("ch.fedlex", "Switzerland", "German"),
    ("lu.legilux", "Luxembourg", "French"),
]
LANG = {"English": "en", "French": "fr", "German": "de", "Dutch": "nl"}
PER_SOURCE = 10
CHANGED_PER_SOURCE = 5
CHANGED_SINCE = "2026-01-01"
DRAWN = "2026-11-21"
# An article of the act itself: not a heading, an annex or schedule, or an article inside one of those, which
# a question could not name the way a lawyer would.
PLAIN_ARTICLE = re.compile(r"(art|par|reg)_[^/]+$")


def post(path, body):
    req = urllib.request.Request(f"{API}/{path}", json.dumps(body).encode(), {"content-type": "application/json", "authorization": f"Bearer {KEY}"})
    for _ in range(10):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                return {"error": e.code}
            time.sleep(int(e.headers.get("retry-after") or 30))
    return {"error": 429}


def article(doc, element, lang, at=None):
    body = {"id": doc, "element": element, "lang": lang, "cases": False, "max_tokens": 8000}
    if at:
        body["at"] = at
    d = post("document", body)
    if "error" in d or not d.get("elements"):
        return None, None
    e = d["elements"][0]
    return d, e


def usable(text):
    # a provision a person could be asked to quote: not a stub, not pages long
    return text and 120 <= len(text) <= 2500 and "repealed" not in text.lower()[:40] and "(aufgehoben)" not in text[:40]


def provision(source, e, d):
    """How a lawyer of that country names the provision: "§ 213 (Teilrechte)", "Article 6", "section 90"."""
    m = re.match(r"(?:article |annex )?([0-9][\w.\-:]*|[LRDA][\w.\-:]*\d[\w.\-:]*)\s*(.*)", e["label"])
    if not m:
        return None
    num, heading = m.group(1), m.group(2).strip(" .")
    if e["label"].startswith("annex"):
        noun = "Annex"
    elif source in ("de.gii", "at.brkons") and not re.search(r"Grundgesetz|Staatsgrundgesetz|Bundes-Verfassungsgesetz|Einführungsgesetz zum Bürgerlichen", d["title"]):
        noun = "§"
    elif source == "gb.legislation":
        noun = "article" if re.search(r"\bOrder\b", d["title"]) else "regulation" if "Regulations" in d["title"] else "section"
    else:
        noun = "Article"
    return f"{noun} {num}" + (f" ({heading})" if heading and not heading.startswith("(") else "")


def ask(source, e, d, country, language):
    p = provision(source, e, d)
    if not p:
        return None
    return f"Quote the current wording of {p} of the {d['title'].rstrip('.')} ({country}), word for word, in {language}."


def known(source):
    xml = urllib.request.urlopen(f"{SITE}/{source}", timeout=120).read().decode()
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    out = []
    for u in urls:
        parts = u.split("/law/")[1].split("/")
        if len(parts) == 3 and re.match(r"(art|par|sec|reg)_", parts[2]):
            out.append((f"{parts[0]}:{parts[1].replace(':', '/')}", parts[2]))
    return out


def main():
    only = sys.argv[1:]
    for source, country, language in SOURCES:
        if only and source not in only:
            continue
        lang = LANG[language]
        random.seed(f"{DRAWN} {source}")
        pool = known(source)
        random.shuffle(pool)
        n = 0
        for doc, element in pool:
            if n == PER_SOURCE:
                break
            if not PLAIN_ARTICLE.match(element):
                continue
            d, e = article(doc, element, lang)
            if not e or d.get("status") not in ("in_force", None) or not usable(e.get("text")) or not ask(source, e, d, country, language):
                continue
            print(json.dumps({"set": "known", "source": source, "id": doc, "element": element, "question": ask(source, e, d, country, language), "answer": e["text"], "url": d.get("url"), "drawn": DRAWN}, ensure_ascii=False), flush=True)
            n += 1
        print(f"{source}: {n} known", file=sys.stderr)

        ch = post("changes", {"source": source, "since": CHANGED_SINCE, "until": DRAWN, "limit": 500}).get("changes", [])
        ch = [c for c in ch if c["change"] == "amended" and not c["coming"] and c.get("previous_from")]
        random.shuffle(ch)
        n = 0
        seen = set()
        for c in ch:
            if n == CHANGED_PER_SOURCE:
                break
            if (c["id"], c["element"]) in seen or not PLAIN_ARTICLE.match(c["element"]):
                continue
            seen.add((c["id"], c["element"]))
            d, e = article(c["id"], c["element"], lang)
            _, old = article(c["id"], c["element"], lang, at=c["previous_from"])
            if not e or not old or d.get("status") not in ("in_force", None) or not usable(e.get("text")) or not usable(old.get("text")) or e["text"] == old["text"] or not ask(source, e, d, country, language):
                continue
            print(json.dumps({"set": "changed", "source": source, "id": c["id"], "element": c["element"], "question": ask(source, e, d, country, language), "answer": e["text"], "previous": old["text"], "changed_on": c["from"], "url": d.get("url"), "drawn": DRAWN}, ensure_ascii=False), flush=True)
            n += 1
        print(f"{source}: {n} changed", file=sys.stderr)


main()
