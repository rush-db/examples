#!/usr/bin/env bash
# Persistent agent memory with @rushdb/agent-memory-contract on a standalone RushDB 3.x engine.
# The script owns the engine: it starts one on a fresh data directory, writes a session's memories,
# stops the engine, starts it again on the same directory, and recalls from a new process.
# Data: two made-up users of one support agent.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_BIN="${RUSHDB_BIN:-rushdb}"
PORT="${PORT:-3123}"
export RUSHDB_URL="http://127.0.0.1:$PORT" RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
DATA=.data
LOG="$DATA.log"

heading() { printf '\n== %s\n' "$1"; }
start() {
  "$RUSHDB_BIN" serve --data-dir "$DATA" --port "$PORT" --token "$RUSHDB_TOKEN" \
    --pgwire-port 0 --disk-space-threshold-percent 0 >>"$LOG" 2>&1 &
  PID=$!
  # /health answers before storage is open, so wait until a real request succeeds.
  for _ in $(seq 100); do
    curl -s "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' \
      -d '{"protocolVersion":1,"operation":{"kind":"describe","describe":{"kind":"vectorIndexes"}}}' 2>/dev/null |
      jq -e 'has("response")' >/dev/null 2>&1 && return
    sleep 0.2
  done
  echo "engine did not start; see $LOG" >&2; exit 1
}
stop() { kill "$PID"; wait "$PID" 2>/dev/null || true; }
trap 'kill "${PID:-0}" 2>/dev/null || true' EXIT
sql() {
  jq -Rs '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:"sql",statement:.}}}' "queries/$1" |
    curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' --data-binary @- |
    jq -c '.response.rows[]? // .error'
}

[ -d node_modules ] || npm install --silent --no-audit --no-fund
rm -rf "$DATA" "$LOG"

heading "Engine 1: start on an empty data directory ($DATA)"
start; echo "  up on :$PORT"

heading "Session 1 (process 1): Ana's turns become EPISODE records, one preference a MEMORY_FACT"
node scripts/1-session-one.mjs
node scripts/0-ben.mjs

heading "Stop the engine; start it again on the same directory"
stop; start; echo "  restarted"

heading "Session 2 (process 2): recall after the restart, scoped to Ana"
node scripts/2-session-two.mjs

heading "SQL over the same records: episodes per session (the retried turn is not a duplicate)"
sql episodes-per-session.sql

heading "Ana changes her mind: supersede the fact"
node scripts/3-supersede.mjs

heading "SQL: every fact, active or not"
sql facts-by-status.sql

heading "Forget Ana: delete by participant hash"
node scripts/4-forget.mjs

stop
