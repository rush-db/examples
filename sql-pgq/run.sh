#!/usr/bin/env bash
# SQL/PGQ on RushDB 3.x: load the shop graph from the PostgreSQL 19 beta docs
# (customers, orders, products; customer_orders and order_items edges), run the
# docs' query verbatim, then the forms the read-only GRAPH_TABLE profile accepts,
# and list the PG19 constructs it does not.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["customers","orders","products"]'

# POST one protocol envelope (stdin); print the whole reply.
post() {
  curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary @-
}
# Same, but stop on an error and print only .response.
rdb() {
  local out
  out=$(post)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then
    echo "request failed: $out" >&2
    exit 1
  fi
  jq '.response' <<<"$out"
}
# Wrap a statement file in query.statement for a language and send it.
statement() {
  jq -Rs --arg lang "$1" \
    '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:$lang,statement:.}}}' \
    "queries/$2"
}
pgq() { statement sqlPgq "$1" | rdb; }
sql() { statement sql "$1" | rdb; }
# Print the error code and the first line of the message.
expect_error() {
  jq -c '{code: .error.code, message: (.error.message | split("\n")[0])}'
}
ingest() {
  jq --arg label "$1" \
    '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:$label,documents:.,options:{}}}}' \
    "data/$1.json" | rdb
}
rows() { jq -r '.rows[] | [.[]] | map(tostring) | join(" | ")'; }
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: three vertex tables as labels"
for label in customers orders products; do
  ingest "$label" | jq -c --arg l "$label" '{label: $l, count}'
done

heading "Seed: the two edge tables become relationships (joined on the foreign-key values)"
rdb < queries/link-customer-orders.json | jq -c '{type: "customer_orders", created}'
rdb < queries/link-order-items.json | jq -c '{type: "order_items", created}'

heading "1. The PG19 docs query, verbatim"
statement sqlPgq 01-pg19-docs-verbatim.pgq | post | expect_error

heading "2. Same question in RushDB's profile: customers with an order on or after 2026-10-30"
pgq 02-customers-active-on-day.pgq | rows

heading "3. The relational form from the same docs page, over rushdb_edges tables"
sql 03-relational-equivalent.sql | rows

heading "4. Reverse edge direction"
pgq 04-reverse-direction.pgq | rows

heading "5. Two hops, grouped and counted by the outer SELECT"
pgq 05-items-per-customer.pgq | rows

heading "6. Four hops: who bought a product Chen Wei bought"
pgq 06-bought-the-same-product.pgq | rows

heading "7. PG19 constructs outside the profile (each fails with an explicit error)"
for file in queries/not-in-profile/*.pgq; do
  name=$(basename "$file" .pgq)
  printf '%s: ' "$name"
  statement sqlPgq "not-in-profile/$name.pgq" | post | jq -c '.error.code'
done

heading "8. A GRAPH_TABLE query sent as a write is refused: the profile is read-only"
jq -Rs '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"statement",language:"sqlPgq",statement:.}}}' \
  queries/04-reverse-direction.pgq | post | expect_error
