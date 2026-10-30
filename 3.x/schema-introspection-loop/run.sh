#!/usr/bin/env bash
# The schema introspection loop on RushDB 3.x: read the shape, narrow on stored
# values, read the shape of the matches, then write one precise query. Two
# questions on one made-up dataset (12 customers with orders and tickets):
#   A. How many refunds did enterprise customers in Germany get last quarter (Q3 2026)?
#   B. Why did enterprise customers cancel after the March price change?
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["CUSTOMER","ORDER","TICKET"]'

# POST one protocol envelope (read from stdin); print .response, stop on .error.
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
# Send a query file from queries/.
send() { rdb < "queries/$1"; }
# Wrap a .sql file in a query.statement envelope and send it.
sql() {
  jq -Rs '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:"sql",statement:.}}}' \
    "queries/$1" | rdb
}
# Ingest a JSON array of documents from data/ under a root label.
ingest() {
  jq --arg label "$1" --argjson options "$3" \
    '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:$label,documents:.,options:$options}}}' \
    "data/$2" | rdb
}
heading() { printf '\n== %s\n' "$1"; }
schema() {
  jq -r '.schema
    | (.labels[] | "label \(.name): \(.recordsCount) records"),
      (.properties[] | "  \(.label).\(.name) (\(.type)): \(.recordsCount)"),
      (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'
}

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: 12 customers with nested orders (PLACED) and support tickets (OPENED)"
ingest CUSTOMER customers.json '{"relationshipTypes":{"ORDER":"PLACED","TICKET":"OPENED"}}' \
  | jq -c '{kind, count, relationships}'

echo
echo "### A. How many refunds did enterprise customers in Germany get last quarter (Q3 2026)?"

heading "Without the loop: the filter an agent guesses (status refunded, Germany, Enterprise) runs and matches nothing"
send 01-guessed-filter.json | jq -c '{total}'

heading "Step 1, read shape: ORDER fields with stored types and counts, and how ORDER links"
send 02-schema-order.json | schema

heading "Step 2, narrow on existing values: stored ORDER.status values with counts"
send 03-values-order-status.json | jq -c '{values, counts}'

heading "Step 2, the customer side: every CUSTOMER field with its few values (segment, not tier; DE, not Germany)"
send 04-schema-summary-customer.json | jq -r '.labels[]
  | "label \(.name): \(.recordsCount) records",
    (.properties[] | "  \(.name) (\(.type)): \(.recordsCount) records, \(.distinctCount) distinct" + (if .values then ": " + (.values | join(", ")) else "" end)),
    (.relationships[] | "  -\(.type)-> \(.label): \(.count)")'

heading "Step 3, read the shape of the matches: refunded orders of enterprise customers in DE (is refundedAt on all of them?)"
send 05-schema-of-de-enterprise-refunds.json | schema

heading "Step 4, precise query: the same filter plus refundedAt in Q3 2026 (the undated refund cannot be placed in a quarter)"
send 06-de-enterprise-refunds-q3.json \
  | jq -c '{total}, (.records[].properties | {order_no, status, amount, refundedAt})'

echo
echo "### B. Why did enterprise customers cancel after the March price change?"

heading "Step 1 was the CUSTOMER summary above: segment, canceled_at, cancel_reason, OPENED -> TICKET"

heading "Step 2, narrow on values that exist: enterprise customers canceled since 2026-03-01 (SQL)"
sql 07-enterprise-cancellations-since-march.sql | jq -c '.rows[0]'

heading "Step 3, read the shape of what matched: cancel_reason is on 3 of the 4 customers"
send 08-schema-of-enterprise-cancellations.json | schema

heading "Step 3, the stored cancel reasons among those customers"
send 09-cancel-reasons-of-matches.json | jq -c '{values, counts}'

heading "Step 4, precise question: customers and support tickets per cancel reason (SQL)"
sql 10-cancel-reasons-with-tickets.sql \
  | jq -r '.rows[] | "\(.cancel_reason // "(no reason recorded)") | customers \(.customers) | tickets \(.tickets)"'

heading "The evidence behind the numbers: the tickets themselves (SQL)"
sql 11-tickets-behind-the-reasons.sql \
  | jq -r '.rows[] | "\(.name) | \(.cancel_reason) | \(.topic) | \(.subject)"'
