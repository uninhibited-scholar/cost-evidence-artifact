#!/usr/bin/env python3
"""Inter-coder agreement on the 606-record abstract screen (Section 2.1).

    python3 code/verify_screening.py

Two independent coders, different model families and vendors, byte-identical
prompt, no shared context, screened the same 606 records against the three
card-building conditions at the abstract level. Each record carries three
binary conditions (E1 object, E2 mechanism, E3 security property); a record
counts as eligible only when all three hold.

Reported in the paper: 21.9% and 26.6% eligible, 110 records both-eligible,
74 disagreements, Po 0.878, kappa 0.669, PPA 0.748, NPA 0.919, PABAK 0.756.
Positive and negative agreement use the conventional two-direction form,
PPA = 2a/(n_A + n_B), NPA = 2d/((n - n_A) + (n - n_B)); the one-directional
figures (what share of one coder's calls the other reproduces) are 0.827 and
0.892 and are NOT what the paper reports.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "data" / "screening"
CODER_A = SCREEN / "CENSUS-XFYUN2-CLEAN.csv"
CODER_B = SCREEN / "CENSUS-V2-ELIG.csv"

EXPECTED = dict(n=606, a=161, b=133, both=110, disagree=74,
                po=0.878, kappa=0.669, ppa=0.748, npa=0.919, pabak=0.756)


def load(path):
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                cond = [int(row.get(k) or 0) for k in ("E1", "E2", "E3")]
            except ValueError:
                continue
            out[row["work_id"]] = all(cond)
    return out


def main():
    a, b = load(CODER_A), load(CODER_B)
    keys = sorted(set(a) & set(b))
    n = len(keys)
    n_a = sum(1 for k in keys if a[k])
    n_b = sum(1 for k in keys if b[k])
    both = sum(1 for k in keys if a[k] and b[k])
    neither = n - n_a - n_b + both
    po = (both + neither) / n
    pa, pb = n_a / n, n_b / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe)
    ppa = 2 * both / (n_a + n_b)
    npa = 2 * neither / ((n - n_a) + (n - n_b))
    pabak = 2 * po - 1

    print(f"records screened            : {n}")
    print(f"coder A eligible            : {n_a} ({100*pa:.1f}%)")
    print(f"coder B eligible            : {n_b} ({100*pb:.1f}%)")
    print(f"both eligible               : {both}")
    print(f"disagreements               : {n_a + n_b - 2*both}")
    print(f"observed agreement (Po)     : {po:.3f}")
    print(f"chance-corrected (kappa)    : {kappa:.3f}")
    print(f"positive agreement (PPA)    : {ppa:.3f}")
    print(f"negative agreement (NPA)    : {npa:.3f}")
    print(f"prevalence-adjusted (PABAK) : {pabak:.3f}")

    got = dict(n=n, a=n_a, b=n_b, both=both, disagree=n_a + n_b - 2 * both,
               po=round(po, 3), kappa=round(kappa, 3), ppa=round(ppa, 3),
               npa=round(npa, 3), pabak=round(pabak, 3))
    bad = {k: (got[k], EXPECTED[k]) for k in EXPECTED if got[k] != EXPECTED[k]}
    if bad:
        print()
        for k, (g, e) in bad.items():
            print(f"  [FAIL] {k}: got {g}, expected {e}")
        print("RESULT: mismatch")
        return 1
    print()
    print("RESULT: all screening figures match the paper.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
