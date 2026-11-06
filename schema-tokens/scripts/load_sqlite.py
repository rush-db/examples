#!/usr/bin/env python3
"""Loads every table of a SQLite database into a RushDB 3.x node: one label per table
(the table name), one record per row, one property per non-NULL column. Also writes the
database's DDL (CREATE TABLE statements from sqlite_master) and the same DDL followed by
3 sample rows per table, the two prompt formats text-to-SQL baselines commonly use.
Standard library only.
With a third argument (BIRD's database_description folder) it also writes the DDL followed
by BIRD's column description CSVs.
Usage: python3 load_sqlite.py <db.sqlite> <out-dir> [description-dir]   (RUSHDB_URL, RUSHDB_TOKEN from env)"""
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request

URL = os.environ.get("RUSHDB_URL", "http://127.0.0.1:3000") + "/protocol/v1/execute"
TOKEN = os.environ.get("RUSHDB_TOKEN", "local-token")


def rdb(operation):
    body = json.dumps({"protocolVersion": 1, "operation": operation}).encode()
    req = urllib.request.Request(URL, body, {"X-RushDB-Token": TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as err:
        out = json.load(err)
    if "response" not in out:
        sys.exit(f"request failed: {json.dumps(out)[:400]}")
    return out["response"]


db_path, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
con = sqlite3.connect(db_path)
tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

ddl = [con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (t,)).fetchone()[0].strip() + ";" for t in tables]
with open(os.path.join(out_dir, "ddl.sql"), "w") as f:
    f.write("\n\n".join(ddl) + "\n")

with open(os.path.join(out_dir, "ddl-with-3-rows.sql"), "w") as f:
    for t, stmt in zip(tables, ddl):
        cur = con.execute(f'SELECT * FROM "{t}" LIMIT 3')
        cols = [d[0] for d in cur.description]
        f.write(stmt + "\n/*\n3 rows from " + t + " table:\n" + "\t".join(cols) + "\n")
        for row in cur.fetchall():
            f.write("\t".join("" if v is None else str(v) for v in row) + "\n")
        f.write("*/\n\n")

if len(sys.argv) > 3:
    with open(os.path.join(out_dir, "ddl-with-descriptions.txt"), "w") as f:
        f.write("\n\n".join(ddl) + "\n")
        for t in tables:
            names = {n.lower(): n for n in os.listdir(sys.argv[3])}
            path = os.path.join(sys.argv[3], names.get(t.lower() + ".csv", t + ".csv"))
            if os.path.exists(path):
                raw = open(path, "rb").read()
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1")
                f.write(f"\n-- column descriptions for {t}\n" + text.strip() + "\n")

rdb({"kind": "mutate", "mutation": {"kind": "deleteRecords", "query": {"labels": tables}}})
for t in tables:
    cur = con.execute(f'SELECT * FROM "{t}"')
    cols = [d[0] for d in cur.description]
    total = 0
    while True:
        rows = cur.fetchmany(1000)
        if not rows:
            break
        docs = [{c: v for c, v in zip(cols, row) if v is not None} for row in rows]
        rdb({"kind": "ingest", "ingest": {"kind": "documents", "label": t, "documents": docs}})
        total += len(docs)
    print(f"  {t}: {total} records")
