#!/usr/bin/env bash
# Company brain on RushDB 3.x: import Slack-, Notion- and Jira-style JSON,
# link it on shared keys, query it with SearchQuery and SQL, add keyword
# search, then narrow what a reader sees with a data-access policy.
# Needs: curl, jq, a running RushDB 3.x engine. Safe to rerun.
set -euo pipefail

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
cd "$(dirname "$0")"

# POST one envelope (from a file or stdin) and fail on a protocol error.
rdb() {
  local out
  out="$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary "@${1:--}")"
  if [ "${2:-}" != "allow-error" ] && jq -e '.error' >/dev/null <<<"$out"; then
    echo "request failed: $(jq -c '.error' <<<"$out")" >&2
    return 1
  fi
  printf '%s\n' "$out"
}

# Wrap a data file in an ingest (nested JSON import) envelope.
ingest() { # label file options-json
  jq -c --arg label "$1" --argjson options "$3" \
    '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: $label, documents: ., options: $options}}}' "$2"
}

# Wrap a .sql file in a read-only statement envelope.
sql() {
  jq -Rsc '{protocolVersion: 1, operation: {kind: "query", query: {kind: "statement", language: "sql", statement: .}}}' "$1"
}

names() { jq -c "[.response.records[].properties.$1]"; }

# Always switch the demo policy off again, even if a step fails.
trap 'rdb queries/25-policy-off.json allow-error >/dev/null || true' EXIT

echo "== Seed: HR export -> PERSON (upsert on email)"
ingest PERSON data/people.json '{"mergeBy":["email"],"mergeStrategy":"append"}' | rdb | jq -c '.response | {count, relationships}'

echo "== Seed: Notion-like pages -> DOC + SECTION, linked HAS_SECTION"
ingest DOC data/docs.json '{"relationshipType":"HAS_SECTION","mergeStrategy":"append"}' | rdb | jq -c '.response | {count, relationships}'

echo "== Seed: Jira-like issues -> ISSUE + COMMENT, linked HAS_COMMENT"
ingest ISSUE data/issues.json '{"relationshipType":"HAS_COMMENT","mergeStrategy":"append"}' | rdb | jq -c '.response | {count, relationships}'

echo "== Seed: Slack-like messages -> MESSAGE (upsert on message_id)"
ingest MESSAGE data/messages.json '{"mergeBy":["message_id"],"mergeStrategy":"append"}' | rdb | jq -c '.response | {count, relationships}'

echo "== Link records across sources on matching keys (existing edges are skipped)"
for f in queries/0[1-6]-link-*.json; do
  printf '%-28s ' "$(jq -r '.operation.mutation.command | "\(.source.label) \(.relationType)"' "$f")"
  # created on the first run, skippedExisting on reruns; the total is stable
  rdb "$f" | jq -r '.response | "edges: \(.created + .skippedExisting)"'
done

echo "== Catalog: labels with counts"
rdb queries/10-catalog-schema.json | jq -c '[.response.schema.labels[] | "\(.name)=\(.recordsCount)"]'
echo "== Catalog: relationship shapes"
rdb queries/10-catalog-schema.json | jq -r '.response.schema.relationships[] | "  \(.sourceLabel) -\(.type)-> \(.targetLabel) (\(.count))"'
echo "== Catalog: datetime properties"
rdb queries/10-catalog-schema.json | jq -c '[.response.schema.properties[] | select(.type == "datetime") | .name] | unique'

echo "== SearchQuery: who has discussed ENG-142?"
rdb queries/11-who-discussed-eng-142.json | names name

echo "== SearchQuery: which refund policy is current? (\$not around a block that holds only \$relation)"
rdb queries/12-current-refund-policy.json | names title

echo "== SearchQuery: what does the current policy say about retries?"
rdb queries/13-current-policy-retry-section.json | names body

echo "== SearchQuery: open, high-priority issues raised in #payments-incidents"
rdb queries/14-hot-issues-in-incident-channel.json | names ticket_key

echo "== SQL: most-discussed issues and their assignees (LEFT JOIN + count)"
sql queries/15-most-discussed-issues.sql | rdb | jq -c '.response.rows[]'

echo "== Keyword search: BM25 text index on MESSAGE.text"
# A rerun gets "conflict: index message_text already exists", which is fine.
rdb queries/16-create-text-index.json allow-error >/dev/null
for _ in $(seq 1 50); do
  state="$(rdb queries/17-list-indexes.json | jq -r '.response.indexes[] | select(.name == "message_text") | .state')"
  [ "$state" = "ready" ] && break
  sleep 0.1
done
echo "message_text: $state"

echo "== Keyword search: 'EUR refunds'"
hits="$(rdb queries/18-text-search-eur-refunds.json)"
jq -c '{total: .response.total}' <<<"$hits"
top="$(jq -r '.response.rows[0].id' <<<"$hits")"
jq -nc --arg id "$top" '{protocolVersion: 1, operation: {kind: "query", query: {kind: "record", id: $id}}}' \
  | rdb | jq -c '{top_hit: .response.record.properties.text}'

echo "== Follow links from the top hit to the issue it mentions"
sed "s/__HIT_ID__/$top/" queries/19-issues-mentioned-by-top-hit.json | rdb | names ticket_key

echo "== Policy: support agent sees PERSON (name, team only), ISSUE and MESSAGE"
rdb queries/20-policy-support-agent.json | jq -c '.response | {enforced, allowedLabels: .policy.allowedLabels}'
echo "== Policy: PERSON records show only visible properties"
rdb queries/21-policy-read-people.json | jq -c '.response.records[].properties | to_entries | sort_by(.key) | from_entries'
echo "== Policy: DOC records are not readable"
rdb queries/22-policy-read-docs.json allow-error | jq -c '.error | {code}'
echo "== Policy: the catalog names only allowed labels"
rdb queries/23-policy-catalog-labels.json | jq -c '.response.labels | sort'
echo "== Policy: SQL sees no doc table"
sql queries/24-policy-sql-doc.sql | rdb - allow-error | jq -c '.error | {code}'
echo "== Policy: switched off"
rdb queries/25-policy-off.json | jq -c '.response | {enforced}'
