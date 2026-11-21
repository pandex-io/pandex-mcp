"""Score every results file against the official wording and print the table.

    python3 bench/score.py            # the table
    python3 bench/score.py --json     # the same as JSON, for the site

An answer is compared word by word with the wording Pandex held on the day the questions were drawn (case,
punctuation and paragraph numbers aside). The measure is how much of the official text the answer holds, in
order, so a correct quote with a line of comment around it still counts as correct:
  exact     95% or more of the official words are there, in order
  close     80 to 95%: the right provision, worded a little differently
  wrong     under 80%, and the answer gives a text: another wording, another provision, or an invented one
  declined  under 80%, and the answer gives no text of the provision: UNKNOWN, "I can't quote it", a summary,
            a list of where to look, or an attempt to call a tool it does not have. Whether it gives a text is
            asked of Claude Sonnet once per answer; the verdicts are in results/judged.json
For an article that changed this year, an answer that holds at least 80% of the wording before the change, and
is more like it than like the current one, is counted as "old". Légifrance's notes after an article ("NOTA :",
on when a change applies) are not part of its wording and are left out of the comparison.
"""
import difflib, glob, hashlib, json, os, re, subprocess, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def words(t):
    t = unicodedata.normalize("NFKC", t).lower()
    t = re.sub(r"[’'`´]", "'", t)
    return re.findall(r"\w+", t)


def covered(official, answer):
    """The share of the official words that the answer holds, in the same order."""
    a, b = words(official), words(answer)
    if not a or not b:
        return 0.0
    m = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(x.size for x in m.get_matching_blocks()) / len(a)


# Whether an answer under 80% gives a text at all, or declines, is asked of Claude Sonnet once per answer
# (results/judged.json keeps the verdicts, so the score can be checked and re-run without it).
JUDGED = os.path.join(HERE, "results", "judged.json")
JUDGE = ("Below is a reply to a request to quote a provision of law word for word. Answer YES if the reply sets out "
         "text that it offers as the wording of the provision itself, even only part of it, even with a warning that it "
         "may be inaccurate. Answer NO if it declines to give the wording and offers at most a description in its own "
         "words, a summary, a heading, a list of where to look, or an attempt to call a tool. Answer YES or NO only.\n\n"
         "<reply>\n{}\n</reply>")
judged = json.load(open(JUDGED)) if os.path.exists(JUDGED) else {}


def judge(answer):
    k = hashlib.sha256(answer.encode()).hexdigest()[:16]
    if k not in judged:
        p = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--setting-sources", "", "--strict-mcp-config",
                            "--no-session-persistence", "--", JUDGE.format(answer)], capture_output=True, text=True, timeout=300)
        judged[k] = "YES" in p.stdout.upper()
    return judged[k]


def wording(text):
    """The provision itself: Légifrance's notes on when a change applies ("NOTA :") are not part of it."""
    return re.split(r"\n\s*NOTA\s*:", text)[0]


def similar(a, b):
    a, b = words(a), words(b)
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0.0


def grade(q, answer):
    a = answer.strip()
    now = wording(q["answer"])
    r = covered(now, a)
    if q.get("previous"):
        before = wording(q["previous"])
        if covered(before, a) >= 0.8 and similar(before, a) > similar(now, a):
            return "old", r
    if r >= 0.95:
        return "exact", r
    if r >= 0.8:
        return "close", r
    if not a or "<invoke" in a or re.fullmatch(r"\W*UNKNOWN\W*", a) or not judge(a):
        return "declined", r
    return "wrong", r


def main():
    qs = [json.loads(l) for l in open(os.path.join(HERE, "questions.jsonl"))]
    todo = []
    for path in glob.glob(os.path.join(HERE, "results", "*.jsonl")):
        for l in open(path):
            r = json.loads(l)
            a = r["answer"].strip()
            if a and not qs[r["n"]].get("excluded") and covered(wording(qs[r["n"]]["answer"]), a) < 0.8:
                todo.append(a)
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(judge, todo))
    json.dump(judged, open(JUDGED, "w"), indent=0)
    table = []
    for path in sorted(glob.glob(os.path.join(HERE, "results", "*.jsonl"))):
        run = os.path.basename(path)[:-6]
        rows = [json.loads(l) for l in open(path)]
        for part in ("known", "changed"):
            got = [(qs[r["n"]], grade(qs[r["n"]], r["answer"])) for r in rows if qs[r["n"]]["set"] == part and not qs[r["n"]].get("excluded")]
            if not got:
                continue
            count = {k: sum(1 for _, (g, _) in got if g == k) for k in ("exact", "close", "wrong", "old", "declined")}
            table.append({"run": run, "set": part, "n": len(got), **count,
                          "by_source": {s: sum(1 for q, (g, _) in got if q["source"] == s and g == "exact") for s in sorted({q["source"] for q, _ in got})}})
    if "--json" in sys.argv:
        print(json.dumps(table, indent=1))
        return
    print(f"{'run':20} {'set':8} {'n':>4} {'exact':>6} {'close':>6} {'wrong':>6} {'old':>5} {'declined':>9}")
    for t in table:
        print(f"{t['run']:20} {t['set']:8} {t['n']:>4} {t['exact']:>6} {t['close']:>6} {t['wrong']:>6} {t['old']:>5} {t['declined']:>9}")


main()
