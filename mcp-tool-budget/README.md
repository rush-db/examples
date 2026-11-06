# mcp-tool-budget

How many tokens does the RushDB MCP server put in front of a model? This example starts
`@rushdb/mcp-server` 3.0.1 in direct mode against a local engine, plays a minimal MCP client over stdio
(`initialize`, `tools/list`, then ten tool calls), and counts the tokens of the server instructions, every
tool definition and every tool result.

Article: [MCP database tools: a design reference](https://rushdb.com/blog/mcp-database-tools-design)

## Prerequisites

- A RushDB 3.x engine seeded with the `supply-chain-tier-n` example (44 records, 7 labels, 43 links):
  run `../supply-chain-tier-n/run.sh` first.
- Node.js 18+ and npm (installs `@rushdb/mcp-server@3.0.1`), `jq`, Python 3.10+ with
  `pip install -r requirements.txt` (tiktoken).

## Run

```bash
rushdb up
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
(cd ../supply-chain-tier-n && ./run.sh)
./run.sh
```

`expected-output.txt` is a real run against the engine build of 2026-10-27. Token counts use tiktoken's
`o200k_base` encoding, which approximates but does not equal any particular model's tokenizer; compare the
rows with each other rather than reading them as exact bills. Only the text content of each result is
counted. The server also returns the same data as `structuredContent`; a client that forwards both pays
roughly twice.

## Files

| Path | What |
|---|---|
| `probe.mjs` | a ~40-line MCP stdio client: one JSON line per response |
| `calls.json` | the calls (`REGION_PROPERTY_ID` is resolved by `run.sh` with a `findProperties` call) |
| `count_tokens.py` | token counts per instructions, tool definition and tool result |

`probe.mjs` works with any calls. For example, against the `tenant-isolation` engine with a read-only
capability token in `RUSHDB_ENGINE_TOKEN` and `RUSHDB_ENGINE_SCOPE=example-globex`, a `bulkDeleteRecords`
call reaches the engine, which refuses it (`401 unauthorized`); the records stay. In 3.0.1 the MCP server
turns that 401 into a generic "you haven't configured your RushDB credentials" message.
