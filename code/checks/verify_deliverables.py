#!/usr/bin/env python3
"""Package-integrity check for this artifact.

    python3 code/checks/verify_deliverables.py

Verifies that every file this artifact promises is present and well-formed:
  1. all data files parse as JSON / are non-empty
  2. data/cards has 129 card files; data/cost_tags.json has cards_total=129 and
     the same card id set as data/cards
  3. data/registry.json holds 1,184 records
  4. the headline counts recompute (runs the same checks as
     code/recompute_counts.py in-process)
  5. every code script parses as Python 3
  6. README.md and BUILD-REPORT.md exist
Exit code 0 only if every check passes.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

REQUIRED_DATA = [
    "cost_tags.json", "cost_tags_adjudication.json", "cost_tags_quote_exceptions.json",
    "same_loop_matrix.json", "same_loop_scan.json", "registry.json",
    "tables_final.md", "legacy/cards.csv", "legacy/cards.jsonl",
]
REQUIRED_CODE = [
    "recompute_counts.py", "verify_quotes.py", "fetch_source.py", "screen_same_loop.py",
    "build_same_loop_matrix.py", "build_tables_final.py",
    "fig1_lifecycle.py", "fig2_matrix.py", "fig3_cost.py", "fig4_audit.py",
    "checks/verify_deliverables.py", "checks/audit_draft.py",
]
REQUIRED_DOCS = ["README.md", "BUILD-REPORT.md"]
REQUIRED_PROTOCOL = ["SPEC.md", "FIELD-SAMPLE-PROTOCOL.md", "CODEBOOK.md"]


def main():
    ok = 0
    total = 0

    def chk(label, cond):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print(f"  [{'OK ' if cond else 'FAIL'}] {label}")

    print("== files ==")
    for rel in REQUIRED_DATA:
        chk(f"data/{rel}", (DATA / rel).is_file() and (DATA / rel).stat().st_size > 0)
    for rel in REQUIRED_DOCS:
        chk(rel, (ROOT / rel).is_file() and (ROOT / rel).stat().st_size > 0)
    for rel in ["cost_tags_rules.md", "cost_tags_summary.md", "registry_reconciliation.md"]:
        chk(f"data/{rel}", (DATA / rel).is_file() and (DATA / rel).stat().st_size > 0)
    for rel in REQUIRED_PROTOCOL:
        chk(f"protocol/{rel}", (ROOT / "protocol" / rel).is_file())
    n_cards = len(list((DATA / "cards").glob("*.json")))
    chk(f"data/cards/*.json (expect 129)", n_cards == 129)
    for rel in REQUIRED_CODE:
        chk(f"code/{rel}", (ROOT / "code" / rel).is_file())

    print("== data well-formedness ==")
    try:
        ct = json.loads((DATA / "cost_tags.json").read_text(encoding="utf-8"))
        chk("cost_tags.json parses; cards_total=129", ct.get("cards_total") == 129)
        card_ids = {p.stem for p in (DATA / "cards").glob("*.json")}
        chk("cost_tags card ids == card files", set(ct["cards"].keys()) == card_ids)
    except Exception as e:
        chk(f"cost_tags.json parses ({e})", False)
    try:
        reg = json.loads((DATA / "registry.json").read_text(encoding="utf-8"))
        chk("registry.json parses; 1,184 records", isinstance(reg, list) and len(reg) == 1184)
    except Exception as e:
        chk(f"registry.json parses ({e})", False)
    for name in ["same_loop_matrix.json", "same_loop_scan.json",
                 "cost_tags_adjudication.json", "cost_tags_quote_exceptions.json"]:
        try:
            json.loads((DATA / name).read_text(encoding="utf-8"))
            chk(f"{name} parses", True)
        except Exception as e:
            chk(f"{name} parses ({e})", False)

    print("== code parses ==")
    for rel in REQUIRED_CODE:
        try:
            ast.parse((ROOT / "code" / rel).read_text(encoding="utf-8"))
            chk(f"code/{rel} is valid Python", True)
        except Exception as e:
            chk(f"code/{rel} is valid Python ({e})", False)

    print("== headline counts ==")
    sys.path.insert(0, str(ROOT / "code"))
    buf = __import__("io").StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = __import__("recompute_counts").main()
    finally:
        sys.stdout = old
    chk(f"recompute_counts.py passes all paper-count assertions (exit {rc})", rc == 0)

    print(f"\nRESULT: {ok}/{total} checks passed.")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
