#!/usr/bin/env python3
"""Figure 3: cost-evidence reporting by defense execution layer.

    python3 code/fig3_cost.py

Recomputes, from data/cost_tags.json (per-card adjudication, cards_total=129):
  * the four class main counts (has=true and not qualitative-only),
  * the union of cards with any cost evidence, by layer (qualitative included),
  * the per-layer reporting rates quoted in the paper:
    execution-time gating 8/8, provenance tracing 13/18, content filtering 12/32,
    formal guarantees 2/4.
Layers include the 'n/a' bucket (cards coded before a layer assignment existed);
it enters no matrix cell and is printed for completeness. Renders a stacked bar
chart to figures/out/fig3_cost.pdf/.png.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTD = ROOT / "figures" / "out"
CLS = ["utility_loss", "latency_compute", "false_positive", "revocability"]
SHORT = {"utility_loss": "C1", "latency_compute": "C2", "false_positive": "C3", "revocability": "C4"}
LAYERS = ["execution", "provenance", "content", "formal", "architecture", "weight-space", "none", "n/a"]

ct = json.loads((ROOT / "data" / "cost_tags.json").read_text(encoding="utf-8"))
cards = ct["cards"]
if ct.get("cards_total") != len(cards):
    raise SystemExit(f"[fig3] cards_total={ct.get('cards_total')} != len(cards)={len(cards)}")

num = Counter()
n_lay = Counter(c["layer"] for c in cards.values())
union_any = Counter()
union_num = Counter()
per_class_layer = {ck: Counter() for ck in CLS}
for c in cards.values():
    lay = c["layer"]
    has_any = has_num = False
    for ck in CLS:
        e = c["classes"][ck]
        if e["has"]:
            has_any = True
            if e["qualitative"]:
                pass
            else:
                has_num = True
                num[ck] += 1
                per_class_layer[ck][lay] += 1
    if has_any:
        union_any[lay] += 1
    if has_num:
        union_num[lay] += 1

print(f"[fig3] class main counts (cards with numeric readings): "
      + ", ".join(f"{SHORT[k]}={num[k]}" for k in CLS) + " (denominator 129)")
union_total = sum(union_any.values())
print(f"[fig3] union: {union_total}/129 cards with any cost evidence "
      f"(numeric {sum(union_num.values())}, qualitative-only {union_total - sum(union_num.values())})")
print("[fig3] per-layer union (cards with cost evidence / cards in the layer):")
for l in LAYERS:
    if n_lay[l]:
        print(f"    {l:14s} {union_any[l]}/{n_lay[l]} (numeric {union_num[l]})")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except Exception as e:
    print(f"[fig3] matplotlib unavailable ({e}); console counts above are the artifact of record.")
    raise SystemExit(0)

OUTD.mkdir(parents=True, exist_ok=True)
colors = {"utility_loss": "#4a7ebb", "latency_compute": "#e08214",
          "false_positive": "#4d9959", "revocability": "#7b6bb0"}
layers = [l for l in LAYERS if n_lay[l]][::-1]
fig, ax = plt.subplots(figsize=(8.2, 4.2))
left = np.zeros(len(layers))
for ck in CLS:
    vals = np.array([per_class_layer[ck][l] for l in layers], dtype=float)
    ax.barh(layers, vals, left=left, color=colors[ck], edgecolor="0.25", label=SHORT[ck])
    for y, v in enumerate(vals):
        if v:
            ax.text(left[y] + v / 2, y, SHORT[ck], ha="center", va="center", fontsize=8, color="white")
    left += vals
for y, l in enumerate(layers):
    ax.text(max(left) + 0.5, y, f"union {union_any[l]}/{n_lay[l]}", va="center", fontsize=8.5, color="#2b6cb0")
ax.set_xlabel("cards with numeric cost readings (main counts; one card may carry several classes)")
ax.set_title(f"Figure 3: cost evidence by defense layer (union {union_total}/129)")
ax.legend(title="cost class", fontsize=8.5)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
for ext in ("pdf", "png"):
    out = OUTD / f"fig3_cost.{ext}"
    fig.savefig(out)
    print(f"[fig3] written: {out.relative_to(ROOT)}")
