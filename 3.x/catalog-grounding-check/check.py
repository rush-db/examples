"""Check an agent's SQL against the RushDB catalog before running it.

For every table, column and string literal compared with =, != or IN, look up
what is actually stored. On a miss, reject the query and return what is stored
instead; otherwise run it. Client-side version of the check described in
https://rushdb.com/blog/grounding-analytics-agents (RushDB is building a
server-side check; this is not it).

Usage: python3 check.py queries/*.sql
"""
import difflib
import json
import os
import sys
import urllib.request

import sqlglot
from sqlglot import exp

URL = os.environ.get("RUSHDB_URL", "http://127.0.0.1:3000").rstrip("/") + "/protocol/v1/execute"
TOKEN = os.environ.get("RUSHDB_TOKEN", "local-token")
SMALL_DOMAIN = 20  # list every stored value when a column has at most this many


def rushdb(operation: dict) -> dict:
    body = json.dumps({"protocolVersion": 1, "operation": operation}).encode()
    req = urllib.request.Request(URL, body, {"X-RushDB-Token": TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        out = json.load(resp)
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["response"]


def property_values(label: str, prop: str, **extra) -> dict:
    query = {"kind": "propertyValues", "property": prop, "query": {"labels": [label]}, **extra}
    return rushdb({"kind": "query", "query": query})


class Catalog:
    """Labels, properties and stored values, read from RushDB and cached per run."""

    def __init__(self):
        labels = rushdb({"kind": "describe", "describe": {"kind": "labels", "query": {}}})["labels"]
        self.labels = {name.lower(): name for name in labels}  # SQL table names are case-insensitive
        self._props, self._values = {}, {}

    def props(self, label: str) -> list[str]:
        if label not in self._props:
            r = rushdb({"kind": "describe", "describe": {"kind": "properties", "query": {"labels": [label]}, "detail": "catalog"}})
            self._props[label] = sorted({p["name"] for p in r["properties"]})
        return self._props[label]

    def values(self, label: str, prop: str) -> tuple[set, int, bool]:
        if (label, prop) not in self._values:
            r = property_values(label, prop, mode="values", limit=1000)
            self._values[label, prop] = (set(map(str, r["values"])), r["distinctCount"], r.get("truncated", False))
        return self._values[label, prop]


def alternatives(cat: Catalog, label: str, prop: str, literal: str) -> str:
    """What is stored instead: near matches in the column, other columns holding the literal, or the domain."""
    near = []
    for match in ("contains", "similar"):  # contains also matches dates written in another layout
        r = property_values(label, prop, mode="topK", limit=5, search={"text": literal, "match": match})
        near += [v for v in r.get("values", []) if v not in near]
    if near:
        return f"close stored values: {near}"
    hits = rushdb({"kind": "query", "query": {"kind": "searchValues", "search": {"text": literal, "match": "exact"}, "limit": 5}})
    elsewhere = [f"{m['label']}.{m['property']}" for m in hits["matches"]]
    stored, count, truncated = cat.values(label, prop)
    domain = f"stored: {sorted(stored)}" if count <= SMALL_DOMAIN and not truncated else f"{count} distinct values stored"
    return (f"'{literal}' is stored in {elsewhere}; " if elsewhere else "") + domain


def check(sql: str, cat: Catalog) -> list[str]:
    problems = []
    tree = sqlglot.parse_one(sql, read="postgres")
    aliases = {}
    for t in tree.find_all(exp.Table):
        label = cat.labels.get(t.name.lower())
        if label is None:
            hint = difflib.get_close_matches(t.name.lower(), cat.labels, n=1)
            problems.append(f"no table '{t.name}'" + (f"; did you mean '{cat.labels[hint[0]]}'?" if hint else ""))
        aliases[t.alias_or_name] = label
    tables = [label for label in aliases.values() if label]

    def resolve(col: exp.Column):
        """The label a column belongs to, or None (and a problem) if no table has it."""
        candidates = [aliases.get(col.table)] if col.table else tables
        for label in candidates:
            if label and col.name in cat.props(label):
                return label
        if candidates and all(candidates):
            known = sorted({p for label in candidates for p in cat.props(label)})
            hint = difflib.get_close_matches(col.name, known, n=1)
            where = candidates[0] if len(candidates) == 1 else "any table"
            problems.append(f"{where} has no column '{col.name}'" + (f"; did you mean '{hint[0]}'?" if hint else ""))
        return None

    owners = {id(col): resolve(col) for col in tree.find_all(exp.Column)}
    for cmp in tree.find_all(exp.EQ, exp.NEQ, exp.In):
        col = cmp.this if isinstance(cmp.this, exp.Column) else None
        label = owners.get(id(col)) if col is not None else None
        if label is None:
            continue
        literals = cmp.expressions if isinstance(cmp, exp.In) else [cmp.expression]
        for lit in literals:
            if isinstance(lit, exp.Literal) and lit.is_string:
                stored, _, truncated = cat.values(label, col.name)
                if lit.this in stored:
                    continue
                if truncated:  # too many values to list: ask for this one exactly
                    r = property_values(label, col.name, mode="count", search={"text": lit.this, "match": "exact", "caseSensitive": True})
                    if r["distinctCount"]:
                        continue
                problems.append(f"{label}.{col.name} stores no '{lit.this}'; {alternatives(cat, label, col.name, lit.this)}")
    return problems


def main(paths: list[str]) -> None:
    cat = Catalog()
    for path in paths:
        sql = open(path).read().strip()
        print(f"== {os.path.basename(path)}")
        print("   " + " ".join(sql.split()))
        problems = check(sql, cat)
        if problems:
            print("   REJECTED, not run:")
            for p in problems:
                print(f"   - {p}")
            continue
        rows = rushdb({"kind": "query", "query": {"kind": "statement", "language": "sql", "statement": sql}})["rows"]
        print(f"   PASSED, ran: {json.dumps(rows)}")


if __name__ == "__main__":
    main(sys.argv[1:])
