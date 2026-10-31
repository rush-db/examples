#!/usr/bin/env bash
# Token budget of the RushDB MCP server (direct mode) on the supply-chain-tier-n example data.
# Needs: node 18+, npm, python 3.10+ with tiktoken, an engine seeded by ../supply-chain-tier-n/run.sh.
set -euo pipefail
cd "$(dirname "$0")"
export RUSHDB_MODE=direct RUSHDB_ENGINE_URL="${RUSHDB_URL:-http://127.0.0.1:3000}" RUSHDB_ENGINE_TOKEN="${RUSHDB_TOKEN:-local-token}"
[ -d node_modules/@rushdb/mcp-server ] || npm install --silent >/dev/null
# Look up the id of SUPPLIER.region for the propertyValues call.
REGION_ID="$(node probe.mjs '[["tools/call",{"name":"findProperties","arguments":{}}]]' \
  | tail -1 | jq -r '.result.structuredContent | (.properties // .data // .) | map(select(.name == "region"))[0].id')"
sed "s/REGION_PROPERTY_ID/$REGION_ID/" calls.json > .calls.resolved.json
node probe.mjs "$(cat .calls.resolved.json)" > probe-output.jsonl
rm -f .calls.resolved.json
${PYTHON:-python3} count_tokens.py < probe-output.jsonl
