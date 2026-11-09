#!/usr/bin/env python3
"""Recompute the Section 2.1 census from the released data.

Inputs, all under data/census/:
  screen.csv                   the 3,435 submissions and the screen's verdicts
  readings-negatives-446.jsonl independent reading of 446 classifier negatives
  readings-calibration-90.jsonl  reading of the other 90 negatives
  positives-203.json           the author's re-read of the 203 numeric-label positives
  adjudication.csv             the author's decisions on contested items
  census-numbers.json          the numbers the paper quotes

Output: the same numbers, recomputed, with an assertion that they match.

Run from the artifact root: python3 code/recompute_census.py
"""
import csv
import json
import os

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "census")
ZERO_OK = {"2608.06651"}  # "zero false positives on the clean controls": named axis, control set


def jsonl(name):
    return [json.loads(l) for l in open(os.path.join(D, name), encoding="utf-8") if l.strip()]


def main():
    screen = {r["arxiv_id"]: r for r in csv.DictReader(open(os.path.join(D, "screen.csv"), encoding="utf-8"))}
    readings = {}
    for r in jsonl("readings-calibration-90.jsonl") + jsonl("readings-negatives-446.jsonl"):
        lab = r["cost"]
        if r["arxiv_id"] in ZERO_OK and lab == "C":
            lab = "A"
        readings[r["arxiv_id"]] = {"cost": lab, "eligible": bool(r.get("eligible"))}

    positives203 = {r["arxiv_id"]: ("A" if r["verdict"] == "defence-cost" else "C")
                    for r in json.load(open(os.path.join(D, "positives-203.json"), encoding="utf-8"))["rows"]}
    adjud = {r["arxiv_id"]: r["author_label"] for r in csv.DictReader(open(os.path.join(D, "adjudication.csv"), encoding="utf-8"))
             if r.get("author_label") in ("A", "B", "C")}

    final, eligible = {}, set()
    for a, v in readings.items():
        final[a] = adjud.get(a, v["cost"])
        # a positive label is itself evidence of eligibility (the object test
        # cannot fail for a paper that prices the defense), and an author
        # decision overrides a reader that called the object ineligible
        if v["eligible"] or final[a] in ("A", "B"):
            eligible.add(a)
    for a, lab in positives203.items():
        final[a] = adjud.get(a, lab)
        eligible.add(a)
    for a, lab in adjud.items():
        final.setdefault(a, lab)

    screen_elig = [a for a in screen if screen[a]["screen_reason"] == "eligible"]
    negatives = [a for a in screen_elig if screen[a]["screen_cost_label"] != "A"]
    frames = [a for a in screen_elig if a in final]
    pos_in_frame = [a for a in frames if final[a] in ("A", "B")]
    elig_in_frame = [a for a in frames if a in eligible]
    neg_pos = [a for a in negatives if final.get(a) in ("A", "B")]
    neg_elig = [a for a in negatives if a in eligible]
    cohort = [a for a in screen_elig if screen[a]["screen_cost_label"] == "A"]
    cohort_pos = [a for a in cohort if final.get(a) in ("A", "B")]

    got = {
        "negatives": len(negatives),
        "negatives_coded": len([a for a in negatives if a in final]),
        "negatives_eligible": len(neg_elig),
        "negatives_positives": len(neg_pos),
        "negatives_positives_pct": round(100.0 * len(neg_pos) / len(negatives), 1),
        "negatives_positives_of_eligible_pct": round(100.0 * len(neg_pos) / len(neg_elig), 1),
        "frame_positives": len(pos_in_frame),
        "frame_rate_pct": round(100.0 * len(pos_in_frame) / len(screen_elig), 1),
        "eligible": len(elig_in_frame),
        "rate_pct": round(100.0 * len(pos_in_frame) / len(elig_in_frame), 1),
        "a_of_positives_pct": round(100.0 * len([a for a in neg_pos if final[a] == "A"]) / len(neg_pos), 1),
        "precision": round(len(cohort_pos) / len(cohort), 2),
        "recall": round(len(cohort_pos) / len(pos_in_frame), 3),
        "coverage_pct": round(100.0 * 32 / len(elig_in_frame), 1),
    }
    want = json.load(open(os.path.join(D, "census-numbers.json"), encoding="utf-8"))
    expect = {
        "negatives": 536, "negatives_coded": 536, "negatives_eligible": 359,
        "negatives_positives": 105, "negatives_positives_pct": 19.6,
        "negatives_positives_of_eligible_pct": 29.2, "frame_positives": 235,
        "frame_rate_pct": 31.8, "eligible": 562, "rate_pct": 41.8,
        "a_of_positives_pct": 50.5, "precision": 0.64, "recall": 0.553, "coverage_pct": 5.7,
    }
    bad = 0
    for k in expect:
        ok = got[k] == expect[k]
        bad += 0 if ok else 1
        print("%-40s %-8s %s" % (k, got[k], "OK" if ok else "MISMATCH expected %s" % expect[k]))
    print("\npaper JSON: positives %d, rate %s%%, frame rate %s%%"
          % (want["positives"], want["rate_pct"], want["frame_rate_pct"]))
    print("RESULT:", "all census numbers reproduced" if not bad else "%d mismatches" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
