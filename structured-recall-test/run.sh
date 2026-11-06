#!/usr/bin/env bash
# A structured-recall test for agent memory: 12 questions about counts, sums, dates and
# filters over 107 made-up memories, answered three ways on one RushDB 3.x node:
#   catalog + filters   read describe.schemaSummary, then one native query with a predicate
#                       and an aggregate (the query documents are in data/questions.json)
#   vector-only top-k   rank memories by cosine similarity to the question, keep k = 5, 10, 20,
#                       then answer from those k memories with a perfect reader
#   filtered vector     the same predicate as the catalog query, top 10 by similarity
# The "perfect reader" applies the question's exact logic (data/questions.json: match, answer)
# to the retrieved memories, so vector-only memory is scored on what retrieval returned,
# not on how well a model reads it. Gold answers come from the same logic over every memory.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

rdb() {
  local out
  out=$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' --data-binary @-)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then echo "request failed: $out" >&2; exit 1; fi
  jq '.response' <<<"$out"
}
rdb_try() { curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @- >/dev/null; }
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete MEMORY records and the vector index left by an earlier run"
jq -n '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:["MEMORY"]}}}}' | rdb_try
jq -n '{protocolVersion:1,operation:{kind:"index",index:{kind:"dropVector",name:"mem-embedding"}}}' | rdb_try
echo done

heading "Seed: 107 memories (text + extracted fields + a bge-small-en-v1.5 embedding of the text)"
jq -n '{protocolVersion:1,operation:{kind:"index",index:{kind:"createVector",definition:{
  name:"mem-embedding",label:"MEMORY",property:"embedding",dimensions:384,similarity:"cosine",model:"BAAI/bge-small-en-v1.5"}}}}' \
  | rdb | jq -c '{kind, name: .index.name}'
jq '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"MEMORY",
  documents: map(del(.embedding) + {"$vectors":[{propertyName:"embedding",vector:.embedding,index:"mem-embedding"}]})}}}' \
  data/memories.json | rdb | jq -c '{kind, count}'

heading "What the catalog tells an agent before it writes a filter (describe.schemaSummary, fewValues 10)"
jq -n '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"schemaSummary",labels:["MEMORY"],fewValues:10}}}' \
  | rdb | jq -r '.labels[] | "label \(.name): \(.recordsCount) records",
    (.properties[] | select(.name != "text") | "  \(.name) (\(.type)): \(.recordsCount) records, \(.distinctCount) distinct"
      + (if .min != null then ", \(.min)..\(.max)" else "" end)
      + (if .values and .type == "string" then ": " + (.values | join(", ")) else "" end))'

n=$(jq length data/questions.json)
for i in $(seq 0 $((n - 1))); do
  jq ".[$i]" data/questions.json > "$TMP/q.json"
  id=$(jq -r .id "$TMP/q.json"); match=$(jq -r .match "$TMP/q.json"); answer=$(jq -r .answer "$TMP/q.json")

  # Gold: the question's logic over every memory in the data file.
  gold=$(jq -c "$match | $answer" data/memories.json)
  relevant=$(jq -c "$match | map(.memory_no)" data/memories.json)

  # Catalog + filters: one native query.
  jq '{protocolVersion:1,operation:{kind:"query",query:{kind:"records",query:(
      {labels:["MEMORY"], predicate:.predicate}
      + (if .select then {select:.select}
         elif .list then {select:{(.list):("$record." + .list)}, order:{(.list):"asc"}}
         else {select:{n:{"$count":"*"}}, groupBy:["$record." + .distinct]} end))}}}' "$TMP/q.json" \
    | rdb > "$TMP/catalog.json"
  catalog=$(jq -c --slurpfile q "$TMP/q.json" '$q[0] as $q
    | if $q.select then ((.rows[0].answer)
        # A global aggregate over zero matches returns rows: [] and total: 0 (SQL returns 0).
        // (if .total == 0 and ($q.select.answer | has("$count")) then 0 else null end)
        | if $q.datetime then (. / 1000 | todate | .[0:10])
          elif $q.round then (. * pow(10; $q.round) | round / pow(10; $q.round))
          elif type == "number" and . == floor then floor else . end)
      elif $q.list then (.rows | map(.[$q.list]) | sort)
      else (.rows | length) end' "$TMP/catalog.json")

  # Vector-only: top 20 by similarity, sliced to k.
  jq '{protocolVersion:1,operation:{kind:"query",query:{kind:"vector",query:{
      labels:["MEMORY"],property:"embedding",index:"mem-embedding",vector:.embedding,limit:20,mode:"exact"}}}}' "$TMP/q.json" \
    | rdb | jq '[.records[].properties]' > "$TMP/top20.json"
  # Filtered vector: the catalog query's predicate, top 10.
  jq '{protocolVersion:1,operation:{kind:"query",query:{kind:"vector",query:{
      labels:["MEMORY"],property:"embedding",index:"mem-embedding",vector:.embedding,predicate:.predicate,limit:10,mode:"exact"}}}}' "$TMP/q.json" \
    | rdb | jq '[.records[].properties]' > "$TMP/filtered10.json"

  printf '\n%s [%s] %s\n' "$id" "$(jq -r .type "$TMP/q.json")" "$(jq -r .text "$TMP/q.json")"
  printf '  gold                     %s   (%s relevant memories)\n' "$gold" "$(jq length <<<"$relevant")"
  verdict() { [ "$1" = "$gold" ] && echo "correct" || echo "WRONG"; }
  printf '  catalog + filters        %-28s %s\n' "$catalog" "$(verdict "$catalog")"
  for k in 5 10 20; do
    got=$(jq -c ".[0:$k] | $match | $answer" "$TMP/top20.json")
    ev=$(jq -c --argjson rel "$relevant" ".[0:$k] | map(.memory_no) as \$ids | [\$rel[] | select(. as \$r | \$ids | index(\$r))] | length" "$TMP/top20.json")
    printf '  vector-only k=%-2s        %-28s %-8s evidence %s/%s\n' "$k" "$got" "$(verdict "$got")" "$ev" "$(jq length <<<"$relevant")"
    echo "$id vector-k$k $(verdict "$got")" >> "$TMP/tally"
  done
  got=$(jq -c "$match | $answer" "$TMP/filtered10.json")
  ev=$(jq -c --argjson rel "$relevant" "map(.memory_no) as \$ids | [\$rel[] | select(. as \$r | \$ids | index(\$r))] | length" "$TMP/filtered10.json")
  printf '  filtered vector k=10     %-28s %-8s evidence %s/%s\n' "$got" "$(verdict "$got")" "$ev" "$(jq length <<<"$relevant")"
  echo "$id catalog $(verdict "$catalog")" >> "$TMP/tally"
  echo "$id filtered-k10 $(verdict "$got")" >> "$TMP/tally"
done

heading "Correct answers out of $n"
for arm in catalog vector-k5 vector-k10 vector-k20 filtered-k10; do
  printf '  %-14s %s\n' "$arm" "$(awk -v a="$arm" '$2 == a && $3 == "correct"' "$TMP/tally" | wc -l)"
done
