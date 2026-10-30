#!/usr/bin/env bash
# Seeds the supply chain example data, then runs every query from the article.
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
ingest SUPPLIER       data/suppliers.json       code
ingest COMPONENT      data/components.json      code
ingest PART           data/parts.json           code
ingest BATCH          data/batches.json         lotId
ingest PRODUCTION_RUN data/production-runs.json runId
ingest PRODUCT        data/products.json        sku
ingest SHIPMENT       data/shipments.json       shipmentId
for f in seed/*.json; do link "$f"; done

query queries/01-tier-n-exposure.json \
  "Tier-N exposure: tier-1 suppliers with a flood-zone-07 supplier up to 4 tiers behind them" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)"'

query queries/02-recall-downstream-shipments.json \
  "Recall downstream: shipments carrying product made from LOT-2025-001" \
  '.response.records[] | "  \(.properties.shipmentId)  \(.properties.customer) -> \(.properties.destination)"'

query queries/03-recall-upstream-lots.json \
  "Recall upstream: lots that went into PROD-001" \
  '.response.records[] | "  \(.properties.lotId)  \(.properties.material)"'

query queries/04-recall-upstream-suppliers.json \
  "Recall upstream: suppliers of the lots behind PROD-001" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)"'

query queries/05-bom-explosion.json \
  "BOM explosion: everything FG-100 contains, at any depth up to 6" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name) (\(.properties.kind))"'

query queries/06-bom-where-used.json \
  "BOM where-used: finished goods that contain P-118 at any depth up to 6" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)"'

# The engine counts suppliers per component; "exactly one" is filtered here in
# jq because the native query has no HAVING-style filter on a computed count.
query queries/07-single-source-components.json \
  "Single-source dependency: components with exactly one supplier" \
  '.response.rows[] | select(.suppliers == 1) | "  \(.component)  \(.name)  suppliers=\(.suppliers)"'
