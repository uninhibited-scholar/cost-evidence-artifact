# Coding prompt v10 — census of cost reporting (frozen 2026-11-08)

You are reading abstracts for a systematic review of how LLM-agent security papers
report the cost of their defenses. Your labels become numbers in a published paper.
One wrong **A** inflates a headline rate; one missed **A** deflates it; one lazy
**C** hides a cost that no later check can recover. Read every abstract in full,
including the last two sentences, where cost statements usually sit.

## Hard rules

- Use only the abstract text in front of you. No outside knowledge about the paper.
- Do not infer a label from the title. Titles describe benefits, not costs.
- Do not decide from the first sentence. Scan the whole abstract for numerals.
- Do not pattern-match: "overhead" is not automatically a cost; "efficient",
  "lightweight" and "scalable" are usually claims, not costs.
- Do not skip, merge, reorder or duplicate items. Do not write prose.

## Working method — two independent readers, then you adjudicate

Do not code the batch alone. Use at least two subagents, and keep them blind
to each other.

1. Spawn **reader 1** and **reader 2**. Give each the full codebook above and
   the same items, in the same order. Neither may see the other's output, your
   notes, or this reconciliation step.
2. Each reader writes its own JSONL file with exactly one line per item.
3. Compare the two files line by line on `cost` and `cost_class`.
   - **Same label and same class** -> keep it, set `agreement` to "both".
   - **Different label or class** -> you read that abstract yourself, decide
     from the evidence, and set `agreement` to "adjudicated". Record which
     reader you followed (or neither) in `adjudication_note`, in at most 20
     words.
   - **A reader skipped, duplicated or misordered a line** -> send it back and
     have it redo only the broken items. Never patch a missing line yourself.
4. Also re-check every item where either reader set `confidence` to "low" or
   `borderline` to true: read the abstract yourself and settle it.
5. Do not average, vote or split the difference. When the readers differ, the
   decision is made on the abstract text, not on who said what.
6. Write the final JSONL (one line per item, item order) and a short summary
   line to stderr or as a separate .summary.txt file: items, A/B/C counts,
   how many were adjudicated, and how many low-confidence items you re-read.

If you cannot spawn subagents (no delegation depth), do the two passes yourself:
finish pass 1, write it to a file, and only then start pass 2, without rereading
pass 1. Reconcile as above and say so in the summary.

## Step 1 — harvest every numeral (do this before deciding anything)

For each item, list every quantity in the abstract that measures something:
percentages, multipliers ("2.8x"), times ("293 ms"), tokens, calls, queries,
bytes, dollars, GPU-hours, percentage points. Skip years, section numbers, dataset
counts used only as corpus size, and model names.

For each harvested numeral assign **one role**:

- `cost` — a price the defense imposes on its deployer
- `benefit` — an improvement the paper claims
- `attack` — how well the attack works, or how well the defense detects attacks
- `benchmark` — corpus, dataset or test-set size, number of cases
- `level` — a bare level with no contrast ("accuracy 91.7%")
- `other` — anything else

This step exists so that a missed cost is visible: if an abstract contains a
numeral and your `numbers` list is empty, the line is wrong.

## Step 2 — eligibility (three conditions, all must hold)

- **Object.** An LLM agent, or a memory, skill, tool or policy component serving
  one, whose state is reusable across turns, sessions or tasks.
- **Role.** That state is the intervention target, the threat entry, the
  constrained carrier, or the evaluated component.
- **Security property.** An identifiable one, backed by methods, formal analysis,
  or measured evidence.

Not eligible: model alignment with no persistent agent state; governance, position
or survey papers with no evaluation; infrastructure papers (TPM, blockchain
identity, network policy) where the agent's state is not the object; single-turn
studies that touch no reusable state.

If not eligible: `cost` = "C", `quote` = "", and say which condition fails.

## Step 3 — cost class and label

Judge only the cost the **defense imposes on the party that deploys it**.

- **C1 — utility loss.** Change in task success, accuracy, recall, F1 or
  authorized-use rate against an undefended baseline, under benign or no-attack
  conditions. A level reading with no contrast is **not** C1.
- **C2 — latency and compute.** Wall-clock time, tokens, model calls, queries,
  storage or money that the defense adds **or saves**.
- **C3 — false positives and collateral damage.** Benign inputs wrongly blocked,
  isolated or flagged; over-refusal; the defense's own false-positive rate.
- **C4 — revocability.** The cost, residue or failure of revoking, forgetting,
  cleaning or repairing state.

Then:

- **A** — a numeral from Step 1 has role `cost`.
- **B** — a cost is stated in words, with no numeral attached.
- **C** — no cost is stated at all.

## Null result or stated burden?

This is the boundary that decides B. Ask two questions of the sentence, in order.

**Q0. Is there a number attached, even a zero?**

A counted zero is a measurement, not an absence: "0% false positives on the clean
controls", "zero over-blocking", "no drop of 0.0 points" price the cost axis at
zero and are **A** on that class. A worded claim of absence with no number
("preserves utility") is C.

**Q1. Does the sentence say the deployer pays something?**

- If it says there is no loss, it is not a cost statement: **C**.
- If it names any burden, even a small one, go to Q2.

**Q2. Is the size of that burden given in words rather than a number?**

- Words only -> **B**. A number -> **A**.

| Sentence | Label | Why |
|---|---|---|
| "preserves utility" | C | says there is no loss |
| "maintains comparable accuracy" | C | says there is no loss |
| "no noticeable reduction in benign utility" | C | asserts absence of a cost |
| "while largely preserving task utility" | C | asserts absence of a cost |
| "at near-zero utility loss" | B | states a loss, only its size is qualitative |
| "with negligible clean-performance overhead" | B | states a burden, size qualitative |
| "minimal overhead" | B | states a burden, size qualitative |
| "practical inference overhead" | B | states a burden, no size at all |
| "at the cost of accuracy" | B | states a burden, no size at all |
| "latency 2.82x" | A / C2 | burden with a number |
| "0% false positives on the clean controls" | A / C3 | a counted zero prices the axis |
| "blocks with zero false positives" | A / C3 | same, value zero |
| "preserves utility" (no number anywhere) | C | worded absence, not a counted zero |
| "six of eleven benign scenarios" | A / C3 | a numeral in words still sizes a burden |
| "twice the latency of X" | A / C2 | spelled multiple, still a numeral |
| "within a few percent of X" | B | "a few" is not a numeral |
| "allows 99.5% of benign workflows to pass" | A / C3 | the complement is a 0.5% block |
| "retains 94.1% of task utility" (no baseline) | C | a level, not a loss |

**Polarity on the collateral axis.** On C3 a benign pass rate and a false-positive
rate are the same quantity with the opposite sign, so "allowing 99.5% of benign
workflows to pass" prices a 0.5% block and is **A / C3**. On the utility axis
(C1) a retention rate is a level, not a cost, unless the undefended baseline is
stated: "retains 94.1% of utility" alone is **C**, mark the numeral `level`.

Do not treat the words "negligible", "near-zero", "minimal" or "slight" as
absence: they describe a small burden, so the label is B. Only "preserves",
"maintains", "comparable", "no reduction" and "without loss" assert absence.

A numeral may be written in words ("six of eleven scenarios", "twice the
latency", "one in four"): that is still a size, so the label is A. A vague
quantity word ("a few percent", "several hours", "vastly") is not a numeral.

## Step 4 — what is NOT a cost (check every A against this list)

1. Attack damage, attack success, ASR, evasion rate.
2. The defense's detection quality as a security result: recall, precision,
   detection rate, TPR. (Its **false-positive rate on benign data is a cost**.)
3. Corpus, benchmark or dataset size; number of test cases or scenarios.
4. Speedups or savings that are the paper's selling point. A saving is a cost only
   when the paper frames it as the price paid.
5. A numeral attached to a benefit ("improves accuracy by 3 points").
6. A bare level with no contrast ("accuracy 91.7%").
7. Attacker cost: what the attacker spends.
8. A design claim with no measurement ("our design is efficient and lightweight").
9. A null result: "preserves utility", "maintains accuracy", "comparable performance", "no significant loss". Saying a cost is absent is not reporting a cost — unless the absence is a number ("0% FPR"), which is A.
10. A security shortfall: an attack that still succeeds, protection that is weaker than hoped, a threat model the defense does not cover. That is the benefit side, not the price. (Residue left after an attempt to revoke or forget is different: that is the cost of the revocation mechanism, C4.)

## Step 5 — tie-breaks

| Situation | Label |
|---|---|
| Numeral attached to the cost | A, with the class |
| A burden in words only ("minimal overhead", "at the cost of accuracy", "practical inference overhead") | B |
| A null result ("preserves utility", "maintains accuracy") | C |
| Only a benefit numeral, no cost | C |
| Numeral is a level with no contrast | C, and mark the numeral `level` |
| Numeral is the defense's own FPR on benign data | A / C3 |
| That FPR numeral is zero ("0% FPR") | A / C3, a counted zero still counts |
| Worded claim that the defense protects less well than hoped | C, that is the benefit side |
| Numeral is ASR or detection recall | C, mark `attack` |
| Saving framed as the price ("at 40% fewer calls per request than X") | A / C2 |
| Saving framed as a gain ("40% faster than X") | C, mark `benefit` |
| Both a benefit and a cost in one sentence | Quote the cost clause only |
| Two cost classes in one sentence | Pick the one with the clearer numeral, name it |

Separately: **when a numeral could be read as either a benefit or a cost, and the
abstract does not say which, do not invent a cost.** Label C and mark the numeral
`other`. A doubtful A is worse than a missed B, because only A enters the
headline rate.

## Step 6 — quote and sentence

For A or B, copy:

- `sentence` — the complete sentence the cost comes from, verbatim, any length.
- `quote` — the cost clause only, verbatim, at most 30 words, no ellipsis inside
  a numeral, no paraphrase, no added brackets.

The quote must be an exact substring of the abstract, and for A the numeral marked
`cost` must appear inside it.

## Step 7 — self-audit before writing each line

1. Does `numbers` list every numeral that could plausibly be a cost? If the
   abstract has numerals and the list is empty, redo the item.
2. Is the entry marked `cost` really paid by the deployer, not by the attacker
   and not by the benchmark?
3. Is the quote an exact substring, and does it contain the `cost` numeral?
4. If `eligible` is false, are `cost` and `quote` empty?
5. Would a second reader, given only this line and the abstract, agree? If not,
   set `confidence` to "low" and still give your best label.

## Output — one JSON object per line, in item order, nothing else

{"arxiv_id":"...","eligible":true,"eligibility_reason":"all three hold; persistent memory","numbers":[{"n":"2.82x","role":"cost"},{"n":"97%","role":"benefit"}],"cost":"A","cost_class":"C2","sentence":"...","quote":"...","confidence":"high","agreement":"both|adjudicated","adjudication_note":""}

- `numbers`: 0-6 entries, most decision-relevant first. Empty only when the
  abstract contains no quantity at all.
- `cost_class`: "C1", "C2", "C3", "C4", or "" when `cost` is "C".
- `quote` and `sentence`: "" when `cost` is "C".
- `confidence`: "high", "medium", "low".
- `agreement`: "both" when the two readers matched, "adjudicated" when you had to decide.
- `adjudication_note`: "" when both agreed; otherwise the reason you overrode a reader, <=20 words.

## Final instruction

Output exactly one line per item, in the given order. Your final file is the reconciled one, not either reader's raw file. Before finishing the batch,
re-read every line marked C: if its `numbers` list is empty but the abstract
contains a quantity, or if any listed numeral could be a cost, redo that item.
