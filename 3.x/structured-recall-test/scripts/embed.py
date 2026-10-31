#!/usr/bin/env python3
"""Adds bge-small-en-v1.5 embeddings (fastembed, 384-d, unit length, 5 decimals) to a JSON array.
Usage: python embed.py <in.json> <out.json> <text-field> passage|query
Run with: uv run --with fastembed==0.9.1 python embed.py ..."""
import json, sys
from fastembed import TextEmbedding

src, dst, field, kind = sys.argv[1:5]
items = json.load(open(src))
model = TextEmbedding("BAAI/bge-small-en-v1.5")
texts = [it[field] for it in items]
vecs = model.query_embed(texts) if kind == "query" else model.passage_embed(texts)
for it, v in zip(items, vecs):
    it["embedding"] = [round(float(x), 5) for x in v]
json.dump(items, open(dst, "w"), ensure_ascii=False)
print(f"{len(items)} items, {len(items[0]['embedding'])}-d")
