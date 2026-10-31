#!/usr/bin/env python3
"""Counts tokens of every file given, with tiktoken's o200k_base and cl100k_base encodings.
Usage: uv run --with tiktoken==0.14.0 python count_tokens.py <file>..."""
import os
import sys

import tiktoken

encs = {name: tiktoken.get_encoding(name) for name in ("o200k_base", "cl100k_base")}
print(f"{'file':44} {'bytes':>8} {'o200k':>8} {'cl100k':>8}")
for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read()
    counts = [len(e.encode(text)) for e in encs.values()]
    print(f"{os.path.relpath(path):44} {len(text.encode()):>8} {counts[0]:>8} {counts[1]:>8}")
