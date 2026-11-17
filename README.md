# Pandex MCP

Official European law for AI agents: legislation with its past versions and the decisions of the highest courts, collected directly from the institutions that publish them, served as passages with their source.

- **Server:** `https://api.pandex.io/mcp` (streamable HTTP, five read-only tools)
- **No key needed to try it:** 50 requests a day without one. A free key (1,000 a day) takes a minute at [api.pandex.io](https://api.pandex.io).
- **Held:** European Union, France, Germany, Netherlands, United Kingdom, Austria, Switzerland, Luxembourg, European Court of Human Rights. 2.8 million documents, 37 million citations linked to the text they point at.
- **Coverage is published per institution**, including what is missing: [api.pandex.io/coverage](https://api.pandex.io/coverage)

## Connect

**Claude Code**

```bash
claude mcp add --transport http pandex https://api.pandex.io/mcp
```

or as a plugin, with a skill that teaches Claude how to research with it:

```
/plugin marketplace add pandex-io/pandex-mcp
/plugin install pandex@pandex
```

**Claude (claude.ai, desktop):** Settings → Connectors → Add custom connector → `https://api.pandex.io/mcp`

**Cursor** (`.cursor/mcp.json`), **Windsurf**, **VS Code**, **Zed** and any client that takes a remote server:

```json
{ "mcpServers": { "pandex": { "url": "https://api.pandex.io/mcp" } } }
```

With a key, add a header: `"headers": { "Authorization": "Bearer px_..." }`. A client that takes an address only can use `https://api.pandex.io/mcp/px_...`.

**HTTP**

```bash
curl -s "https://api.pandex.io/v1/search?format=text" -H "content-type: application/json" \
  -d '{"query": "art. 6:162 BW", "limit": 1}'
```

## Tools

| Tool | What it does |
|---|---|
| `search` | Find passages by words, by meaning or both, in any of the languages. A citation such as `art. 6:162 BW`, `§ 823 BGB` or an ECLI is answered with that text. |
| `get_document` | Read a law, one article or a decision in its official wording, also as it stood on a past date. |
| `get_outline` | The structure of a long law. |
| `get_citations` | What cites an article or a decision, the leading ones first, and what it cites. |
| `list_sources` | What is loaded, per jurisdiction and institution. |

Full reference: [api.pandex.io/docs](https://api.pandex.io/docs).

## Things to ask

- "What does article 6:162 of the Dutch Civil Code say, and which Hoge Raad decisions cite it most?"
- "Is a pre-ticked checkbox valid consent for cookies under EU law? Quote the Court of Justice."
- "Show article 1382 of the French Code civil as it stood on 1 January 2015."
- "What do you hold for Austria, and what is missing?"

## Terms

The texts come from official publications and remain the publishers'; each source's reuse terms are linked on the coverage page. They are not the authentic versions, and nothing here is legal advice. [Terms](https://pandex.io/terms) · [Privacy](https://pandex.io/privacy) · [pandex.io](https://pandex.io)

The files in this repository are under the MIT licence; the legal texts served are not part of it.

`server.json` is this server's entry in the [MCP Registry](https://registry.modelcontextprotocol.io) (`io.pandex/law`).
