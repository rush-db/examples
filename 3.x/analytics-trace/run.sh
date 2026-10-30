#!/usr/bin/env bash
# An inspectable analytics answer on RushDB 3.x: the agent reads with a
# read-only capability token, every step and its catalog evidence goes into a
# trace file, the trace is stored as linked records, and anyone can rerun the
# final query from the trace. The "agent" is a fixed script, not a model.
# Needs: curl, jq, openssl, an engine started with --capability-secret. Safe to rerun.
set -euo pipefail
cd "$(dirname "$0")"
. ./lib.sh

QUESTION="Refunds for enterprise customers in Germany, Q3 2026"
USER_ID="analyst-17"

echo "== Seed: 40 example orders (boot token, upsert on order_id)"
jq -c '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: "ORDER", documents: ., options: {mergeBy: ["order_id"], mergeStrategy: "append"}}}}' data/orders.json \
  | rdb "$RUSHDB_TOKEN" | jq -c '.response | {ORDER: .count}'

echo "== Agent credential: a read-only capability token, 10 minutes"
AGENT_TOKEN="$(mint_read_token analytics-agent 600)"
jq -R 'split(".")[0] | gsub("-"; "+") | gsub("_"; "/") | . + ("=" * ((4 - length % 4) % 4)) | @base64d | fromjson | {sub, scope}' -c <<<"$AGENT_TOKEN"

echo "== The token cannot write"
rdb "$AGENT_TOKEN" queries/06-write-attempt.json allow-error | jq -c '{error}'

steps='[]'
step() { # order tool file evidence-jq-filter
  local out
  out="$(rdb "$AGENT_TOKEN" "$3")"
  steps="$(jq -c --argjson s "$steps" --argjson order "$1" --arg tool "$2" --slurpfile input "$3" \
    --argjson output "$out" "\$s + [{order: \$order, tool: \$tool, input: (\$input[0].operation | tojson),
       outputBytes: (\$output | tojson | length)} + (\$output.response | $4)]" <<<'null')"
  jq -c ".[-1] | del(.input, .outputBytes)" <<<"$steps"
}

echo "== Agent steps (each read with the agent token, evidence kept in the trace)"
step 1 describe.schema queries/01-step-schema.json '{evidence: ([.schema.properties[] | "\(.name):\(.type)"] | join(", "))}'
step 2 propertyValues queries/02-step-status-values.json '{property, seen: .values, counts}'
step 3 propertyValues queries/03-step-country-search.json '{property, searched: "Germany", searchMissed, seen: .values, counts}'
step 4 propertyValues queries/04-step-segment-search.json '{property, searched: "enterprise", seen: .values, counts}'

echo "== Final query (SearchQuery), run with the agent token"
final="$(rdb "$AGENT_TOKEN" queries/05-final-query.json)"
jq -c '{rowCount: .response.total, citations: [.response.records[].properties.order_id],
        refunded: ([.response.records[].properties.amount] | add)}' <<<"$final"

echo "== Write trace.json (question, user, credential, steps, final query, rows, citations, outcome)"
analysis_id="$(printf '%s' "$QUESTION$(jq -c . queries/05-final-query.json)" | { sha256sum 2>/dev/null || shasum -a 256; } | cut -c1-16)"
jq -n --arg id "$analysis_id" --arg q "$QUESTION" --arg user "$USER_ID" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson steps "$steps" --slurpfile query queries/05-final-query.json --argjson final "$final" '{
    analysisId: $id, question: $q, user: $user, askedAt: $at,
    model: "scripted-demo-agent", promptVersion: "v1",
    credential: {sub: "analytics-agent", scope: "read"},
    steps: $steps,
    finalQuery: $query[0],
    rowCount: $final.response.total,
    sampleRows: [$final.response.records[:3][].properties],
    citations: [$final.response.records[].properties.order_id],
    recordIds: [$final.response.records[].id],
    outcome: "answered",
    answer: "\($final.response.total) refunded enterprise orders in DE (stored code for Germany), Q3 2026, \([$final.response.records[].properties.amount] | add) in total"
  }' > trace.json
jq -c '{analysisId, steps: (.steps | length), rowCount, outcome, answer}' trace.json

echo "== Store the trace as ANALYSIS + STEP records (harness writes with its own token, not the agent's)"
sed "s/__ANALYSIS_ID__/$analysis_id/" queries/08-delete-previous-trace.json | rdb "$RUSHDB_TOKEN" >/dev/null
jq -c '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: "ANALYSIS",
  documents: ({analysisId, question, user, askedAt, model, promptVersion, credentialSub: .credential.sub,
               finalQuery: (.finalQuery | tojson), rowCount, outcome, citations,
               STEP: [.steps[] | {analysisId: $id} + (. | with_entries(.value |= (if type == "object" then tojson else . end)))]}),
  options: {relationshipType: "HAS_STEP"}}}}' --arg id "$analysis_id" trace.json \
  | rdb "$RUSHDB_TOKEN" | jq -c '.response | {count, relationships}'

echo "== Query the trace store: answered analyses where a question word was mapped to a stored code"
rdb "$AGENT_TOKEN" queries/09-analyses-with-mapped-values.json | jq -c '[.response.records[].properties | {question, rowCount}]'

echo "== Rerun from the trace with a fresh read-only token"
./rerun.sh trace.json

echo "== A late order arrives; the same rerun now tells 'the data moved' from 'the agent was wrong'"
rdb "$RUSHDB_TOKEN" queries/06-write-attempt.json >/dev/null
./rerun.sh trace.json
rdb "$RUSHDB_TOKEN" queries/07-remove-late-order.json >/dev/null
