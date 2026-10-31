#!/usr/bin/env python3
"""Recall@10 versus filter selectivity on a RushDB 3.x node.

Seeds 20,000 synthetic 128-d vectors (50 Gaussian clusters, seed 7) as DOC records,
each written by one of 100 AUTHOR records (10 teams), then for each filter compares:

  exact     query.vector, mode exact, with the predicate          -> ground truth
  pre       query.vector, mode ann, with the predicate            -> RushDB's filtered ANN
  post10    query.vector, mode ann, no predicate, limit 10, then the filter applied in the client
  post100   the same with limit 100, filtered in the client, first 10 kept

recall@10 = |method's top 10 ∩ exact top 10| / |exact top 10|, averaged over 50 queries.
Standard library only. Usage: RUSHDB_URL=http://127.0.0.1:3000 python3 measure.py
"""
import json
import math
import os
import random
import statistics
import sys
import time
import urllib.error
import urllib.request

URL = os.environ.get("RUSHDB_URL", "http://127.0.0.1:3000") + "/protocol/v1/execute"
TOKEN = os.environ.get("RUSHDB_TOKEN", "local-token")
N_DOCS, DIM, N_CLUSTERS, N_AUTHORS, N_TEAMS, N_QUERIES, K = 20_000, 128, 50, 100, 10, 50, 10
INDEX = "fvs-doc-embedding"


def rdb(operation):
    body = json.dumps({"protocolVersion": 1, "operation": operation}).encode()
    req = urllib.request.Request(URL, body, {"X-RushDB-Token": TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as err:
        out = json.load(err)
    if "response" not in out:
        sys.exit(f"request failed: {json.dumps(out)[:500]}")
    return out["response"]


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [round(x / n, 5) for x in v]


rng = random.Random(7)
centers = [[rng.gauss(0, 1) for _ in range(DIM)] for _ in range(N_CLUSTERS)]


def near(center, sigma):
    return unit([c + rng.gauss(0, sigma) for c in center])


# Reset and seed.
rdb({"kind": "mutate", "mutation": {"kind": "deleteRecords", "query": {"labels": ["AUTHOR", "DOC"]}}})
for drop in ({"kind": "dropVector", "name": INDEX}, {"kind": "drop", "name": "fvs-doc-bucket"}):
    try:
        rdb({"kind": "index", "index": drop})
    except SystemExit:
        pass
rdb({"kind": "index", "index": {"kind": "createVector", "definition": {
    "name": INDEX, "label": "DOC", "property": "embedding", "dimensions": DIM, "similarity": "cosine"}}})

t0 = time.time()
per_author = N_DOCS // N_AUTHORS
for a in range(N_AUTHORS):
    docs = []
    for i in range(per_author):
        cluster = rng.randrange(N_CLUSTERS)
        docs.append({
            "doc_no": a * per_author + i,
            "bucket": rng.randrange(1000),  # uniform 0..999: bucket < b keeps b/1000 of the docs
            "cluster": cluster,
            "$vectors": [{"propertyName": "embedding", "vector": near(centers[cluster], 0.35), "index": INDEX}],
        })
    rdb({"kind": "ingest", "ingest": {"kind": "documents", "label": "AUTHOR",
         "documents": [{"name": f"author-{a}", "team": f"team-{a % N_TEAMS}", "DOC": docs}],
         "options": {"relationshipTypes": {"DOC": "WROTE"}}}})
print(f"seeded {N_DOCS} DOC records ({DIM}-d, {N_CLUSTERS} clusters) and {N_AUTHORS} AUTHOR records in {time.time() - t0:.0f} s")

queries = []
for _ in range(N_QUERIES):
    c = rng.randrange(N_CLUSTERS)
    queries.append((c, near(centers[c], 0.35)))


def search(vector, predicate, mode, limit):
    q = {"labels": ["DOC"], "property": "embedding", "index": INDEX, "vector": vector,
         "predicate": predicate, "limit": limit, "mode": mode}
    t = time.perf_counter()
    r = rdb({"kind": "query", "query": {"kind": "vector", "query": q}})
    ms = (time.perf_counter() - t) * 1000
    return r, ms


# Build the ANN graph once (first ann search builds it).
t = time.perf_counter()
r, _ = search(queries[0][1], {}, "ann", K)
print(f"ANN graph built by first ann search in {time.perf_counter() - t:.1f} s; vectorSearch={json.dumps(r.get('vectorSearch'))}")


def ids(r):
    return [rec["id"] for rec in r["records"]]


def run(name, predicate, keep):
    """keep(record) is the same filter evaluated in the client, for post-filtering."""
    cand = rdb({"kind": "describe", "describe": {"kind": "explainVector", "query": {
        "labels": ["DOC"], "property": "embedding", "index": INDEX, "vector": queries[0][1],
        "predicate": predicate, "limit": K}}})
    count = cand["plan"]["candidateCount"] if "plan" in cand else cand.get("candidateCount")
    rows = {m: {"recall": [], "n": [], "ms": []} for m in ("pre", "post10", "post100")}
    fallbacks = {}
    for _, v in queries:
        truth, _ = search(v, predicate, "exact", K)
        gt = set(ids(truth))
        pre, ms = search(v, predicate, "ann", K)
        fb = pre.get("vectorSearch", {}).get("fallback", "none")
        fallbacks[fb] = fallbacks.get(fb, 0) + 1
        got = {"pre": (ids(pre), ms)}
        for lim, key in ((10, "post10"), (100, "post100")):
            raw, ms = search(v, {}, "ann", lim)
            kept = [rec["id"] for rec in raw["records"] if keep(rec)][:K]
            got[key] = (kept, ms)
        for key, (lst, ms) in got.items():
            rows[key]["recall"].append(len(gt & set(lst)) / max(1, len(gt)))
            rows[key]["n"].append(len(lst))
            rows[key]["ms"].append(ms)
    def fmt(key):
        x = rows[key]
        return f"recall {statistics.mean(x['recall']):.3f}, results {statistics.mean(x['n']):4.1f}/10, p50 {statistics.median(x['ms']):5.1f} ms"
    print(f"\n{name}  (candidates: {count} of {N_DOCS})")
    print(f"  pre-filter ANN : {fmt('pre')}   fallback: {json.dumps(fallbacks, sort_keys=True)}")
    print(f"  post-filter k10: {fmt('post10')}")
    print(f"  post-filter k100: {fmt('post100')}")


prop = lambda rec, k: rec["properties"].get(k)
for b in (1000, 500, 100, 10, 1):
    run(f"bucket < {b} ({b / 10:g}% selectivity, uncorrelated with the vectors)",
        {"bucket": {"$lt": b}} if b < 1000 else {}, lambda rec, b=b: prop(rec, "bucket") < b)

# Correlated: keep only one cluster that is not the query's own (cluster + 25), per query.
print("\nCorrelated filter: cluster = a cluster other than the query's own (2% of docs, far from the query)")
stats = {m: {"recall": [], "n": []} for m in ("pre", "post10", "post100")}
fbs = {}
for c, v in queries:
    pred = {"cluster": (c + 25) % N_CLUSTERS}
    truth, _ = search(v, pred, "exact", K)
    gt = set(ids(truth))
    pre, _ = search(v, pred, "ann", K)
    fb = pre.get("vectorSearch", {}).get("fallback", "none")
    fbs[fb] = fbs.get(fb, 0) + 1
    res = {"pre": ids(pre)}
    for lim, key in ((10, "post10"), (100, "post100")):
        raw, _ = search(v, {}, "ann", lim)
        res[key] = [r["id"] for r in raw["records"] if prop(r, "cluster") == pred["cluster"]][:K]
    for key, lst in res.items():
        stats[key]["recall"].append(len(gt & set(lst)) / max(1, len(gt)))
        stats[key]["n"].append(len(lst))
for key, label in (("pre", "pre-filter ANN "), ("post10", "post-filter k10"), ("post100", "post-filter k100")):
    extra = f"   fallback: {json.dumps(fbs, sort_keys=True)}" if key == "pre" else ""
    print(f"  {label}: recall {statistics.mean(stats[key]['recall']):.3f}, results {statistics.mean(stats[key]['n']):4.1f}/10{extra}")

# Across a relationship: docs whose author is on team-3 (10%).
print("\nAcross a relationship: DOC whose AUTHOR has team = team-3 (10% of docs)")
pred = {"AUTHOR": {"team": "team-3"}}
rec_pre, ms_pre, ms_ex, fbs = [], [], [], {}
for _, v in queries:
    truth, me = search(v, pred, "exact", K)
    pre, mp = search(v, pred, "ann", K)
    fb = pre.get("vectorSearch", {}).get("fallback", "none")
    fbs[fb] = fbs.get(fb, 0) + 1
    rec_pre.append(len(set(ids(truth)) & set(ids(pre))) / max(1, len(ids(truth))))
    ms_pre.append(mp)
    ms_ex.append(me)
print(f"  pre-filter ANN : recall {statistics.mean(rec_pre):.3f}, p50 {statistics.median(ms_pre):.1f} ms   fallback: {json.dumps(fbs, sort_keys=True)}")
print(f"  exact          : recall 1.000, p50 {statistics.median(ms_ex):.1f} ms")

# The filter stage with a declared ordered index on DOC.bucket.
rdb({"kind": "index", "index": {"kind": "create", "definition": {"name": "fvs-doc-bucket", "label": "DOC", "property": "bucket"}}})
for _ in range(600):
    listed = rdb({"kind": "describe", "describe": {"kind": "indexes"}})
    status = [i.get("state") for i in listed.get("indexes", []) if i.get("name") == "fvs-doc-bucket"]
    if status == ["ready"]:
        break
    time.sleep(0.1)
print(f"\nWith an ordered index on DOC.bucket (status {status}): pre-filter ANN")
for b in (500, 100, 10, 1):
    rec, ms = [], []
    for _, v in queries:
        truth, _ = search(v, {"bucket": {"$lt": b}}, "exact", K)
        pre, m = search(v, {"bucket": {"$lt": b}}, "ann", K)
        rec.append(len(set(ids(truth)) & set(ids(pre))) / max(1, len(ids(truth))))
        ms.append(m)
    print(f"  bucket < {b:<4}: recall {statistics.mean(rec):.3f}, p50 {statistics.median(ms):5.1f} ms")
