#!/usr/bin/env bash
# Seed two small tables, then check five agent-written SQL queries against the
# catalog before running them. Needs: curl, jq, python3 with requirements.txt
# installed, a running RushDB 3.x engine. Safe to rerun.
set -euo pipefail

export RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
export RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
PYTHON="${PYTHON:-python3}"
cd "$(dirname "$0")"

ingest() { # label key file
  jq -c --arg label "$1" --arg key "$2" \
    '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: $label, documents: ., options: {mergeBy: [$key], mergeStrategy: "append"}}}}' "$3" \
  | curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" \
      -H 'Content-Type: application/json' --data-binary @- \
  | jq -e -c --arg label "$1" '.response | {($label): .count}'
}

echo "== Seed: district and loan (example data, upserts on their ids)"
ingest district district_id data/district.json
ingest loan loan_id data/loan.json

echo "== Check each agent query against the catalog; run only the ones that pass"
"$PYTHON" check.py queries/*.sql
