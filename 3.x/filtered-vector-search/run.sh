#!/usr/bin/env bash
# Filtered vector search on RushDB 3.x: post-filtering (rank, then filter in the client),
# pre-filtering (the predicate narrows the candidates before ranking), and a filter on a
# related record's property. Nine made-up docs by three authors, with 3-d vectors so the
# scores are easy to follow. The recall-versus-selectivity measurement is in measure/.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"

post() { curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @-; }
rdb() {
  local out; out=$(post)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then echo "request failed: $out" >&2; exit 1; fi
  jq '.response' <<<"$out"
}
send() { rdb < "queries/$1"; }
rows() { jq -r '.records[] | "  \(.score | tostring | .[0:6])  \(.properties.title)  [\(.properties.lang), \(.properties.year)]"'; }
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete AUTHOR and DOC records and the vector index left by an earlier run"
jq -n '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:["AUTHOR","DOC"]}}}}' | post >/dev/null
jq -n '{protocolVersion:1,operation:{kind:"index",index:{kind:"dropVector",name:"doc-embedding"}}}' | post >/dev/null
echo done

heading "Seed: a 3-d cosine index, then 3 authors with 9 docs (AUTHOR -WROTE-> DOC), vectors inline"
send 00-create-vector-index.json | jq -c '{kind, name: .index.name, status: .index.status}'
jq '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"AUTHOR",documents:.,options:{relationshipTypes:{DOC:"WROTE"}}}}}' \
  data/authors.json | rdb | jq -c '{kind, count, relationships}'

heading "No filter: the 3 nearest docs to [1.0, 0.1, 0.0]"
send 01-unfiltered-top3.json | tee /tmp/rushdb-fvs-top3.json | rows

heading "Post-filter: keep the German docs from that top 3 (what an unfiltered ANN plus a client-side filter returns)"
jq '.records |= map(select(.properties.lang == "de"))' /tmp/rushdb-fvs-top3.json | jq -c '{kept: (.records | length)}'

heading "Pre-filter: the same search with predicate lang = de (filter first, rank the candidates)"
send 02-prefilter-lang-de.json | tee /tmp/rushdb-fvs-de.json | rows
jq -c '{vectorSearch}' /tmp/rushdb-fvs-de.json

heading "Across a relationship: docs since 2025 whose AUTHOR is on the search team"
send 03-filter-across-relationship.json | rows

heading "explainVector: the candidate set the ranking will see"
send 04-explain-vector.json | jq -c '.plan | {accessPath, candidateCount, k}'

heading "mode ann with a filter that leaves one candidate: answered exactly, and the response says why"
send 05-ann-selective-filter.json | tee /tmp/rushdb-fvs-ann.json | rows
jq -c '{vectorSearch}' /tmp/rushdb-fvs-ann.json
rm -f /tmp/rushdb-fvs-*.json
