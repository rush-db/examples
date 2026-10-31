# A structured-recall test for agent memory

Twelve questions of the kind people ask an assistant about their own history: counts, sums,
"how many X since Y", the latest of something, a filtered list, a distinct count. They run over 107
made-up memories on one RushDB 3.x node, answered three ways:

| Arm | How it answers |
|---|---|
| catalog + filters | reads `describe.schemaSummary`, then one native query with a predicate and an aggregate |
| vector-only top-k | ranks memories by cosine similarity to the question (k = 5, 10, 20), then answers from those k |
| filtered vector k=10 | the catalog query's predicate, then the 10 most similar memories |

Every per-question answer is printed in `expected-output.txt`, with how many of the relevant memories
each vector arm retrieved ("evidence").

Article: [Agent memory benchmarks skip the questions databases answer](https://rushdb.com/blog/structured-recall-test)

## What this test is and is not

- Both arms get every benefit. Vector arms are scored with a **perfect reader**: the question's exact
  logic (`match` and `answer` in `data/questions.json`) applied to the memories retrieval returned,
  including their dates and fields. Real models read worse. The catalog arm uses **hand-written**
  query documents (`predicate`, `select`); a model has to write those itself. So this tests what each
  store can return, not how well a model uses it.
- Gold answers come from the same logic over every memory in `data/memories.json`.
- It is small (107 memories fit in any context window). The point is the shape of the questions, not
  the size. It is not LoCoMo, LongMemEval or any published benchmark, and its numbers are not
  comparable with theirs.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

## Files

- `data/memories.json`: 107 memories (text, extracted fields, 384-d embedding of the text)
- `data/questions.json`: 12 questions with the catalog query, the gold logic and the question embedding
- `scripts/make_memories.py`: generates the memories (seed 11)
- `scripts/embed.py`: `BAAI/bge-small-en-v1.5` through fastembed 0.9.1 (`passage_embed` for memories,
  `query_embed` for questions), 5 decimals
- `expected-output.txt`: a real run against the engine build of 2026-10-27 (`rushdb 3.0.1`)

## A detail the run surfaced

A native aggregate with no `groupBy` over zero matching records returns `rows: []` and `total: 0`,
not a row with a zero count (SQL `count(*)` returns `0`). `run.sh` reads an empty result as 0 for
`$count` questions; an agent tool should do the same.
