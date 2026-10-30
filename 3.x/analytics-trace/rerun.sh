#!/usr/bin/env bash
# Rerun the final query of a saved trace with a fresh read-only token and say
# whether the result still matches what the agent saw.
# Usage: ./rerun.sh [trace.json]
set -euo pipefail
cd "$(dirname "$0")"
. ./lib.sh
trace="${1:-trace.json}"

token="$(mint_read_token "$(jq -r '.user' "$trace")-rerun" 300)"
now="$(jq '.finalQuery' "$trace" | rdb "$token")"
jq -n --argjson then "$(jq '{rowCount, citations}' "$trace")" --argjson now "$now" '
  ($now.response.records | map(.properties.order_id)) as $ids
  | if $ids == $then.citations and $now.response.total == $then.rowCount
    then "same result: \($then.rowCount) rows, same order_ids"
    else "data moved: \($then.rowCount) rows then, \($now.response.total) now; new: \($ids - $then.citations), gone: \($then.citations - $ids)"
    end' -r
