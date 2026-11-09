#!/usr/bin/env python3
"""Recompute every number in the worked example of the appendix.

The example is deliberately small enough that a reviewer can check it by hand;
this script does that check mechanically. Each expected value is the number the
paper prints; the script recomputes it from the stated parameters and fails if
the two disagree.

Run: python3 code/check_example_math.py
"""
# parameters, all stated in the appendix
rho = 0.994      # share of attack loss removed, taken equal to the reported recall
s = 1.0          # undefended success probability, assumed
L = 3600.0       # seconds lost per successful attack, assumed (one analyst-hour)
f = 60.0         # seconds lost per false block, assumed
kappa = 1 / 3600 # one second of defence compute in analyst-seconds
c1 = 0.35        # running cost per request, case 1 (s)
C1 = 876.0       # one-time build, case 1 (s): 14.6 minutes
p1 = 0.00012     # assumed attack rate per request, case 1: 0.012%
q1 = 0.026       # observed false-positive rate, case 1
VH_small = 7e3
VH_large = 3.65e5

C2 = 7296 * 3600.0  # 7,296 GPU-hours in seconds of compute (case 2)
q2 = 0.001
c2 = 0.0
p2 = 0.00010     # assumed attack rate per request, case 2: 0.010%

checks = []

def check(name, got, want, tol=0.02):
    ok = abs(got - want) <= tol * max(abs(want), 1e-9)
    checks.append(ok)
    print("%-42s %12.6g  expected %-10s %s" % (name, got, want, "OK" if ok else "MISMATCH"))

# case 1
check("false-positive term (1-p)qf", (1 - p1) * q1 * f, 1.56)
check("running term kappa*c", kappa * c1, 0.0001, tol=0.05)  # printed rounded to one significant figure
check("build term at VH=7e3", kappa * C1 / VH_small, 0.000035)
check("benefit p*rho*s*L", p1 * rho * s * L, 0.43)
check("break-even rate p*", (1 - p1) * q1 * f / (rho * s * L), 0.000436)

# case 2
kC2 = kappa * C2
check("build in analyst-seconds, case 2", kC2, 7296.0, tol=0.001)
tot_small = kC2 / VH_small + (1 - p2) * q2 * f + kappa * c2
tot_large = kC2 / VH_large + (1 - p2) * q2 * f + kappa * c2
check("per-request cost at VH=7e3", tot_small, 1.10)
check("per-request cost at VH=3.65e5", tot_large, 0.08)
check("break-even at one week", tot_small / (rho * s * L), 0.00031)
check("break-even at one year", tot_large / (rho * s * L), 0.000022)

# the verdicts the text claims
check("weekly verdict (cost > benefit)", tot_small / (rho * s * L) > p2, 1)
check("yearly verdict (benefit > cost)", p2 > tot_large / (rho * s * L), 1)
check("case 1 does not pay", p1 * rho * s * L < (1 - p1) * q1 * f, 1)

print("\nRESULT:", "all example numbers reproduce" if all(checks) else "MISMATCH")
raise SystemExit(0 if all(checks) else 1)
