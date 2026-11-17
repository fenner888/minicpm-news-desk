# Changelog

Public package versions; updating source does not automatically update a private deployment.

## Unreleased — synthetic AI boundary fixes

- Instruction holds use an NFKC-normalized, Cyrillic/Greek-lookalike-folded view
  with zero-width format characters removed. Split ignore/task instructions and
  chooser-directed selection commands hold the source for review, not silently
  drop it. Exact source text and offsets remain unchanged. Policy v7 changes
  packet hashes; regenerate packets for replay and preserve original artifacts.
- Model transport rejects exact, reversed, standard/URL-safe base64 (padded or
  unpadded), and whitespace/punctuation-split key echoes before persistence.
  This is defense in depth: the model prompt never receives the HTTP API key.
- Synthetic regressions first reproduced both gaps (32 failing subcases); extra
  instruction variants and benign text/empty-response checks cover the repairs.
  The separate after-fixes mock evidence leaves the baseline untouched and does
  not rescore the frozen private benchmark. No fresh inference or delivery.
- Raw reasoning/response retention and legacy free-prose behavior are unchanged.
  No package/runtime/model setting, reasoning budget or private deployment change.

- Add pinned Gitleaks secret scanning and weekly GitHub Actions dependency updates
  with a seven-day cooldown. Runtime and model settings are unchanged.

## 0.8.1 — September 21, 2026

Deterministic repairs derived from the private frozen benchmark of 0.8.0
(eight GitHub articles, two repeats, no-model baseline). Shipped model, prompt,
runtime setting and reasoning budget remain unchanged. The initial repairs were
offline; the separately authorized 512/1024 comparison is recorded in EVALUATION.md.

- Parser keeps simple table rows on separate lines with ` | ` between cells.
  Previously pretty-printed cells became separate blocks and minified cells ran
  together. Final review adds fail-closed handling for nested/spanning tables
  and prevents hidden markup from corrupting visible row state.
- Selector pool excludes short blocks without terminal punctuation. Emoji,
  apostrophe or digit headings and bare table cells had occupied lead pool slots
  in five of eight benchmark articles, and the first-two baseline quoted them.
- Protection policy v6 adds stated prerequisites (`you’ll need`, `or later`,
  `prerequisites`) and rejection clauses (`rejects`, `refuses`). The version/2FA
  prerequisites were neither protected nor selectable; the direct-publish
  rejection was selectable but unprotected and omitted on one repeat.
- `verified_card` carries `highlight_rules` and `condition_rules`; section- or
  exclusion-tagged field passages stay visible whether selected or independently
  retained. Absent metadata keeps legacy behavior; malformed/misaligned metadata
  is rejected. Existing navigation and incomplete-context guards remain.
- Final review passes 270 offline tests: seven initial additions plus six final
  edge-case tests, including five reproduced failures and one preventive guard.
  The final corrections were not part of the frozen live budget comparison.
- At the initial 264-test checkpoint, offline replay of
  the benchmark's saved selections through the new preparation/reading layers
  retains 7/7 units on both npm-token runs (was 6 and 4), 6/7 on both
  dashboard runs (was 4) and 5/7 on the CLI-metrics run (was 4); the deprecation
  table remains correctly held. This is a replay against frozen text and saved
  IDs, not a new benchmark; pool changes alter packet hashes, so the model may
  select differently on a fresh run.

Policy v6 changes packet hashes. Regenerate packets for explicit replay; retain
older artifacts as historical evidence. The final offline replay revalidates the
two original acceptance responses under their old packets, then applies unchanged
IDs to new packets: both qualification checks pass, with two unsent message parts.
`REASONING_BUDGET` stays 512. Token-count/ending heuristics suggest budget pressure
but do not establish its cause or justify a production setting change.

## 0.8.0 — September 21, 2026

- Preserve operators, paths, commands and Markdown literals using safe output
  escaping; protect tested licensing/prohibition clauses with policy v5.
- Add opt-in public RSS collection, build/preview, explicit Telegram approval/send,
  owner-only locked state and known-unsent cancellation/receipt reconciliation.
- Configurable public title/timezone; unchanged private-library defaults.
- Add inert HTML preview, full fictional sample sources and responsive report rows.
- Add public setup instructions, disabled scheduler example and pinned offline CI.
- Retain complete, hash-verified `To prepare:` context instead of unnecessarily
  withholding a brief. Incomplete/ambiguous/oversized restriction lists stay held.
- 257 offline tests pass; both registered feeds fetched successfully after new
  compatibility regressions. Two fresh local requests and a confirmed Telegram
  test exposed the preparation-context issue; both saved responses pass after
  the deterministic repair. The repaired output was not sent again.
- Source publication is owner-approved. No private promotion or schedule change;
  unattended operation and broader model reliability are not established.

Packet hashes change with policy v5. Retain older artifacts as historical evidence.
Do not deploy the new escaped Markdown into an old sender without validating its
rendering path; the public sender includes the matching safe HTML renderer.

## 0.7.5 — September 18, 2026

- Preserve qualifications in model-selected navigation/API-field passages, plus
  ISO dates, migration guidance and background safety warnings in reading views.
- Add six regression tests (203 public offline tests total).
- Document the actual 0.7.4 fresh-model/two-part Telegram test and its manual
  launch recovery; distinguish it from the earlier unsent validation preview.
- Clarify repository-root execution, timezone prerequisites, current evidence,
  historical fixtures and the boundary between public code and private delivery.
- Refresh the fictional daily sample and contributor guidance.

The initial source cleanup made no model calls, deployment or sends. A subsequent
owner-approved 0.7.5 promotion passed 203 public plus 74 private tests and five saved
replays. Two fresh local requests produced two briefs; those and seven source-only
quick hits reached Telegram in two confirmed messages. Schedule/archive unchanged.
See EVALUATION.md for the new evidence, separate from historical 0.7.4 results.

Follow-up documentation adds SETUP.md and clearly separates the offline demo,
local inference and custom delivery integration.

## 0.7.4 — September 18, 2026

- Retain migration date ranges and version-pinning guidance with protection
  policy v4; move unqualified documentation navigation into the full report.
- 197 public tests; 74 separate private integration tests.
- Five saved-result replays and a fresh local affected-case request validated
  the original omission repair. A later fresh call reached Telegram; see EVALUATION.md.

## 0.7.3 / 0.7.2 / 0.7.1 — September 18, 2026

- Add bounded publisher context for source-only quick hits.
- Improve headings, paragraph grouping, source links and multi-part layout.
- Separate reading-view content from the complete supporting source report.

## 0.7.0 — September 18, 2026

- Daily 08:00 America/New_York layout and exact preceding-24-hour archive window.
- Deterministic ranking/deduplication and reserved/confirmed delivery state.

## 0.6.1 — September 17, 2026

- Initial MIT public package: source-bound ID selection, guarded source-only
  fallback, fictional samples and explicitly limited development evidence.
