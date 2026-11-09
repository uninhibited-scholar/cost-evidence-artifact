#!/usr/bin/env python3
"""Figure 1: lifecycle of persistent state and the six matrix row operations.

    python3 code/fig1_lifecycle.py

Recomputes the six operation-row cell counts from data/cards/*.json at runtime,
prints them, and draws a bar chart to figures/out/fig1_lifecycle.pdf/.png.
Row-to-operation mapping: formation=O1 write, update=O3 merge, retention is the
temporal consequence of O2/O4/O6, retrieval=O2 read, revocation=O6, repair is
the O3+O6 compound.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data" / "cards"
OUTD = ROOT / "figures" / "out"
LAYERS5 = ["content", "provenance", "execution", "architecture", "formal"]
OPS = ["formation", "update", "retention", "retrieval", "revocation", "repair"]

tot = {op: 0 for op in OPS}
n5 = 0
for p in sorted(CARDS.glob("*.json")):
    c = json.loads(p.read_text(encoding="utf-8"))
    ml = (c.get("intervention") or {}).get("mechanism_layer")
    if ml in LAYERS5:
        n5 += 1
        for op in (c.get("object") or {}).get("operations_covered") or []:
            if op in tot:
                tot[op] += 1
grand = sum(tot.values())
print(f"[fig1] cards contributing to the matrix: {n5}")
print(f"[fig1] row cell counts: " + ", ".join(f"{op}={tot[op]}" for op in OPS) + f" | total {grand}")
print(f"[fig1] unique zero cell: repair x formal guarantees (see code/fig2_matrix.py)")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception as e:
    print(f"[fig1] matplotlib unavailable ({e}); console counts above are the artifact of record.")
    raise SystemExit(0)

OUTD.mkdir(parents=True, exist_ok=True)
labels = [f"{op}" for op in OPS][::-1]
vals = [tot[op] for op in OPS][::-1]
fig, ax = plt.subplots(figsize=(7.0, 3.4))
ax.barh(labels, vals, color="#4a7ebb", edgecolor="0.25")
for y, v in enumerate(vals):
    ax.text(v + 0.4, y, str(v), va="center", fontsize=10)
ax.set_xlabel("matrix cells (operations x five defense layers)")
ax.set_title(f"Figure 1: operation-row totals over the six lifecycle rows (total {grand})")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
for ext in ("pdf", "png"):
    out = OUTD / f"fig1_lifecycle.{ext}"
    fig.savefig(out)
    print(f"[fig1] written: {out.relative_to(ROOT)}")
