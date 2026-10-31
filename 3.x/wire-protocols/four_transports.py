"""One question over four wire protocols on one RushDB 3.x engine.

Seeds 7 example suppliers over HTTP, then asks "how many suppliers are in flood-zone-07?" over
HTTP (native envelope), gRPC (the same envelope as protobuf bytes), the PostgreSQL wire (SQL) and
Bolt (Cypher, official Neo4j driver). With --bench it also times 3,000 round trips per transport.

Engine: rushdb serve --grpc-port 50051 --bolt-port 7687 --languages sql,cypher
"""
import json, os, sys, time, http.client
import grpc, psycopg
from neo4j import GraphDatabase

HOST = os.environ.get("RUSHDB_HOST", "127.0.0.1")
TOKEN = os.environ.get("RUSHDB_TOKEN", "local-token")
HTTP_PORT, PG_PORT = int(os.environ.get("HTTP_PORT", 3000)), int(os.environ.get("PG_PORT", 5432))
GRPC_PORT, BOLT_PORT = int(os.environ.get("GRPC_PORT", 50051)), int(os.environ.get("BOLT_PORT", 7687))
SQL = "SELECT count(*) AS n FROM supplier WHERE region = 'flood-zone-07'"
CYPHER = "MATCH (s:SUPPLIER) WHERE s.region = 'flood-zone-07' RETURN count(s) AS n"

def envelope(operation):
    return {"protocolVersion": 1, "operation": operation}

def statement(text, language):
    return envelope({"kind": "query", "query": {"kind": "statement", "language": language, "statement": text}})

http_conn = http.client.HTTPConnection(HOST, HTTP_PORT)
HEADERS = {"X-RushDB-Token": TOKEN, "Content-Type": "application/json"}

def http_execute(env):
    http_conn.request("POST", "/protocol/v1/execute", json.dumps(env), HEADERS)
    return json.loads(http_conn.getresponse().read())

# gRPC: rushdb.v1.Database/Execute takes a message with one field: bytes json = 1.
def encode(payload: bytes) -> bytes:
    out, n = bytearray([0x0A]), len(payload)  # field 1, wire type 2 (length-delimited)
    while True:
        byte, n = n & 0x7F, n >> 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out) + payload

def decode(message: bytes) -> bytes:
    i, shift, n = 1, 0, 0
    while True:
        byte = message[i]; i += 1
        n |= (byte & 0x7F) << shift; shift += 7
        if not byte & 0x80:
            return message[i:i + n]

channel = grpc.insecure_channel(f"{HOST}:{GRPC_PORT}")
grpc_execute = channel.unary_unary("/rushdb.v1.Database/Execute", request_serializer=encode, response_deserializer=decode)
GRPC_META = [("authorization", f"Bearer {TOKEN}")]

def grpc_call(env):
    return json.loads(grpc_execute(json.dumps(env).encode(), metadata=GRPC_META))

print("== Seed (HTTP): reset SUPPLIER, ingest 7 suppliers as nested JSON")
http_execute(envelope({"kind": "mutate", "mutation": {"kind": "deleteRecords", "query": {"labels": ["SUPPLIER"]}}}))
docs = json.load(open(os.path.join(os.path.dirname(__file__), "data", "suppliers.json")))
seeded = http_execute(envelope({"kind": "ingest", "ingest": {"kind": "documents", "label": "SUPPLIER", "documents": docs,
                                                            "options": {"relationshipTypes": {"SUPPLIER": "BUYS_FROM"}}}}))
print({k: seeded["response"][k] for k in ("kind", "count", "relationships")})

print("== One question, four transports")
print("HTTP   sql   ", http_execute(statement(SQL, "sql"))["response"]["rows"])
print("gRPC   sql   ", grpc_call(statement(SQL, "sql"))["response"]["rows"])
pg = psycopg.connect(host=HOST, port=PG_PORT, user="rushdb", dbname="rushdb", password=TOKEN, autocommit=True)
print("pgwire sql   ", pg.execute(SQL).fetchall())
driver = GraphDatabase.driver(f"bolt://{HOST}:{BOLT_PORT}", auth=("rushdb", TOKEN))
session = driver.session()
print("Bolt   cypher", session.run(CYPHER).data())
print("HTTP   cypher", http_execute(statement(CYPHER, "cypher"))["response"]["rows"])

if "--bench" in sys.argv:
    N, WARM = 3000, 300
    print(f"== Round trips: {N} sequential calls each after {WARM} warm-up, one connection, loopback")
    def bench(name, fn):
        for _ in range(WARM):
            fn()
        xs = []
        for _ in range(N):
            t = time.perf_counter(); fn(); xs.append((time.perf_counter() - t) * 1e6)
        xs.sort()
        print(f"{name:14s} p50 {xs[N // 2]:6.0f} us   p99 {xs[int(N * 0.99)]:6.0f} us")
    for lang, text in (("sql", SQL), ("cypher", CYPHER)):
        env = statement(text, lang)
        bench(f"HTTP   {lang}", lambda: http_execute(env))
        bench(f"gRPC   {lang}", lambda: grpc_call(env))
    bench("pgwire sql", lambda: pg.execute(SQL).fetchall())
    bench("Bolt   cypher", lambda: session.run(CYPHER).data())

session.close(); driver.close(); pg.close()
