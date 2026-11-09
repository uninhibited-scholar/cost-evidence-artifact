#!/usr/bin/env python3
"""Figure 4: the denominator-coverage picture (the computable part of the audit).

    python3 code/fig4_audit.py

Recomputes from data/cards/*.json: the number of results, how many carry an
explicit denominator (n_total or n_valid stated, or a non-empty scalar
denominator), and how many cards are flagged denominator_unclear. These are the
paper's 1,077 / 675 (62.7%) / 48-of-129 figures.

The original audit had five steps; steps 1, 2 and 5 parsed two working documents
(a manual-audit record and a denominator to-do list) that are NOT shipped in
this artifact, because they are internal working documents rather than data.
Only the computed coverage (steps 0/4) is reproduced here; the shipped numbers
that came out of those steps are quoted in the paper with their own caveats.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data" / "cards"
OUTD = ROOT / "figures" / "out"


def explicit(r):
    d = r.get("denominator")
    if isinstance(d, dict):
        return d.get("n_total") is not None or d.get("n_valid") is not None
    return d is not None and str(d).strip() != ""


cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CARDS.glob("*.json"))]
results = [r for c in cards for r in (c.get("results") or []) if isinstance(r, dict)]
n_explicit = sum(1 for r in results if explicit(r))
n_unclear = sum(1 for c in cards if "denominator_unclear" in (c.get("quality_flags") or []))
n_results = len(results)
print(f"[fig4] results: {n_results}")
print(f"[fig4] explicit denominators: {n_explicit} ({100.0*n_explicit/n_results:.1f}%)")
print(f"[fig4] cards flagged denominator_unclear: {n_unclear}/{len(cards)}")
print("[fig4] notice: audit steps 1/2/5 parsed internal working documents that are "
      "not shipped; only the computed coverage (steps 0/4) is reproduced.")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception as e:
    print(f"[fig4] matplotlib unavailable ({e}); console counts above are the artifact of record.")
    raise SystemExit(0)

OUTD.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(6.6, 2.9))
ax.barh(["explicit denominator", "no explicit denominator"],
        [n_explicit, n_results - n_explicit], color=["#4d9959", "#b0b0b0"], edgecolor="0.25")
for y, v in enumerate([n_explicit, n_results - n_explicit]):
    ax.text(v + 8, y, f"{v} ({100.0*v/n_results:.1f}%)", va="center", fontsize=10)
ax.set_xlim(0, n_results * 1.22)
ax.set_xlabel(f"results (total {n_results}); {n_unclear}/{len(cards)} cards flagged denominator_unclear")
ax.set_title("Figure 4: denominator coverage of the extracted claims")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
for ext in ("pdf", "png"):
    out = OUTD / f"fig4_audit.{ext}"
    fig.savefig(out)
    print(f"[fig4] written: {out.relative_to(ROOT)}")
