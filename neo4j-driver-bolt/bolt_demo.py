"""Point the official Neo4j Python driver at RushDB over Bolt 5.0.

Each numbered step prints what the driver returned. Example data only.
"""
import os

from neo4j import GraphDatabase
from neo4j.exceptions import ClientError

URI = os.environ.get("RUSHDB_BOLT_URI", "bolt://127.0.0.1:7687")
TOKEN = os.environ.get("RUSHDB_TOKEN", "local-token")


def step(title):
    print(f"\n== {title}")


driver = GraphDatabase.driver(URI, auth=("rushdb", TOKEN))

step("1. Connectivity and server agent")
driver.verify_connectivity()
info = driver.get_server_info()
print(f"agent={info.agent} protocol={info.protocol_version}")

with driver.session() as session:
    step("2. Reset: delete records left by an earlier run")
    summary = session.run("MATCH (n:Team) DETACH DELETE n").consume()
    summary = session.run("MATCH (n:Engineer) DETACH DELETE n").consume()
    print("done")

    step("3. Auto-commit writes with parameters (relationships included)")
    for team, name, level, remote, rating, since in [
        ("Storage", "Ines", 3, True, 4.5, 2021),
        ("Storage", "Kofi", 2, False, 3.9, 2023),
        ("Storage", "Mei", 4, True, 4.8, 2024),
    ]:
        summary = session.run(
            "MERGE (t:Team {name: $team}) "
            "CREATE (t)-[:EMPLOYS {since: $since}]->(:Engineer {name: $name, level: $level, remote: $remote, rating: $rating})",
            team=team, name=name, level=level, remote=remote, rating=rating, since=since,
        ).consume()
    print(session.run("MATCH (:Team)-[r:EMPLOYS]->(:Engineer) RETURN count(r) AS n").single()["n"], "EMPLOYS relationships")
    # The result summary does not carry update counters on this build.
    print(f"summary of the last write: query_type={summary.query_type!r} "
          f"nodes_created={summary.counters.nodes_created} contains_updates={summary.counters.contains_updates}")

    step("4. Managed write transaction: property updates commit together")
    def promote(tx):
        tx.run("MATCH (e:Engineer {name: 'Kofi'}) SET e.level = 3").consume()
        tx.run("MATCH (e:Engineer {name: 'Mei'}) SET e.lead = true").consume()
    session.execute_write(promote)
    print("committed")

    step("4b. Creating a relationship inside a managed write transaction")
    try:
        session.execute_write(lambda tx: tx.run(
            "MATCH (t:Team {name: 'Storage'}) CREATE (t)-[:EMPLOYS {since: 2026}]->(:Engineer {name: 'Lena'})"
        ).consume())
    except Exception as error:
        print(f"{type(error).__name__}: {error.code}")
    print("Lena records:", session.run("MATCH (e:Engineer {name: 'Lena'}) RETURN count(e) AS n").single()["n"])

    step("5. Read typed columns (booleans and floats come back as Python bool and float)")
    for record in session.run(
        "MATCH (t:Team)-[r:EMPLOYS]->(e:Engineer) "
        "RETURN e.name AS name, e.level AS level, e.remote AS remote, e.rating AS rating, r.since AS since "
        "ORDER BY since"
    ):
        print(f"{record['name']:<5} level={record['level']} remote={record['remote']!r:<5} "
              f"rating={record['rating']!r} since={record['since']}  types=({type(record['remote']).__name__}, {type(record['rating']).__name__})")

    step("6. Managed read transaction with an aggregate")
    count = session.execute_read(
        lambda tx: tx.run("MATCH (e:Engineer) WHERE e.remote = true RETURN count(e) AS n").single()["n"]
    )
    print(f"remote engineers: {count}")

    step("7. RETURN n gives a map, not a driver Node")
    node = session.run("MATCH (e:Engineer {name: 'Ines'}) RETURN e").single()["e"]
    print(f"python type: {type(node).__name__}; keys: {sorted(node.keys())}")

    step("8. Explicit transaction rolled back: nothing is published")
    tx = session.begin_transaction()
    tx.run("CREATE (:Engineer {name: 'Temp', level: 1})").consume()
    tx.rollback()
    left = session.run("MATCH (e:Engineer {name: 'Temp'}) RETURN count(e) AS n").single()["n"]
    print(f"Temp engineers after rollback: {left}")

    step("9. A syntax error comes back as a Neo4j client error, and the session keeps working")
    try:
        session.run("MATCH (e:Engineer RETURN e").consume()
    except ClientError as error:
        print(f"code={error.code}")
    print("after error:", session.run("MATCH (e:Engineer) RETURN count(e) AS n").single()["n"])

step("10. execute_query (driver-level API)")
records, summary, keys = driver.execute_query(
    "MATCH (e:Engineer) WHERE e.level >= $min RETURN e.name AS name ORDER BY name", min=3
)
print(keys, [r["name"] for r in records])

driver.close()
