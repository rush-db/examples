#!/usr/bin/env bash
# Type drift on RushDB 3.x: two extractor versions write the same property names with
# different types (price as a number, then as text; in_stock as a boolean, then "yes"/"no").
# The engine accepts both. This shows what the catalog reports, how filters, aggregates,
# sorting and SQL behave on the split, a drift gate for a pipeline, and the repair.
# Data: 12 made-up products (data/).
set -euo pipefail
cd "$(dirname "$0")"

RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"

post() { curl -sS "$RUSHDB_URL/protocol/v1/execute" -H "X-RushDB-Token: $RUSHDB_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @-; }
# Print .response, or print the error and exit.
rdb() {
  local out; out=$(post)
  if ! jq -e 'has("response")' >/dev/null 2>&1 <<<"$out"; then echo "request failed: $out" >&2; exit 1; fi
  jq '.response' <<<"$out"
}
# Print .response, or the error object (for statements expected to fail).
rdb_or_error() { post | jq -c '.response // {error: .error}'; }
send() { rdb < "queries/$1"; }
sql() { jq -Rs '{protocolVersion:1,operation:{kind:"query",query:{kind:"statement",language:"sql",statement:.}}}' "queries/$1"; }
ingest() { jq --argjson options "$2" '{protocolVersion:1,operation:{kind:"ingest",ingest:{kind:"documents",label:"PRODUCT",documents:.,options:$options}}}' "$1" | rdb | jq -c '{kind, count}'; }
heading() { printf '\n== %s\n' "$1"; }
props() { jq -r '.properties[] | select(.name == "price" or .name == "in_stock")
  | "  \(.name) (\(.type)): \(.recordsCount) records" + (if .siblingTypes then ", siblingTypes \(.siblingTypes | join(","))" else "" end)
    + ", sample \(.sampleValues | map(tostring) | join(" | "))"'; }
# The drift gate: list every property name stored with more than one type on PRODUCT.
gate() {
  send 01-describe-product.json | jq -r '[.properties[] | select(.siblingTypes) | .name] | unique
    | if length == 0 then "  gate: no property is split across types" else "  gate: DRIFT in " + join(", ") end'
}

heading "Reset: delete PRODUCT records left by an earlier run"
jq -n '{protocolVersion:1,operation:{kind:"mutate",mutation:{kind:"deleteRecords",query:{labels:["PRODUCT"]}}}}' | post >/dev/null
echo done

heading "Seed: 8 products from extractor v1 (price is a number, in_stock a boolean)"
ingest data/products-extractor-v1.json '{}'
heading "Seed: 4 products from extractor v2 (price is text, in_stock is \"yes\"/\"no\"); nothing is rejected"
ingest data/products-extractor-v2.json '{}'

heading "The catalog: one entry per stored type, with siblingTypes naming the other one"
send 01-describe-product.json | props
gate

heading "Filter price > 30: the numeric filter skips the text prices (gold: 8 products cost more than 30)"
send 02-price-over-30.json | jq -c '{total, skus: [.records[].properties.sku]}'
jq -s 'add | map(.price | tostring | ltrimstr("$") | tonumber) | map(select(. > 30)) | length' \
  data/products-extractor-v1.json data/products-extractor-v2.json | sed 's/^/  gold count from the raw files: /'

heading "Aggregates: \$sum and \$max use the numeric values only; \$count of price counts all 12"
send 03-price-totals.json | jq -c '.rows[0]'

heading "propertyValues range: numbers only (the 249.00 monitor is not the max)"
send 04-price-range.json | jq -c '{min, max, distinctCount}'

heading "Sort by price, descending: numbers first, then text"
send 05-sorted-by-price.json | jq -c '[.records[].properties | [.sku, .price]]'

heading "\$type string finds the drifted records"
send 06-price-type-string.json | jq -c '{total, skus: [.records[].properties.sku]}'
heading "\$type number matches all 12: for scalar names it reads the catalog's type for the property"
send 07-price-type-number.json | jq -c '{total}'

heading "SQL: a column with numbers and text reads as text"
sql 08-sql-columns.sql | rdb | jq -c '.rows[]'
heading "SQL: price > 30 against the text column fails"
sql 09-sql-price-over-30.sql | rdb_or_error
heading "SQL: price > '30' runs, but compares text (\"249.00\" < \"30\")"
sql 10-sql-price-over-text-30.sql | rdb | jq -c '[.rows[].sku]'
heading "SQL: try_cast reads the numbers; \"\$59.99\" becomes NULL"
sql 11-sql-try-cast.sql | rdb | jq -c '.rows[]'

heading "Repair 1: re-ingest v2 with convertNumericValuesToNumbers, upserting by sku"
jq 'map({sku, price})' data/products-extractor-v2.json > /tmp/rushdb-drift-prices.json
ingest /tmp/rushdb-drift-prices.json '{"mergeBy":["sku"],"convertNumericValuesToNumbers":true}'
send 01-describe-product.json | props
heading "What is still text: values the converter cannot parse"
send 06-price-type-string.json | jq -c '[.records[].properties | {sku, price}]'

heading "Repair 2: clean the leftovers in the pipeline (strip \"\$\", map yes/no to booleans) and upsert"
jq 'map({sku, price: (.price | tostring | ltrimstr("$") | tonumber), in_stock: (.in_stock == "yes")})' \
  data/products-extractor-v2.json > /tmp/rushdb-drift-clean.json
ingest /tmp/rushdb-drift-clean.json '{"mergeBy":["sku"]}'
send 01-describe-product.json | props
gate

heading "Filter price > 30 again"
send 02-price-over-30.json | jq -c '{total, skus: [.records[].properties.sku]}'
rm -f /tmp/rushdb-drift-*.json
