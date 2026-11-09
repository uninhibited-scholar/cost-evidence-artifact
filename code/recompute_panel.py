#!/usr/bin/env python3
"""Recompute the three-reader panel comparison behind Section 2.3.

The panel re-coded all 129 cards from windowed text alone; the ledger is the
codebook applied by the authors. This script checks the agreement statistics the
paper prints, under two ledgers:

  - as it stands: cards with at least one numeric C1-C3 reading (62);
  - harmonized: the same set without cards whose every numeric C1-C3 reading is
    a negative cost, that is, a saving counted as a price (59).

The ledger is scored against the panel majority as the reference, so precision
is taken over the ledger's priced cards and recall over the panel's.

Run from the artifact root:  python3 code/recompute_panel.py [--write]
Standard library only. Exits non-zero on mismatch.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data" / "reader-panel"
CLASSES = ("c1", "c2", "c3")
READERS = ("r2", "r3", "r4")
SHARDS = range(1, 6)
LEDGER_CLASSES = ("utility_loss", "latency_compute", "false_positive")

cards = json.loads((ROOT / "data" / "cost_tags.json").read_text(encoding="utf-8"))["cards"]

votes = {key: [] for key in cards}
for reader in READERS:
    for shard in SHARDS:
        path = PANEL / f"codes-{reader}-{shard}.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = row["key"]
                if key not in votes:
                    raise SystemExit(f"unknown card key in {path.name}: {key}")
                votes[key].append(any(row[c] == "numeric" for c in CLASSES))

if not all(len(items) == 3 for items in votes.values()):
    raise SystemExit("a card does not carry exactly three reader votes")
majority = {key: sum(items) >= 2 for key, items in votes.items()}


def numeric(key, cls):
    data = cards[key]["classes"][cls]
    return bool(data["has"]) and not data.get("qualitative")


ledger = {key for key in cards if any(numeric(key, c) for c in LEDGER_CLASSES)}
all_numeric_negative = {
    key for key in ledger
    if all("负成本" in (cards[key]["classes"][c].get("reason") or "")
           for c in LEDGER_CLASSES if numeric(key, c))
}
harmonized = ledger - all_numeric_negative


def score(priced):
    both = sum(1 for key in cards if majority[key] and key in priced)
    ledger_only = sum(1 for key in cards if key in priced and not majority[key])
    panel_only = sum(1 for key in cards if majority[key] and key not in priced)
    neither = len(cards) - both - ledger_only - panel_only
    return {
        "ledger_priced": len(priced),
        "panel_priced": sum(majority.values()),
        "both": both,
        "ledger_only": ledger_only,
        "panel_only": panel_only,
        "neither": neither,
        "agreement": both + neither,
        "flips": ledger_only + panel_only,
        "precision": both / len(priced),
        "recall": both / sum(majority.values()),
    }


as_is = score(ledger)
harm = score(harmonized)

EXPECTED = {
    "as_is": {"ledger_priced": 62, "panel_priced": 63, "both": 47, "ledger_only": 15,
              "panel_only": 16, "neither": 51, "agreement": 98, "flips": 31,
              "precision": 0.758, "recall": 0.746},
    "harmonized": {"ledger_priced": 59, "panel_priced": 63, "both": 44, "ledger_only": 15,
                   "panel_only": 19, "neither": 51, "agreement": 95, "flips": 34,
                   "precision": 0.746, "recall": 0.698},
}

failed = False
for name, got in (("as_is", as_is), ("harmonized", harm)):
    for field, want in EXPECTED[name].items():
        have = got[field]
        ok = abs(have - want) < 5e-4 if isinstance(want, float) else have == want
        if not ok:
            print(f"MISMATCH {name}.{field}: got {have}, expected {want}")
            failed = True

print(f"cards {len(cards)}  excluded as negative cost {sorted(all_numeric_negative)}")
header = f"{'panel':<12}{'ledger':>7}{'panel':>7}{'both':>6}{'L only':>8}{'P only':>8}{'neither':>9}{'agree':>7}{'flips':>7}{'prec':>7}{'rec':>7}"
print(header)
for name, got in (("as it stands", as_is), ("harmonized", harm)):
    print(f"{name:<12}{got['ledger_priced']:>7}{got['panel_priced']:>7}{got['both']:>6}"
          f"{got['ledger_only']:>8}{got['panel_only']:>8}{got['neither']:>9}"
          f"{got['agreement']:>7}{got['flips']:>7}{got['precision']:>7.3f}{got['recall']:>7.3f}")

if "--write" in sys.argv:
    out = PANEL / "panel-harmonized.json"
    out.write_text(json.dumps({
        "rule": {
            "panel": "a card is priced when at least two of three readers mark any of c1-c3 numeric",
            "ledger": "any of utility_loss/latency_compute/false_positive has=true and qualitative=false",
            "harmonized": "drop cards whose every numeric c1-c3 reading is a negative cost",
        },
        "excluded": sorted(all_numeric_negative),
        "as_is": as_is,
        "harmonized": harm,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")

print("RESULT:", "MISMATCH" if failed else "all panel statistics match")
sys.exit(1 if failed else 0)
