# FIELD-SAMPLE-PROTOCOL - independent field-level sampling of cost-reporting rates (pre-registered)

Version v1, written **before any coding result in this protocol was produced**;
the v2 revision below was appended before its own coding started as well. Any
later change must be appended as a new revision entry, never folded back into
earlier text.

---

## 1. Why a sample is needed

Each of the corpus's existing readings has a known selection bias; none of them
answers "do papers in this direction report cost?":

| Reading | n | level | known bias | what it can answer |
|---|---|---|---|---|
| Card-built corpus | 129 | full text | card building and selection favored cost-proximate work | how costs are reported when cost is the topic |
| Same-frame uncarded | 60 | abstract | the residual tail of include decisions; systematically lower cost relevance | a lower-bound reference |
| Candidate pool | 284 | abstract | contains 101 off-topic items | a lower bound for the frame |

The problem is **selection after outcomes are known**. This protocol exists to
build a sample whose **selection is blind to cost**.

## 2. Frame

- **Single source**: the deduplicated candidate list (653 records) from the
  project's 2026-10 retrieval (query strings archived in the project's search
  log).
- **Freeze clause**: the protocol froze this frame at its date. Papers appearing
  later belong to a **second wave** with their own frame, date, and report -
  they are not merged into this frame. Merging later papers into a frozen frame
  destroys reproducibility.
- **Why not "the whole agent-security literature"**: that population has no
  executable boundary. A dated frame with archived queries that can be re-run
  is stronger than "we tried to read everything", even though it is smaller.
- **Known frame defect**: it contains off-topic items (control theory,
  bibliographic fragments, non-LLM systems), so the eligibility judgment
  (Section 4) is a prerequisite, not an option.

## 3. Sampling

- Simple random sampling, without replacement; n = 300; the seed and n are
  hardcoded in the sampling script and reproducible.
- Sampling happened **before any cost information was viewed**.
- Sampling fraction 300/653 = 45.9%; interval estimates use the finite
  population correction fpc = sqrt((N-n)/(N-1)) = sqrt(353/652) = 0.736.
- 129 of the sampled records carried an arXiv id; 171 were title-only.
- **Phase two (conditional)**: if coding capacity allowed, extend to a full
  census of the frame (653). The n=300 sample remains a **pre-registered
  pilot**: if the two sets of results disagree beyond sampling error, coding
  drift occurred and must be investigated.

## 4. Eligibility (E1-E3, cost-blind)

All three must hold; the criteria use title and abstract only:

- **E1 object**: an agent driven by an LLM/multimodal foundation model, or a
  persistent-state component directly serving one (memory, skill library, tool
  set, system prompt, policy configuration).
- **E2 persistent state**: the intervened-with / protected / evaluated object
  has state reusable across turns, sessions, or tasks.
- **E3 security mechanism**: the paper proposes, evaluates, or formalizes a
  defense / safeguard / security constraint (pure attack papers and pure
  capability papers do not qualify).

Four-value output: `eligible` / `ineligible-topic` / `ineligible-no-defense` /
`unresolved`.

**P(eligible) is itself a reading of frame quality and must be reported.**

## 5. Cost coding (abstract level, three values)

Read only the abstract; no full text, no external sources.

- **A**: the abstract contains at least one numerical value with a unit that
  describes a cost or saving of an intervention, **attributable to the
  intervention**.
- **B**: cost / overhead / latency / utility loss / over-refusal is mentioned,
  without numbers.
- **C**: not touched at all.

Additional field **`cost_is_topic`** in {yes, partial, no}: whether the
cost/overhead/trade-off itself is claimed as the paper's contribution. Every
row must carry this field.

## 6. Estimators and intervals

- **Primary**: P(A | eligible), Wilson interval x fpc.
- **Secondary**: P(eligible); P(A | frame); stratified by `cost_is_topic`.
- **Not allowed**: calling any such ratio "the field's cost-reporting rate".
  Say "within the reach of this retrieval frame" only.

## 7. Blinding and independence

1. **Sampling is cost-blind**: the seed is public; abstracts were fetched only
   after sampling.
2. **Eligibility is cost-blind**: E1-E3 were judged without viewing the A/B/C
   fields; the two passes were run separately.
3. **Coders cannot see screening conclusions**: the sheet handed to a coder
   contains only work_id, title, year, arxiv_ids, abstract - not the triage
   decision or reason.
4. **Relation to the 129-card corpus**: same frame, but independent of the
   cost-proximate selection that produced the cards. That is the only
   independence this sample claims.

## 8. Non-response

- arXiv lane: all records with an arXiv id resolved.
- Other lanes: report the resolution rate; compare year distribution and
  title-keyword composition of unresolved records against resolved ones to test
  whether non-response is topic-correlated.
- Unresolved records are **never imputed**; they are counted separately and
  enter no denominator.

## 9. Revision log

- v1 - initial version, written before coding; sample drawn, not yet coded.

### v2 revision - the main evidence moves to a 284-record stratum census; the 300-sample becomes corroborating evidence

**Finding 1: the binding constraint is abstract availability, not sampling.**
- All 129 sampled records with an arXiv id had abstracts (129/129).
- Title-only records: title search on arXiv matched ~9; OpenAlex was
  rate-limited and unusable from the network in question; Crossref had
  metadata but largely no abstracts. Resolution ~46%. Under Section 8 (no
  imputation), the primary estimator would cover under half the sample -
  **non-response bias worse than sampling error**.

**Finding 2: a stronger design exists.**
The 284 frame records that carry an arXiv id have abstracts 284/284 in hand.
Their eligibility was already adjudicated by the triage pass under E1-E3,
**without using any cost information** (cost entered only later, at card
selection). This stratum can therefore be **censused** rather than sampled:

| | 284-stratum census | 300-sample |
|---|---|---|
| coverage | 100% (284/284) | 46% |
| sampling error | none | yes |
| non-response bias | none | 54% unresolved |
| selection condition | topic (cost-blind) | topic (cost-blind) |

In a 284-record stratum, sampling buys no precision, only non-response risk.

**Finding 3: near-disjoint from the 129-card corpus (11 shared records).** The
284 stratum is a candidate pool from a **different retrieval round**, which
gives the census an independent-replication character: different round,
cost-blind inclusion, 100% coverage.

**Revised claim hierarchy**
1. **Primary**: the 284-stratum census, full recoding under the rubric,
   exact counts (a census needs no interval).
2. **Secondary**: the 129-card corpus's full-text conditional readings.
3. **Boundary**: the 369 non-arXiv frame records are **not estimated**; they
   are reported as an uncovered stratum. The only checkable substitute is a
   title-topic match rate (resolved 96.4% vs unresolved 96.3% - no difference),
   which rules out different topics, not different reporting habits.
4. The 300-sample is retained on record as corroboration, not the primary
   estimate.

**Unchanged**: Section 4 eligibility, Section 5 coding, Section 6 estimator
form, Section 7 blinding, Section 10 prohibited claims all remain in force; the
284 census is subject to Section 7 item 3 as well.

## 10. Claims this protocol does NOT license

- "92% of papers in this field do not report cost" - the frame does not
  license "field".
- Dividing this sample's abstract-level ratio by the 129-corpus full-text ratio
  to announce an "enrichment factor" - different levels, not the same quantity.
- Inferring authorial intent from non-reporting. A sample measures reporting
  behavior, not motives.

## 11. What this sample can and cannot change

**Can**: turn "the field's rate" from unsayable into sayable-within-a-frame
that can be recomputed.
**Cannot**: prove motives; represent the whole field; replace the full-text
readings (abstract-level numbers are lower bounds).
