#!/usr/bin/env bash
# Customer 360 on RushDB 3.x: nested CRM/billing/support JSON plus flat product
# events, an identity check before linking, then filtered schema, facets, a
# graph filter and SQL over label and rushdb_edges tables.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["CUSTOMER","SUBSCRIPTION","INVOICE","TICKET","PRODUCT_EVENT"]'

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

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: 4 customers as nested JSON (subscriptions, invoices, tickets become linked records)"
ingest CUSTOMER customers.json \
  '{"relationshipTypes":{"SUBSCRIPTION":"HAS_SUBSCRIPTION","INVOICE":"HAS_INVOICE","TICKET":"OPENED"}}' \
  | jq -c '{kind, count, relationships}'

heading "Seed: 4 flat product events from the tracking system, not linked yet"
ingest PRODUCT_EVENT product-events.json '{}' | jq -c '{kind, count, relationships}'

heading "Identity check: how well does PRODUCT_EVENT.user_email match CUSTOMER.email?"
send 01-value-overlap.json | jq -c '.pairs[] | del(.source, .target) | .coverage |= (. * 1000 | round / 1000)'

heading "Link events to customers on the exact email (the anonymous visitor stays unlinked)"
send 02-link-events.json | jq -c .

heading "Schema: record counts per label and relationship shapes"
send 03-schema.json | jq -r '.schema
  | (.labels[] | "label \(.name): \(.recordsCount) records"),
    (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'

heading "Properties of all CUSTOMER records (records carrying each one)"
send 04-properties-all-customers.json | jq -r '.properties[] | "\(.name) (\(.type)): \(.recordsCount)"'

heading "Same read filtered to plan = pro: every count narrows to the 2 pro customers"
send 05-properties-pro-customers.json | jq -r '.properties[] | "\(.name) (\(.type)): \(.recordsCount)"'

heading "Facet: stored values of CUSTOMER.plan with counts"
send 06-facet-plan.json | jq -c '{values, counts, distinctCount}'

heading "Customers with an overdue invoice and an open high-priority ticket"
send 07-overdue-and-open-high-ticket.json | jq -c '{total, customers: [.records[].properties | {name, email}]}'

heading "SQL: product events per customer through rushdb_edges.performed_by"
sql 08-events-per-customer.sql | jq -r '.rows[] | "\(.email) | \(.plan) | \(.events)"'
