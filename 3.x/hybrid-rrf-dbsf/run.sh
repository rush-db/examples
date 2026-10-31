#!/usr/bin/env bash
# Hybrid search on RushDB 3.x: one BM25 leg, one vector leg, fused by RRF and by DBSF.
# Prints each leg's ranks and scores, the fused scores, and recomputes both fusions by
# hand with jq so you can see where every number comes from.
# Data: 20 made-up help-center articles with bge-small-en-v1.5 embeddings (data/).
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"

# POST one protocol envelope (stdin); print .response, or print the error and exit.
rdb() {
  local out
  out=$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' --data-binary @-)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then echo "request failed: $out" >&2; exit 1; fi
  jq '.response' <<<"$out"
}
# Same, but an error is fine (used for cleanup).
rdb_try() { curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @- >/dev/null; }
# send <query file> <query id>: fill "@text" and "@vector" from data/queries.json, then POST.
send() {
  jq --slurpfile q data/queries.json --arg id "$2" '
    ($q[0][] | select(.id == $id)) as $query
    | walk(if . == "@text" then $query.text elif . == "@vector" then $query.embedding else . end)' \
    "queries/$1" | rdb
}
# probe <text>: text leg only, with an arbitrary query string.
probe() { jq --arg t "$1" 'walk(if . == "@text" then $t else . end)' queries/08-analyzer-probe.json | rdb; }
rows() { jq -r '.records[] | "  \(.properties.slug | .[0:22] | . + " " * (22 - length))  score \(.score | tostring | .[0:8])  vector \(.vectorScore // "-" | tostring | .[0:6])  bm25 \(.textScore // "-" | tostring | .[0:6])  \(.provenance | join(" "))"'; }
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete ARTICLE records and the two indexes left by an earlier run"
jq -n '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:["ARTICLE"]}}}}' | rdb_try
for n in kb-embedding; do jq -n --arg n $n '{protocolVersion:1,operation:{kind:"index",index:{kind:"dropVector",name:$n}}}' | rdb_try; done
for n in kb-text; do jq -n --arg n $n '{protocolVersion:1,operation:{kind:"index",index:{kind:"drop",name:$n}}}' | rdb_try; done
echo "done"

heading "Indexes: a 384-d cosine vector index and an immediate BM25 text index on ARTICLE.text"
jq -c '.[]' queries/00-create-indexes.json | while read -r env; do rdb <<<"$env" | jq -c '{kind, name: (.index.name), state: (.index.state // .index.status)}'; done

# Wait until the text index is ready (a search on a building index fails).
for _ in $(seq 1 100); do
  state=$(jq -n '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"indexes"}}}' | rdb | jq -r '.indexes[] | select(.name=="kb-text") | .state')
  [ "$state" = ready ] && break; sleep 0.1
done

heading "Seed: 20 articles, each with its embedding inline (\$vectors)"
jq '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"ARTICLE",
  documents: map({slug, title, product, text, "$vectors":[{propertyName:"embedding", vector:.embedding, index:"kb-embedding"}]})}}}' \
  data/articles.json | rdb | jq -c '{kind, count}'

echo
echo "### Query q2: \"$(jq -r '.[] | select(.id=="q2") | .text' data/queries.json)\""

heading "Text leg alone: BM25 finds only the two articles that contain \"credentials\" (no stemming: \"rotating\" is not \"rotate\")"
send 01-text-leg-only.json q2 | tee /tmp/rushdb-hybrid-q2-text.json | jq -c '{textSearch}'
rows < /tmp/rushdb-hybrid-q2-text.json

heading "Vector leg alone: cosine similarity ranks rotate-api-key first"
send 02-vector-leg-only.json q2 | rows

heading "RRF (k = 60): records found by both legs win; rotate-api-key, found by one leg, drops to third"
send 03-hybrid-rrf.json q2 | rows

echo
echo "### Query q3: \"$(jq -r '.[] | select(.id=="q3") | .text' data/queries.json)\""

heading "RRF: self-hosted-env-key first (vector rank 0, BM25 rank 1)"
send 03-hybrid-rrf.json q3 | tee /tmp/rushdb-hybrid-q3-rrf.json | rows

heading "RRF by hand: 1/(60 + rank + 1) per leg, summed"
jq -r '.records[0:3][] | (.provenance | map(split(":")[1] | tonumber | 1 / (60 + . + 1)) | add) as $s
  | "  \(.properties.slug): \(.provenance | join(" + ")) = \($s)   engine: \(.score)"' /tmp/rushdb-hybrid-q3-rrf.json

heading "DBSF: the order of the top two flips; self-hosted-secrets has the clearest BM25 lead"
send 04-hybrid-dbsf.json q3 | tee /tmp/rushdb-hybrid-q3-dbsf.json | rows

heading "DBSF by hand: each leg's scores mapped by its own mean +/- 3 standard deviations to [0, 1], then summed"
send 05-leg-scores-vector.json q3 > /tmp/rushdb-hybrid-q3-v.json
send 06-leg-scores-text.json q3 > /tmp/rushdb-hybrid-q3-t.json
jq -n -r --slurpfile v /tmp/rushdb-hybrid-q3-v.json --slurpfile t /tmp/rushdb-hybrid-q3-t.json --slurpfile f /tmp/rushdb-hybrid-q3-dbsf.json '
  def stats: (map(.score)) as $x | ($x | add / length) as $m
    | {m: $m, sd: (($x | map((. - $m) * (. - $m)) | add / length) | sqrt), n: length};
  def norm($st): ((. - ($st.m - 3 * $st.sd)) / (6 * $st.sd)) | if . < 0 then 0 elif . > 1 then 1 else . end;
  ($v[0].records | stats) as $vs | ($t[0].records | stats) as $ts
  | "  vector leg: \($vs.n) scores, mean \($vs.m | tostring | .[0:6]), sd \($vs.sd | tostring | .[0:6])",
    "  text leg:   \($ts.n) scores, mean \($ts.m | tostring | .[0:6]), sd \($ts.sd | tostring | .[0:6])",
    ($f[0].records[0:3][]
      | ((.vectorScore // null) as $vv | (.textScore // null) as $tt
         | ((if $vv then ($vv | norm($vs)) else 0 end) + (if $tt then ($tt | norm($ts)) else 0 end))) as $s
      | "  \(.properties.slug): \($s)   engine: \(.score)")'

heading "A filter runs before both legs: product = self-hosted (BM25 matches drop from 15 to 5)"
send 07-hybrid-rrf-filtered.json q3 | tee /tmp/rushdb-hybrid-q3-filtered.json | jq -c '{textSearch}'
rows < /tmp/rushdb-hybrid-q3-filtered.json

heading "The fixed analyzer: what the BM25 leg matches for each query string"
for t in rotate rotation rotating 'rotat*' credentials credential the; do
  probe "$t" | jq -r --arg t "$t" '"  \($t | . + " " * (12 - length)) \(.textSearch.matches) matches: \([.records[].properties.slug] | .[0:4] | join(", "))\(if (.records | length) > 4 then ", ..." else "" end)"'
done

rm -f /tmp/rushdb-hybrid-q*.json
