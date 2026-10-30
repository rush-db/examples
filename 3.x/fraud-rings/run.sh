#!/usr/bin/env bash
# Seeds the fraud example data, then runs every query from the article.
# Safe to run more than once: records are upserted by their business key and
# existing relationships are skipped.
set -euo pipefail

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
cd "$(dirname "$0")"

# POST one Protocol v1 envelope (read from stdin) to the native HTTP endpoint.
rdb() {
  curl -sS --fail-with-body -X POST "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary @-
}

# ingest LABEL FILE KEY: upsert a JSON array of flat records, matched on KEY.
ingest() {
  jq -n --arg label "$1" --arg key "$3" --slurpfile docs "$2" '{
    protocolVersion: 1,
    operation: { kind: "ingest", ingest: {
      kind: "documents", label: $label, documents: $docs[0],
      options: { mergeBy: [$key], mergeStrategy: "rewrite" } } }
  }' | rdb | jq -r --arg label "$1" '"  \($label): \(.response.count) records"'
}

# link FILE: run a linkRecords request; prints the relationships now in place.
link() {
  rdb < "$1" | jq -r --arg f "$(basename "$1" .json)" \
    '"  \($f): \(.response.created + .response.skippedExisting) relationships"'
}

# query FILE HEADING JQ_FILTER: run a saved request and print a compact result.
query() {
  echo
  echo "== $2"
  rdb < "$1" | jq -r "$3"
}

echo "== Seeding example data"
ingest ACCOUNT     data/accounts.json     accountId
ingest APPLICATION data/applications.json applicationId
ingest PHONE       data/phones.json       number
ingest DEVICE      data/devices.json      deviceId
for f in seed/*.json; do link "$f"; done

query queries/01-ring-suspects.json \
  "Circular money flow: high-risk CY/LV/MT accounts on a directed TRANSFERRED_TO ring of 2-6 hops" \
  '.response.records[] | "  \(.properties.accountId)  \(.properties.holder)  \(.properties.country)"'

query queries/02-all-ring-participants.json \
  "Circular money flow, unscoped: every account on a directed ring of 2-6 hops" \
  '.response.records[] | "  \(.properties.accountId)  \(.properties.country)  risk=\(.properties.riskTier)"'

query queries/03-cycles-ignoring-direction.json \
  "Same, ignoring direction: acct-d, acct-e, acct-f join (d pays e and f, e pays f; no money comes back)" \
  '.response.records[] | "  \(.properties.accountId)  \(.properties.country)  risk=\(.properties.riskTier)"'

query queries/04-shared-phone-with-fraud.json \
  "Shared identifiers: applications that share a phone with a confirmed-fraud application" \
  '.response.records[] | "  \(.properties.applicationId)  \(.properties.applicant)  \(.properties.status)  \(.properties.phone)"'

query queries/05-shared-phone-or-device-with-fraud.json \
  "Shared identifiers: phone or device shared with a confirmed-fraud application" \
  '.response.records[] | "  \(.properties.applicationId)  \(.properties.applicant)  \(.properties.status)"'

query queries/06-count-shared-phone-pairs.json \
  "Before the links exist: joinPairs count of application pairs with the same phone value" \
  '"  pairs=\(.response.value)  (ordered: each matching pair counts once in each direction)"'
