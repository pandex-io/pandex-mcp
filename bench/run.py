"""Ask a model every question, once from memory and once with the Pandex MCP server, through the Claude Code CLI.

    python3 bench/run.py MODEL            # from memory: no tools at all, "UNKNOWN" allowed
    python3 bench/run.py MODEL --plain    # from memory, asked plainly: no way out offered
    PANDEX_KEY=px_... python3 bench/run.py MODEL --pandex

Answers go to bench/results/{MODEL}{-pandex}.jsonl; a question already answered there is not asked again.
"""
import json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SYSTEM = "You are a legal research assistant. You answer with the exact wording of the law and never make it up."
TAIL = " Reply with the text of the provision only. If you cannot give its exact wording, reply UNKNOWN."
PLAIN = " Reply with the text of the provision only."

model = sys.argv[1]
pandex = "--pandex" in sys.argv
plain = "--plain" in sys.argv
out = os.path.join(HERE, "results", f"{model}{'-pandex' if pandex else ''}{'-plain' if plain else ''}.jsonl")
os.makedirs(os.path.dirname(out), exist_ok=True)

done = set()
if os.path.exists(out):
    done = {json.loads(l)["n"] for l in open(out)}
questions = [json.loads(l) for l in open(os.path.join(HERE, "questions.jsonl"))]

cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--no-session-persistence",
       "--setting-sources", "", "--strict-mcp-config", "--tools", "", "--system-prompt", SYSTEM]
if pandex:
    cfg = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"mcpServers": {"pandex": {"type": "http", "url": "https://api.pandex.io/mcp",
                                         "headers": {"Authorization": f"Bearer {os.environ['PANDEX_KEY']}"}}}}, cfg)
    cfg.close()
    cmd += ["--mcp-config", cfg.name, "--allowedTools", "mcp__pandex__*"]
work = tempfile.mkdtemp()  # an empty directory: no project files, no CLAUDE.md


def ask(n):
    q = questions[n]
    try:
        p = subprocess.run(cmd + ["--", q["question"] + (PLAIN if plain else TAIL)], capture_output=True, text=True, cwd=work, timeout=600)
        r = json.loads(p.stdout)
        return {"n": n, "answer": r.get("result", ""), "turns": r.get("num_turns"), "cost": r.get("total_cost_usd"), "error": r.get("is_error")}
    except Exception as e:  # noqa: BLE001
        return {"n": n, "answer": "", "error": str(e)[:200]}


with open(out, "a") as f, ThreadPoolExecutor(6) as pool:
    for r in pool.map(ask, [n for n in range(len(questions)) if n not in done]):
        if pandex and re.search(r"rate.limit|requests.a.minute", r["answer"], re.I):
            r["error"] = "the key's rate limit, not the model"
        if r.get("error") and (not r["answer"] or pandex):
            print(r["n"], "failed, asked again on the next run:", r["error"], flush=True)
            continue
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        print(r["n"], (r["answer"] or r.get("error") or "")[:70].replace("\n", " "), flush=True)
