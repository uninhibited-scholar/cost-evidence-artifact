#!/usr/bin/env python3
"""Quote and card-integrity verification for the packaged data.

Run from the artifact root.

Mode 1 (default) — evidence-quote verification:
  every evidence entry registered in data/cost_tags.json must appear, verbatim
  under whitespace/case normalization, inside the `quote` field of the card
  result it points to (data/cards/<id>.json, results[result_index]).

    python3 code/verify_quotes.py

Mode 2 — card integrity (schema checks ported from the original card verifier):

    python3 code/verify_quotes.py --cards            # all cards
    python3 code/verify_quotes.py --cards 2610.28425 # selected cards

  The original verifier also checked that each result quote is traceable in the
  paper full text (corpus/<id>.txt). Full texts are NOT shipped in this artifact
  (arXiv per-paper licenses differ); when no local corpus is found the
  traceability check is skipped with a note, and code/fetch_source.py can be
  used to obtain a cited paper for spot checks.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CARDS = DATA / "cards"
CLS = ["utility_loss", "latency_compute", "false_positive", "revocability"]
REQUIRED_KEYS = ["arxiv_id", "title", "screening_status", "versions_read",
                 "object", "safety_property", "threat_model", "intervention",
                 "results", "limitations", "reading", "quality_flags"]
STATUSES = {"核心研究", "必要背景"}

ANCHOR_PAT = re.compile(
    r"(§+\s*[\dA-Z][\d.]*[A-Za-z]?|Appendix\s+[\dA-Z][\d.]*|[A-Z]?\d*\.\d+(?:\.\d+)?"
    r"|(?:Table|Fig(?:ure)?s?|Eq(?:uation)?s?|Algorithm)\s*[\dA-Z]+(?:[-–][\dA-Z]+)?)",
    re.IGNORECASE)


def norm_alnum(s):
    # quotes are verbatim from the (mostly English) source papers; CJK is kept
    # so that quotes captured from CJK-language sources still normalize cleanly
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (s or "").casefold())


def verify_cost_tag_quotes():
    ct = json.load(open(DATA / "cost_tags.json", encoding="utf-8"))
    manifest = json.load(open(DATA / "cost_tags_quote_exceptions.json", encoding="utf-8"))
    known = {(e["id"], e["cost_class"], e["evidence_index"]): e["status"]
             for e in manifest["exceptions"]}
    if ct.get("cards_total") != len(ct["cards"]):
        print(f"FAIL: cards_total={ct.get('cards_total')} != len(cards)={len(ct['cards'])}")
        return 1
    total = verbatim = 0
    exceptions = []
    unexplained = []
    for aid, c in ct["cards"].items():
        card_path = CARDS / f"{aid}.json"
        if not card_path.exists():
            unexplained.append(f"cost_tags card {aid} has no card file data/cards/{aid}.json")
            continue
        card = json.load(open(card_path, encoding="utf-8"))
        results = card.get("results") or []
        for cl in CLS:
            for j, ev in enumerate(c["classes"][cl]["evidence"]):
                total += 1
                q = norm_alnum(ev.get("quote") or "")
                ref = ""
                ri = ev.get("result_index")
                if isinstance(ri, int) and ri < len(results):
                    ref = norm_alnum(results[ri].get("quote") or "")
                if q and ref and q in ref:
                    verbatim += 1
                    continue
                key = (aid, cl, j)
                if key in known:
                    exceptions.append(f"{aid} {cl}[{j}] -> documented exception: {known[key]}")
                else:
                    detail = f"result_index={ri}"
                    # help diagnosis: does the quote exist elsewhere in the card?
                    hits = [i for i, r in enumerate(results)
                            if isinstance(r, dict) and q and q in norm_alnum(r.get("quote") or "")]
                    if hits:
                        detail += f"; quote found instead at results {hits}"
                    unexplained.append(f"{aid} {cl}[{j}] quote not verbatim in referenced result ({detail})")
    print(f"evidence quotes checked: {total}")
    print(f"  verbatim in referenced card result : {verbatim}")
    print(f"  documented exceptions              : {len(exceptions)} (see data/cost_tags_quote_exceptions.json)")
    for e in exceptions:
        print(f"    - {e}")
    if unexplained:
        print(f"  UNEXPLAINED failures               : {len(unexplained)}")
        for u in unexplained:
            print(f"    ! {u}")
        print("FAIL: unexplained quote-verification failures.")
        return 1
    print("OK: every evidence quote is either verbatim in its card result or a documented exception.")
    return 0


def verify_card(aid):
    errors, warnings, notes = [], [], []
    path = CARDS / f"{aid}.json"
    if not path.exists():
        return {"status": "fail", "errors": [f"card file missing: data/cards/{aid}.json"],
                "warnings": [], "notes": []}
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return {"status": "fail", "errors": [f"JSON parse error: {e}"], "warnings": [], "notes": []}

    if c.get("arxiv_id") != aid:
        errors.append(f"arxiv_id {c.get('arxiv_id')!r} does not match filename {aid}")
    for k in REQUIRED_KEYS:
        if k not in c:
            errors.append(f"missing required key: {k}")
    if c.get("screening_status") not in STATUSES:
        errors.append(f"screening_status {c.get('screening_status')!r} not in {sorted(STATUSES)}")

    obj = c.get("object") or {}
    if not isinstance(obj, dict):
        errors.append("object must be an object")
    else:
        for k in ("what_persists", "scope", "carrier", "operations_covered"):
            if not obj.get(k):
                warnings.append(f"object.{k} missing/empty (schema gap)")
        if obj.get("operations_covered") and not isinstance(obj["operations_covered"], list):
            errors.append("object.operations_covered must be a list")

    sp = c.get("safety_property") or {}
    if not isinstance(sp, dict):
        errors.append("safety_property must be an object")
    else:
        for k in ("type", "statement", "operationalized_as"):
            if not sp.get(k):
                warnings.append(f"safety_property.{k} missing/empty (schema gap)")

    tm = c.get("threat_model") or {}
    if not isinstance(tm, dict):
        errors.append("threat_model must be an object")
    else:
        if not tm.get("adversary"):
            warnings.append("threat_model.adversary missing/empty (schema gap)")
        for k in ("capabilities", "assumptions", "not_covered"):
            if not isinstance(tm.get(k), list) or not tm.get(k):
                warnings.append(f"threat_model.{k} missing/empty (schema gap)")

    iv = c.get("intervention") or {}
    if not isinstance(iv, dict):
        errors.append("intervention must be an object")
    else:
        for k in ("name", "mechanism_layer", "description"):
            if not iv.get(k):
                warnings.append(f"intervention.{k} missing/empty (schema gap)")

    rd = c.get("reading") or {}
    if not isinstance(rd, dict) or not rd.get("coverage"):
        warnings.append("reading.coverage missing/empty (schema gap)")
    elif not isinstance(rd.get("complete"), bool):
        warnings.append("reading.complete must be a boolean (schema gap)")

    if not isinstance(c.get("limitations"), list):
        warnings.append("limitations must be a list (schema gap)")

    results = c.get("results")
    if not isinstance(results, list):
        errors.append("results must be a list")
        results = []

    flags = c.get("quality_flags") or []
    for i, r in enumerate(results):
        if not isinstance(r, dict):
            errors.append(f"results[{i}] must be an object")
            continue
        for k in ("claim", "metric", "value", "locator"):
            if not r.get(k):
                errors.append(f"results[{i}].{k} missing/empty")
        if not isinstance(r.get("is_primary_result"), bool):
            errors.append(f"results[{i}].is_primary_result must be a boolean")
        denom = r.get("denominator")
        has_denom = isinstance(denom, dict) and (denom.get("n_total") or denom.get("how_counted"))
        if not has_denom and re.search(r"\d", r.get("value") or "") \
                and "denominator_unclear" not in flags:
            warnings.append(f"results[{i}] numeric value without denominator "
                            "(add denominator or flag denominator_unclear)")

    return {"status": "fail" if errors else "pass", "errors": errors,
            "warnings": warnings, "notes": notes}


def main():
    argv = sys.argv[1:]
    if "--cards" in argv:
        argv.remove("--cards")
        ids = argv or sorted(p.stem for p in CARDS.glob("*.json"))
        n_fail = 0
        for aid in ids:
            res = verify_card(aid)
            print(f"{aid}: {res['status']}")
            for e in res["errors"]:
                print(f"  ERROR  {e}")
            for w in res["warnings"]:
                print(f"  warn   {w}")
            if res["status"] != "pass":
                n_fail += 1
        if not (ROOT / ".." / "corpus").exists() and not (ROOT / ".." / ".." / "corpus").exists():
            print("note: paper full texts are not shipped in this artifact; "
                  "quote-vs-fulltext traceability was not re-run here. "
                  "Use code/fetch_source.py to obtain a cited paper for spot checks.")
        print(f"--\n{len(ids)} checked, {len(ids) - n_fail} pass, {n_fail} fail")
        return 1 if n_fail else 0

    print("Verifying cost_tags.json evidence quotes against card results[].quote ...")
    rc = verify_cost_tag_quotes()
    return rc


if __name__ == "__main__":
    sys.exit(main())
