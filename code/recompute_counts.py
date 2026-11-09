#!/usr/bin/env python3
"""Recompute every headline count of the paper from the packaged data.

Run from the artifact root:   python3 code/recompute_counts.py
Standard library only; no network access.

Sources (all inside this artifact):
  data/cards/<arxiv_id>.json      129 evidence cards (results[], quality_flags, object, intervention)
  data/cost_tags.json             per-card four-class cost adjudication (cards_total=129)
  data/same_loop_matrix.json      same-loop adjudications (L1/L2/L3 criterion)

Counting rules (documented in data/cost_tags_rules.md):
  * main class count  = cards with has=true AND not qualitative-only (a numeric reading exists)
  * union             = cards with has=true in any class (qualitative included)
  * explicit denominator = results[].denominator with n_total or n_valid stated,
                           or a non-empty scalar denominator string
  * unit families are classified from each evidence entry's value+metric text
    (regex classifier documented below; "one reading, one class, multiple unit
    families possible")
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CLS = ["utility_loss", "latency_compute", "false_positive", "revocability"]
NAME = {"utility_loss": "C1 utility loss", "latency_compute": "C2 latency & compute",
        "false_positive": "C3 false positives & collateral", "revocability": "C4 revocability"}
LAYERS5 = ["content", "provenance", "execution", "architecture", "formal"]
OPS = ["formation", "update", "retention", "retrieval", "revocation", "repair"]

# --- unit-family classifier (identical to the archived strict rule) -------------
# A unit mark must sit right next to a number (or be the value itself); this
# avoids possessive-s and label false positives. A reading can carry several
# families (e.g., "-4.4 pp (2.7% tokens)" is relative only; "0.4 s per query
# (8-20%)" is time and relative).
REL = re.compile(r"%|\bpp\b|percentage point|×|(?<![\w])\d[\d.]*\s*[xX]\b|\btimes\b|fold|\bratio\b")
TIME = re.compile(r"\d[\d.,]*\s*(ms|s|sec|secs|min|mins|h|hr|hrs|hour|hours|second|seconds|minute|minutes|µs|μs|us)\b", re.I)
TOK = re.compile(r"\d[\d.,]*\s*[kKmM]?\s*tokens?\b|\btokens?\b", re.I)
MEM = re.compile(r"\d[\d.,]*\s*(MB|GB|KB|TB|bytes?)\b", re.I)
MON = re.compile(r"\$|USD|dollar", re.I)
ENE = re.compile(r"kWh|joule|watt", re.I)
GPU = re.compile(r"GPU[- ]?hours?|A100[- ]?hours?|H100[- ]?hours?", re.I)

EXPECTED = {
    "cards": 129, "results": 1086, "explicit_denominators": 676, "unclear_cards": 48,
    "C1": 34, "C2": 26, "C3": 19, "C4": 21, "union": 75, "union_numeric": 70, "qualitative_only_cards": 5,
    "price": 66, "price_numeric": 62, "price_qual_only": 4, "c4_only": 9, "c4_only_numeric": 8,
    "readings": 133, "rel": 78, "time": 12, "token": 6, "mem": 2,
    "money": 2, "energy": 0, "gpuh": 0, "no_unit": 40,
    "cards_with_readings": 75, "cards_with_unit": 59, "cards_multi_family": 12,
    "split_pure_rel": 71, "split_pure_rel_den": 42, "split_pure_abs": 15,
    "split_pure_abs_den": 0, "split_mixed": 7, "split_mixed_den": 3, "split_none": 40,
    "matrix_grand": 350, "empty_cell": ("repair", "formal"),
    "single_evidence_cells": {("revocation", "execution"), ("repair", "execution")},
    "rate_execution": "7/8", "rate_provenance": "14/18", "rate_content": "16/32", "rate_formal": "2/4",
    "p_rate_execution": "7/8", "p_rate_provenance": "13/18", "p_rate_content": "13/32", "p_rate_formal": "1/4",
    "strict_persistent_state": 2, "strict_weight_space": 4, "evolution_compute_bill": "0/4",
    "regression_value": "0/129", "regression_hit_cards": 13,
}


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def main():
    cards = {p.stem: json.load(open(p, encoding="utf-8")) for p in sorted((DATA / "cards").glob("*.json"))}
    ct = load("cost_tags.json")
    sl = load("same_loop_matrix.json")

    ok = []

    def chk(label, got, want):
        good = got == want
        ok.append(good)
        print(f"  [{'OK ' if good else 'FAIL'}] {label}: {got}" + ("" if good else f"   (paper: {want})"))

    print("=" * 78)
    print("A. CORPUS AND DENOMINATORS  (from data/cards/*.json)")
    print("=" * 78)
    results = [r for c in cards.values() for r in (c.get("results") or [])]
    results = [r for r in results if isinstance(r, dict)]

    def explicit(r):
        d = r.get("denominator")
        if isinstance(d, dict):
            return d.get("n_total") is not None or d.get("n_valid") is not None
        return d is not None and str(d).strip() != ""

    n_explicit = sum(1 for r in results if explicit(r))
    n_unclear = sum(1 for c in cards.values() if "denominator_unclear" in (c.get("quality_flags") or []))
    chk("cards", len(cards), EXPECTED["cards"])
    chk("results", len(results), EXPECTED["results"])
    chk("explicit denominators", n_explicit, EXPECTED["explicit_denominators"])
    print(f"         -> {n_explicit}/{len(results)} = {100.0*n_explicit/len(results):.1f}%")
    chk("denominator_unclear cards", n_unclear, EXPECTED["unclear_cards"])

    print()
    print("=" * 78)
    print("B. FOUR COST CLASSES (from data/cost_tags.json, adjudicated per card)")
    print("=" * 78)
    cc = ct["cards"]
    if ct.get("cards_total") != len(cc) or len(cc) != len(cards):
        print(f"  [FAIL] cards_total={ct.get('cards_total')} vs cards dir={len(cards)}")
        ok.append(False)
    else:
        ok.append(True)
        print(f"  [OK ] cards_total={ct['cards_total']} matches card files ({len(cards)})")
    numeric = Counter()
    has = Counter()
    qual_only = Counter()
    for c in cc.values():
        for k in CLS:
            e = c["classes"][k]
            if e["has"]:
                has[k] += 1
                if e["qualitative"]:
                    qual_only[k] += 1
                else:
                    numeric[k] += 1
    for i, k in enumerate(CLS):
        chk(NAME[k], numeric[k], EXPECTED[f"C{i+1}"])
    union = sum(1 for c in cc.values() if any(c["classes"][k]["has"] for k in CLS))
    unum = sum(1 for c in cc.values() if any(c["classes"][k]["has"] and not c["classes"][k]["qualitative"] for k in CLS))
    chk("union (any cost evidence)", union, EXPECTED["union"])
    chk("union with numeric readings", unum, EXPECTED["union_numeric"])
    chk("qualitative-only cards", union - unum, EXPECTED["qualitative_only_cards"])
    for k in CLS:
        if qual_only[k]:
            print(f"         ({NAME[k]}: qualitative-only cards {qual_only[k]})")

    # --- headline definition (paper v3): a card "prices a defense" only if it
    # reports a C1-C3 reading.  C4 records whether revocation succeeded, not what
    # it cost, so cards that appear only in C4 are counted separately.
    PRICE = CLS[:3]
    def any_in(c, ks):
        return any(c["classes"][k]["has"] for k in ks)
    price = sum(1 for c in cc.values() if any_in(c, PRICE))
    price_num = sum(1 for c in cc.values()
                    if any(c["classes"][k]["has"] and not c["classes"][k]["qualitative"] for k in PRICE))
    c4_only = sum(1 for c in cc.values() if any_in(c, CLS) and not any_in(c, PRICE))
    c4_only_num = sum(1 for c in cc.values() if any_in(c, CLS) and not any_in(c, PRICE)
                      and any(c["classes"][k]["has"] and not c["classes"][k]["qualitative"] for k in CLS))
    chk("cards that price a defense (C1-C3, any evidence)", price, EXPECTED["price"])
    chk("cards that price a defense, numeric reading", price_num, EXPECTED["price_numeric"])
    chk("cards that price a defense, qualitative only", price - price_num, EXPECTED["price_qual_only"])
    chk("cards only in C4 (revocation-success evidence)", c4_only, EXPECTED["c4_only"])
    chk("... of those, numeric", c4_only_num, EXPECTED["c4_only_numeric"])

    print()
    print("=" * 78)
    print("C. COST READINGS AND UNIT FAMILIES (from data/cost_tags.json evidence entries)")
    print("=" * 78)
    fam = Counter()
    per_class = defaultdict(Counter)
    fam_card = defaultdict(set)
    cards_ev = set()
    n_read = 0
    no_unit = 0
    for aid, c in cc.items():
        for k in CLS:
            for e in c["classes"][k]["evidence"]:
                n_read += 1
                cards_ev.add(aid)
                s = str(e.get("value", "")) + " || " + str(e.get("metric", ""))
                fs = []
                if REL.search(s): fs.append("rel")
                if TIME.search(s): fs.append("time")
                if TOK.search(s): fs.append("token")
                if MEM.search(s): fs.append("mem")
                if MON.search(s): fs.append("money")
                if ENE.search(s): fs.append("energy")
                if GPU.search(s): fs.append("gpuh")
                if not fs:
                    no_unit += 1
                for f in fs:
                    fam[f] += 1
                    per_class[k][f] += 1
                    fam_card[aid].add(f)
    chk("cost readings (evidence entries)", n_read, EXPECTED["readings"])
    chk("relative quantities", fam["rel"], EXPECTED["rel"])
    chk("wall-clock time", fam["time"], EXPECTED["time"])
    chk("tokens", fam["token"], EXPECTED["token"])
    chk("memory", fam["mem"], EXPECTED["mem"])
    chk("money / energy / GPU-hours", (fam["money"], fam["energy"], fam["gpuh"]),
        (EXPECTED["money"], EXPECTED["energy"], EXPECTED["gpuh"]))
    chk("readings with no unit", no_unit, EXPECTED["no_unit"])
    chk("cards with >=1 reading", len(cards_ev), EXPECTED["cards_with_readings"])
    unit_cards = sum(1 for v in fam_card.values() if v)
    multi = sum(1 for v in fam_card.values() if len(v) >= 2)
    chk("cards with >=1 unit family", unit_cards, EXPECTED["cards_with_unit"])
    chk("cards in >=2 families", multi, EXPECTED["cards_multi_family"])
    print("         unit-bearing cards: single-family %d, two-or-more %d (%d/%d = %.0f%%)" %
          (unit_cards - multi, multi, multi, unit_cards, 100.0 * multi / unit_cards))
    print("         per class:", {NAME[k]: dict(per_class[k]) for k in CLS})

    print()
    print("=" * 78)
    print("D. 350-CELL MATRIX (from data/cards mechanism_layer x operations_covered)")
    print("=" * 78)
    M = {op: {l: 0 for l in LAYERS5} for op in OPS}
    n5 = 0
    for c in cards.values():
        ml = (c.get("intervention") or {}).get("mechanism_layer")
        if ml in LAYERS5:
            n5 += 1
        if ml not in LAYERS5:
            continue
        for op in (c.get("object") or {}).get("operations_covered") or []:
            if op in M:
                M[op][ml] += 1
    print("  matrix (rows=operations x cols=layers):")
    for op in OPS:
        print(f"    {op:11s}" + "".join(f"{M[op][l]:9d}" for l in LAYERS5) + f"   row={sum(M[op].values())}")
    cols = {l: sum(M[op][l] for op in OPS) for l in LAYERS5}
    grand = sum(sum(M[op].values()) for op in OPS)
    chk("occupied cells", grand, EXPECTED["matrix_grand"])
    chk("cards with a five-layer defense claim", n5, 103)
    zero = {(op, l) for op in OPS for l in LAYERS5 if M[op][l] == 0}
    single = {(op, l) for op in OPS for l in LAYERS5 if M[op][l] == 1}
    chk("unique empty cell", sorted(zero), [EXPECTED["empty_cell"]])
    chk("two single-evidence cells", sorted(single), sorted(EXPECTED["single_evidence_cells"]))
    print("         column totals:", {l: cols[l] for l in LAYERS5})
    print("         NOTE: row/column breakdowns are recomputed values; see README section 4")

    print()
    print("=" * 78)
    print("E. PER-LAYER COST-REPORTING RATES (from data/cost_tags.json layer field)")
    print("=" * 78)
    lay_n = Counter(c["layer"] for c in cc.values())
    lay_union = Counter()
    lay_num = Counter()
    for c in cc.values():
        a = n = False
        for k in CLS:
            e = c["classes"][k]
            if e["has"]:
                a = True
                if not e["qualitative"]:
                    n = True
        if a: lay_union[c["layer"]] += 1
        if n: lay_num[c["layer"]] += 1
    rates = {}
    for l in ["execution", "provenance", "content", "formal", "architecture", "none", "weight-space", "n/a"]:
        rates[l] = f"{lay_union[l]}/{lay_n[l]}"
    chk("execution-time gating", rates["execution"], EXPECTED["rate_execution"])
    chk("provenance tracing", rates["provenance"], EXPECTED["rate_provenance"])
    chk("content filtering", rates["content"], EXPECTED["rate_content"])
    chk("formal guarantees", rates["formal"], EXPECTED["rate_formal"])
    print(f"         full by-layer union: " + ", ".join(f"{l} {rates[l]}" for l in rates))
    print(f"         numeric-only by layer: " + ", ".join(f"{l} {lay_num[l]}" for l in rates))
    # the paper's headline layer rates use the C1-C3 definition
    lay_price = Counter()
    for c in cc.values():
        if any(c["classes"][k]["has"] for k in CLS[:3]):
            lay_price[c["layer"]] += 1
    prates = {l: f"{lay_price[l]}/{lay_n[l]}" for l in rates}
    chk("price: execution-time gating", prates["execution"], EXPECTED["p_rate_execution"])
    chk("price: provenance tracing", prates["provenance"], EXPECTED["p_rate_provenance"])
    chk("price: content filtering", prates["content"], EXPECTED["p_rate_content"])
    chk("price: formal guarantees", prates["formal"], EXPECTED["p_rate_formal"])
    print(f"         price by layer (C1-C3): " + ", ".join(f"{l} {prates[l]}" for l in rates))

    print()
    print("=" * 78)
    print("F. SAME-LOOP CO-EVOLUTION COUNTS (from data/same_loop_matrix.json)")
    print("=" * 78)
    cnts = sl["counts"]
    chk("corpus_n in matrix", sl.get("corpus_n"), 129)
    chk("strict same-loop, persistent state", cnts["strict_persistent_state"], EXPECTED["strict_persistent_state"])
    chk("strict same-loop, weight space", cnts["strict_weight_space"], EXPECTED["strict_weight_space"])
    chk("strict binary lower bound", cnts.get("strict_binary_lower_bound"), 1)
    evol4 = ["2609.36580", "2609.36603", "2610.02920", "2607.19351"]
    e4 = sum(1 for a in evol4 if cc[a]["classes"]["latency_compute"]["has"]
             and not cc[a]["classes"]["latency_compute"]["qualitative"])
    chk("evolution-compute bill (numeric C2 latency/compute reading among the 4 deployment-stage evolution cards)",
        f"{e4}/4", EXPECTED["evolution_compute_bill"])
    print(f"         deployment-stage: {cnts['by_stage']['deployment']} (2 strict + 1 weak), training-stage: {cnts['by_stage']['training']}")
    reg = sl["regression_measurement"]
    chk("regression-risk measurement count", reg["value"], EXPECTED["regression_value"])
    chk("REG lexicon hit cards (all read and rejected)", len(reg["hit_cards"]), EXPECTED["regression_hit_cards"])
    print(f"         regression-risk scan: {reg['value']} (REG lexicon hit "
          f"{len(reg['hit_cards'])} cards; all conceptual mentions, capability loss or one-sided ablations)")

    print()
    print("=" * 78)
    print("G. COMPARABILITY SPLIT OF THE 122 READINGS (Section 7.4, Appendix A.5)")
    print("=" * 78)
    pure_rel = pure_rel_d = 0
    pure_abs = pure_abs_d = 0
    mixed = mixed_d = 0
    none_u = none_u_d = 0
    for aid, c in cc.items():
        for k in CLS:
            for e in c["classes"][k]["evidence"]:
                s_ = str(e.get("value", "")) + " || " + str(e.get("metric", ""))
                fs = set()
                if REL.search(s_): fs.add("rel")
                if TIME.search(s_): fs.add("time")
                if TOK.search(s_): fs.add("token")
                if MEM.search(s_): fs.add("mem")
                if MON.search(s_): fs.add("money")
                if ENE.search(s_): fs.add("energy")
                if GPU.search(s_): fs.add("gpuh")
                has_d = 1 if e.get("denominator") not in (None, "", "None") else 0
                if fs == {"rel"}:
                    pure_rel += 1; pure_rel_d += has_d
                elif fs and "rel" not in fs:
                    pure_abs += 1; pure_abs_d += has_d
                elif fs:
                    mixed += 1; mixed_d += has_d
                else:
                    none_u += 1; none_u_d += has_d
    chk("purely relative readings", pure_rel, EXPECTED["split_pure_rel"])
    chk("  of which carry a denominator", pure_rel_d, EXPECTED["split_pure_rel_den"])
    chk("purely absolute readings", pure_abs, EXPECTED["split_pure_abs"])
    chk("  of which carry a denominator", pure_abs_d, EXPECTED["split_pure_abs_den"])
    chk("readings carrying both families", mixed, EXPECTED["split_mixed"])
    chk("  of which carry a denominator", mixed_d, EXPECTED["split_mixed_den"])
    chk("readings with no unit family", none_u, EXPECTED["split_none"])
    chk("split covers every reading", pure_rel + pure_abs + mixed + none_u, EXPECTED["readings"])
    print(f"         pure relative {pure_rel} ({pure_rel_d} with a denominator), "
          f"pure absolute {pure_abs} ({pure_abs_d}), both {mixed} ({mixed_d}), none {none_u} ({none_u_d})")

    print()
    print("=" * 78)
    print(f"RESULT: {sum(ok)}/{len(ok)} checks match the paper. " +
          ("ALL MAIN COUNTS REPRODUCED." if all(ok) else "SOME CHECKS FAILED."))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
