# Registry-to-cards reconciliation (HISTORICAL RECORD)

**Status banner - read first.** This document records a reconciliation exercise
performed on 2026-10-29, when the corpus stood at 117 cards (109 registry-backed
+ 8 backfills). The final corpus is **129 cards** (12 further backfills added
after this exercise). The funnel numbers below (109 / 8 / 117 / 1,075 / 1,056 /
19) are the record of that exercise and are NOT the paper's counts. For current
counts run `python3 code/recompute_counts.py`. The registry itself
(`data/registry.json`, 1,184 records) is unchanged since the exercise.
Internal working-document pointers from the original have been replaced by
generic descriptions.

---

## 0. One-line conclusion (as of 2026-10-29)

The correct way to write the funnel was: **1,184 registry records -> 109
registry-backed cards + 8 out-of-registry backfills = a 117-card corpus**, with
**1,075 uncarded registry records** (= 1,056 pending + 19 record-level
necessary-background annotations). A figure then in circulation (1,067 =
1,184 - 117) double-subtracted the 8 backfills, which have no registry record;
it was an accounting error, not a finding.

## 1. Method

Three read-only inputs: the registry (1,184 records; fields include work_id,
arxiv_ids, titles, display_title, screening_status, reason, provenance), the
card directory (one JSON per card), and the backfill index (8 out-of-registry
cards). Matching: arXiv ids are compared after stripping version suffixes
(v1/v2...); on a miss, card titles are matched against all registry title
fields with a similarity ratio, **threshold 0.92**; below the threshold a card
is classified as backfill. The 8 backfill cards' best title similarity was
0.73 - far from the threshold, no borderline calls.

Script output (as observed on 2026-10-29):

```
registry total: 1184 {core-research: 57, pending: 1056, necessary-background: 71}
registry status x card status: {(background, background): 52, (core, core): 57}
card status distribution: {background: 57, core: 60}
hit method: {register_arxiv: 107, backfill: 8, register_title: 2}
title hits: 6caf23c8ecb9 -> record:6caf23c8ecb9 (1.0); d6f6b6c78cd3 -> record:d6f6b6c78cd3 (1.0)
backfill: [2607.19351, 2608.15012, 2609.07529, 2609.34463, 2610.02920, 2610.19005, 2610.19422, 2610.24896]
marked candidates: 128; carded: 109; marked-but-uncarded: 19
uncarded registry records: 1075 {pending: 1056, necessary-background: 19}
funnel: 1184 -> 109 (+8) = 117 ; uncarded 1075 ; pending 1056
```

Two structural facts were asserted by the script: (1) the 109 registry-backed
cards map one-to-one onto registry judgments with zero conflicts (57 core ->
core, 52 background -> background; no card was ever built from a "pending"
record); (2) the 8 backfills are exactly 3 core + 5 background, completing the
card-level 60/57 split of that date.

## 2. The three residual numbers

| number | definition | arithmetic |
|---|---|---|
| 1,184 | registry records | - |
| 1,056 | records with screening_status = pending | 1,184 - 57 - 71 |
| 1,075 | registry records without a card | 1,184 - 109 |
| 1,067 | (retired) 1,184 - 117 | mixes card and record units; equivalent to 1,075 - 8 |

These close: 1,184 = 109 + 1,075; 1,075 = 1,056 + 19; and 1,067 - 1,056 = 11 =
19 - 8 (the 19 uncarded background annotations stay inside 1,075; the 8
backfills sit outside the registry). The recommendation of the exercise was to
use 1,075 and retire 1,067.

## 3. The two title-matched cards

Both hash-id cards match registry records at similarity 1.000, with the next
best candidate far below (0.695 / 0.667), and their card filename equals the
registry work_id hash - i.e., the cards were built from exactly those records,
which simply have no arXiv id (both are ACL/NAACL anthology entries with DOIs).
Known technical debt: their `arxiv_id` field holds the hash, so any downstream
filter keyed on arXiv-id shape will skip them.

## 4. The 19 uncarded necessary-background records

All 19 share one profile: DOI-only (no arXiv id), the same template reason
(background/structural contrast, not core memory-mechanism evidence),
abstract-level reading status, no individual findings. Title-similarity checks
against all 117 then-existing cards peaked at 0.845 - none is a version of an
already-carded paper. Conclusion: they never entered the carding queue because
the pipeline keys on arXiv id and the title fallback was executed for the 2
hash cards only. This is a procedural, not an adjudicative, gap. **Left
unexplained on purpose**: why the title fallback ran for the 2 hash cards and
for no other record - no document records that decision. Disposition: not
carded, denominators unchanged; any future carding requires a new screening
round with a recorded status change.

## 5. The screening ledger and its spec conflict

The reconciliation also emitted a per-record ledger CSV (not shipped in this
artifact). One spec conflict is worth recording: "one row per registry record"
and "in_corpus = 117" cannot both hold exactly, because 8 corpus cards have no
registry row. The ledger kept the 1,184 registry rows (109 with in_corpus=yes)
and appended the 8 backfills under a distinct work_id prefix, preserving the
corpus invariant without polluting the registry namespace.

## 6. Open items left by the exercise

1. The 1,056 pending records remained a per-record to-do; this document only
   established the arithmetic that ties them to 1,075.
2. Whether any of the 19 should be carded was left undecided (not carded,
   denominators unchanged).
3. A version-relation question between two uncarded same-cluster records was
   left unverified.
