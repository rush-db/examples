#!/usr/bin/env bash
# What works over RushDB's PostgreSQL wire listener, and what fails, with the SQLSTATE each failure returns.
# Seeds 7 example suppliers over HTTP, then runs every probe through psql.
# Needs: curl, jq, psql (any recent libpq), a single-tenant engine with sql enabled (the default).
set -uo pipefail
cd "$(dirname "$0")"
RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
PG="host=${PGHOST:-127.0.0.1} port=${PGPORT:-5432} user=rushdb dbname=rushdb sslmode=disable"
export PGPASSWORD="$RUSHDB_TOKEN"

rdb() { curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' --data-binary "$1"; }
pg() { psql "$PG" -X -v VERBOSITY=verbose "$@" 2>&1; }

echo "== Reset: delete SUPPLIER records and the indexes an earlier run created"
rdb '{"protocolVersion":1,"operation":{"kind":"mutate","mutation":{"kind":"deleteRecords","query":{"labels":["SUPPLIER"]}}}}' | jq -c '{kind: .response.kind}'
for ix in supplier_region supplier_region_lower; do pg -q -c "DROP INDEX $ix" >/dev/null; done

echo "== Seed: 7 suppliers as nested JSON over HTTP (each nested SUPPLIER is linked with BUYS_FROM)"
jq -c '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: "SUPPLIER", documents: ., options: {relationshipTypes: {SUPPLIER: "BUYS_FROM"}}}}}' data/suppliers.json \
  | rdb "$(cat)" | jq -c '.response | {kind, count, relationships}'

echo "== Startup: TLS is refused, a wrong token is refused"
psql "${PG/sslmode=disable/sslmode=require}" -X -c 'SELECT 1' 2>&1
PGPASSWORD=wrong-token psql "$PG" -X -c 'SELECT 1' 2>&1

echo "== Probes (one connection each; ERROR lines carry the SQLSTATE)"
while IFS=$'\t' read -r name sql; do
  [ -z "$name" ] && continue
  echo "-- $name: $sql"
  if [[ "$sql" == *\\* ]]; then printf '%s\n' "$sql" | pg -q; else pg -c "$sql"; fi
done < queries/probes.tsv

echo "== One session: SET/SHOW/RESET, refusing unindexed filters, two indexes (built in the background; the script waits), a statement timeout"
pg -e -f queries/session-settings.sql

echo "== The two indexes the session created: the lowercase label name made an index on a label 'supplier' that has no records"
rdb '{"protocolVersion":1,"operation":{"kind":"describe","describe":{"kind":"indexes"}}}' | jq -c '.response.indexes[] | {name, label, property, state}'

echo "== One session: single-statement writes (each commits on its own)"
pg -e -f queries/writes.sql
