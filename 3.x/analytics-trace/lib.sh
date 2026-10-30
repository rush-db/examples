# Shared helpers for run.sh and rerun.sh.
RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
# Demo secret: start the engine with the same --capability-secret. Use your own for real data.
RUSHDB_CAPABILITY_SECRET="${RUSHDB_CAPABILITY_SECRET:-00112233445566778899aabbccddeeff}"

# rdb TOKEN [FILE|-] [allow-error]: POST one envelope; fail on a protocol error unless allowed.
rdb() {
  local out
  out="$(curl -sS "$RUSHDB_URL/protocol/v1/execute" \
    -H "X-RushDB-Token: $1" -H 'Content-Type: application/json' \
    --data-binary "@${2:--}")"
  if [ "${3:-}" != "allow-error" ] && jq -e '.error' >/dev/null <<<"$out"; then
    echo "request failed: $(jq -c '.error' <<<"$out")" >&2
    return 1
  fi
  printf '%s\n' "$out"
}

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

# mint_read_token SUBJECT TTL_SECONDS: a read-only capability token
# (base64url(claims) "." base64url(HMAC-SHA256(secret, base64url(claims)))).
mint_read_token() {
  local now payload sig
  now="$(date +%s)"
  payload="$(jq -cn --arg sub "$1" --argjson iat "$now" --argjson exp "$((now + $2))" \
    '{sub: $sub, scope: "read", iat: $iat, exp: $exp}' | tr -d '\n' | b64url)"
  sig="$(printf '%s' "$payload" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:$RUSHDB_CAPABILITY_SECRET" -binary | b64url)"
  printf '%s.%s' "$payload" "$sig"
}
