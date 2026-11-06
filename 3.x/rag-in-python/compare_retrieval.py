"""Should the retriever add a BM25 leg? Ranks the same questions four ways.

Run rag.py first (it stores the articles and their vectors). This script adds a
BM25 text index on DOC.body and prints the top 3 of: the vector leg alone, the
BM25 leg alone, and both legs fused with RRF at text weight 1 and 0.5.
"""

import sys

from rag import db, model

QUESTIONS = sys.argv[1:] or [
    "Can I change the currency on an invoice I already sent?",
    "Why do I get INV-412?",
    "How do I fix error 409?",
]

if not any(i["label"] == "DOC" for i in db.text_indexes.find().data):
    db.text_indexes.create({"label": "DOC", "property": "body", "consistency": "immediate"})


def top(results) -> str:
    return ", ".join(f"{r.get('slug')} {r.score:.4g}" for r in results)


for question in QUESTIONS:
    vector = next(model.query_embed(question)).tolist()
    base = {"labels": ["DOC"], "propertyName": "body", "queryVector": vector, "limit": 3}
    bm25 = db.records.text_search({"labels": ["DOC"], "query": question, "limit": 3})
    print(f"\nQ: {question}")
    print(f"  vector        {top(db.records.vector_search(base))}")
    print(f"  bm25          {top(bm25)}  ({bm25.total} of 11 articles match)")
    for weight in (1, 0.5):
        fused = db.records.vector_search({**base, "text": {"query": question, "weight": weight}})
        print(f"  rrf, text {weight:<3} {top(fused)}")
