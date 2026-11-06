#!/usr/bin/env bash
# Run the official Neo4j Python driver against RushDB 3.x over Bolt 5.0.
# Start the engine with Cypher and a Bolt port first:
#   rushdb serve --languages sql,cypher,gremlin,sql-pgq,mongodb --bolt-port 7687
set -euo pipefail
cd "$(dirname "$0")"
export RUSHDB_BOLT_URI="${RUSHDB_BOLT_URI:-bolt://127.0.0.1:7687}"
export RUSHDB_TOKEN="${RUSHDB_TOKEN:-local-token}"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import neo4j' 2>/dev/null || { echo "run: pip install -r requirements.txt" >&2; exit 1; }
"$PYTHON" bolt_demo.py
