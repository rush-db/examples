#!/usr/bin/env bash
# Seeds the healthcare example data, then runs every query from the article.
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
ingest CONCEPT   data/concepts.json  code
ingest PATIENT   data/patients.json  patientId
ingest DIAGNOSIS data/diagnoses.json diagnosisId
ingest COMPOUND  data/compounds.json code
ingest GENE      data/genes.json     symbol
ingest DISEASE   data/diseases.json  name
for f in seed/*.json; do link "$f"; done

query queries/01-compounds-for-disease.json \
  "Drug-target-disease: compounds that bind a gene associated with multiple sclerosis" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)  binds=\(.properties.binds | join(","))"'

query queries/02-cohort-descendants.json \
  "Ontology expansion: patients with a diagnosis 1-6 IS_A levels under Diabetes mellitus" \
  '.response.records[] | "  \(.properties.patientId)  age=\(.properties.age)  sex=\(.properties.sex)"'

query queries/03-cohort-including-parent.json \
  "Same cohort plus diagnoses coded at Diabetes mellitus itself (\$or branch)" \
  '.response.records[] | "  \(.properties.patientId)  age=\(.properties.age)  sex=\(.properties.sex)"'
