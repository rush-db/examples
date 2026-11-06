"""Retrieval-augmented generation over 11 made-up help-center articles.

Retrieval runs locally: fastembed computes the vectors on the CPU and a RushDB
engine stores and searches them. Generation calls any OpenAI-compatible
endpoint and is skipped when OPENAI_API_KEY is not set.

    python rag.py                          # the two built-in questions
    python rag.py "How do I refund a card payment?"
    SHOW_PROMPT=1 python rag.py            # print the whole prompt
"""

import json
import os
import sys
from pathlib import Path

from fastembed import TextEmbedding
from rushdb import RushDB

db = RushDB(
    os.environ.get("RUSHDB_TOKEN", "local-token"),
    direct=True,  # a self-hosted engine; for RushDB Cloud see README.md
    engine_url=os.environ.get("RUSHDB_URL", "http://127.0.0.1:3000"),
)
model = TextEmbedding("BAAI/bge-small-en-v1.5")  # 384 dimensions, runs on the CPU


def index_docs(path: Path) -> None:
    """Step 1: store the articles as records, each with its vector."""
    docs = json.loads(path.read_text())
    db.ai.indexes.create(
        {"label": "DOC", "propertyName": "body", "sourceType": "external", "dimensions": 384}
    )
    vectors = model.passage_embed([f"{d['title']}. {d['body']}" for d in docs])
    db.records.create_many(
        "DOC", docs, vectors=[[{"propertyName": "body", "vector": v.tolist()}] for v in vectors]
    )
    print(f"indexed {len(docs)} articles")


def retrieve(question: str, k: int = 3, where: dict | None = None):
    """Step 2: the k nearest articles by cosine similarity, optionally filtered first."""
    return db.records.vector_search({
        "labels": ["DOC"],
        "propertyName": "body",
        "queryVector": next(model.query_embed(question)).tolist(),
        "where": where or {},
        "limit": k,
    })


def build_prompt(question: str, hits) -> str:
    """Step 3: a prompt that carries the sources and asks the model to cite them."""
    context = "\n\n".join(
        f"[{i}] {h.get('title')} ({h.get('url')})\n{h.get('body')}" for i, h in enumerate(hits, 1)
    )
    return (
        "Answer the question using only the sources below. Cite them as [1], [2]. "
        "If the sources do not contain the answer, say so.\n\n"
        f"Sources:\n{context}\n\nQuestion: {question}"
    )


def generate(prompt: str) -> str:
    """Step 4: any OpenAI-compatible chat endpoint (OpenAI, a local server, a gateway)."""
    from openai import OpenAI  # reads OPENAI_API_KEY and OPENAI_BASE_URL

    reply = OpenAI().chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return reply.choices[0].message.content


if __name__ == "__main__":
    if db.records.find({"labels": ["DOC"], "limit": 1}).total == 0:
        index_docs(Path(__file__).parent / "data" / "docs.json")

    questions = sys.argv[1:] or [
        "Can I change the currency on an invoice I already sent?",
        "Why do I get INV-412?",
    ]
    for question in questions:
        hits = retrieve(question)
        print(f"\nQ: {question}")
        for i, h in enumerate(hits, 1):
            print(f"  [{i}] {h.score:.4f}  {h.get('title'):<32} {h.get('url')}")
        prompt = build_prompt(question, hits)
        if os.environ.get("SHOW_PROMPT"):
            print(prompt)
        if os.environ.get("OPENAI_API_KEY"):
            print("A:", generate(prompt))
        else:
            print(f"  (prompt: {len(prompt)} characters; set OPENAI_API_KEY to generate an answer)")
