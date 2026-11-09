#!/usr/bin/env python3
"""Figure 2: the coverage matrix, five defense layers x six state operations.

    python3 code/fig2_matrix.py

Recomputes the matrix from data/cards/*.json at runtime (card
intervention.mechanism_layer x object.operations_covered), prints every cell,
and renders a heatmap to figures/out/fig2_matrix.pdf/.png. The unique zero cell
(repair x formal guarantees) and the two single-evidence cells are marked.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data" / "cards"
OUTD = ROOT / "figures" / "out"
LAYERS5 = ["content", "provenance", "execution", "architecture", "formal"]
OPS = ["formation", "update", "retention", "retrieval", "revocation", "repair"]

M = {op: {l: 0 for l in LAYERS5} for op in OPS}
n5 = 0
for p in sorted(CARDS.glob("*.json")):
    c = json.loads(p.read_text(encoding="utf-8"))
    ml = (c.get("intervention") or {}).get("mechanism_layer")
    if ml in LAYERS5:
        n5 += 1
        for op in (c.get("object") or {}).get("operations_covered") or []:
            if op in M:
                M[op][ml] += 1

rows = {op: sum(M[op].values()) for op in OPS}
cols = {l: sum(M[op][l] for op in OPS) for l in LAYERS5}
grand = sum(rows.values())
print(f"[fig2] cards contributing to the matrix: {n5}")
print("[fig2] matrix (rows = operations, columns = layers):")
print("         " + "".join(f"{l:>14s}" for l in LAYERS5) + "   row total")
for op in OPS:
    print(f"    {op:11s}" + "".join(f"{M[op][l]:14d}" for l in LAYERS5) + f"   {rows[op]}")
print("    " + "column total ".rjust(11) + "".join(f"{cols[l]:14d}" for l in LAYERS5) + f"   {grand}")
zero = [(op, l) for op in OPS for l in LAYERS5 if M[op][l] == 0]
single = [(op, l) for op in OPS for l in LAYERS5 if M[op][l] == 1]
print(f"[fig2] zero cells: {zero}")
print(f"[fig2] single-evidence cells: {single}")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
except Exception as e:
    print(f"[fig2] matplotlib unavailable ({e}); console matrix above is the artifact of record.")
    raise SystemExit(0)

OUTD.mkdir(parents=True, exist_ok=True)
import numpy as np
A = np.array([[M[op][l] for l in LAYERS5] for op in OPS], dtype=float)
fig, ax = plt.subplots(figsize=(7.6, 4.6))
im = ax.imshow(A, cmap="Blues", vmin=0, vmax=A.max(), aspect="auto")
ax.set_xticks(range(len(LAYERS5)), LAYERS5, fontsize=9, rotation=20, ha="right")
ax.set_yticks(range(len(OPS)), OPS, fontsize=9)
ax.set_title(f"Figure 2: coverage matrix, five layers x six operations ({grand} occupied cells)")
for i, op in enumerate(OPS):
    for j, l in enumerate(LAYERS5):
        v = int(A[i, j])
        if v == 0:
            ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="crimson", lw=2.0))
            ax.text(j, i, "0", ha="center", va="center", fontsize=10, color="crimson",
                    bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
        else:
            ax.text(j, i, str(v), ha="center", va="center", fontsize=10,
                    color="white" if v > A.max() * 0.55 else "#1a365d")
fig.tight_layout()
for ext in ("pdf", "png"):
    out = OUTD / f"fig2_matrix.{ext}"
    fig.savefig(out)
    print(f"[fig2] written: {out.relative_to(ROOT)}")
