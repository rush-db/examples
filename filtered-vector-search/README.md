# Filtered vector search: post-filter, pre-filter and filters across relationships

Two parts, both against a local RushDB 3.x engine:

- `run.sh` (curl + jq): nine made-up docs by three authors with 3-d vectors, so every score is easy
  to follow. It shows an unfiltered top 3, the same top 3 post-filtered in the client (nothing left),
  the pre-filtered search (`predicate` before ranking), a filter on a related record's property
  (`"AUTHOR": {"team": "search"}`), `describe.explainVector`, and an `ann` search whose filter leaves
  one candidate (answered exactly, `fallback: lowConfidence`).
- `measure/measure.py` (Python standard library): recall@10 against selectivity on 20,000 synthetic
  128-d vectors in 50 Gaussian clusters (seed 7), 50 queries per filter. It compares RushDB's filtered
  ANN with post-filtering at k = 10 and k = 100, adds a filter correlated with the vectors, a filter
  across a relationship, and the filter stage with an ordered index.

Article: [Filtered vector search: pre-filter, post-filter and filters across relationships](https://rushdb.com/blog/filtered-vector-search)

## Prerequisites

- A RushDB 3.x engine reachable over HTTP; use an empty node (both parts delete `AUTHOR` and `DOC` records)
- `bash`, `curl`, `jq`; Python 3.10+ for `measure/`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
python3 measure/measure.py       # about 3 minutes on a laptop
```

## Method (measure/)

- Ground truth for every query is `query.vector` with `mode: "exact"` and the same predicate.
- `pre`: `mode: "ann"` with the predicate (default `ef` 64).
- `post10` / `post100`: `mode: "ann"` with no predicate and `limit` 10 or 100, then the filter applied
  in the client and the first 10 kept. This is what a vector store without filtering, or with
  filtering after the index search, returns.
- recall@10 = |method's top 10 ∩ exact top 10| / |exact top 10|, averaged over 50 queries.
- Latencies are client-side wall time per HTTP request (p50 over 50 queries) on one in-memory node.
  They depend on the machine and on what else runs on it; treat them as relative, not as a benchmark.

## Files

- `data/authors.json`: example data for `run.sh`
- `queries/`: every request `run.sh` sends after seeding
- `expected-output.txt`, `measure/expected-output.txt`: real runs against the engine build of 2026-10-27
  (`rushdb 3.0.1`, in-memory, i9-12900H laptop)
