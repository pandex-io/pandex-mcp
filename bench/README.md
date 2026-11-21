# Can a model quote the law from memory?

120 articles of European legislation, drawn at random. We ask a model for the current wording of each one,
without tools and with the Pandex MCP server, and compare what it says with the official text.

Results and examples: [pandex.io/benchmark](https://www.pandex.io/benchmark)

## The questions

`questions.jsonl`, drawn on 21 November 2026 by `sample.py`:

- **known** (80): ten articles from each of EU, France, Germany, the Netherlands, the UK, Austria, Switzerland
  and Luxembourg. They are drawn from the articles of the 60 most cited laws of each source (the ones the
  [law pages](https://www.pandex.io/law) list), with 120 to 2,500 characters of text and still in force.
- **changed** (40): five articles from each country whose wording changed between 1 January and 21 November
  2026. Each line also holds the wording before the change.

Each question names the provision the way a lawyer of that country would ("§ 342 (Andere als Geldstrafe) of
the Bürgerliches Gesetzbuch", "Article 1596 of the Code civil") and asks for it in its own language. Articles
inside an annex or schedule are left out, because a question cannot name them that way.

One question is excluded from the score, with the reason in its line: § 49 of the "Außerstreitgesetz" drew the
act of 1854 (still listed in force in RIS), while the name normally means the act of 2005, and every model
quoted that one.

## The runs

`run.py` asks through the Claude Code CLI (`claude -p`), from an empty directory, with no settings, no
CLAUDE.md and no built-in tools. Three variants:

| file | tools | the question ends with |
|---|---|---|
| `results/MODEL.jsonl` | none | "Reply with the text of the provision only. If you cannot give its exact wording, reply UNKNOWN." |
| `results/MODEL-plain.jsonl` | none | "Reply with the text of the provision only." |
| `results/MODEL-pandex.jsonl` | the Pandex MCP server only | as the first |

An answer that ran into the API key's rate limit is not kept, and is asked again on the next run.

The system prompt is the same for all: "You are a legal research assistant. You answer with the exact wording
of the law and never make it up." Every question is asked once.

## The score

`score.py` measures how much of the official text the answer holds, word by word and in order (case and
punctuation aside), so a correct quote with a line of comment around it still counts:

- **exact**: 95% or more of the official words are there
- **close**: 80 to 95%: the right provision, worded a little differently
- **old**: an answer to a changed article that holds 80% of the wording before the change and is more like it
  than like the current one
- **wrong**: under 80%, and the answer offers a text as the provision: another wording, another provision, or
  an invented one
- **declined**: under 80%, and the answer gives no such text: UNKNOWN, "I can't quote it", a summary, a list of
  where to look

Whether an answer under 80% offers a text or declines is asked of Claude Sonnet, once per answer; the verdicts
are in `results/judged.json`. Légifrance's notes after a French article ("NOTA :", on when a change applies),
which Pandex keeps with the article, are not part of its wording and are left out of the comparison.

Word overlap is blunt. A close answer can still miss a word that matters ("not", a number, a date), and a
long article quoted correctly but with a different layout can fall under 95%. Read the answers in
`results/` before quoting a number.

## Run it yourself

```bash
PANDEX_KEY=px_... python3 bench/sample.py > bench/questions.jsonl   # optional: draws a new set
python3 bench/run.py sonnet
python3 bench/run.py sonnet --plain
PANDEX_KEY=px_... python3 bench/run.py sonnet --pandex
python3 bench/score.py
```

A key is free at [api.pandex.io](https://api.pandex.io). Results for other models are welcome as a pull request.
