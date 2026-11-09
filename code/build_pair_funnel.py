#!/usr/bin/env python3
"""Rebuild the candidate-pair funnel behind the "cannot be ranked" claim (S7.4) from the
cards in this package and the per-pair verdicts beside it.

Stage 0  all unordered card pairs                              8,256
Stage 1  the two cards name a shared benchmark                   110
Stage 2  both sides carry a numeric cost reading                  54
Stage 3  a shared measurement key (metric family + population
         + attack family) survives, read one by one                N

Writes extraction/derived/pair-funnel.csv with one row per stage-2 pair and,
for the pairs that reach stage 3, the fields the reading turns on.
"""
import collections
import csv
import glob
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "data" / "cards"
LEDGER = ROOT / "data" / "cost_tags.json"
OUT = ROOT / "data" / "pair-funnel.csv"

CLASSES = ("utility_loss", "latency_compute", "false_positive", "revocability")
BENCH = re.compile(r"\b[A-Z][A-Za-z0-9\-]{2,}(?:Bench|Dojo|World|QA|Eval|Benchmark|Set|Hub|Shop|Arena)\b")

# metric families, first match wins; order matters (attack success before success)
FAMILIES = [
    ("attack_success", r"attack success|\bASR\b|success rate of (the )?attack|jailbreak success"),
    ("detection", r"detection|true positive|recall|precision|AUROC|\bAUC\b|F1"),
    ("false_positive", r"false positive|\bFPR\b|over-refusal|false refusal"),
    ("utility", r"utility|task success|accuracy|solved|completion rate|benign"),
    ("latency", r"latency|overhead|\bms\b|millisecond|wall-clock|runtime|throughput"),
    ("tokens", r"token|prompt length|cost per query|\$"),
]

ATTACKS = re.compile(r"\b(GCG|AutoDAN|TAP|PAIR|Crescendo|injection|jailbreak|poison|backdoor|adversarial|adaptive|"
                     r"indirect prompt|prompt injection|memory poisoning)\b", re.I)


def family(text):
    for name, pattern in FAMILIES:
        if re.search(pattern, text, re.I):
            return name
    return "other"


def load():
    cards = {}
    for path in glob.glob(str(CARDS / "*.json")):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        cards[data["arxiv_id"]] = data
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))["cards"]
    return cards, ledger


def costs(ledger, key):
    out = []
    for cls in CLASSES:
        data = ledger[key]["classes"][cls]
        if data["has"] and not data.get("qualitative"):
            quote = (data.get("evidence") or [{}])[0].get("quote") or ""
            out.append((cls, quote.replace("\n", " ")[:120]))
    return out


def readings(card):
    rows = []
    for res in card.get("results", []):
        metric = res.get("metric") or ""
        setting = res.get("setting") or ""
        rows.append({
            "family": family(metric),
            "metric": metric[:60],
            "value": (res.get("value") or "")[:50],
            "setting": setting[:80],
            "attack": bool(ATTACKS.search(setting + " " + (res.get("value") or ""))),
            "denominator": str((res.get("denominator") or {}).get("n_total") or ""),
        })
    return rows


def main():
    cards, ledger = load()
    benchmarks = collections.defaultdict(set)
    for key, card in cards.items():
        text = " ".join((r.get("setting") or "") + " " + (r.get("metric") or "") for r in card.get("results", []))
        for name in set(BENCH.findall(text)):
            benchmarks[name].add(key)

    shared = {}
    for name, keys in benchmarks.items():
        for a, b in itertools.combinations(sorted(keys), 2):
            shared.setdefault((a, b), set()).add(name)

    priced = {key for key in cards if costs(ledger, key)}
    stage2 = sorted((pair, names) for pair, names in shared.items() if pair[0] in priced and pair[1] in priced)

    rows = []
    for (a, b), names in stage2:
        ra, rb = readings(cards[a]), readings(cards[b])
        fams_a = {r["family"] for r in ra} - {"other"}
        fams_b = {r["family"] for r in rb} - {"other"}
        common_fams = fams_a & fams_b
        # a shared measurement key needs the same metric family, the same attack
        # family and an overlapping denominator
        den_a = {r["denominator"] for r in ra if r["denominator"]}
        den_b = {r["denominator"] for r in rb if r["denominator"]}
        shared_den = den_a & den_b
        atk_a = any(r["attack"] for r in ra)
        atk_b = any(r["attack"] for r in rb)
        rows.append({
            "card_a": a,
            "card_b": b,
            "benchmark": ";".join(sorted(names)),
            "metric_families_a": ";".join(sorted(fams_a)),
            "metric_families_b": ";".join(sorted(fams_b)),
            "shared_families": ";".join(sorted(common_fams)),
            "denominator_a": ";".join(sorted(den_a)) or "-",
            "denominator_b": ";".join(sorted(den_b)) or "-",
            "shared_denominator": ";".join(sorted(shared_den)) or "-",
            "attack_in_a": int(atk_a),
            "attack_in_b": int(atk_b),
            "cost_a": " | ".join(f"{c}: {q}" for c, q in costs(ledger, a)),
            "cost_b": " | ".join(f"{c}: {q}" for c, q in costs(ledger, b)),
        })

    verdicts = json.loads((ROOT / "data" / "pair-verdicts.json").read_text(encoding="utf-8"))
    security = {"attack_success", "utility", "detection", "false_positive"}
    stage3 = []
    for row in rows:
        families = {f for f in row["shared_families"].split(";") if f} & security
        same_attack = row["attack_in_a"] == row["attack_in_b"]
        if families and same_attack:
            verdict, note = verdicts.get(f"{row['card_a']}|{row['card_b']}", ["unread", ""])
            row["fails_on"] = verdict
            row["note"] = note
            stage3.append(row)
    for row in rows:
        row.setdefault("fails_on", "-")
        row.setdefault("note", "")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["card_a", "card_b", "benchmark", "shared_families", "denominator_a", "denominator_b",
              "attack_in_a", "attack_in_b", "fails_on", "note", "cost_a", "cost_b"]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in stage3:
            writer.writerow(row)

    terms = collections.Counter(row["fails_on"] for row in stage3)
    print(f"stage 0 all pairs            {len(cards) * (len(cards) - 1) // 2}")
    print(f"stage 1 shared benchmark     {len(shared)}")
    print(f"stage 2 both priced          {len(stage2)}")
    print(f"stage 3 same family+attack   {len(stage3)}")
    print(f"stage 4 match on all three   {sum(1 for r in stage3 if r['fails_on'] == 'license')}")
    print("fails on:", dict(terms))
    if "unread" in terms:
        print("still to read:", [f"{r['card_a']}|{r['card_b']}" for r in stage3 if r["fails_on"] == "unread"])
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()