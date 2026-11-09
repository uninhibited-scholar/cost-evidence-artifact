#!/usr/bin/env python3
"""Verify the internal consistency of the shipped same-loop adjudication record.

    python3 code/build_same_loop_matrix.py

data/same_loop_matrix.json is the HUMAN adjudication record (per-paper L1/L2/L3
judgments with quotes and notes, protocol v3). This script re-derives the
paper-relevant counts from the record's own judgment list and reports any
mismatch:

  * strict / weak determination counts and sets
  * by-stage split (deployment / training)
  * strict_persistent_state vs strict_weight_space (the paper's 2/129 + 4/129)
  * the binary lower bound (persistent-state strict under a binary L2/L3 reading)
  * the regression-scan record

Known stale sub-block (reported, not silently accepted): counts.L1 and sets.L1
were last refreshed before the 2026-10-31 additions; the paper cites only the
strict counts, which are unaffected.

The mechanical screening that feeds this record is code/screen_same_loop.py.
The historical v2 generator script (which wrote a 117-card-caliber version of
this file on 2026-10-28) is intentionally NOT shipped: re-running it would
overwrite the v3 record with stale counts.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "same_loop_matrix.json"


def yes(v):
    return v in ("yes", "yes_weak")


def main():
    m = json.loads(MATRIX.read_text(encoding="utf-8"))
    judged = m["judgments"]
    notapp = m.get("not_applicable", [])
    problems = []
    warnings = []
    ok = 0

    def chk(label, record, rederived):
        nonlocal ok
        good = record == rederived
        ok += good
        if not good:
            problems.append(f"{label}: record={record}, re-derived={rederived}")

    by_id = {j["id"]: j for j in judged}
    if len(by_id) != len(judged):
        problems.append("duplicate judgment ids present")
    L1 = [j["id"] for j in judged if yes(j["L1"]["value"])]
    L1L2 = [j["id"] for j in judged if yes(j["L1"]["value"]) and yes(j["L2"]["value"])]
    L3 = [i for i in L1L2 if yes(by_id[i]["L3a"]["value"]) or yes(by_id[i]["L3b"]["value"])]
    strict = [j["id"] for j in judged if j["determination"] == "strict"]
    weak = [j["id"] for j in judged if j["determination"] == "weak"]
    by_stage = {}
    for j in judged:
        if j["determination"] in ("strict", "weak"):
            by_stage.setdefault(j["stage"], []).append(j["id"])

    counts = m["counts"]
    sets = m["sets"]

    # ---- paper-relevant blocks ----
    chk("count.strict", counts["strict"], len(strict))
    chk("count.weak", counts["weak"], len(weak))
    chk("count.L1_and_L2", counts["L1_and_L2"], len(L1L2))
    chk("count.L1_L2_L3", counts["L1_L2_L3"], len(L3))
    chk("count.by_stage", counts["by_stage"], {k: len(v) for k, v in by_stage.items()})
    chk("set.strict", sets["strict"], strict)
    chk("set.weak", sets["weak"], weak)
    chk("set.L1_and_L2", sets["L1_and_L2"], L1L2)
    chk("set.L1_L2_L3", sets["L1_L2_L3"], L3)

    rec = m["reclassified_20261029"]
    chk("count.strict_persistent_state", counts["strict_persistent_state"], len(rec["persistent_state_strict"]))
    chk("count.strict_weight_space", counts["strict_weight_space"], len(rec["weight_space_strict"]))
    chk("persistent-state set", rec["persistent_state_strict"], [i for i in strict if by_id[i]["stage"] == "deployment"])
    chk("weight-space set", rec["weight_space_strict"], [i for i in strict if by_id[i]["stage"] == "training"])
    binary_pass = [i for i in rec["persistent_state_strict"]
                   if by_id[i]["L3a"]["value"] == "yes" or by_id[i]["L3b"]["value"] == "yes"]
    chk("binary lower bound (persistent-state strict under a binary L2/L3 reading)",
        counts.get("strict_binary_lower_bound"), len(binary_pass))
    stage_split = m["stage_split"]
    chk("stage_split.deployment", stage_split["deployment"], by_stage.get("deployment", []))
    chk("stage_split.training", stage_split["training"], by_stage.get("training", []))

    reg = m["regression_measurement"]
    chk("regression hit_cards", reg["hit_cards"],
        ["2312.11513", "2410.23308", "2609.08747", "2609.13734", "2609.34151", "2609.38372",
         "2610.00347", "2610.11270", "2610.11781", "2610.14488", "2610.27495", "2610.29784"])
    chk("not_applicable count", len(notapp), 3)

    # ---- known stale sub-block ----
    if counts["L1"] != len(L1) or set(sets["L1"]) != set(L1):
        warnings.append(
            f"counts.L1={counts['L1']} / sets.L1 ({len(sets['L1'])} ids) predate the "
            f"2026-10-31 additions: the judgment list now yields L1=yes for {len(L1)} cards "
            f"(the record's own note counts '+3', one of the four newer L1-yes judgments is "
            f"L1=yes_weak with determination=out). The paper cites only the strict counts "
            f"(2/129 + 4/129), which are unaffected.")

    print(f"matrix protocol: {m['protocol']['version']} | corpus_n: {m['corpus_n']} | "
          f"judgments: {len(judged)} (+{len(notapp)} not-applicable)")
    print(f"counts: strict={counts['strict']} weak={counts['weak']} | "
          f"persistent-state strict {counts['strict_persistent_state']} + weight-space strict "
          f"{counts['strict_weight_space']} (binary lower bound {counts.get('strict_binary_lower_bound')})")
    print(f"stage split: deployment {stage_split['deployment']}, training {stage_split['training']}")
    print(f"regression scan: {reg['value']} ({len(reg['hit_cards'])} lexicon hits, no measurement)")
    for w in warnings:
        print(f"NOTE (documented inconsistency): {w}")
    print(f"internal-consistency checks passed: {ok}/{ok + len(problems)}")
    if problems:
        print("MISMATCHES:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: every paper-relevant count re-derives from the record's own judgment list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
