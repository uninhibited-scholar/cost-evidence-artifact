# Cost-tag summary (regenerated from data/cost_tags.json, cards_total=129)

Generated from the shipped per-card adjudication; recompute with
`python3 code/recompute_counts.py` (sections B-E) or `python3 code/fig3_cost.py`.

| class | main count (numeric readings) | qualitative-only cards |
|---|---|---|
| C1 utility loss | 34/129 | 6 |
| C2 latency & compute | 26/129 | 2 |
| C3 false positives & collateral | 19/129 | 0 |
| C4 revocability | 21/129 | 1 |

**Union**: 75/129 cards carry any cost evidence (70 with numeric readings,
5 qualitative-only). One card can belong to several classes.

**Union by layer** (cards with cost evidence / cards in the layer; numeric in
parentheses): execution-time gating 7/8 (7), provenance tracing 14/18 (14),
content filtering 16/32 (13), formal guarantees 2/4 (2), architecture isolation
21/38 (19), no defense 3/13 (3), weight space 2/4 (2), n/a 10/12 (10). The last
two buckets and n/a enter no matrix cell. On the C1-C3 price caliber the four
rates quoted in the paper are 7/8, 13/18, 13/32, 1/4.

**Cost readings**: 133 evidence entries. Unit families (one reading can carry
several): relative quantities 78, wall-clock time 12, tokens 6, memory 2;
money 2, energy 0, GPU-hours 0; 40 readings carry no unit at all. Of the 75
reading-bearing cards, 59 carry at least one unit family; 47 of those in a
single family and 12 (20%) in two or more. Per class: C1 carries 31 relative
readings; C2 carries every time (12), token (6), memory (2) and money (2)
reading plus 15 relative; C3 relative only (14); C4 relative only (18).

**Flagged-uncertain entries** (cite only with their annotation):
- `2609.01222` C3: source-identification precision 100%/97% (30 human-annotated
  sources) - 0-3% mislabeling of benign sources (source-identification
  semantics).
- `2609.01852` C1: metadata-representation accuracy gains +.30~.54 vs oracle
  +.46~.63 - recovery incomplete (mitigation reading).
- `2610.03020` C1: memory-pipeline QA gap to gold 33.9/42.9 points
  (den=61,210) - the intervention is a memory pipeline, not an adversarial
  defense (flagged bucket).
- `2610.03020` C4: unsafe-deletion rate 84.1%/78.1% (group means; worst model
  98.51%) - benign mis-deletion (denominator not stated).
- `2610.23559` C2: 405 tokens (-92.2%, den=5,210) - negative cost (audit tool,
  not an adversarial defense).
- `2610.24603` C3: 0/40 false refusals on pure-safety instructions (a level
  reading; its 40/40 completion was moved out of C1 on 2026-11-03 for lacking a
  control arm).

**Registered corrections** (kept as part of the record):
- `2609.08747`: the widely cited "0/1,000 false positives" does not survive
  quote checking - the source text describes a deliberate fail-to-review
  behavior for trusted insiders, not a false-positive measurement. The card was
  removed from C3.
- `2607.27080` (2026-11-03): the repair-selectivity reading (SRSR 56.1%,
  F1 86.3% / F2 62.5%) moved out of C3; the same entry is already booked as C4
  repair evidence, and one reading is counted once, at its reading endpoint.
- `2603.22350`, `2610.07258`, `2610.07639` (2026-11-03): added under the
  level-vs-change boundary (C2) and the benign-object boundary (C3) - a new
  component's absolute per-turn consumption, a detector's false-alarm share on
  benign changes, and a harness refusing startup on 40 of 40 benign workspaces.
- `2610.14836`: the card carries an attack-pipeline cost measurement (32.57
  LLM calls / 121,080 tokens per skill, Table 7) - attacker cost, never counted
  in the four defense-cost classes (it is the corpus's only attacker-cost
  reading).
- `2609.05339`: the migration-fidelity reading (-13.28 pp) is a carrier
  portability measurement, excluded; its repair-success readings 34/48 and
  0/48 count as C4.
