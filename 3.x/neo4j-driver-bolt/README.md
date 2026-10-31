# Neo4j Python driver over Bolt

Runs the official `neo4j` Python driver against RushDB's Bolt 5.0 listener: connectivity, auto-commit
writes with parameters, a managed write transaction, a relationship created inside a transaction (refused
on the tested build), typed reads, a managed read, `RETURN n` as a map, rollback, a syntax error, and
`execute_query`.

Article: [Neo4j driver and Bolt compatibility: a RushDB how-to](https://rushdb.com/blog/neo4j-driver-bolt-compatibility)

## Prerequisites

- A RushDB 3.x engine with Cypher and a Bolt port. Cypher is a release candidate and opt-in:

  ```bash
  rushdb serve --token local-token --languages sql,cypher,gremlin,sql-pgq,mongodb --bolt-port 7687
  ```

- Python 3 (tested with 3.15) and `pip install -r requirements.txt` (pins `neo4j==6.4.1`)

## Run

```bash
export RUSHDB_BOLT_URI=bolt://127.0.0.1:7687 RUSHDB_TOKEN=local-token
./run.sh
```

The script deletes every `Team` and `Engineer` record first, so it can be re-run.

## Files

- `bolt_demo.py`: the numbered steps
- `requirements.txt`
- `expected-output.txt`: output of a real run (Python 3.15, neo4j 6.4.1) against the engine build of 2026-10-27
