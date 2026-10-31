#!/usr/bin/env bash
# JSON to graph on RushDB 3.x: import a nested support-ticket export as-is, read
# what the catalog says it became, then reshape the three spots that should not
# be records (a 1:1 attribute bag, a drifting type, an empty array) and re-import
# with relationship names and merge, so shared people and companies are stored once.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["TICKET","CUSTOM_FIELDS","REQUESTER","ORGANIZATION","COMMENTS"]'

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
sql() {
  jq -Rs '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:"sql",statement:.}}}' \
    "queries/$1" | rdb
}
# ingest <options-json>  (documents on stdin)
ingest() {
  jq --argjson options "$1" \
    '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"TICKET",documents:.,options:$options}}}' \
    | rdb | jq -c '{kind, count, relationships}'
}
reset() {
  jq -n --argjson labels "$LABELS" \
    '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
    | rdb | jq -c '{kind}'
}
catalog() {
  rdb < queries/catalog.json | jq -r '.schema
    | (.labels[] | "label \(.name): \(.recordsCount)"),
      (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'
}
props() {
  rdb < queries/ticket-properties.json | jq -c '.properties[]
    | {name, type, recordsCount, isArray} + (if .siblingTypes then {siblingTypes} else {} end)'
}
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete records left by an earlier run of this example"
reset

heading "Import A: the export as-is (labels upper-cased, nothing else)"
ingest '{"capitalizeLabels":true}' < data/tickets.json

heading "A. Catalog: labels and relationship shapes"
catalog

heading "A. TICKET properties: one name with two types, an empty array stored as a property"
props

heading "A. The drift in values: priority holds text and a number"
rdb < queries/priority-values.json | jq -c '{values, counts, distinctCount}'

heading "A. custom_fields became its own label, one record per ticket"
sql ticket-custom-fields.sql | jq -r '.rows[] | "\(.ticket_id) | \(.plan) | \(.region)"'

heading "Reset before the second import"
reset

heading "Import B: reshape (queries/reshape.jq), name relationships, merge identical children"
OPTIONS='{"capitalizeLabels":true,"merge":true,"relationshipTypes":{"requester":"REQUESTED_BY","organization":"MEMBER_OF","comments":"HAS_COMMENT"}}'
jq -f queries/reshape.jq data/tickets.json | ingest "$OPTIONS"

heading "B. Catalog: Maya and Northwind are stored once; relationships carry names"
catalog

heading "B. TICKET properties: plan and region are columns now; priority has one type"
props

heading "B. Import the same export again: merge keeps the counts"
jq -f queries/reshape.jq data/tickets.json | ingest "$OPTIONS"
catalog

heading "B. Filter across two relationships: Northwind's billing tickets"
rdb < queries/northwind-billing-tickets.json | jq -c '.rows[]'

heading "B. Same graph from SQL: tickets per organization"
sql tickets-per-organization.sql | jq -r '.rows[] | "\(.organization) | \(.tickets)"'
