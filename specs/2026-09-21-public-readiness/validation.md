# Evaluation and release gate

Evaluation ID: public-readiness-v1; workflow and deterministic software evaluation,
not model ranking. Owner/decision owner: Mark. Baseline: 0.7.5, 203 offline tests.
Regression set: audit technical-syntax and omitted-prohibition cases. New development
cases: fixed-source RSS, permission matrix, crashes, replay, partial/ambiguous sends,
malformed/hostile inputs, report rendering. No untouched model holdout in this stage.

Grading: deterministic assertions and isolated execution; visual desktop/mobile
inspection. All existing and new tests must pass; zero permission failures or
duplicate sends allowed. No paid calls, no retries, zero real model/send calls in
offline stage. Record versions, test count and limitations in EVALUATION.md.

Before release: source/diff review, allowlist and documentation checks, secret and
dependency review, both demos and clean-export command smoke tests. Run local model
and test-chat delivery only at a separately approved checkpoint, inspect actual
source qualifications, then observe scheduling separately. Unverified live evidence
blocks an unattended reliability claim, not offline implementation work.

Rollback: do not promote into private runtime during this work; keep previous
release and all historical evidence. Any live failure becomes a sanitized case.

September 21 publication approval: owner requested pushing all reviewed changes.
The two-call acceptance run exposed a preparation-context false hold. Fix and
replay the two saved responses with zero additional model requests or sends;
require new negative-context regression cases and the full offline suite. Keep
the initial failed live result separate from the repaired offline evidence.
Source publication is not private runtime or unattended delivery promotion.

### 0.8.1 final review

Six additional synthetic tests cover nested/spanning tables, hidden table state,
selected protected field passages, malformed parallel rule lists and unchanged
navigation/incomplete-highlight guards. Five tests reproduced defects before
correction; the guard test is preventive. All 270 offline tests pass, including
with real socket connections and process launches blocked. Run both demos and
isolated source-only initialization/build before committing the final candidate.
The independently frozen 512/1024-budget arms use commit 8065f2e, not these later
corrections; report live measurements and final offline verification separately.
Keep all failed/empty/security-edge outcomes in the experiment report. A passing
software suite does not establish semantic reliability or justify deployment.
