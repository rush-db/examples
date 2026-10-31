#!/usr/bin/env bash
# How many tokens does it cost to describe a database to an agent?
# Loads one BIRD dev database (SQLite) into an empty RushDB 3.x node, writes the same
# database described seven ways into out/<db>/, and counts the tokens of each with
# tiktoken (o200k_base and cl100k_base).
#
# Usage: ./run.sh <path-to-bird>/dev_databases/<db>   e.g. .../california_schools
# Needs: curl, jq, python3, node (npm install first), uv (or tiktoken installed).
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
export RUSHDB_URL RUSHDB_TOKEN
DB_DIR="${1:?usage: ./run.sh <bird dev_databases/<db> folder>}"
DB=$(basename "$DB_DIR")
OUT="out/$DB"
mkdir -p "$OUT"

rdb() {
  local out
  out=$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $RUSHDB_TOKEN" -H 'Content-Type: application/json' --data-binary @-)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then echo "request failed: $out" >&2; exit 1; fi
  jq -c '.response' <<<"$out"
}
heading() { printf '\n== %s\n' "$1"; }

tables=$(python3 -I -c "import sqlite3,sys,json; c=sqlite3.connect(sys.argv[1]); print(json.dumps([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\")]))" "$DB_DIR/$DB.sqlite")
others=$(jq -n '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"labels",query:{}}}}' | rdb | jq -c --argjson t "$tables" '[.labels[] | if type == "string" then . else .name end] - $t')
if [ "$others" != "[]" ]; then echo "this node holds other labels ($others); use an empty node" >&2; exit 1; fi

heading "Load $DB: one label per table, one record per row (and write the DDL files)"
python3 -I scripts/load_sqlite.py "$DB_DIR/$DB.sqlite" "$OUT" "$DB_DIR/database_description"

heading "getSchemaMarkdown (JavaScript SDK, direct mode; the same Markdown as the MCP tool)"
node scripts/schema-markdown.mjs > "$OUT/schema-markdown.md"
echo "$(wc -l < "$OUT/schema-markdown.md") lines"

heading "describe.schemaSummary, every label (fewValues 10), compact JSON as returned"
jq -n '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"schemaSummary",fewValues:10}}}' | rdb > "$OUT/schema-summary.json"
jq -r '.labels[] | "  \(.name): \(.properties | length) properties"' "$OUT/schema-summary.json"

# The narrow reads: the largest label with a text property of few values, and that property, so the
# same commands work on every BIRD database.
pick=$(jq -c '[.labels | sort_by(-.recordsCount)[]
  | {name, p: ([.properties[] | select(.type == "string" and .distinctCount > 1)] | min_by(.distinctCount) | .name)}
  | select(.p != null)][0]' "$OUT/schema-summary.json")
big=$(jq -r .name <<<"$pick"); prop=$(jq -r .p <<<"$pick")
value=$(jq -n --arg l "$big" --arg p "$prop" '{protocolVersion:1,operation:{kind:"query",query:{kind:"propertyValues",property:$p,mode:"topK",limit:1,query:{labels:[$l]}}}}' | rdb | jq -r '.values[0]')
echo "  narrow reads use label $big, property \"$prop\", value \"$value\""

heading "describe.schemaSummary for one label ($big)"
jq -n --arg l "$big" '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"schemaSummary",labels:[$l],fewValues:10}}}' | rdb > "$OUT/schema-summary-one-label.json"

heading "Filtered describe.properties: $big records where $prop = $value"
jq -n --arg l "$big" --arg p "$prop" --arg v "$value" '{protocolVersion:1,operation:{kind:"describe",describe:{kind:"properties",query:{labels:[$l],predicate:{($p):$v}}}}}' \
  | rdb > "$OUT/properties-filtered.json"
jq -c '{properties: [.properties[] | {name, type, recordsCount}]}' "$OUT/properties-filtered.json" > "$OUT/properties-filtered-trimmed.json"
jq -r '"  \(.properties | length) property entries"' "$OUT/properties-filtered.json"

heading "propertyValues topK 10 for $big.$prop"
jq -n --arg l "$big" --arg p "$prop" '{protocolVersion:1,operation:{kind:"query",query:{kind:"propertyValues",property:$p,mode:"topK",limit:10,query:{labels:[$l]}}}}' \
  | rdb > "$OUT/values-top10.json"
cat "$OUT/values-top10.json"

heading "Tokens"
files=("$OUT/ddl.sql" "$OUT/ddl-with-3-rows.sql")
[ -f "$OUT/ddl-with-descriptions.txt" ] && files+=("$OUT/ddl-with-descriptions.txt")
files+=("$OUT/schema-markdown.md" "$OUT/schema-summary.json" "$OUT/schema-summary-one-label.json"
  "$OUT/properties-filtered.json" "$OUT/properties-filtered-trimmed.json" "$OUT/values-top10.json")
if python3 -I -c "import tiktoken" 2>/dev/null; then
  python3 -I scripts/count_tokens.py "${files[@]}"
else
  uv run --quiet --no-project --with tiktoken==0.14.0 python -I scripts/count_tokens.py "${files[@]}"
fi
