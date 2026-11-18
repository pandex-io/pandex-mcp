---
name: legal-research
description: Answer questions about European law (EU, France, Germany, Netherlands, United Kingdom, Austria, Switzerland, Luxembourg, ECHR) from the official texts with the Pandex tools. Use when a question asks what a law or court decision says, what an article said on a past date, or which decisions cite a provision.
---

# Legal research with Pandex

Pandex holds official legislation (with past versions) and highest-court decisions. Every answer you give must rest on a passage a tool returned, quoted in its original language, with its source address.

1. **Find.** Call `search`. Write the query in the language of the documents (Dutch for Dutch law, German for German law) and set `jurisdiction` when you know it (`eu`, `fr`, `de`, `nl`, `gb`, `at`, `ch`, `lu`, `coe`). A citation is answered directly: `art. 6:162 BW`, `§ 823 BGB`, `ECLI:NL:HR:2019:2006`, `32016R0679 art 17`.
2. **Read.** Every result carries an id in square brackets, written `id#element`. Pass it to `get_document` for the full official wording. For law as it stood on a date, pass `at` (`2015-01-01`). Use `get_outline` first for a long code.
3. **Follow.** `get_citations` lists what cites an article or decision (leading ones first) and what it cites.
4. **Track changes.** `get_changes` lists the articles of a law (pass its `id`), or of a whole source or jurisdiction, whose wording changed, was inserted or repealed, newest first with the day; a wording still to come is marked. Read the article with `get_document` (and `at` for the wording before) to say what changed.
5. **Check coverage.** If nothing is found, call `list_sources` with the jurisdiction: it says what is held of each court and legislator and what is missing. Say so plainly rather than answering from memory.

Rules: quote the official wording and give the source address the tool returned; say which version (date) of a provision you quote; the texts are not the authentic versions and this is not legal advice.
