#!/usr/bin/env python3
"""Recompute the inter-coder screen of Appendix A from the released data.

Inputs, all under data/census/:
  screen.csv          the 3,435 submissions and our screen's verdicts
  zcode/batch-*.jsonl the second coder's verdicts, 86 batches of 40 (the last 35)

Output: the same numbers the appendix quotes, recomputed, with an assertion.

Run from the artifact root: python3 code/zcode_agreement.py
"""
import csv
import glob
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(HERE, "data", "census")

WANT = {
    "n": 3435,
    "both": 454, "zcode_only": 272, "ours_only": 285, "neither": 2424,
    "agree": 2878, "zcode_eligible": 726, "ours_eligible": 739,
    "zcode_numeral": 158, "ours_numeral": 203,
}


def main():
    rows = list(csv.DictReader(open(os.path.join(D, "screen.csv"))))
    z = {}
    for f in sorted(glob.glob(os.path.join(D, "zcode", "batch-*.jsonl"))):
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            z[o["arxiv_id"]] = o

    tab = Counter()
    numeral = Counter()
    for r in rows:
        ours = r["screen_reason"] == "eligible"
        theirs = z[r["arxiv_id"]].get("eligible") is True
        tab[(ours, theirs)] += 1
        if ours and theirs:
            numeral[(r["screen_cost_label"] == "A", z[r["arxiv_id"]].get("cost") == "A")] += 1

    n = sum(tab.values())
    both, zcode_only = tab[(True, True)], tab[(False, True)]
    ours_only, neither = tab[(True, False)], tab[(False, False)]
    agree = both + neither
    po = agree / n
    pe = ((both + zcode_only) * (both + ours_only)
          + (ours_only + neither) * (zcode_only + neither)) / (n * n)
    kappa = (po - pe) / (1 - pe)

    got = {
        "n": n, "both": both, "zcode_only": zcode_only,
        "ours_only": ours_only, "neither": neither, "agree": agree,
        "zcode_eligible": both + zcode_only, "ours_eligible": both + ours_only,
        "zcode_numeral": sum(1 for o in z.values() if o.get("cost") == "A"),
        "ours_numeral": sum(1 for r in rows
                            if r["screen_reason"] == "eligible" and r["screen_cost_label"] == "A"),
    }

    print("%-16s %8s %8s" % ("metric", "value", "paper"))
    for k in WANT:
        print("%-16s %8d %8d%s" % (k, got[k], WANT[k], "" if got[k] == WANT[k] else "   <-- MISMATCH"))
    print("%-16s %7.1f%% %8s" % ("agreement", 100 * po, "83.8%"))
    print("%-16s %8.3f %8s" % ("kappa", kappa, "0.52"))
    print("numeral, both eligible: both %d, second coder only %d, we only %d, neither %d"
          % (numeral[(True, True)], numeral[(False, True)], numeral[(True, False)], numeral[(False, False)]))

    bad = [k for k in WANT if got[k] != WANT[k]]
    if bad or abs(100 * po - 83.8) > 0.05 or abs(kappa - 0.52) > 0.005:
        raise SystemExit("MISMATCH: %s" % ", ".join(bad or ["agreement/kappa"]))
    print("RESULT: all %d pinned values plus agreement and kappa match. OK" % len(WANT))


if __name__ == "__main__":
    main()
