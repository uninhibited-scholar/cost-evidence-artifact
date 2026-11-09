# Cost-tag adjudication rules (v2, adjudicated edition)

These rules govern the per-card cost adjudication recorded in
`data/cost_tags.json` (cards_total=129). They replace two earlier keyword-rule
variants (a strict v1 and a wide v2), both of which spot-checks showed to
under- and over-count (e.g., the -4.4 pp utility reading of `2609.22818` was
missed by both; the migration-fidelity reading of `2609.05339` was miscounted
as revocability by the wide variant). The keyword candidates are a search
starting point only; the adjudication under these rules is authoritative.

## 1. Unit of adjudication and unit of evidence

- **The card is the adjudication unit**: each card is judged has=true/false for
  each of the four classes; counts are per card (denominator 129).
- **The evidence unit is a `results[]` entry** of the card: one evidence entry
  = one result of `data/cards/<id>.json`, registered with its verbatim `quote`,
  `locator`, and `denominator`. Statements in `limitations`/`not_covered` are
  non-reporting declarations, not evidence.
- **One evidence entry, one class**: the same result entry goes to a single
  class; different entries of the same card can go to different classes (e.g.,
  `2609.22818`: -4.4 pp to utility loss, 33.6% mis-quarantine to false
  positives, 2.7% token overhead to latency & compute - three different
  entries). The merge step enforces deduplication and errors on conflicts.
- **Only numeric readings enter the main count**: `value` or `quote` must carry
  a checkable quantitative reading (including "0", "100%", "zero change").
  Purely qualitative statements (a self-noted "nonzero overhead", design
  intent, theorem-style guarantees) are recorded `qualitative: true` - kept as
  evidence, excluded from the main count, citable only with that annotation.

## 2. The four classes: definitions and boundaries

### C1 utility loss
**Definition**: task-side performance-change readings that an intervention
(defense mechanism, defensive feedback, deployment decision) causes **under
benign or no-attack conditions** - decreases, zero change, and improvements
(an improvement = negative loss, marked as such in the reading). Task-side =
"did the task get done": task success rate, accuracy, recall/usability,
authorization usage, request success rate.
**Boundaries**:
- vs C3: the reading's **task side** goes to C1; the **defender's adjudication
  side** (blocked what should not have been blocked / failed to block) goes to
  C3. One card can carry one of each.
- vs C2: a token increase per se goes to C2; a token increase that leads to,
  and is **separately reported as**, an accuracy drop goes to C1.
- **Exclusions**: utility-under-attack readings (unless the same study has a
  benign contrast); pure capability gains without an intervention contrast;
  dataset-size statements (size is not a measurement).

### C2 latency & compute
**Definition**: quantitative readings of compute resources the intervention
causes **or saves**: latency (ms/s), token multiples or percentages,
LLM/validator call counts, per-request queries, throughput caps,
training/inference overhead. Negative readings (speedups, reductions) are part
of this class's evidence, not exclusions.
**Boundaries**:
- vs C1: a resource reading goes to C2 even when it also hurts the task (that
  task reading, if separately reported, goes to C1).
- vs C4: validation/recompute overhead of a revocation operation is about
  revocation - one entry, one class, it goes to C4.
**Exclusions**: system latency unrelated to the intervention (e.g., a malicious
link still retrievable 46 hours after the attack - an attack-persistence
reading); the inherent cost of a deployment without an intervention.

### C3 false positives & collateral damage
**Definition**: quantitative readings of the intervention misjudging
**benign/legitimate inputs or actions**: FPR, false-alarm counts,
mis-quarantine/mis-isolation rates, wrongful-block rates, over-refusal rates,
the specificity side of a specificity-recall pair (including zero-FP readings -
"0/1,000" is a measurement, not a missing measurement).
**Boundaries**:
- vs C1: adjudication-side readings go to C3; task-consequence readings go to
  C1.
- **Exclusions**: misses on attack inputs (a failure on the security-benefit
  side); escalation-to-human on attack inputs (no benign-misjudgment semantics;
  recorded as a boundary case, not counted); the attack tooling's own
  misclassifications (attack-pipeline readings).

### C4 revocability
**Definition**: quantitative readings of the **success, residue, and extra
overhead of revoke / forget / cleanup / source-removal / authorization-revocation
operations**: end-to-end forget-request success rates, residual influence after
revocation (still returned / still trusted / still reproducible / still
reconstructable), behavior recovery after cleanup, post-deletion publication
rates of derived artifacts, validation/recompute overhead of undo mechanisms.
Formalized revocation guarantees (theorems) are recorded `qualitative: true`
(a guarantee is not a measurement).
**Boundaries**:
- vs C1: the endpoint "the delete/revoke operation's own success and residue"
  goes to C4; a separately reported task-performance change after an erroneous
  removal would go to C1 (no such reading exists in this corpus - a gap).
- vs C3: a failed revocation is not a detection miss; a detection miss is not a
  revocation failure.
- vs C2: compute about the revocation operation (validation calls) goes to C4.
**Exclusions**: migration fidelity (model-upgrade / cross-system porting
readings - carrier portability, not revocation; e.g., `2609.05339`'s -13.28 pp);
attack success rates that exploit residual state (e.g., `2609.33910`'s +35.1 pp
is attack-side; that study's **defense-side** residue reading 0.012-0.039 is
the C4 entry). An attack-side re-triggering rate after deletion IS counted as
C4 "residual influence" when the reading directly measures whether the deleted
operation's influence has terminated (`2608.03509`'s 32/40 is counted on this
basis).

## 3. Relation to no-defense and weight-space cards

C1-C3 presuppose an intervention in principle; a card with
`defense_layer=none` that studies an intervention-like feedback (e.g.,
refusal-type experience mixing) can carry C1 with layer recorded as none (the
layer distribution has a "no defense" bucket). C4 requires no defense artifact
(revocation is a state-operations task; `2610.18052` is a no-defense card).
Weight-space cards are adjudicated normally by their readings, with the layer
recorded as weight-space; cards coded before a layer assignment existed carry
layer `n/a` and enter no matrix cell.

## 4. Outputs and falsifiability

- `data/cost_tags.json`: per-card four-class adjudication (has / qualitative /
  evidence[quote, locator, denominator] / one-line reason / layer). Quotes were
  extracted verbatim from the card text fields by script; humans supplied the
  entry indices and the judgments, which keeps the quotes verbatim.
- `data/cost_tags_summary.md`: the summary counts.
- **Falsifiability**: a third party can re-adjudicate under these rules; if any
  class count moves by more than plus/minus 3, the paper's corresponding
  layer-distribution and gap statements are void.

Note on language: the one-line per-card `reason` strings and some `value`
annotations in `data/cost_tags.json` were written by the adjudicators in their
working language and are shipped as-is; the registered `quote` fields are
verbatim from the source papers.
## 5. Amendment of 2026-11-07 (applies to the shipped adjudication)

Two kinds of cost are excluded from C1-C4 and from the construction ledger, and
the exclusion binds both sides of the ledger:

- **Mechanism costs.** Task-side losses that are properties of the evaluated
  system rather than of adopting a defense - persistent memory or skill
  self-improvement making the agent worse (e.g., saving a claim that raises the
  downstream failure rate from 45.0% to 71.9%; a $3.7 charge per successful
  practice run).
- **Study-internal evaluation spend.** Compute and money spent producing the
  paper's own findings (an $8,368 campaign, a five-hour 1,600-task sweep) are
  research overhead and enter neither the operating classes nor the
  construction ledger.

Construction cost is a separate ledger (`construction-operating.csv` in the
working repository): it records only quantified build-side readings with a
resource unit (GPU-hours, Wh, minutes, money), and its operating column is by
definition the C1-C4 union. Four cards carry a construction reading and three
carry both ledgers; one card reports only what it cost to build the defense.

The 2026-11-07 re-adjudication moved `2608.12851` into C1, reclassified
`2609.07529` from qualitative to numeric, added `2602.01146` to C3 and
`2610.19005` to C3 and C4, and removed `2510.17276`, `2605.09315` and
`2609.34463` from C1 (attack-side readings under this amendment).
