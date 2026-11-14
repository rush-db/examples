"""psycopg 3 against RushDB's pgwire: reads work in its default transaction; writes need autocommit."""
import os, psycopg
kw = dict(host="127.0.0.1", port=int(os.environ.get("PGPORT", 5432)), user="rushdb", dbname="rushdb",
          password=os.environ.get("RUSHDB_TOKEN", "local-token"))
try:
    with psycopg.connect(**kw) as conn:  # default: autocommit off, so psycopg sends BEGIN first
        rows = conn.execute("SELECT code FROM supplier ORDER BY code LIMIT 1").fetchall()
        print("autocommit off: read in a BEGIN block:", rows)
except psycopg.Error as e:
    print("autocommit off:", e.sqlstate, str(e).strip())
with psycopg.connect(**kw, autocommit=True) as conn:
    print("select:", conn.execute("SELECT code, tier FROM supplier WHERE tier >= %s ORDER BY code", (3,)).fetchall())
    cur = conn.execute("INSERT INTO supplier (code, name, tier) VALUES (%s, %s, %s)", ("S-402", "Fen Alloys (example)", 4))
    print("insert rowcount:", cur.rowcount, "status:", cur.statusmessage)
    print("delete rowcount:", conn.execute("DELETE FROM supplier WHERE code = %s", ("S-402",)).rowcount)
    value = conn.execute('SELECT "onboardedAt" FROM supplier WHERE code = %s', ("S-101",)).fetchone()[0]
    print("datetime column:", type(value).__name__, value)
