#!/usr/bin/env bash
# One dataset, four questions, six ways to ask on RushDB 3.x: SQL, openCypher,
# ISO GQL, SQL/PGQ, Gremlin and the native SearchQuery document. Cypher and GQL
# are release candidates and opt-in, so start the engine with every language:
#   rushdb serve --languages sql,gql,cypher,gremlin,sql-pgq,mongodb
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["CUSTOMER","ORDER","PRODUCT"]'

rdb() {
  local out
  out=$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary @-)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then
    echo "request failed: $out" >&2
    exit 1
  fi
  jq '.response' <<<"$out"
}
statement() {
  jq -Rs --arg lang "$1" \
    '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:$lang,statement:.}}}' \
    "queries/$2" | rdb
}
searchquery() {
  jq '{protocolVersion:1,operation:{kind:"query",query:{kind:"records",query:.}}}' "queries/$1" | rdb
}
rows() { jq -c '.rows'; }
heading() { printf '\n== %s\n' "$1"; }

# Run one question in every language, one line each.
ask() {
  local q="$1"
  printf '%-12s ' sql;          statement sql      "$q.sql"     | rows
  printf '%-12s ' cypher;       statement cypher   "$q.cypher"  | rows
  printf '%-12s ' gql;          statement gql      "$q.gql"     | rows
  printf '%-12s ' sql-pgq;      statement sqlPgq   "$q.pgq"     | rows
  printf '%-12s ' gremlin;      statement gremlin  "$q.gremlin" | rows
  printf '%-12s ' searchquery;  searchquery "$q.searchquery.json" | rows
}

heading "Enabled languages and their status, as the server reports them"
rdb < queries/languages.json | jq -r '.languages[] | "\(.language): \(.status), \(.access)"'

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: nested customers -> orders -> products (products merged on sku)"
jq '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"CUSTOMER",documents:.,
      options:{mergeBy:["sku"],relationshipTypes:{ORDER:"PLACED",PRODUCT:"CONTAINS"}}}}}' \
  data/customers.json | rdb | jq -c '{kind, count, relationships}'
rdb < queries/schema.json | jq -r '.schema
  | (.labels[] | "label \(.name): \(.recordsCount)"),
    (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'

heading "Q1. Products over 50, most expensive first"
ask q1

heading "Q2. Which customers bought Paper filters? (two hops)"
ask q2

heading "Q3. Orders and spend per customer (does the customer with no orders appear?)"
ask q3

heading "Q4. Customers who bought Paper filters also bought... (four hops, distinct customers)"
ask q4
