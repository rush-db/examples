# company-brain

A small company brain for a made-up company, Acme. It imports HR-, Notion-, Jira- and Slack-style JSON
(nested pages and issues become linked `SECTION` and `COMMENT` records), links the sources on shared keys
(emails, ticket keys, document ids), reads the catalog, answers questions with SearchQuery and SQL, adds a
BM25 keyword index, and shows a data-access policy hiding labels and fields from a reader.

Articles: [How to build a company brain with RushDB](https://rushdb.com/blog/build-company-brain-rushdb)
(the queries mirror steps 2–7 and 9), and the series it closes:
[What is a company brain?](https://rushdb.com/blog/what-is-a-company-brain) ·
[architecture](https://rushdb.com/blog/company-brain-architecture) ·
[access control](https://rushdb.com/blog/company-brain-access-control) ·
[relationships](https://rushdb.com/blog/company-brain-relationships).

## Prerequisites

- A RushDB 3.x engine you can throw away (the script writes `PERSON`, `DOC`, `SECTION`, `ISSUE`, `COMMENT`
  and `MESSAGE` records and installs, then removes, a data-access policy). An in-memory node is ideal.
- `curl` and `jq`.

## Run

```bash
rushdb serve --token local-token          # in-memory node on :3000
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The output should match `expected-output.txt`. The script is safe to rerun: people and messages upsert on
their source id, pages and issues upsert on all their fields (`mergeStrategy: "append"` with no `mergeBy`,
so the nested sections and comments match too), link requests skip existing edges, and the policy is
switched off on exit.

## What is in here

| Path | What |
|---|---|
| `data/*.json` | Example data: 3 people, 2 versions of a refund policy page, 2 issues with comments, 3 chat messages |
| `queries/01–06` | `linkRecords` requests, one per relationship type, joining a field on one label to a field on another |
| `queries/10` | `describe.schema`: labels with counts, relationship shapes, property types |
| `queries/11–14` | SearchQuery: who discussed ENG-142, which refund policy is current (`$not` around a related block), what it says about retries, hot issues from the incident channel |
| `queries/15-most-discussed-issues.sql` | SQL with `JOIN`s on `rushdb_edges.*`, `LEFT JOIN` and `count()` |
| `queries/16–19` | A BM25 text index on `MESSAGE.text`, a keyword search, and a hop from the top hit to the issue it mentions |
| `queries/20–25` | A data-access policy: allowed labels, visible properties, and what a reader sees under it |

The SQL file runs over the HTTP protocol (`query.statement`) in `run.sh`. It runs unchanged in `psql` too:

```bash
PGPASSWORD="$RUSHDB_TOKEN" psql "host=127.0.0.1 port=5432 user=rushdb dbname=rushdb sslmode=disable" \
  -f queries/15-most-discussed-issues.sql
```

## Notes

- The article uses the TypeScript SDK; this example sends the same operations as native protocol envelopes
  (`importJson` is `ingest.documents`, `relationships.createMany` is `mutate.linkRecords`, `records.find` is
  `query.records`, where `where` is called `predicate`).
- The policy demo uses the boot token for brevity. An enforced policy narrows every read in the tenant,
  boot token included. In production, keep the boot token on the server and give agents short-lived,
  read-only capability tokens (`--capability-secret`); see the access-control article.
- Not covered, because they are RushDB Cloud features: managed embeddings (`db.ai.indexes.create`,
  `vectorSearch` with a text `query`) and the hosted MCP endpoint (`https://mcp.rushdb.com/mcp`). On a
  self-hosted engine, create a vector index, write vectors from your own model and search with a query
  vector; connect agents with `@rushdb/mcp-server` in direct mode (`RUSHDB_MODE=direct`).
- Expected output was captured against the engine build of 2026-10-27.
