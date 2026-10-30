# agent-memory-provenance

Agent memory stored as linked records, following the AgentMemoryEvent v1 labels: each `MEMORY_FACT` links to
the `EPISODE` (turn) that produced it, each episode to its `SESSION`, its user `ENTITY` and the `REFERENCE`
documents it cited. The script shows idempotent writes (deterministic `eventId`), recall of recent episodes
and their sources, scoped recall before vector ranking, supersession with history, and deleting one user's
memories completely, vectors and relationships included.

Articles: [Choosing an AI agent memory database](https://rushdb.com/blog/ai-agent-memory-database) (the queries
mirror its recall, upsert, supersession, prefilter and deletion examples) and
[Agent memory tools for enterprise AI](https://rushdb.com/blog/agent-memory-tools-enterprise-ai) (isolation,
traceable memories, complete deletion).

## Prerequisites

- A RushDB 3.x engine you can throw away (the script writes `ENTITY`, `SESSION`, `EPISODE`, `MEMORY_FACT` and
  `REFERENCE` records and a vector index named `fact-embedding`). An in-memory node is ideal.
- `curl`, `jq`, and `sha256sum` (or `shasum` on macOS).

## Run

```bash
rushdb serve --token local-token          # in-memory node on :3000
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The output should match `expected-output.txt`. The script is safe to rerun: every write upserts on its id
(`entityId`, `refId`, `sessionId`, `eventId`, `factId`), link requests skip existing edges, and user-77 is
seeded again and deleted again on each run.

## What is in here

| Path | What |
|---|---|
| `data/*.json` | Example data: two users, three sessions, four turns, four facts (one superseded) with 3-dimensional example embeddings, three knowledge-base references |
| `queries/00` | The vector index (`index.createVector`, cosine, 3 dimensions) |
| `queries/01–06` | `linkRecords` on shared keys: `HAD_EPISODE`, `HAS_EPISODE`, `CITED` (a multi-value `citedRefIds` key), `HAS_FACT`, `DERIVED_FROM`, `SUPERSEDES` |
| `queries/10–12` | Retry check, the 5 most recent episodes of a user, references cited by the latest one |
| `queries/13–15` | Active facts scoped by `agentId`, `profileId`, `privacyScope`, with their source turn (`$alias` + `$collect`); the documents behind one fact; a fact's history |
| `queries/16–17` | Vector recall without and with the scope prefilter (`predicate`, applied before ranking) |
| `queries/18–21` | Delete user-77's sessions, turns and facts by `profileId`, then the user record; check nothing is left |

## Notes

- The articles show TypeScript SDK calls; this example sends the same operations as native protocol
  envelopes (`records.upsert` / `importJson` is `ingest.documents` with `mergeBy`; `find` with `where` is
  `query.records` with `predicate`; `orderBy` is `order`; `vectorSearch` is `query.vector`).
- `eventId` is computed as the contract describes: a SHA-256 digest over canonical JSON of the event's
  identity and text. `factId`s are short readable strings here; the contract hashes them too.
- The vectors are made up so the ranking is easy to follow. The engine never calls an embedding model: on a
  self-hosted engine your adapter computes embeddings; RushDB Cloud can embed for you (managed embeddings,
  not covered here).
- A `profileId` field is a convention your service enforces, not a boundary. For hard isolation between
  customers, use a tenant per customer on a multitenant engine (or a project on RushDB Cloud) with
  tenant-bound capability tokens; `purgeTenant` then erases a whole tenant. That needs a server started
  with `--multitenant`, so it is not part of this script.
- Expected output was captured against the engine build of 2026-10-27.
