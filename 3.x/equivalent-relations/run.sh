#!/usr/bin/env bash
# Semantically equivalent relations on RushDB 3.x: two imports name the same
# relation differently (WORKS_AT / EMPLOYED_BY) and the same key differently
# (customer_id / cust_id). Collect exact evidence, then merge with a retype.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["EMPLOYEE","COMPANY","ORDER","INVOICE"]'

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
shapes() {
  jq -r '.schema.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)"'
}

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: HR import links employees to companies with WORKS_AT"
ingest EMPLOYEE hr-employees.json '{"mergeBy":["name"],"relationshipTypes":{"COMPANY":"WORKS_AT"}}' \
  | jq -c '{kind, count, relationships}'

heading "Seed: CRM import of overlapping people uses EMPLOYED_BY (mergeBy name: same records)"
ingest EMPLOYEE crm-contacts.json '{"mergeBy":["name"],"relationshipTypes":{"COMPANY":"EMPLOYED_BY"}}' \
  | jq -c '{kind, count, relationships}'

heading "Seed: orders carry customer_id, invoices carry cust_id"
ingest ORDER orders.json '{}' | jq -c '{kind, count}'
ingest INVOICE invoices.json '{}' | jq -c '{kind, count}'

heading "1. Same endpoint labels: relationship shapes from the catalog"
send 01-relationship-shapes.json | jq -r '.schema
  | (.labels[] | "label \(.name): \(.recordsCount) records"),
    (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'

heading "2. Shared endpoint pairs: edges of both types joining the same employee and company"
sql 02-shared-endpoint-pairs.sql | jq -c '.rows[0]'

heading "3. Name similarity: labels and properties spelled like customer_id (whole node)"
send 03-names-like-customer-id.json | jq -c '.names[]'

heading "4. Value overlap: an identifier pair and a numeric decoy"
send 04-value-overlap.json | jq -c '.pairs[]
  | {pair: "\(.source.label).\(.source.property) -> \(.target.label).\(.target.property)",
     sourceDistinct, matchedDistinct, coverage: (.coverage * 100 | round / 100),
     sourceUniqueness, targetUniqueness}'

heading "5a. Values spelled differently: COMPANY.name similar to 'Initech LLC'"
send 05-similar-company-name.json | jq -c '{values, distinctCount}'

heading "5b. One value, every property: where is 'C-17' stored?"
send 06-search-values-c17.json | jq -c '.matches[]'

heading "Merge: retype EMPLOYED_BY to WORKS_AT between EMPLOYEE and COMPANY"
send 07-retype-employed-by.json | jq -c .

heading "Re-read the shapes: one type left; the 2 shared pairs did not become duplicate edges"
send 01-relationship-shapes.json | shapes

heading "SQL check: one WORKS_AT edge per employee after the merge"
sql 08-employers-after-merge.sql | jq -r '.rows[] | "\(.name) | \(.company) | \(.works_at_edges)"'
