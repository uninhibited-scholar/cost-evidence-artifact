#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""screen_same_loop.py - coarse screen (L1/L2/L3 + regression risk) + structured triage.

Reproducible screening stage behind the same-loop adjudication:
  1) screen: regex marker scan over all cards -> candidate set (recall-oriented)
  2) triage: structured exclusion of candidates (no persistent artifact / no experiment /
     author-disclaimed adversary / attack-side-only markers)
  3) adjudicate: the remaining candidates are judged one by one; the judgments live in
     data/same_loop_matrix.json (human layer).

Usage:
    python3 code/screen_same_loop.py              # summary
    python3 code/screen_same_loop.py --verbose    # print candidates and triage buckets
Output: data/same_loop_scan.json (deterministic regeneration; only the matrix judgments
are human work).

Criterion (L1/L2/L3), as used in the paper:
  L1 defense side: the defense artifact's own state is updated at least once inside the
     evaluated loop, driven by feedback (deployment stream or adversarial training loop).
  L2 attack side: the attack observes/iterates/adapts within the evaluation run.
  L3a same-stream separation: a frozen-vs-evolving contrast exists and attacks continue
     past the freeze point.
  L3b attack closure: the target of the attack is the defense's own artifacts
     (memory / skills / rules / gating / harness).
  REG: a denominator-bearing measurement of "after a defense update, previously handled
     attacks revive" (conceptual mentions do not count).

Only positive fields are scanned; threat_model.not_covered is recorded separately as
counter-evidence (an author's "we do not cover X" is not evidence of doing X).
The Chinese-language regex alternatives (tag prefix zh-) are part of the archived method:
the card annotations are partly Chinese, so dropping them would change scan results.
They are functional pattern text, not commentary.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_DIR = ROOT / "data" / "cards"

# ---------------------------------------------------------------- lexicon
L1_STRONG = [
    (r"updat(e|ed|es|ing)[^.\n]{0,50}\b(after|at|per|every|each|on)\b[^.\n]{0,40}(episode|task|round|step|session|batch|iteration)", "update-after-episode"),
    (r"\b(test[- ]time|online|in[- ]stream|continual|continuous(ly)?|incremental)\s*(updat|adapt|learn|train|evolv)", "test-time-update"),
    (r"\b(harness|guard|polic(y|ies)|skill librar\w*|rule set|defen[cs]e)[^.\n]{0,50}\b(is|are|gets?|become)\s+(updated|revised|rewritten|refined|retrained)", "artifact-updated"),
    (r"\b(non-?stationary|drift\w*)[^.\n]{0,60}\b(updat|adapt|defen[cs]e)", "nonstationary-update"),
    (r"(每轮|逐轮|每个?episode|每个?回合|在线|流内|部署期间|随部署|运行中|跨轮)[^。\n]{0,24}(更新|演化|进化|适配|改写|修正|补丁)", "zh-in-stream-update"),
    (r"(更新|改写|修正|补丁)[^。\n]{0,16}(策略库|规则库|技能库|记忆库|护栏|门控|guard|harness)", "zh-artifact-update"),
]
L1_WEAK = [
    (r"\b(self[- ]?evolv|co[- ]?evolv|auto[- ]?evolv|evolving defen[cs]e)", "self-evolve"),
    (r"(自演化|自进化|自我演化|共演化|协同演化|共同演化|演化中)", "zh-coevolve"),
]
L2 = [
    (r"\b(adaptive|adapting|adapts?)\s+(attack|adversar|attacker|opponent|red)", "adaptive-attack"),
    (r"\b(attack|adversar\w+|attacker|opponent)[^.\n]{0,70}\b(adapt|react|respond|observe|quer(y|ies)|iterat|refine|escalat)", "attacker-adapts"),
    (r"\b(iterativ\w+|in[- ]the[- ]loop|closed[- ]loop|feedback[- ]driven|multi[- ]turn)\b", "iterative-loop"),
    (r"\b(query|attack)\s+budget\b", "query-budget"),
    (r"(自适应|适应性)(攻击|对手|攻击者|对抗)", "zh-adaptive-attack"),
    (r"(攻击|对手|红队)[^。\n]{0,30}(观察|反馈|迭代|适应|反应|改写|升级)", "zh-attacker-iterates"),
    (r"(迭代|闭环|多轮|对抗)(攻击|对抗|优化|搜索|训练)", "zh-iterative"),
]
L3A = [
    (r"\b(frozen|freeze|froze)\b[^.\n]{0,70}\b(control|baseline|comparison|arm|condition|defen[cs]e)", "frozen-control"),
    (r"\b(held[- ]out|control arm|ablation|on[/ ]off|without[- ]update|no[- ]update)\b", "held-out-control"),
    (r"(冻结)[^。\n]{0,30}(对照|基线|比较|条件|防御)", "zh-frozen-control"),
]
L3B = [
    (r"\b(poison|poisoning|tamper|corrupt)\w*[^.\n]{0,70}\b(memory|skill librar|policy librar|rule|guard|harness|defen[cs]e)\b", "attack-on-defense-artifact"),
    (r"\battack(s|ing)?\s+(on\s+)?the\s+(safety|defen[cs]e|guard|policy|harness)\s+(system|layer|component|itself)", "attack-on-defense-system"),
    (r"(投毒|污染|篡改)[^。\n]{0,24}(记忆|技能库|策略库|规则库|护栏|防御|门控)", "zh-attack-on-artifact"),
]
REG = [
    (r"\bregression\b", "regression"),
    (r"\bcatastrophic\s+forgetting\b", "catastrophic-forgetting"),
    (r"\b(resurrect|re-?emerge|reappear|re-?introduc)\w*", "resurrection"),
    (r"\b(previously|formerly)\s+(mitigated|blocked|defended|patched)", "previously-mitigated"),
    (r"(回归|复活|复发|重新出现|灾难性遗忘)", "zh-regression"),
]
NC_DISCLAIM = [
    (r"\b(no|not|without|never)\b[^.\n]{0,40}\b(adaptive|iterative|reacting|evolving|in[- ]the[- ]loop)\b", "no-adaptive-adversary"),
    (r"\b(static|pre-?scheduled|pre-?defined|fixed|non-?adaptive)\b[^.\n]{0,40}\b(attack|adversar|opponent|threat)\b", "static-adversary"),
    (r"\b(no|not|without)\b[^.\n]{0,30}\b(attacker|adversar|opponent)\b", "no-adversary"),
    (r"(无|没有|不涉及)[^。\n]{0,16}(攻击者|自适应|对手|对抗)", "zh-no-adversary"),
]

def C(spec):
    return [(re.compile(p, re.I), t) for p, t in spec]


RULES = {"L1_strong": C(L1_STRONG), "L1_weak": C(L1_WEAK), "L2": C(L2), "L3a": C(L3A), "L3b": C(L3B), "REG": C(REG), "NC": C(NC_DISCLAIM)}

POS_FIELDS = ["object", "intervention", "threat_model", "results", "controls", "counterexamples", "limitations"]
NO_EXPERIMENT_FLAGS = {"no_empirical_results", "no_denominators_reported", "survey_card_all_results_are_synthesis_not_experiments", "not_an_experimental_paper"}


def flatten(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "not_covered":
                continue
            out.append(flatten(v))
    elif isinstance(obj, list):
        for v in obj:
            out.append(flatten(v))
    elif isinstance(obj, str):
        out.append(obj)
    return "\n".join(x for x in out if x)


def scan(text, rules, cap=40):
    hits = []
    for rx, tag in rules:
        for m in rx.finditer(text):
            hits.append({"tag": tag, "match": m.group(0)[:120]})
            if len(hits) >= cap:
                return hits
    return hits


def triage(rec):
    """Structured exclusion for candidates that did not reach manual adjudication."""
    if rec["what_persists"] == "none" and not rec["L1_strong"]:
        return "E1_no_persistent_artifact", "object.what_persists=none and no in-stream artifact-update statement"
    if rec["flags"] & NO_EXPERIMENT_FLAGS:
        return "E2_no_experiment", "quality_flags=" + ",".join(sorted(rec["flags"] & NO_EXPERIMENT_FLAGS))
    if rec["NC"] and not rec["L1_strong"]:
        return "E3_author_disclaims_adversary", "not_covered disclaimer: " + rec["NC"][0]["match"]
    if not (rec["L1_strong"] or rec["L1_weak"]):
        return "E4_attack_or_regression_only", "attack-side/regression markers only; no defense-side evolution statement"
    return "MANUAL", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "data" / "same_loop_scan.json"))
    ap.add_argument("--matrix", default=str(ROOT / "data" / "same_loop_matrix.json"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    def contained(p):
        rp = Path(p).resolve()
        rp.relative_to(ROOT)  # raises if the path escapes the artifact root
        return rp

    out_path = contained(args.json)
    matrix_path = contained(args.matrix)

    manual_ids = []
    if matrix_path.is_file():
        m = json.loads(matrix_path.read_text(encoding="utf-8"))
        manual_ids = ([j["id"] for j in m.get("judgments", [])]
                      + [j["id"] for j in m.get("not_applicable", [])]
                      + list(m.get("extra_manual_ids", [])))

    cards = {}
    for f in sorted(CARD_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        cards[d.get("arxiv_id") or f.stem] = d

    recs = []
    for cid, d in cards.items():
        text = flatten({k: d.get(k) for k in POS_FIELDS if k in d})
        nc_text = flatten((d.get("threat_model") or {}).get("not_covered", []))
        r = {"id": cid, "title": (d.get("title") or "")[:100],
             "what_persists": (d.get("object") or {}).get("what_persists"),
             "scope": (d.get("object") or {}).get("scope"),
             "flags": set(d.get("quality_flags") or []),
             "n_results": len(d.get("results") or [])}
        for lvl in ("L1_strong", "L1_weak", "L2", "L3a", "L3b", "REG"):
            r[lvl] = scan(text, RULES[lvl])
        r["NC"] = scan(nc_text, RULES["NC"])
        r["candidate"] = bool(r["L1_strong"] or r["L1_weak"] or (r["L2"] and r["L3b"]) or r["L3b"] or r["REG"])
        r["bucket"] = "JUDGED" if cid in manual_ids else (triage(r)[0] if r["candidate"] else "NOT_CANDIDATE")
        r["bucket_reason"] = ("adjudicated in data/same_loop_matrix.json" if r["bucket"] == "JUDGED"
                             else (triage(r)[1] if r["bucket"] != "JUDGED" and r["candidate"] else None))
        r["flags"] = sorted(r["flags"])
        recs.append(r)

    def ids(pred):
        return [r["id"] for r in recs if pred(r)]

    buckets = {}
    for r in recs:
        buckets.setdefault(r["bucket"], []).append(r["id"])
    counts = {
        "corpus_n": len(recs),
        "candidate": len(ids(lambda r: r["candidate"])),
        "L1_strong": len(ids(lambda r: r["L1_strong"])),
        "L1_strong_or_weak": len(ids(lambda r: r["L1_strong"] or r["L1_weak"])),
        "L1_L2": len(ids(lambda r: (r["L1_strong"] or r["L1_weak"]) and r["L2"])),
        "REG": len(ids(lambda r: r["REG"])),
        "manual": len(buckets.get("MANUAL", [])),
    }
    out = {"generated_by": "code/screen_same_loop.py", "corpus_n": len(recs),
           "rules": {"L1_STRONG": L1_STRONG, "L1_WEAK": L1_WEAK, "L2": L2, "L3A": L3A, "L3B": L3B, "REG": REG, "NC_DISCLAIM": NC_DISCLAIM},
           "counts": counts, "buckets": {k: sorted(v) for k, v in sorted(buckets.items())}, "cards": recs}
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"corpus_n = {len(recs)}")
    for k, v in counts.items():
        print(f"  {k:18s} {v}")
    print("")
    print("buckets:")
    for k, v in out["buckets"].items():
        suffix = " (and more)" if len(v) > 8 else ""
        print(f"  {k:32s} {len(v):3d}  {' '.join(v[:8])}{suffix}")
    if args.verbose:
        print("MANUAL (candidates awaiting per-paper adjudication):")
        for r in recs:
            if r["bucket"] == "MANUAL":
                print(f"  {r['id']:14s} L1s={len(r['L1_strong'])} L1w={len(r['L1_weak'])} L2={len(r['L2'])} L3a={len(r['L3a'])} L3b={len(r['L3b'])} nc={len(r['NC'])}  {r['title'][:50]}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
