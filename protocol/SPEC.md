# Evidence-card SPEC (data/cards/&lt;arxiv_id&gt;.json)

Reconstructed specification of the per-paper evidence cards. Each card is one
JSON file, one paper per file (filename = card id; an arXiv id for arXiv
papers, a stable hash id for the two non-arXiv records).

## Top-level keys (12 required, 3 optional)

| key | required | meaning |
|---|---|---|
| `arxiv_id` | yes | must match the filename; non-arXiv sources use a stable hash id |
| `title` | yes | paper title (of the version that was read) |
| `screening_status` | yes | core-research or necessary-background |
| `versions_read` | yes | list of versions actually read, e.g. `["v1"]` |
| `object` | yes | the persistent-state object (see below) |
| `safety_property` | yes | the security property and its operationalization |
| `threat_model` | yes | adversary capabilities, assumptions, not-covered items |
| `intervention` | yes | the evaluated method / intervention |
| `results` | yes | list; core-research cards carry at least one primary result; necessary-background cards may be empty |
| `limitations` | yes | the source paper's self-stated limitations, each with quote + locator |
| `reading` | yes | `{coverage: [...], complete: bool}`; complete=false when appendices were not read |
| `quality_flags` | yes | free-form string list; a numeric value without a denominator must carry `denominator_unclear` |
| `controls` | optional | control/ablation list `{name, purpose}`, purpose in {baseline, fair-comparison, ablation} |
| `counterexamples` | optional | counterexamples or reverse findings `{observation, locator}` |
| `reproduction` | optional | `{code, data, run_by_us}` |

## Nested objects

- `object`: `what_persists` (memory/experience/skill/policy/mixed/none...),
  `scope` (within-task / cross-task / cross-session), `carrier` (concrete
  description of the state carrier), `operations_covered` (subset of
  formation/update/retention/retrieval/revocation/repair).
- `safety_property`: `type`, `statement` (what is protected, when it fails, how
  it is judged), `operationalized_as` (measured endpoint + benchmark +
  denominator basis).
- `threat_model`: `adversary` (none/external/internal/...), `capabilities[]`,
  `assumptions[]`, `not_covered[]`. **Whether the adversary re-adapts to an
  evolved defense must be stated in capabilities or not_covered.**
- `intervention`: `name`, `mechanism_layer`, `description`.

## results[i]

Required: `claim` (one sentence), `metric`, `value`, `locator` (section/table/
figure), `is_primary_result` (bool). Strongly recommended: `quote` (verbatim
quotation from the paper), `comparison` (against what), `setting` (model +
benchmark + protocol), `denominator`: `{n_total, n_valid?, how_counted}`.
**Any numeric value requires a denominator, or a `denominator_unclear` flag in
quality_flags; if no denominator can be recovered, record null and flag it -
never guess.**

## Discipline

1. Register only facts read directly in the source; `quote` must be verbatim.
2. Numbers carry denominators; unclear denominators are flagged, not invented.
3. Every card was verified after writing (schema, quote format, denominators);
   `code/verify_quotes.py --cards` re-runs the structural part of that check.
4. Full paper texts are not redistributed in this artifact; obtain a cited
   paper with `code/fetch_source.py` for spot checks.

Note on language: the annotation fields of the cards (claims, settings,
limitation notes, some quality flags) were written by the coding team in the
team's working language and are shipped as-is; the verbatim `quote` fields are
in the source papers' language (overwhelmingly English).
