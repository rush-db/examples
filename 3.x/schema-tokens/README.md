# How many tokens does it cost to describe a database to an agent?

Loads one BIRD dev database (SQLite) into an empty RushDB 3.x node and writes the same database
described nine ways, then counts tokens with tiktoken:

| File | What it is |
|---|---|
| `ddl.sql` | the `CREATE TABLE` statements from `sqlite_master` |
| `ddl-with-3-rows.sql` | the DDL with 3 sample rows per table, a common text-to-SQL prompt format |
| `ddl-with-descriptions.txt` | the DDL plus BIRD's column description CSVs |
| `schema-markdown.md` | `getSchemaMarkdown` (JavaScript SDK in direct mode; the MCP tool returns the same Markdown) |
| `schema-summary.json` | `describe.schemaSummary` for every label, `fewValues` 10, compact JSON as returned |
| `schema-summary-one-label.json` | the same for one label |
| `properties-filtered.json` | `describe.properties` for one label under a filter, as returned |
| `properties-filtered-trimmed.json` | the same, keeping only `name`, `type`, `recordsCount` |
| `values-top10.json` | `propertyValues` `topK` 10 for one property |

The one-label and filtered reads use the largest label that has a text property with few values, so
the script runs unchanged on any BIRD database.

Article: [How many tokens does it cost to describe a database to an agent?](https://rushdb.com/blog/schema-tokens-for-agents)

## Prerequisites

- An **empty** RushDB 3.x node (the script refuses a node holding other labels)
- `bash`, `curl`, `jq`, Python 3.10+, Node.js 18+ (`npm install` here first), and `uv` or
  `pip install tiktoken==0.14.0`
- The BIRD mini-dev databases (CC BY-SA 4.0): https://github.com/bird-bench/mini_dev

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
npm install
./run.sh /path/to/MINIDEV/dev_databases/california_schools
```

Restart with an empty node (or delete the labels) before the next database.

## Notes on the method

- Tokenizers: tiktoken 0.14.0, `o200k_base` (GPT-4o and later OpenAI models) and `cl100k_base`
  (GPT-4, GPT-3.5). Other model families tokenize differently; Anthropic's tokenizer is not available
  offline, so it is not measured here.
- JSON is counted compact, as the engine returns it. Pretty-printed JSON costs more.
- Tables are loaded flat (one label per table). BIRD's foreign keys appear in the DDL but are not
  turned into relationships, so the RushDB descriptions carry no relationship rows for these databases.
- `expected-output.txt` holds real runs on `california_schools`, `student_club` and `superhero`
  against the engine build of 2026-10-27 (`rushdb 3.0.1`), each on a fresh in-memory node.
