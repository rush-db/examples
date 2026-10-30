# catalog-grounding-check

A client-side check for agent-written SQL. Before a query runs, `check.py` parses it with sqlglot, resolves
every table and column against the RushDB catalog, and compares each string literal used with `=`, `!=` or
`IN` against the values the column stores. On a miss it rejects the query and says what is stored instead:
close spellings, other columns that hold the literal, or the column's whole domain when it is small.

Article: [Text-to-SQL hallucination: grounding agents in what is stored](https://rushdb.com/blog/grounding-analytics-agents)
(this is the article's sqlglot sketch with `STORED` backed by the engine's catalog).

> **This is not RushDB's checked submission.** RushDB is building a server-side check, SQL first; it is not a
> shipped feature. This script is the client-side version you can run today.

## Prerequisites

- A RushDB 3.x engine you can throw away (the script writes `district` and `loan` records). An in-memory
  node is ideal.
- `curl`, `jq`, Python 3.9+ and sqlglot:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt     # sqlglot 26.17.1; the client itself uses only the standard library
```

## Run

```bash
rushdb serve --token local-token          # in-memory node on :3000
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh                                  # or PYTHON=/path/to/python ./run.sh
```

The output should match `expected-output.txt`. Seeding upserts on `district_id` and `loan_id`, so reruns
change nothing. To check your own query: `python3 check.py my-query.sql`.

## What is in here

| Path | What |
|---|---|
| `data/*.json` | Example data: 3 districts (names echo the BIRD `financial` database's spellings) and 12 loans |
| `queries/01-agent-prague.sql` | The article's query: `'Prague'` is not a stored `district.name` (it is a `district.region` value) |
| `queries/02-agent-retry-stored-spelling.sql` | The retry with the stored spelling `'Hl.m. Praha'`: passes and runs |
| `queries/03-agent-near-miss.sql` | `'Brno-mesto'` for `'Brno - mesto'`: found by a near-match search |
| `queries/04-agent-date-layout.sql` | `'2013-06'` against a column that stores `'201306'`: found by the date-aware search |
| `queries/05-agent-unknown-column.sql` | A column that does not exist, with a "did you mean" from the catalog |
| `check.py` | The check (under 140 lines) |

## Which RushDB calls it uses

| Step | Request |
|---|---|
| Tables | `describe.labels` (SQL table names are label names, case-insensitive) |
| Columns | `describe.properties` with `detail: "catalog"` (no record reads) |
| Is the literal stored? | `query.propertyValues`, `mode: "values"`, from the per-label value dictionary; for a column with more than 1,000 values, an exact `search` for that one literal |
| Alternatives | `propertyValues` with `search` (`contains`, which also matches other date layouts, then `similar`), and `query.searchValues` across every property |
| Run | `query.statement` with `language: "sql"` (read-only; writes are refused on this path) |

`propertyValues` modes are in the public docs. The `search` option and `searchValues` are in the RushDB 3.0
engine but not yet in the public docs (synced 2026-10-15).

## Limits

- It checks names and compared literals, not meaning: a query with the right values and the wrong join
  still passes. The article's advice holds: check, then run, then look at the result.
- `LIKE`, numeric and date-typed comparisons, and literals inside functions are not checked.
- Cap retries in your agent loop (the article's harness allowed two rejections per question).
- Expected output was captured against the engine build of 2026-10-27 with sqlglot 26.17.1.
