# Build report

Anonymized artifact for the SoK submission. Frozen 2026-11-02; data resynced to the 2026-11-07 ledger (recon-9).

## Contents

| Path | What it is |
|---|---|
| `data/cost_tags.json` | the adjudication table: 129 cards, four cost classes, 133 evidence readings |
| `data/cards/<id>.json` | 129 evidence cards, one JSON per paper (schema: `protocol/SPEC.md`) |
| `data/registry.json` | 1,184 screening records; 129 were carded |
| `data/screening/` | the 606-record abstract screen and its two coder outputs |
| `data/cost_tags_rules.md` | the four-class rule set the counts depend on |
| `data/cost_tags_quote_exceptions.json` | the 15 evidence entries whose quote is not verbatim in the card result it points to, with the reason for each |
| `data/same_loop_matrix.json` | same-loop (L1/L2/L3) adjudications, protocol v3 |
| `code/` | every script that produces a number in the paper |
| `protocol/` | card schema, blind-coding protocol, codebook |
| `figures/` | the four figures, as PDF and PNG |

## Reproduction

`python3 code/recompute_counts.py` recomputes every headline count from `data/` and
asserts 54 of them against the values in the paper. It needs only the Python standard
library and the files in this package.

`python3 code/verify_quotes.py` checks the 133 evidence quotations against the card
results they point to: 118 match verbatim and 15 are listed in the exceptions file.

`python3 code/verify_screening.py` recomputes the abstract-screen statistics
(606 records, prevalence, Cohen's kappa, positive and negative agreement, PABAK).

`python3 code/checks/verify_deliverables.py` runs the package-level checks.

## Known limitations

1. The per-card labels were produced by model coders under a written rule set, not by
   human annotators. Agreement between two coders from different vendors is reported in
   the paper; no human double-coded the full corpus.
2. The second coder's archived outputs do not echo a per-response model identifier; its
   model is fixed by the endpoint and the configured model name for that run.
3. Ten evidence quotations are not verbatim in the card result they point to. All ten are
   verbatim in the source text; the exceptions file records each one and its cause.
4. One revocability reading is anchored to a section of its source rather than to a
   registered result entry; it is flagged in the exceptions file and carries a locator.
5. Source full texts are not shipped (publisher terms). `code/verify_quotes.py` therefore
   checks internal consistency only; the source-text check is described in the paper.

## Provenance

`data/registry.json` records, per paper, the retrieval route and the version read.
Card-level fields follow `protocol/SPEC.md`. The rule set in `data/cost_tags_rules.md`
is the one the adjudication was run under, and the exceptions file is exhaustive: every
deviation from a clean internal check is listed there rather than omitted.
