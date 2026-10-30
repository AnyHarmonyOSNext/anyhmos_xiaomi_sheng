"""Select read-only disassembled Ark functions by their record/name substrings."""
from pathlib import Path
import sys

source, output, *patterns = sys.argv[1:]
count = 0
keep = False
with Path(source).open(encoding="utf-8", errors="replace") as src, Path(output).open("w", encoding="utf-8") as dest:
    for line in src:
        if line.startswith(".function "):
            keep = any(p in line for p in patterns)
            count += keep
        if keep:
            dest.write(line)
        if line == "}\n":
            keep = False
print(f"Selected {count} functions into {output}")
