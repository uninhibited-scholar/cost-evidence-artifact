#!/usr/bin/env python3
"""Text health check for a markdown file, against the packaged card library.

    python3 code/checks/audit_draft.py [file.md]     # default: README.md

Machine-checkable hygiene for any prose file in this artifact:
  1. every arXiv-style id it cites (dddd.ddddd or a 12-hex card id in backticks)
     exists as a card in data/cards/
  2. advisory: percentages that appear without any denominator cue in the
     surrounding window (advisory only, never pass/fail)
  3. leftover TODO / TBD markers
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "data" / "cards"
ID_RE = re.compile(r"(?<![\d.])(\d{4}\.\d{4,5})(?![\d.])")
HEX_RE = re.compile(r"`([0-9a-f]{12})`")
PCT_RE = re.compile(r"\d+(?:\.\d+)?\s*%")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    path = ROOT / target
    if not path.is_file():
        print(f"target not found: {path}")
        return 2
    text = path.read_text(encoding="utf-8")
    card_ids = {p.stem for p in CARDS.glob("*.json")}

    cited = set(ID_RE.findall(text)) | set(HEX_RE.findall(text))
    bad = sorted(i for i in cited if i not in card_ids)
    print(f"== {target} ==")
    print(f"cited ids: {len(cited)}; not in the card library: {len(bad)}"
          + (f" -> {', '.join(bad)}" if bad else ""))

    badpct = []
    for m in PCT_RE.finditer(text):
        lo, hi = max(0, m.start() - 120), min(len(text), m.end() + 120)
        win = text[lo:hi]
        if re.search(r"/\s*\d+|\bdenominator\b|\bn\s*=|\bof\s+\d+", win, re.I):
            continue
        if re.search(r"\d+\s*(?:trials?|runs?|samples?|queries|tasks?|seeds?|episodes?|cards?|papers?|readings?)", win, re.I):
            continue
        if re.search(r"95%\s*CI|CI\s*\[", win):
            continue
        line = text.count("\n", 0, m.start()) + 1
        badpct.append((line, m.group(0)))
    print(f"percentages: {len(PCT_RE.findall(text))}; advisory no-denominator-in-window: {len(badpct)}")
    for line, v in badpct[:8]:
        print(f"   line {line}: {v}")

    todos = re.findall(r"\bTODO\b|\bTBD\b", text)
    print(f"TODO/TBD markers: {len(todos)}")

    ok = not bad
    print("RESULT: " + ("OK" if ok else "FAIL (cited ids outside the card library)"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
