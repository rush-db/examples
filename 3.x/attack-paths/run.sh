#!/usr/bin/env bash
# Seeds the security example data, then runs every query from the article.
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

# ingest_host_export FILE: the article's nightly import. Upsert HOST records by
# hostname with mergeStrategy "append", so fields another tool wrote survive.
ingest_host_export() {
  jq -n --slurpfile docs "$1" '{
    protocolVersion: 1,
    operation: { kind: "ingest", ingest: {
      kind: "documents", label: "HOST", documents: $docs[0],
      options: { mergeBy: ["hostname"], mergeStrategy: "append" } } }
  }' | rdb | jq -r --arg f "$(basename "$1")" '"  HOST (\($f)): \(.response.count) records"'
}

echo "== Seeding example data"
ingest USER     data/users.json     username
ingest GROUP    data/groups.json    name
ingest COMPUTER data/computers.json hostname
ingest SERVICE  data/services.json  code
ingest CUSTOMER data/customers.json code
ingest INCIDENT data/incidents.json incidentId
ingest_host_export data/scanner-hosts.json
ingest_host_export data/edr-hosts.json
for f in seed/*.json; do link "$f"; done

query queries/01-hosts-after-both-imports.json \
  "Upsert by hostname: three HOST records carry both the scanner's and the EDR's fields" \
  '.response.records[] | .properties | "  \(.hostname)  cvssScore=\(.cvssScore)  edrAgent=\(.edrAgent)  isolated=\(.isolated)"'

query queries/02-tier0-admins.json \
  "Transitive group membership: users whose groups (up to 6 MEMBER_OF hops) are ADMIN_TO a tier-0 computer" \
  '.response.records[] | "  \(.properties.username)  \(.properties.department)"'

query queries/03-effective-groups-of-user.json \
  "Effective groups of alice.hart: direct membership or up to 6 nested MEMBER_OF hops" \
  '.response.records[] | "  \(.properties.name)"'

query queries/04-attack-path-to-privileged-session.json \
  "Identity attack path: non-privileged users who are admin (through groups) on a computer where a privileged user has a session" \
  '.response.records[] | "  \(.properties.username)  \(.properties.department)"'

# Blast radius: look up the incident's record id, then put it in the $id filter.
incident_id="$(rdb < queries/05-find-incident.json | jq -r '.response.records[0].id')"

query <(jq --arg id "$incident_id" '(.. | objects | select(has("$id"))."$id") |= $id' queries/06-blast-radius-count.json) \
  "Incident blast radius: customers behind the services INC-2026-031 affects (count)" \
  '.response.rows[] | "  customers=\(.count)"'

query <(jq --arg id "$incident_id" '(.. | objects | select(has("$id"))."$id") |= $id' queries/07-blast-radius-customers.json) \
  "Incident blast radius: the same customers, listed" \
  '.response.records[] | "  \(.properties.code)  \(.properties.name)  \(.properties.plan)"'
