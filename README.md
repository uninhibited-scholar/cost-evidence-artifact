# Artifact: Cost Evidence in Self-Evolving Agent Defenses Is Reported but Not Commensurable

This artifact accompanies the SoK submission *"Cost Evidence in Self-Evolving
Agent Defenses Is Reported but Not Commensurable"*. It contains the per-paper
evidence records behind every count in the paper, the four-class cost
adjudication, the same-loop adjudication matrix, the coding protocols, and the
scripts that recompute each headline number. Everything runs on Python 3.9+
standard library only; matplotlib is optional and used only by the four figure
scripts. The only script that touches the network is `code/fetch_source.py`,
which you invoke yourself to fetch a cited paper from arXiv.

## 1. Layout

| Path | Contents |
|---|---|
| `data/cards/<id>.json` | 129 evidence cards, one JSON per paper (schema: `protocol/SPEC.md`) |
| `data/cost_tags.json` | **the authoritative per-card cost adjudication**; `cards_total=129`; its C1-C4 main counts are 34/26/19/21 with 133 evidence entries |
| `data/cost_tags_rules.md` | the four-class rule set the counts depend on |
| `data/cost_tags_adjudication.json` | the human adjudication table (class assignments + per-card exclusion reasons) |
| `data/cost_tags_summary.md` | summary counts and registered corrections |
| `data/cost_tags_quote_exceptions.json` | documented exceptions to the evidence-quote verbatim check (15 of 133; see Section 3) |
| `data/human-audit-20.csv` | the author's 80 four-class labels on the 20-card audit, beside the model labels and the per-label agreement (61/80, kappa 0.44) |
| `data/same_loop_matrix.json` | per-paper same-loop (L1/L2/L3) adjudications, protocol v3 |
| `data/same_loop_scan.json` | the mechanical regex screen that feeds those adjudications |
| `data/registry.json` | the 1,184-record retrieval registry |
| `data/screening/` | the two independent coder sheets for the 606-record abstract screen (three binary conditions per record: object, mechanism, security property) |
| `data/reader-panel/` | the three-reader panel behind Section 2.3: 15 coding sheets (three readers x five shards, four classes each with the quote the label rests on), the windowed text each reader saw, and `panel-harmonized.json`; `code/recompute_panel.py` reproduces 63 priced cards, 47 both, precision 0.758 / recall 0.746, and the harmonized row 59 / 44 / 0.746 / 0.698 |
| `data/pair-funnel.csv` | the Section 7.4 pair screen: all 30 card pairs that survive the automated stages, the term each fails on, and the registered cost quotes on both sides; `data/pair-author-review.jsonl` `data/pair-author-review-30.jsonl` holds the author's verdict on all 30 pairs (23 terms confirmed, 7 changed, with a reason for each) and `data/pair-author-review.jsonl` the earlier notes on the three closest; `code/build_pair_funnel.py` rebuilds the table from `data/cards/` and `data/pair-verdicts.json` (8,256 pairs, 110 sharing a benchmark, 54 with a numeric cost on both sides, 30 read, none matching all three terms) |
| `data/census/` | the Section 2.1 frame census: the 3,435-record screen, two independent readings of the 536 classifier negatives, the author's re-read of the 203 numeric-label positives, the adjudication table with reasons, the frozen codebook, and the numbers the paper quotes; `ids.csv` lists the 3,435 identifiers with announcement month (abstracts are not redistributed, refetch them by id with `code/fetch_source.py`); `zcode/` holds the second coder's per-record verdicts described in Appendix A (`code/zcode_agreement.py`) |
| `data/registry_reconciliation.md` | registry-to-cards reconciliation (historical record; see its status banner) |
| `data/tables_final.md` | the three summary tables, regenerated from the 129 cards |
| `data/legacy/` | CSV/JSONL exports of the card corpus - redundant with `data/cards/`; not needed for any recomputation |
| `code/` | recomputation and verification scripts (this is the entry point) |
| `protocol/` | card schema, blind-coding protocol, and coding codebook |

## 2. Recompute every headline count

Run from the artifact root. One command reproduces everything:

```
python3 code/recompute_counts.py
```

Expected: `54/54 checks match the paper. ALL MAIN COUNTS REPRODUCED.` It prints
every count below and asserts it. Individual numbers can also be reproduced or
cross-checked with the scripts in the right-hand column.

Four checks are separate because they read different inputs, and each exits
non-zero on mismatch: `code/check_example_math.py` (the worked-example
arithmetic of the appendix), `code/recompute_panel.py` (the Section 2.3 reader
panel, unharmonized and harmonized), `code/build_pair_funnel.py` (the
Section 7.4 pair screen), `code/recompute_census.py` (the Section 2.1 frame
census) and `code/zcode_agreement.py` (the second-coder screen of Appendix A,
726 eligible against 739, 83.8% agreement, kappa 0.52).

| Paper count | Expected output | Command |
|---|---|---|
| corpus: 129 cards, 1,086 results, 676 (62.2%) with explicit denominators, 48/129 flagged `denominator_unclear` | section A of the recompute output | `python3 code/recompute_counts.py` (or `python3 code/checks/verify_deliverables.py`) |
| C1 utility loss 34/129, C2 latency & compute 26/129, C3 false positives & collateral 19/129, C4 revocability 21/129 | section B | `python3 code/recompute_counts.py` |
| cards that price a defense 66/129 (62 numeric + 4 qualitative-only); union counting revocation-success ratios 75/129 (70 + 5), of which 9 cards appear only in C4 | section B | `python3 code/recompute_counts.py` |
| 133 cost readings; unit families: relative 78, wall-clock 12, tokens 6, memory 2; money 2, energy 0, GPU-hours 0; 40 readings with no unit; 75 reading-bearing cards; 59 unit-bearing; 12 in two or more families | section C | `python3 code/recompute_counts.py` |
| 350-cell matrix; unique empty cell repair x formal guarantees; two single-evidence cells | section D | `python3 code/recompute_counts.py` (full matrix: `python3 code/fig2_matrix.py`) |
| per-layer cost-reporting rates (C1-C3): execution-time gating 7/8, provenance tracing 13/18, content filtering 13/32, formal guarantees 1/4; on the wider union definition 7/8, 14/18, 16/32, 2/4 | section E | `python3 code/recompute_counts.py` (per-layer chart: `python3 code/fig3_cost.py`) |
| same-loop co-evolution: strict 2/129 in persistent state + 4/129 in weight space; compute bill 0/4 among the four deployment-stage evolution cards | section F | `python3 code/recompute_counts.py`; internal consistency of the record: `python3 code/build_same_loop_matrix.py` |
| verbatim quotes: 118 of 133 evidence quotes verbatim in their card result; 15 documented exceptions | `OK: every evidence quote is either verbatim ... or a documented exception.` | `python3 code/verify_quotes.py` |
| card schema integrity | per-card pass/fail summary | `python3 code/verify_quotes.py --cards` |
| inter-coder screen: 606 records, 21.9% / 26.6% eligible, Po 0.878, kappa 0.669, PPA 0.748, NPA 0.919, PABAK 0.756 | `RESULT: all screening figures match the paper.` | `python3 code/verify_screening.py` |
| package self-check (files + counts + parse) | `RESULT: nn/nn checks passed.` | `python3 code/checks/verify_deliverables.py` |
| figures 1-4 (PDF+PNG, optional matplotlib) | console counts + written files | `python3 code/fig1_lifecycle.py` ... `python3 code/fig4_audit.py` |
| fetch a cited paper for quote spot-checks (network; you invoke it) | saved PDF/e-print under `fetch/` | `python3 code/fetch_source.py <arxiv-id> [--source]` |

### The frame census (Section 2.1)

```
python3 code/recompute_census.py
```

Expected: `RESULT: all census numbers reproduced` (14 checks). The census asks a
different question from the rest of the artifact: not what the 129 cards report,
but what share of the eligible literature reports a cost at all, measured on the
three announcement months 2026-08 to 2026-10.

| Quantity | Value | File |
|---|---|---|
| submissions screened | 3,435 | `data/census/screen.csv` |
| screen calls eligible | 739 (21.5%) | `data/census/screen.csv` |
| classifier numeric label among them | 203 (27.5%) | `data/census/screen.csv` |
| classifier negatives | 536 | derived: eligible minus the 203 |
| negatives read for the cost question | 536 of 536 | `readings-negatives-446.jsonl`, `readings-calibration-90.jsonl` |
| negatives passing the three conditions | 359 (67.0%) | recomputed |
| negatives naming a cost | 105 (19.6%; 29.2% of the 359) | recomputed |
| positives naming a cost | 130 of 203 (64.0%) | `positives-203.json` |
| total naming a cost, screen frame | 235 of 739 (31.8%) | recomputed |
| total naming a cost, re-read frame | 235 of 562 (41.8%) | recomputed |
| classifier precision / recall | 0.64 / 0.55 | recomputed |
| second coder, eligible | 726 against our 739 (83.8% agreement, kappa 0.52) | `python3 code/zcode_agreement.py` |
| second coder, numeral label | 158 of its 726 (21.8%) against 203 of 739 (27.5%) | `python3 code/zcode_agreement.py` |
| coverage of the re-read frame | 32 of 562 (5.7%) | recomputed |

Three things a reader should know before using these numbers.

1. **The screen is a filter, not a frame.** A second look at the 536 negatives
   finds 177 failing the same three conditions, mostly on the object test. The
   paper reports the screen count as the filter and the re-read count as the
   frame, never one in place of the other.
2. **Nothing is extrapolated.** The earlier version of this analysis drew 90
   negatives at random and scaled the rate to 536; the current one reads all 536.
   There is no sampling interval because there is no sample.
3. **A zero is a reading only when the paper shows it looked.** "Zero false
   positives on 48 clean models" is A/C3 (named axis, stated denominator);
   "these bindings block with zero false positives" is C. The full rule and five
   worked cases are in `data/census/codebook-v10.md` and the method note.

## 3. Caliber notes (read before comparing with the paper)

1. **Matrix row/column breakdown.** This artifact recomputes the current
   129-card corpus: 350 occupied cells, rows
   formation 81 / update 67 / retention 72 / retrieval 78 / revocation 31 /
   repair 21, columns content 96 / provenance 63 / execution 16 /
   architecture 161 / formal 14. The paper's Table 2 grand-total cell and text
   say 350 and its unique empty cell (repair x formal guarantees) and two
   single-evidence cells match this recomputation exactly; the per-row /
   per-column cells printed in the paper's table body still show the earlier
   pre-final-caliber breakdown (whose cells sum to 341) and are being corrected
   to the values printed here.
2. **Cards with a five-layer defense claim.** 103 of the 129 cards carry a
   mechanism layer inside the five defense layers; the excluded 26 are 13
   `none`, 4 weight-space, 3 evaluation, 3 prompt, 2 memory, 1 mixed.
3. **Quote exceptions.** 118 of the 133 evidence entries verify verbatim
   against the card result they point to. The 15 exceptions are itemized with
   reasons in `data/cost_tags_quote_exceptions.json`: 8 carry quotes
   registered from pre-revision card texts (the quotes themselves are verbatim
   from the source papers), 1 is a stale pointer whose quote matches the current
   card at a shifted index, 1 is the C4-from-19-to-20 addition registered
   without a card anchor, and 5 are additions made in the 2026-11-07 fold whose
   quote is a different, also verbatim, sentence of the same paper than the
   result entry points at. Every one of the 15 still has `has=true` on its card,
   so no count changes. Two earlier exceptions were resolved on 2026-11-02 by
   re-deriving the evidence quote from the version of record and syncing the
   card to it; they are kept in the same file under `resolved_20261102`.
   Separately from this internal check, all 133 quotes were verified against the
   full text of their own paper in the working repository (a coverage test and a
   numeric-token test per quote; 133/133 pass). That check is not shipped here
   because it needs the paper texts, which this artifact does not redistribute.
4. **`data/legacy/`.** These CSV/JSONL exports contain the same 129 cards as
   `data/cards/`. They are redundant with `data/cards/` and are not an input to
   any recomputation in this artifact; do not cite counts from them.

5. **129 cards, 75 reading-bearing cards, 133 readings.** Three different
   counts that are easy to confuse:

   | Count | What it counts |
   |---|---|
   | 129 | papers in the corpus |
   | 75 | papers with at least one cost reading (70 numeric + 5 qualitative-only) |
   | 133 | evidence entries on those 75 papers |

   The 133 are not papers. They distribute over the 75 cards as 38 cards with
   one entry, 21 with two, 13 with three, 1 with four, and 2 with five. The
   other 54 cards carry no evidence entry at all (53 price nothing in any class
   and one reports only what it cost to build the defense): the gap is 129
   minus 75, not 129 minus 133, and the two quantities are never supposed to
   coincide.

   One trap: **53 appears twice in this dataset with two different meanings.**
   53 cards report no cost reading of any kind, and, separately, 53 of the 105
   cost readings are purely relative quantities with no absolute family. The two
   53s are different sets and they are not complements. When quoting 53, say
   which one is meant.

   75 is the union over all four classes. The paper's headline count is **66**:
   the cards that report a cost a defense imposes, i.e. a C1-C3 reading. The
   other 9 appear only in C4, which records whether revocation succeeded, not
   what it cost. 66 is not a new label: it is recomputed from the same four
   per-class adjudications, and section B of the recompute prints both numbers.

## 4. What is NOT included, and why

- **No paper full texts.** arXiv licenses differ per paper and the default
  license does not permit redistribution. Every claim in the cards carries a
  verbatim quote, a section/table locator, and the version that was read;
  `code/fetch_source.py` retrieves a cited paper on demand for spot checks.
- **No internal working documents.** Task instructions, work logs, handoff
  notes, editing ledgers, and reviewer-response drafts are workflow records,
  not evidence, and are excluded.
- **No credential-bearing or vendor-specific scripts.** No API keys exist in
  this artifact; no model-provider-specific invocation scripts are shipped -
  the coding protocols are documented in `protocol/` instead.
- **No identity information.** No author names, affiliations, emails, or
  funding acknowledgments are present anywhere in this artifact.
- **No per-card cost-coding sheets of the second coder.** The second-coder
  reliability summary is quoted in the paper; the blind sheets themselves are
  internal QA records.

## 5. Notes on data language

The evidence cards and adjudication records were produced by a coding team
whose working language left annotation strings (claims, settings, limitation
notes, one-line adjudication reasons) in that language. These annotation
fields are shipped as-is; the verbatim `quote` fields are in the source
papers' language (overwhelmingly English), and every count recomputes
identically regardless of annotation language. Fully translated variants can be
made available on request.
