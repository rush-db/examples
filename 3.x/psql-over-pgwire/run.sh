#!/usr/bin/env bash
# psql against RushDB 3.x over the PostgreSQL wire protocol: seed a small shop
# graph over HTTP (labels and relationship types become tables), then run
# queries/session-1.sql and session-2.sql through psql, including what fails and with which SQLSTATE.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
LABELS='["CUSTOMER","ORDER","PRODUCT"]'

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

echo "== Reset and seed over HTTP"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'
# Drop the index from an earlier run if it exists (ignore "not found").
curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' \
  -d '{"protocolVersion":1,"operation":{"kind":"mutate","mutation":{"kind":"statement","language":"sql","statement":"DROP INDEX customer_city"}}}' >/dev/null
jq '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"CUSTOMER",documents:.,
      options:{mergeBy:["sku"],relationshipTypes:{ORDER:"PLACED",PRODUCT:"CONTAINS"}}}}}' \
  data/customers.json | rdb | jq -c '{kind, count, relationships}'

run_psql() {
  PGPASSWORD="$RUSHDB_TOKEN" psql -X \
    "host=$PGHOST port=$PGPORT user=rushdb dbname=rushdb sslmode=disable" \
    -f "queries/$1" 2>&1
}

echo
run_psql session-1.sql
# CREATE INDEX returns at once and the index backfills in the background;
# the planner uses it once its state is "ready".
until jq -n '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"indexes"}}}' | rdb \
  | jq -e '.indexes[] | select(.name == "customer_city" and .state == "ready")' >/dev/null; do
  sleep 0.2
done
run_psql session-2.sql
