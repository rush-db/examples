#!/usr/bin/env bash
# Entity resolution on RushDB 3.x: a CRM export (ACCOUNT) and a billing export
# (CUSTOMER) describe the same companies with different names and key formats.
# Collect exact evidence, link the certain matches, review the rest, and
# record every decision as a SAME_AS relationship.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["ACCOUNT","CUSTOMER"]'

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
  jq --arg label "$1" \
    '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:$label,documents:.,options:{}}}}' \
    "data/$2" | rdb
}
heading() { printf '\n== %s\n' "$1"; }

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: 6 CRM accounts and 8 billing customers (made-up companies)"
ingest ACCOUNT crm-accounts.json | jq -c '{kind, count}'
ingest CUSTOMER billing-customers.json | jq -c '{kind, count}'

heading "1. Which property pairs share values? (exact value dictionaries)"
send 01-value-overlap-keys.json | jq -c '.pairs[]
  | {pair: "\(.source.label).\(.source.property) -> \(.target.label).\(.target.property)",
     sourceDistinct, matchedDistinct, coverage: (.coverage * 100 | round / 100),
     sourceUniqueness, targetUniqueness}'

heading "2. How many account-customer pairs share a tax id?"
send 02-count-key-pairs.json | jq -c .

heading "3. Link the certain matches: equal tax id -> SAME_AS"
send 03-link-exact-tax-id.json | jq -c .

heading "4. Accounts left without a match"
send 04-unmatched-accounts.json | jq -c '.rows[]'

heading "5. Billing customers left without a match"
send 05-unmatched-customers.json | jq -c '.rows[]'

heading "6a. Near matches: billing tax ids spelled like DE299876543"
send 06-similar-tax-id.json | jq -c '{values, distinctCount}'

heading "6b. Near matches: billing names spelled like 'Globex Corporation' (minSimilarity 0.4)"
send 07-similar-company-globex.json | jq -c '{values, distinctCount}'

heading "6c. Same name, different key: the billing record named 'Soylent Foods'"
send 08-soylent-billing-record.json | jq -c '.rows[]'

heading "7. A filter value that is not stored: CUSTOMER.country = 'Germany'?"
send 09-country-domain-on-miss.json | jq -c '{values, counts, distinctCount, searchMissed}'

heading "8. After review: link Umbrella Health (same tax id, spaces) and Globex Corporation (same name and email domain)"
send 10-link-reviewed-umbrella.json | jq -c .
send 11-link-reviewed-globex.json | jq -c .

heading "9. Resolved entities in SQL: one row per SAME_AS link"
sql 12-resolved-entities.sql | jq -r '.rows[] | "\(.account) | \(.billing_name) | \(.tax_id // "-") | \(.rule)"'

heading "10. Catalog after resolution: labels and relationship shapes"
send 13-schema-after.json | jq -r '.schema
  | (.labels[] | "label \(.name): \(.recordsCount) records"),
    (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'
