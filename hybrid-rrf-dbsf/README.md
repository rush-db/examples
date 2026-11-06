# Hybrid search: RRF vs DBSF with real scores

One BM25 leg and one vector leg over 20 made-up help-center articles, fused by reciprocal rank
fusion (RRF) and by distribution-based score fusion (DBSF). The script prints each record's rank and
score in each leg, the fused score, and recomputes both fusions by hand with jq so every number can be
traced. It also shows a filter applied before both legs and what the fixed BM25 analyzer matches
(no stemming, no stop words).

Article: [Hybrid search explained: RRF vs DBSF with real scores](https://rushdb.com/blog/hybrid-search-rrf-vs-dbsf)

## Prerequisites

- A RushDB 3.x engine reachable over HTTP
- `bash`, `curl`, `jq` (1.6 or later, for `walk`)

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script deletes `ARTICLE` records and drops the `kb-embedding` and `kb-text` indexes first, so it
can be re-run.

## Files

- `data/articles.json`: 20 made-up articles with 384-d embeddings of `title. body`
- `data/queries.json`: three queries with their embeddings
- `scripts/embed.py`: how the embeddings were made: `BAAI/bge-small-en-v1.5` through fastembed 0.9.1
  (`passage_embed` for articles, `query_embed` for queries), rounded to 5 decimals. You only need it
  to change the data: `uv run --with fastembed==0.9.1 python scripts/embed.py in.json out.json text passage`
- `queries/`: request templates; `run.sh` fills `"@text"` and `"@vector"` from `data/queries.json`
- `expected-output.txt`: a real run against the engine build of 2026-10-27 (`rushdb 3.0.1`)

## Formulas the script checks

- RRF: each leg adds `weight / (rrfK + rank + 1)`, rank from 0, `rrfK` 60, weight 1.
- DBSF: each leg's returned scores are mapped by that leg's mean ± 3 standard deviations (population
  standard deviation over the scores the leg returned) to [0, 1], clamped, and summed.
