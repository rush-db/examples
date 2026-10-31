# Shared helpers for run.sh.
RUSHDB_URL="${RUSHDB_URL:-http://127.0.0.1:3000}"
RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
# Demo secret: start the engine with the same --capability-secret. Use your own for real data.
RUSHDB_CAPABILITY_SECRET="${RUSHDB_CAPABILITY_SECRET:-00112233445566778899aabbccddeeff}"
ACME="${ACME_TENANT:-example-acme}"
GLOBEX="${GLOBEX_TENANT:-example-globex}"

# call TOKEN TENANT ENVELOPE_JSON: POST one envelope; print "HTTP <code> <body>" on one line.
# TENANT "-" sends no X-RushDB-Tenant header. The envelope's context.scope is set by the caller.
call() {
  local args=(-sS -o /tmp/rushdb-tenant-isolation.$$ -w '%{http_code}' "$RUSHDB_URL/protocol/v1/execute"
    -H "X-RushDB-Token: $1" -H 'Content-Type: application/json' --data-binary "$3")
  [ "$2" != "-" ] && args+=(-H "X-RushDB-Tenant: $2")
  local code; code="$(curl "${args[@]}")"
  printf 'HTTP %s %s\n' "$code" "$(jq -c 'if .response then .response else . end' /tmp/rushdb-tenant-isolation.$$)"
  rm -f /tmp/rushdb-tenant-isolation.$$
}
# envelope SCOPE OPERATION_JSON: a Protocol v1 envelope for one tenant (SCOPE "-" = no context.scope).
envelope() {
  if [ "$1" = "-" ]; then jq -cn --argjson op "$2" '{protocolVersion: 1, operation: $op}'
  else jq -cn --arg s "$1" --argjson op "$2" '{protocolVersion: 1, context: {scope: $s}, operation: $op}'; fi
}
# Statement operations from a file: sql_read FILE, sql_write FILE, statement LANGUAGE FILE.
statement() { jq -Rsc --arg l "$1" '{kind: "query", query: {kind: "statement", language: $l, statement: (. | rtrimstr("\n"))}}' "$2"; }
sql_read() { statement sql "$1"; }
sql_write() { jq -Rsc '{kind: "mutate", mutation: {kind: "statement", language: "sql", statement: (. | rtrimstr("\n"))}}' "$1"; }

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
# mint SUBJECT SCOPE TENANT TTL: a capability token bound to one tenant
# (base64url(claims) "." base64url(HMAC-SHA256(secret, base64url(claims)))).
mint() {
  local now payload sig
  now="$(date +%s)"
  payload="$(jq -cn --arg sub "$1" --arg scope "$2" --arg tenant "$3" --argjson iat "$now" --argjson exp "$((now + $4))" \
    '{sub: $sub, scope: $scope, tenant: $tenant, iat: $iat, exp: $exp}' | tr -d '\n' | b64url)"
  sig="$(printf '%s' "$payload" | openssl dgst -sha256 -mac HMAC -macopt "hexkey:$RUSHDB_CAPABILITY_SECRET" -binary | b64url)"
  printf '%s.%s' "$payload" "$sig"
}
