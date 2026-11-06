#!/usr/bin/env bash
# Agent memory with provenance on RushDB 3.x: memories are records linked to
# the turn that produced them and the documents it cited, recall is scoped by
# user and agent fields before ranking, facts supersede instead of overwrite,
# and one user's memories can be deleted completely.
# Needs: curl, jq, sha256sum (or shasum), a running RushDB 3.x engine. Safe to rerun.
set -euo pipefail

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
cd "$(dirname "$0")"

rdb() {
  local out
  out="$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary "@${1:--}")"
  if jq -e '.error' >/dev/null <<<"$out"; then
    echo "request failed: $(jq -c '.error' <<<"$out")" >&2
    return 1
  fi
  printf '%s\n' "$out"
}

sha256() { if command -v sha256sum >/dev/null; then sha256sum | cut -d' ' -f1; else shasum -a 256 | cut -d' ' -f1; fi; }

ingest() { # label options-json  (documents on stdin)
  jq -c --arg label "$1" --argjson options "$2" \
    '{protocolVersion: 1, operation: {kind: "ingest", ingest: {kind: "documents", label: $label, documents: ., options: $options}}}'
}

# Fill a placeholder in a request file: fill FILE KEY VALUE
fill() { jq --arg v "$3" "walk(if . == \"$2\" then \$v else . end)" "$1"; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Deterministic event ids, as in the AgentMemoryEvent v1 contract: a SHA-256
# digest over canonical JSON of the event's identity and text. A retried write
# computes the same id and merges instead of duplicating.
jq -c '.[]' data/episodes.json | while read -r ep; do
  id="$(jq -cS '{schemaVersion, agentId, profileId, sessionId, turnIndex, summary}' <<<"$ep" | tr -d '\n' | sha256)"
  jq -c --arg id "$id" '. + {eventId: $id}' <<<"$ep"
done | jq -s . > "$work/episodes.json"

# Each fact records the eventId of the turn that produced it, and carries its
# embedding (example vectors; a real adapter calls an embedding model).
jq --slurpfile eps "$work/episodes.json" '
  map(. as $f
      | ($eps[0][] | select(.sessionId == $f.source.sessionId and .turnIndex == $f.source.turnIndex) | .eventId) as $src
      | del(.source, .embedding)
      + {sourceEventId: $src,
         "$vectors": [{propertyName: "embedding", vector: $f.embedding, index: "fact-embedding"}]})
' data/facts.json > "$work/facts.json"

echo "== Vector index for fact embeddings (re-declaring the same index is a no-op)"
rdb queries/00-create-fact-vector-index.json | jq -c '.response.index | {name, dimensions, similarity}'

echo "== Seed: users, references, sessions (upserts on their ids)"
ingest ENTITY '{"mergeBy":["entityId"],"mergeStrategy":"append"}' < data/entities.json | rdb | jq -c '.response | {ENTITY: .count}'
ingest REFERENCE '{"mergeBy":["refId"],"mergeStrategy":"append"}' < data/references.json | rdb | jq -c '.response | {REFERENCE: .count}'
ingest SESSION '{"mergeBy":["sessionId"],"mergeStrategy":"append"}' < data/sessions.json | rdb | jq -c '.response | {SESSION: .count}'

echo "== Seed: episodes (upsert on eventId) and facts (upsert on factId, with vectors)"
ingest EPISODE '{"mergeBy":["eventId"],"mergeStrategy":"append"}' < "$work/episodes.json" | rdb | jq -c '.response | {EPISODE: .count}'
ingest MEMORY_FACT '{"mergeBy":["factId"],"mergeStrategy":"append"}' < "$work/facts.json" | rdb | jq -c '.response | {MEMORY_FACT: .count}'

echo "== Link memories to their owner, session, source turn and cited documents"
for f in queries/0[1-6]-link-*.json; do
  printf '%-36s ' "$(jq -r '.operation.mutation.command | "\(.source.label) \(.relationType) \(.target.label)"' "$f")"
  rdb "$f" | jq -r '.response | "edges: \(.created + .skippedExisting)"'
done

echo "== Retry: the same episode written again merges into the existing record"
jq '[.[0]]' "$work/episodes.json" | ingest EPISODE '{"mergeBy":["eventId"],"mergeStrategy":"append"}' | rdb >/dev/null
rdb queries/10-count-episodes.json | jq -c '{episodes: .response.total}'

echo "== Recall: the 5 most recent episodes of user-42"
recent="$(rdb queries/11-recent-episodes-of-user.json)"
jq -r '.response.records[].properties | "  \(.startedAt)  \(.summary)"' <<<"$recent"

echo "== Recall: references cited in the most recent episode"
latest="$(jq -r '.response.records[0].properties.eventId' <<<"$recent")"
fill queries/12-references-cited-by-episode.json __EVENT_ID__ "$latest" | rdb | jq -c '[.response.records[].properties.refId] | sort'

echo "== Scoped recall: user-42's active facts, each with the turn it came from"
rdb queries/13-active-facts-with-source.json | jq -c '.response.rows[]'

echo "== Why do you think Lena is on Business? Fact -> source turn -> cited documents"
rdb queries/14-evidence-for-fact.json | jq -c '[.response.records[].properties.title] | sort'

echo "== Audit: the plan fact's history (supersession keeps both versions)"
rdb queries/15-plan-fact-history.json | jq -c '.response.records[].properties | {factId, active, supersedesFactId, text}'

echo "== Vector recall without a scope prefilter (do not do this): another user's memory and a superseded fact come back"
rdb queries/16-vector-recall-unscoped.json | jq -c '.response.records[] | {profileId: .properties.profileId, text: .properties.text}'

echo "== Vector recall with the scope prefilter applied before ranking"
rdb queries/17-vector-recall-scoped.json | jq -c '.response.records[] | {profileId: .properties.profileId, text: .properties.text}'

echo "== Delete user-77: every record carrying profileId user-77, then the user entity"
rdb queries/18-delete-user-memories.json | jq -c '{deleted: .response.affected}'
rdb queries/19-delete-user-entity.json | jq -c '{deleted: .response.affected}'

echo "== After the delete: records left for user-77, and what the unscoped vector search returns"
rdb queries/20-count-user-records.json | jq -c '{user77_records: .response.total}'
rdb queries/16-vector-recall-unscoped.json | jq -c '[.response.records[].properties.profileId] | unique'
echo "== After the delete: relationship shapes left (none touch user-77's records)"
rdb queries/21-relationship-shapes.json | jq -r '.response.schema.relationships[] | "  \(.sourceLabel) -\(.type)-> \(.targetLabel) (\(.count))"'
