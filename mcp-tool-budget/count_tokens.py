"""Token sizes of what an MCP client hands the model: server instructions, tool definitions, tool results.
Counts with tiktoken's o200k_base encoding: an approximation, since every model family tokenizes
differently. Reads probe output (JSON lines) on stdin."""
import json, sys
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
tokens = lambda s: len(enc.encode(s))
rows = [json.loads(line) for line in sys.stdin if line.strip()]
init = rows[0]["result"]
print(f"server instructions (initialize): {tokens(init.get('instructions', ''))} tokens")
listed = rows[1]["result"]["tools"]
level = lambda t: "Destructive" if t["annotations"]["destructiveHint"] else "Read" if t["annotations"]["readOnlyHint"] else "Write"
counts = {}
for t in listed:
    counts[level(t)] = counts.get(level(t), 0) + 1
print(f"tools/list: {len(listed)} tools {counts}, {tokens(json.dumps(listed))} tokens "
      f"(descriptions alone {sum(tokens(t['description']) for t in listed)})")
sizes = sorted(((tokens(json.dumps(t)), t["name"]) for t in listed), reverse=True)
print("  largest definitions:", ", ".join(f"{n} {k}" for k, n in sizes[:5]))
print("  smallest definitions:", ", ".join(f"{n} {k}" for k, n in sizes[-3:]))
print("tool results (text content the model reads):")
for r in rows[2:]:
    res = r["result"]
    text = "".join(c.get("text", "") for c in res.get("content", []))
    args = json.dumps(r.get("arguments") or {}, separators=(",", ":"))
    sc = res.get("structuredContent")
    items = sc.get("data", sc.get("properties")) if isinstance(sc, dict) else sc
    n = f", {len(items)} items" if isinstance(items, list) else ""
    print(f"  {r['tool']} {args}: {tokens(text)} tokens{n}")
