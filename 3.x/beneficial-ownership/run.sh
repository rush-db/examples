#!/usr/bin/env bash
# Seeds the beneficial ownership example data, then runs every query from the article.
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
ingest PERSON  data/people.json    code
ingest COMPANY data/companies.json code
# One linkRecords request per ownership link, so each OWNS relationship
# carries its own `percent`.
jq -c '.[] | {
  protocolVersion: 1,
  operation: { kind: "mutate", mutation: { kind: "linkRecords", command: {
    relationType: "OWNS",
    source: { label: .ownerLabel, predicate: { code: .owner } },
    target: { label: "COMPANY",   predicate: { code: .owned } },
    allowCartesian: true, direction: "out",
    properties: { percent: .percent } } } }
}' data/ownership.json | while read -r req; do
  rdb <<< "$req" | jq -r '.response.created + .response.skippedExisting'
done | jq -s -r '"  OWNS: \(add) relationships"'

query queries/01-sanctions-exposure.json \
  "Sanctions exposure: companies owned by a sanctioned person directly or through up to 5 OWNS links between companies" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)"'

query queries/02-circular-ownership.json \
  "Circular ownership: companies on a closed OWNS path of 2-8 links" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)  \(.properties.jurisdiction)"'

# Effective stake: the engine returns records and OWNS links with `percent`;
# multiplying the stakes along each path happens in jq (effective-stake.jq).
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
rdb < queries/03-owners-and-companies.json > "$tmp/records.json"
rdb < queries/04-ownership-links.json      > "$tmp/links.json"
echo
echo "== Effective stake per customer (computed in jq from the OWNS links; 25% threshold)"
jq -n -r --slurpfile records "$tmp/records.json" --slurpfile rels "$tmp/links.json" -f effective-stake.jq
