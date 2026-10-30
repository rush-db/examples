#!/usr/bin/env bash
# Predicate completeness on RushDB 3.x: per-label completeness from the catalog,
# conditional completeness under a filter, and hierarchical (path) predicates
# across linked records. One small graph: 8 PERSON, 6 ORGANIZATION, 3 COUNTRY.
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
LABELS='["PERSON","ORGANIZATION","COUNTRY"]'

# POST one protocol envelope (read from stdin); print .response, stop on .error.
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
# Send a query file from queries/.
send() { rdb < "queries/$1"; }
# Wrap a .sql file in a query.statement envelope and send it.
sql() {
  jq -Rs '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:"sql",statement:.}}}' \
    "queries/$1" | rdb
}
# Ingest a JSON array of documents from data/ under a root label.
ingest() {
  jq --arg label "$1" --argjson options "$3" \
    '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:$label,documents:.,options:$options}}}' \
    "data/$2" | rdb
}
heading() { printf '\n== %s\n' "$1"; }
props() { jq -r '.properties[] | "\(.name) (\(.type)): \(.recordsCount)" + (if .min then "  [\(.min) .. \(.max)]" else "" end)'; }
names() { jq -c '{total, names: [.rows[].name]}'; }
count() { jq -c '.rows[0]'; }

heading "Reset: delete records left by an earlier run of this example"
jq -n --argjson labels "$LABELS" \
  '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:$labels}}}}' \
  | rdb | jq -c '{kind}'

heading "Seed: 8 people with nested employers and countries (mergeBy name dedupes every level)"
ingest PERSON people.json \
  '{"mergeBy":["name"],"relationshipTypes":{"ORGANIZATION":"WORKS_AT","COUNTRY":"LOCATED_IN"}}' \
  | jq -c '{kind, relationships}'

heading "Seed: turn the lab's parent field into a PART_OF edge"
send 01-link-part-of.json | jq -c .

heading "Schema: labels and relationship shapes"
send 02-schema.json | jq -r '.schema
  | (.labels[] | "label \(.name): \(.recordsCount) records"),
    (.relationships[] | "\(.sourceLabel) -\(.type)-> \(.targetLabel): \(.count)")'

echo
echo "### Part 1: predicate completeness (article: predicate-completeness-knowledge-graph)"

heading "Catalog read: records carrying each PERSON property (no records scanned)"
send 03-person-properties-catalog.json | props

heading "Denominator: PERSON records"
send 04-person-count.json | count

heading "SQL: completeness of born over the person table"
sql 05-born-completeness.sql | jq -c '.rows[0]'

heading "Relationship predicate: people with at least one WORKS_AT edge (subjects, not edges)"
send 06-works-at-subjects.json | count

echo
echo "### Part 2: conditional completeness (article: conditional-completeness-knowledge-graph)"

heading "Filtered schema: PERSON properties among people born before 1920"
send 07-properties-born-before-1920.json | props

heading "Who fails it: born before 1920 and no died value"
send 08-born-before-1920-without-died.json | names

heading "Every segment at once: died completeness per nationality (__missing__ = no nationality)"
send 09-died-completeness-by-nationality.json \
  | jq -c '.rows[] | .diedCompleteness |= (. * 1000 | round / 1000)'

heading "SQL: born completeness per occupation"
sql 10-born-completeness-by-occupation.sql \
  | jq -r '.rows[] | "\(.occupation) | \(.people) | \(.with_born) | \(.completeness)"'

heading "Condition over related records: PERSON properties among people whose employer is in the US"
send 11-properties-us-employer.json | jq -r '.properties[] | "\(.name): \(.recordsCount)"'

echo
echo "### Part 3: hierarchical predicates (article: hierarchical-predicates-graph-queries)"

heading "Super-predicate as a union: WORKS_AT or CONSULTS_FOR (no CONSULTS_FOR edges here)"
send 12-affiliated-union.json | names

heading "Fixed path: people whose employer is LOCATED_IN the US"
send 13-us-employer-fixed-path.json | names

heading "Variable path: employer, or an ancestor within 1-3 PART_OF hops, in the US"
send 14-us-employer-with-hops.json | names

heading "SQL anti-join: people whose employer has no LOCATED_IN edge"
sql 15-employer-without-country.sql | jq -r '.rows[] | "\(.name) | \(.employer)"'

heading "Path completeness: employer has a country, one hop"
send 16-employer-has-country-one-hop.json | count

heading "Path completeness: employer or an ancestor (PART_OF up to 3) has a country"
send 17-employer-or-ancestor-has-country.json | count
