# RAG in Python: retrieve with RushDB, answer with any chat model

A retrieval-augmented generation loop in one Python file (`rag.py`, about 65 lines without
comments and docstrings): 11 made-up help-center articles are stored as RushDB records with one vector each,
the three nearest articles to a question come back with their scores and URLs, and a prompt that
cites them goes to any OpenAI-compatible chat endpoint. Retrieval needs no API key: the vectors
are computed on the CPU with fastembed (`BAAI/bge-small-en-v1.5`, 384 dimensions). Generation is
skipped with a message when `OPENAI_API_KEY` is not set.

`compare_retrieval.py` then ranks three questions four ways (vector only, BM25 only, and both
fused with RRF at two text weights) to show whether a keyword leg helps on this data.

Article: [Build RAG in Python in a few lines, with sources](https://rushdb.com/blog/rag-in-python)

## Prerequisites

- A RushDB 3.x engine reachable over HTTP (self-hosted), or a RushDB Cloud API key (see below)
- Python 3.10 or later
- About 70 MB of disk for the embedding model, downloaded from Hugging Face on the first run
- Optional: an OpenAI-compatible endpoint for the generation step

## Run (self-hosted engine)

```bash
rushdb serve --token local-token          # or: rushdb up
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token

python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python rag.py                              # stores the articles, then answers two questions
python rag.py "How do I refund a card payment?"
SHOW_PROMPT=1 python rag.py                # also prints the prompt sent to the model
python compare_retrieval.py                # vector vs BM25 vs hybrid on the same questions
```

To generate answers, point the OpenAI client at any compatible endpoint:

```bash
export OPENAI_API_KEY=...                  # required to run step 4
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1   # optional: a local server or a gateway
export MODEL=gpt-4o-mini                   # optional: the default
python rag.py
```

The first run stores the articles; later runs find `DOC` records and skip that step. To start
over, run on an empty node, or delete the `DOC` records and the vector index (`db.ai.indexes.find()`
lists it) and the text index that `compare_retrieval.py` creates.

## Run on RushDB Cloud

The same file works against RushDB Cloud with one change: connect with an API key from
[app.rushdb.com](https://app.rushdb.com) instead of `direct=True`.

```python
db = RushDB(os.environ["RUSHDB_API_KEY"])
```

External indexes and `queryVector` searches work the same on Cloud, so you keep your own model.
Cloud can also embed for you with a managed index: create the index without `sourceType` and
`dimensions`, write the records without `vectors`, and search with a text `query`. Cloud embeds
every write and backfills existing records, and the index can be searched once its `status` is
`ready` ([manage indexes](https://docs.rushdb.com/3.x/learn/semantic-search/manage-indexes),
[semantic search](https://docs.rushdb.com/3.x/learn/semantic-search)):

```python
db.ai.indexes.create({"label": "DOC", "propertyName": "body"})   # managed: Cloud embeds
db.records.create_many("DOC", docs)
hits = db.records.vector_search(
    {"labels": ["DOC"], "propertyName": "body", "query": question, "limit": 3}
)
```

On a self-hosted engine a managed index or a text `query` raises `CloudOnlyError` before anything
is sent. The Cloud variant was not part of the recorded run.

## Files

- `rag.py`: the four steps (store, retrieve, build the prompt, generate)
- `compare_retrieval.py`: adds a BM25 text index on `DOC.body` and prints four rankings per question
- `data/docs.json`: 11 made-up help-center articles for a fictional invoicing app (`slug`, `title`,
  `area`, `url`, `body`)
- `requirements.txt`: `rushdb` 3.1.0, `fastembed` 0.9.1, `openai`
- `expected-output.txt`: a real run against a fresh RushDB 3.0.0 engine on 2026-11-06, with
  `rushdb` 3.1.0 and fastembed 0.9.1 on Python 3.12, without `OPENAI_API_KEY` (retrieval only)

## SDK calls used

| Step | Call |
|---|---|
| Connect | `RushDB(token, direct=True, engine_url=...)` |
| Vector index | `db.ai.indexes.create({"label", "propertyName", "sourceType": "external", "dimensions": 384})` |
| Store records with vectors | `db.records.create_many("DOC", docs, vectors=[[{"propertyName": "body", "vector": [...]}], ...])` |
| Retrieve | `db.records.vector_search({"labels", "propertyName", "queryVector", "where", "limit"})` |
| Keyword index and search | `db.text_indexes.create(...)`, `db.records.text_search(...)` |
| Hybrid | `db.records.vector_search({..., "text": {"query", "weight"}})` (RRF by default) |

## How it maps to the article

| Article section | Output |
|---|---|
| Steps 1–3 (store, retrieve, prompt) | `$ python rag.py` |
| Should you add BM25? | `$ python compare_retrieval.py` |
| Re-running | the last block: no re-indexing, same scores |
