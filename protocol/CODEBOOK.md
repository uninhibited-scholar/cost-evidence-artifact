# CODEBOOK - blind coding manual for the four cost classes

Version v1. This manual restates the artifact's adjudication rules
(`data/cost_tags_rules.md`) as instructions for a coder. **No new definitions
are introduced**; where the two documents differ, the source rules file prevails
(see "Deviations from the source rules" at the end).

Task: for each paper under review, decide for each of the four cost classes
C1-C4 whether the paper contains qualifying evidence.

---

### 0. Procedure

1. **The coding basis is the paper's full text.** Read the paper; do not rely
   on abstracts or third-party summaries.
2. Judge C1, C2, C3, C4 **independently** of each other.
3. **Threshold for has=1**: the paper contains a **checkable quantitative
   reading** (including values such as "0", "100%", "zero change"). Purely
   descriptive assertions - design intent, theorem-style guarantees, self-noted
   "non-zero overhead" without a number - do not qualify.
4. **One reading, one class**: a single reading goes into exactly one class.
   Different readings of the same paper may fall into different classes (e.g.,
   one into C1, another into C3).
5. If the same reading appears in several places, register it once.
6. Do not force uncertain calls: if a reading genuinely cannot be assigned to
   any class under the definitions below, code all classes as no-evidence.

### 1. C1 Utility loss

**Code 1 when**: the paper reports a **task-side** performance-change reading
caused by an **intervention** (defense mechanism, defensive feedback,
deployment decision) under **benign or no-attack conditions**. Task-side =
readings of "whether the task got done": task success rate, accuracy, recall/
usability, authorization usage, request success rate, and the like. Decreases,
zero change, and improvements all count (an improvement = negative loss).

**Exclusions (no evidence)**:
1. **Utility-under-attack readings** - unless the same study also reports a
   benign-condition contrast reading; that benign reading may qualify, the
   under-attack one still does not.
2. **Pure capability improvements**: capability-side readings without an
   intervention contrast.
3. **Dataset size**: size statements are not measurements (e.g., "we evaluate
   on 250 benign samples").

**Boundaries (decide the class, not the presence)**:
- vs C3: readings taken from the **task side** go to C1; readings taken from
  the **defender's decision side** (should-have-blocked-but-didn't,
  blocked-but-shouldn't-have) go to C3. A paper can have one of each.
- vs C2: extra tokens per se go to C2; extra tokens that lead to a **separately
  reported** accuracy drop go to C1; if both are reported separately, record
  each in its own class.

### 2. C2 Latency & compute

**Code 1 when**: a quantitative reading of compute resources **caused** or
**saved** by the intervention: latency (ms/s), token multiples or percentages,
LLM/validator call counts, per-request queries, throughput caps,
training/inference overhead. **Negative readings count too** (speedups, token
reductions) - a negative cost is part of this class's evidence, not an
exclusion.

**Exclusions (no evidence)**:
1. **System latency unrelated to the intervention** (e.g., attack-persistence
   readings: malicious content still retrievable N hours after the attack).
2. **Inherent cost of deployments without an intervention**.

**Boundaries**:
- vs C1: resource readings go to C2 even when they also hurt the task; that
  task reading, if separately reported, goes to C1.
- vs C4: validation/recompute overhead of revocation operations is about
  revocation - it goes to C4, not C2.

### 3. C3 False positives & collateral

**Code 1 when**: a quantitative reading of misjudgment of **benign/legitimate
inputs or actions** by the intervention: FPR, false-alarm counts,
false-quarantine rate, false-block rate, over-refusal rate, the specificity
side of a specificity-recall pair. **Zero-FP readings count** ("0/1,000" is a
measurement, not a missing measurement).

**Exclusions (no evidence)**:
1. **Missed detections on attack inputs**: failing to block what should be
   blocked is a failure on the security-benefit side, not collateral on the
   benign side.
2. **Routing-to-human on attack inputs**: no benign-misjudgment semantics.
3. **Misclassification of the attack tooling itself**: an attack-pipeline
   reading.

**Boundaries**:
- vs C1: defender-decision-side readings go to C3; task-consequence readings
  go to C1.

### 4. C4 Revocability

**Code 1 when**: a quantitative reading of the success, residual impact, or
extra overhead of **revoke / forget / clean-up / source-removal /
authorization-revocation operations**: end-to-end forget-request success rate,
residual influence after revocation (still returned, still trusted, still
reproducible, still reconstructable), behavior recovery after purging,
post-deletion publication rate of derived artifacts, validation/recompute
overhead of undoing a mistaken mechanism.

**Inclusion clarification**: an attack-side re-triggering rate after deletion
("still attackable") **is coded as C4 evidence ("residual influence after
revocation") when the reading directly measures whether the deleted operation's
influence has terminated** (the source rules adjudicate this explicitly).

**Exclusions (no evidence)**:
1. **Migration fidelity**: model-upgrade / cross-system porting readings - a
   carrier portability issue, not revocation.
2. **Attack success rates that exploit residual state**: attack-side readings
   do not qualify; only the **defense-side** residual reading of the same study
   does.

**Boundaries**:
- vs C1: readings whose endpoint is the delete/revoke operation's own success
  and residue go to C4; a separately reported task-performance change after an
  erroneous removal goes to C1.
- vs C3: a failed revocation (should-have-been-deleted-but-wasn't) is not a
  detection miss; a detection miss is not a revocation failure.
- vs C2: compute about the revocation operation (validation calls) goes to C4.
- Formalized revocation guarantees (theorems): a guarantee is not a measurement
  - no evidence (see the Section 0 threshold).

### 5. Two boundary examples

**Example 1 (C1): a level reading is not a verifiable cost change.**
"We evaluate on 250 benign samples" is a **size/level** statement, not a
measurement of an intervention-caused task-side performance **change**.
C1 evidence requires all of: a task-side reading + benign/no-attack conditions
+ a change attributable to the intervention.

**Example 2 (C4): a ratio reading is not a revocation cost.**
"After porting to the new model/system version, ~90-something percent of
performance is retained" is a **ratio (fidelity) reading** measuring carrier
portability, not revocation. C4 evidence requires the reading to be about the
revoke/forget operation itself (success, residue, or its extra overhead).

### 6. Deviations from the source rules (recorded as required)

1. **Intermediate state collapsed**: the source rules allow an intermediate
   state "evidence present but only non-quantitative" (kept as evidence,
   excluded from the main tally). Binary coding forms collapse it uniformly:
   **checkable quantitative reading -> counts; purely descriptive assertion ->
   no evidence**.
2. **Number of exclusion clauses**: the source rules give 10 sub-clauses across
   the four classes (C1: 3, C2: 2, C3: 3, C4: 2). This manual organizes them as
   class-level exclusion lists with all sub-clauses present; the third item of
   the source's C4 exclusions is in fact an **inclusion clarification** (counted
   into C4 as post-revocation residue) and appears as such above.
3. **Boundary examples**: the two examples correspond to the source's C1
   "non-change readings" exclusions and its C4 "migration fidelity" exclusion;
   they deliberately cite no specific paper identifiers (a blind-coding
   requirement), while the source rules file does.
4. **Quote fields**: the source rules' evidence register also requires locator
   and denominator; a minimal coding form may collect only the verbatim quote.
