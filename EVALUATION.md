# Evaluation — MiniCPM News Desk 0.8.1

## September 21 frozen benchmark of 0.8.0 and deterministic repairs (0.8.1)

A private frozen-set benchmark ran unchanged 0.8.0 on eight GitHub changelog
articles (six labeled prospective, two known regressions) plus four synthetic edge cases, each
twice, with a no-model first-two-eligible baseline and assistant-authored
annotations frozen before inference. Twenty local CPU-only calls completed; no
retries, sends or hosted requests. Raw sources, reasoning and the corpus are
private. Headline outcome: 13/16 detailed briefs; 75/126 preannotated units
retained versus 78/126 for the baseline and 82/126 for a post-hoc sentence-filtered
baseline; 58/58 emitted passages exact source spans; fetch-to-render median
33.8 s, max 39.9 s. **The workflow did not meet its coverage targets and did not
show an information-recall benefit over deterministic extraction on this set.**
Do not cite these figures as model accuracy; the annotations are not independent
human gold and the set is one publisher. The contextual-precision script encodes
the assistant's stated review as fixed all-supported verdicts with article-level
rationales; it is not an automated semantic grader. The earlier review overstated
this as invalidating the recorded judgments. Preserve them as assistant judgments,
not independently reproducible proof of semantic precision.

A separate assistant review traced specific omissions to code and prompted the
0.8.1 repairs listed in CHANGELOG.md: simple table rows kept on one line, short
fragments excluded from the selector pool, policy v6 for prerequisites/rejections,
and protection reasons carried into the reading view. The initial checkpoint
passed 264 offline tests, including seven added tests (some preventive rather
than demonstrated failing-first). Saved-ID replays improved selected known cases;
the deprecation brief remained held. These are development regressions, not a
new model-accuracy measurement. Because only extracted bodies were saved, those
replays and the budget comparison cannot test the repaired HTML table extraction.

Shipped model, prompt, sampling, context and the 512-token reasoning budget remain
unchanged. Eighteen of twenty v1 calls had completion-token counts near the
reasoning cap, suggesting budget pressure. Total completion tokens include the
answer, and a nonterminal reasoning ending is only a heuristic; neither proves
that the budget caused the empty response. The earlier claim that truncation was
almost certainly the cause was too strong. The isolated comparison below tests
1024 without promoting that setting.

The frozen v1 corpus is now development/regression evidence, not a holdout.
Some critical labels combine several facts or make field definitions mandatory
when the brief never mentions the field; they need prospective adjudication,
not score-driven relabeling. A future holdout must verify prior exposure, use
atomic relationship-preserving anchors and preregister the sentence-filtered
baseline and passage-level contextual judgments. No private deployment, schedule
or delivery changed.

## September 21 isolated reasoning-budget comparison

**Decision: keep the shipped 512-token setting and human review; do not promote
production or claim inference superiority.** The owner authorized 40 calls total:
20 at 512 and 20 at 1024, each covering the same eight real articles and four
synthetic cases twice. Four preflight holds per arm made 48 case-runs in total.
All 40 calls completed with valid responses; an empty response is not a quality
success. No retries, hosted requests, source refetches or Telegram sends occurred.

Both arms used the frozen initial 0.8.1 commit `8065f2e`, identical source bodies,
gold, pools, prompt and runtime. Only the isolated 1024 arm's selector budget and
matching transport budget check differed. This is a known-corpus development
comparison, not a new holdout. It does not live-test the final corrections below.

| Real-article measure | 512 tokens | 1024 tokens | First-two deterministic baseline |
|---|---:|---:|---:|
| Detailed briefs (not quality passes) | 12/16 | 14/16 | 12/16 |
| Retained annotated units, holds/empty = zero | 74/126 (58.7%) | 90/126 (71.4%) | 80/126 (63.5%) |
| Recall conditional on a detailed brief | 74/88 (84.1%) | 90/106 (84.9%) | 80/90 (88.9%) |
| Critical omissions in emitted briefs | 5 in 3 briefs | 6 in 4 briefs | 2 in 2 briefs |
| Frozen content gate passes | 6/16 | 6/16 | 6/16 |
| Frozen-text-to-render median | 34.00 s | 54.51 s | 0.26 / 0.21 s by arm |
| Frozen-text-to-render nearest-rank p95/max | 39.06 s | 72.64 s | 0.69 / 0.65 s by arm |

At 512, the dashboard first repeat and roundup second repeat unnecessarily
selected nothing. At 1024, neither did; the deprecation article remained held
both times in both arms. Selected IDs were identical across repeats for 5/8
articles at 512 and 7/8 at 1024. This small, non-counterbalanced comparison ran
512 first, then 1024, with stochastic sampling and different cache histories;
it does not prove why any individual response changed.

All 61/61 and 76/76 emitted real-article passages respectively passed the
normalized source-span check, not an independent semantic-precision test.
Raw model selections covered 43 and 48 units; rules retained 37 and 48 additional
units respectively, while 6 raw-selected units per arm were absent from the final
view. This overlap accounting avoids attributing rules' work to the model.

The first-two baseline was held on R01 because the cleaned pool exposed an
unfinished list introduction. An **exploratory offline recheck**, using the
previously proposed rule (first two pool blocks of at least 60 characters ending
in `.`, `!` or `?`), retained **90/126 units with 14/16 briefs**, matching the
1024 arm's per-article recall. This was not the preregistered comparator for this
budget experiment; its Mac latency is not compared with the remote run.

Security edges remain material: the 512 arm selected the synthetic indirect
instruction paragraph on one repeat. It was quoted in the review output, not
executed; no tools, secrets or delivery authority were available to the model.
The other repeat and both 1024 repeats avoided it. Sparse teaser abstention,
explicit-pattern injection holds and oversized-source holds behaved as expected.
This is not general prompt-injection resistance. Preserve the failed selection.

Completion-token counts were at least the respective reasoning budget on 18/20
and 6/20 calls; the recorded nonterminal-ending heuristic flagged 18/20 and 4/20.
These are proxies, not server-certified budget-exhaustion or natural-finish rates.
The higher budget improved observed coverage/availability but still missed the
90% targets and zero-critical-omission gate, and did not beat the stronger
exploratory deterministic comparator. No automatic default change is warranted.

Timings include warm-runtime selector preflight/inference, validation, formatting
and artifact writes. They exclude fetching, RSS, scheduling, server startup,
human review and Telegram delivery. Among rendered briefs, medians were 34.00 s
and 53.03 s; maxima were unchanged. Repeats are not independent articles, and
small-sample p95 equals max here. Cleanup passed for both arms: temporary listener
closed, original process/health and protected code/configuration/schedule hashes
unchanged. The 40-call authorization is consumed; no further inference is implied.

## Final 0.8.1 offline release verification

Review before publication found additional edge cases in the initial repairs:
nested/spanning table structure, hidden table state, selected protected API
passages and malformed rule metadata. Six additional tests now cover these;
five reproduced failures before correction and one preserves existing guards.
**270 tests pass**, also with real sockets/process launches blocked and in a
fresh 63-file allowlisted export. Both demos and isolated state initialization /
source-only build pass. Export, local-link, standard-library dependency, targeted
credential-pattern and whitespace checks pass; this is not a security certification.

Both original 0.8.0 acceptance responses were revalidated under their original
packets using frozen code, then replayed with unchanged IDs against new policy-v6
packets. Source qualifications survive in both briefs. The labeled saved replay
uses two parts (1,756 and 1,942 UTF-16 units), with zero new model calls or sends.
Earlier evidence and samples remain historical. Final code differs from the
frozen budget experiment; these last corrections have offline evidence only.
Publication shares review-required source code, not a private-runtime deployment.
The proposed next holdout protocol is in [specs/roadmap.md](specs/roadmap.md).

## September 21 publication checkpoint (0.8.0)

The owner authorized Git publication after reviewing the acceptance findings.
The preparation-context false hold below is repaired in the deterministic reading
layer. Three new positive regression cases failed before the correction; all
**257 offline tests** now pass, including incomplete, missing, hash-mismatched,
ambiguous, nested and oversized context cases. General unfinished restriction
lists remain held. No model prompt, selection packet or inference setting changed.

The 257-test suite also passes with real socket connections and process launches
blocked, and in a fresh 63-file export. Both offline demos, state initialization
and source-only build pass from that export. The export allowlist, relative links,
standard-library imports, targeted credential patterns and Git whitespace checks
pass. This is a bounded automated review, not a security certification.

Both original saved responses were revalidated against their source packets and
replayed offline. Both produce usable briefs; migration dates, breakage warning,
test/pinning instructions and relevant access/privacy qualifications survive.
The repaired replay fits one 2,922-UTF-16-unit Markdown part, including its explicit
saved-replay label. No text was cut to force that fit. Original failed output and
delivery history remain intact. This is a known-case regression check, not new
inference, a new Telegram delivery, a holdout or a general completeness guarantee.

Public source release does not deploy to the owner's private runtime. Broader
source evaluation, owner visual acceptance and scheduled-operation observation
remain separate. The reference scheduler still collects/prepares only; per-edition
Telegram approval remains explicit. The historical checkpoints below record what
was known at each stage and do not supersede this current status.

## September 21 actual local-model and Telegram acceptance

**Initial result (before the offline repair above): hold publication.** The authorized live acceptance test found a formatter
regression despite 250 offline tests passing on both Mac and Linux. Two newly
fetched historical GitHub articles received fresh CPU-only MiniCPM selections.
Both responses were valid and source-bound; selector completion took 36.54 and
34.65 seconds (867 and 851 total tokens; the second reported 124 cached prompt
tokens). Two observations on known cases are not a speed or accuracy benchmark.
No inference retries or hosted calls occurred.

The Ubuntu article was correctly selected but its brief was held because a
protected paragraph ends in `To prepare:`. The full source contains the following
guidance. The conservative incomplete-context formatter did not assemble that
context, so it suppressed a useful brief rather than show it. This fails the
two-brief acceptance gate. Fix with complete-context regression coverage; do not
remove the safety check or regrade the source-only result as a success.

One clearly labeled historical test edition reached the existing private Telegram
chat through the candidate's actual HTML sender: one reviewed CLI-metrics brief
and one held Ubuntu source link. Provider confirmation does not establish the
owner's visual acceptance. Model/runtime identities were checked; the temporary
runtime stopped and the original service remained healthy. Production code,
archive, schedule and recipient configuration remained unchanged. No publication
or deployment occurred. Both authorized model requests and the one-edition budget
are consumed. The earlier offline checkpoint below is preserved as history.

## September 21 public-readiness candidate

Decision: offline implementation checks pass; **hold live-release acceptance**
pending an explicitly approved local-model/test-chat run, human review and source
publication. No private deployment or installed schedule changed in this pass.

Baseline public 0.7.5 had 203 passing tests but failed new synthetic audit cases:
technical operators/paths were removed in display, and a commercial-use prohibition
outside the model pool could disappear without a hold. New policy v5/formatter
cases reproduce those failures before the repair. The candidate has **250 passing
offline tests**, also passing with real sockets and subprocess launches blocked.
These are development/regression cases, not an untouched model holdout.

Tests cover visible technical-text round trips, licensing paraphrases, incomplete
restrictions, inert hostile markup, RSS identity/encoding/DTD/size checks, private
state permissions and locks, attempt/fetch budgets, full mocked selection-to-report
flow, report-save failure, changed content/bot/destination, approval expiry/reuse,
partial confirmations, ambiguous send blocks and safe unsent cancellation. All
critical permission/duplicate-send cases pass. Transport/model mocks are labeled
as such; no real model generation or Telegram request was performed in this pass.

Two real registered feed fetches succeeded after correcting two newly observed
compatibility failures: GitHub embeds inert HTML doctypes inside CDATA, and OpenAI
publishes more than 200 historical entries. XML DTDs outside text remain rejected;
the bounded item limit is now 2,000 with a 2 MB response limit. GitHub intake accepted
10 items; OpenAI accepted 1,143 and rejected 68 unsupported article links. These are
feed-entry counts, **not today's news count or complete company coverage**. The
current 24-hour test preview selected one source-only item, with zero article/model
attempts and no delivery. Initial failed checks are not presented as successes.

Both offline demos pass. The generated fictional report was inspected on desktop
and at 390px mobile width; the supporting table now stacks labeled rows. The new
preview screenshot is fictional, not a model outcome. Local documentation links,
63-file export allowlist and standard-library import checks pass. A targeted
credential-pattern scan finds no matches; this is not a security certification.

Environment: Python 3.14.7 on the local Mac; candidate 0.8.0. Model/prompt/runtime
settings remain as documented below, but the protection policy changes packet
hashes. Baseline historical packets/results remain unchanged. CI is defined with
pinned official action commits, but a local run is not a GitHub Actions result.

Remaining gate: test the public commands with the actual local model, compare full
source context, then explicitly approve and inspect a test-chat delivery. A later
scheduled observation is separate. The reference example schedules collection and
preparation only; automatic delivery approval is deliberately not included.
Do not promote these offline counts into a model accuracy, savings or unattended
reliability claim. Release decision owner: Mark; rollback is to keep the unchanged
private runtime until separately approved promotion.

## September 18 deployed 0.7.5 and fresh Telegram delivery

The owner approved promotion of the reviewed 0.7.5 formatter into the private
integration. Staging and deployed checks passed 203 public tests and 74 private
integration tests (277 total), plus five saved-result replays. All nine portable
Python modules match public code commit `2943c67`; later documentation-only commits
do not change those modules. Rollback files and prior evidence were preserved.

One newly prepared edition used the exact preceding 24 hours ending September 18
at 12:16 PM America/New_York. Discovery reported 28/28 registered sources successful;
nine of 24 eligible items were selected. This is not coverage of every company
channel or full-article/model coverage of all 28 sources.

Two fresh local MiniCPM requests produced source-bound briefs, with runtime identity
and cleanup checks passing. The Ubuntu migration request took 37.27 seconds
(342 prompt + 476 completion = 818 tokens); the agentic CLI metrics request took
40.16 seconds (326 + 525 = 851 tokens). Both were manually compared with their full
retrieved source texts. Migration dates, pinning guidance, setup requirements and
relevant access/privacy qualifications remained visible. These are development
cases, not an unseen holdout or independently graded accuracy estimate.

Four fetch reservations and two model attempts were used; no full-article or model
failures, inference retries or hosted requests occurred in this edition. Seven
other selected items were source-only quick hits: six had publisher descriptions,
one was headline-only. Those are not seven additional model summaries. Fifteen
eligible items remained outside this edition and were disclosed as overflow.

The actual delivery adapter confirmed both numbered Telegram messages. Production
archive, schedule, destination and original collector remained unchanged; the test
used isolated delivery state. Provider API charges were zero; hardware/electricity
and review time were not measured. First scheduled morning delivery remains
unobserved as of September 18. This confirms the tested manual end-to-end path,
not future unattended reliability. Private sources, reasoning and recipient IDs
are not published.

## September 18 public-package review (0.7.5)

203 public offline tests pass. Six added tests reproduce selected navigation/API
reference passages losing access, pricing, safety or date qualifications; ISO-date
and migration clauses being hidden as navigation; and a background safety warning
being removed. The earlier suite passed while these new cases failed on 0.7.4.
The formatter now retains those qualifications, still removes plain navigation,
and avoids duplicating a qualification already displayed. No model/prompt,
source-selection policy, schedule or integration change is part of this release.

At the initial public-package checkpoint this was offline-only evidence, with the
private runtime still on 0.7.4. The separately authorized 0.7.5 deployment and new
model/delivery measurements are recorded above; earlier outputs are not relabeled.

The public suite also passed with real network connections and child-process
launches blocked. A clean 43-file copy passed all 203 tests, both no-model demos
and preparation of the historical synthetic article under the current policy.
Relative documentation links, export allowlist, synthetic provenance and private-
file ignore rules passed checks. Imports are standard-library-only. A targeted
credential/private-path scan covered the public tree and 100 historical Git blobs;
reviewed synthetic hostile-URL fixtures were the only matches. This is a bounded
review, not an independent security certification or exhaustive secret detector.

## September 18 fresh model to Telegram (0.7.4)

The final owner-requested test used the deployed private 0.7.4 pipeline and a
current collector snapshot: 28/28 registered sources reported success, with nine
stories selected from 21 eligible in the preceding 24 elapsed hours. Those counts
describe discovery, not full-article/model coverage.

The first manual launch used the wrong working directory. Two fetch workers could
not import the package and failed before HTTP; no model ran. The links-only output
was withheld. Three metadata attempts also consumed fetch budget. After correcting
the test's working directory, only the sixth remaining fetch allowance was used
for the affected Ubuntu migration article. The configured scheduled job already
had the correct working directory; no cron change was made.

One fresh local request completed in 40.57 seconds including runtime checks and
cleanup (342 prompt + 525 completion = 867 tokens). Source comparison confirmed
the migration dates, pinning alternative, supported architectures, setup labels
and breakage warning remained visible. No model retry or hosted fallback occurred.
The resulting one model-derived brief plus eight explicitly source-only items
were delivered in two confirmed Telegram messages. One other failed article was
not fetched again within the budget. Archive and schedule were unchanged.

This verifies that specific repaired case through generation and delivery after
operator recovery, not a clean unattended all-article pass or unseen holdout.
First scheduled morning delivery is still unobserved as of September 18, 2026.
Raw sources, model reasoning and recipient/message identifiers remain private.

## September 18 date-preservation repair

The previous current-data run completed three local requests, but content review
found one incomplete brief: an Ubuntu migration date range and version-pinning
option were absent. The full source was available. Protected-block patterns missed
"between October" and "roll out"; successful requests/tests were not sufficient
evidence of completeness. The original failed output remains preserved privately.

Policy v4 fixes these patterns and protects related compatibility/deferral advice.
197 public tests plus74 private tests pass (271 total), including nine new date,
migration, navigation, identity/qualification and injection regression cases.
Five saved-result replays from four distinct articles preserve prior substantive
content, add the missing date/pinning passages and remove only a navigation note.
Packets were regenerated for explicit replay; historical responses were not
silently relabeled as outputs of the new policy.

One fresh local MiniCPM request on a newly fetched affected article completed in
40.48seconds (866 total tokens). Dates, pinning option, source scope and breakage
warning survived the reading view; runtime identity/cleanup checks passed. No
hosted fallback or retries. Combined validation preview: one fresh card plus two
saved selections, three parts, not sent. It is not a new all-fresh edition.

The known defect is fixed and verified; this is a development regression test,
not an unseen holdout or universal completeness claim. Longer editions can need
three messages. First scheduled daily delivery remains unobserved.

## September 18 quick-hit context

188 public plus 74 private tests pass (262 total). Regression cases cover fixed
source/host/path checks, metadata ambiguity/truncation, hostile markup, preserved
conditions, source identity, shared six-fetch reservation, missing budgets, stale
sources, short one-part and longer lossless multi-part editions. Network and child
process launches were blocked in the offline suite.

The same nine-item development edition was replayed with its two saved model cards.
Two quick-hit descriptions came from complete feed sentences; four bounded official
metadata requests yielded two more usable descriptions. Thus four of seven quick
hits gained context; three remained honest headline-only links. Two full-source
fetches from the original edition plus four metadata requests used its six-fetch
allowance. No new model calls, hosted requests, sends or daily-archive changes.
The preview uses two parts (2,771 and 2,247 formatted UTF-16 units). A single part
would exceed the delivery adapter's safe limit; no text was dropped to force it.

This is source-extractive presentation evidence, not seven full-article summaries,
a new model evaluation, independent verification of publisher claims or a holdout.
The underlying model, prompt, daily schedule and original collector are unchanged.

## September 18 current-data polish test

171 public tests plus 71 private tests pass (242 total). The current-data test
sampled the nine newest discoveries inside a rolling 24-hour window across six
sources. That sampling was test-only; scheduled daily importance ranking is
unchanged. The collector reported 28/28 sources successful, not full-article
coverage of all sources or all company channels.

Two fresh local MiniCPM requests processed newly fetched GitHub pages, finishing
in 40.15 and 41.73 seconds including runtime checks/cleanup (850 and 947 tokens).
Both produced validated selections, with cleanup verified and no retries or paid
fallback. The articles had appeared in earlier saved replays; these are fresh
generations on current retrieved pages, not unseen holdout stories. The other
seven selected items were explicitly source-headline links, including newly
collected Google and AWS posts whose full-source adapters are not implemented.

A two-part live-test edition was confirmed delivered to the private test chat.
The daily production archive, schedule and original collector were unchanged.
The formatter was then promoted after tests; no prompt/model change. A temporary
test ledger separated its delivery from the scheduled daily recap. This proves
the tested current-data path, not broad reliability or new-vendor summarization.
Provider API charges were zero; electricity/hardware costs were not measured.

Polish joins short related passages, uses one inline caveat or multiple bullets,
removes per-headline decorations, uses validated named source links, and groups
quick hits under one source-only disclosure. Exact source words remain intact.
First scheduled daily delivery is still a separate pending observation.

## September 18 editorial repair

166 public tests and 71 private integration tests pass (237 total, not additive
with earlier counts). Nineteen new public cases cover scope/price/date clauses,
field-specific definitions, unsafe/incomplete excerpts, report escaping, preview
dates, whole-story packing and explicit continuations. A private test asserts
the full report is saved before delivery. No model/prompt change or new inference.

Three previously reviewed real GitHub cards were replayed. Story text decreased
from 328/378/336 words to 159/131/151 words; the edition moved from three messages
to two while retaining source access, relevant definitions and rollout limits.
All three complete extracted articles remain in the private report. These are
development replays, not holdout results or broad cross-vendor accuracy evidence.
Word targets remain soft; these examples still exceed some preferred lengths.
The baseline failed reader-quality review despite passing delivery/software tests.

Qualification selection uses English rules and can miss relationships. Unknown
conditions are retained conservatively. Unsupported sources remain headline links.
The fictional multi-company demo demonstrates layout, not live company coverage.
First scheduled morning delivery still requires observation.

## Earlier September18 daily recap update (0.7.0)

Owner approved the daily24-hour recap and public repository update. The public
standard-library suite passes147/147; the separate private integration suite
passes217/217 including those147. These counts are not additive. New cases cover
24-hour boundaries, stale/future dates, late discoveries, revisions, URL/title
deduplication, DST, backlog disclosure, safe formatting, ambiguous sends and
confirmation-before-consumption. No new model generation was needed for the
recap assembly: three saved real GitHub results were replayed with exact source
passages/conditions retained. A three-part private Telegram preview was delivered.
First scheduled daily delivery remains a separate pending observation.

Earlier September18 qualification: three real local MiniCPM calls took41.93,
40.36 and42.52 seconds (2768 total tokens). All three passed structure, source
comparison and runtime cleanup for a limited private pilot. All were GitHub
articles, development cases—not an untouched holdout or cross-source accuracy
claim. No hosted API cost; electricity and human review costs were not measured.

Presentation remains extractive, not fluent free-form newsletter writing.
Some preserved source transitions can be awkward; word targets are soft to avoid
cutting qualifiers. Unsupported/blocked vendors get source links. The ranking
heuristic does not establish objective importance. No breaking alerts.

The current protection policy adds thresholds/count definitions, effective dates
and important-note sections. The policy hash in the historical section below
belongs to v0.6.1 and is not the current runtime policy. Current packets bind
their own policy/source hashes. Previous failed runs remain valid evidence.

## Historical v0.6.1 record

Run date: September 17, 2026. Owner: Mark Fenner. Decision: owner approved public
source publication as a local package on September 17, 2026.
This approval does not establish unattended production reliability. A separate
private three-hour delivery pilot was scheduled at that checkpoint; its results
are not included in the historical measurements below. Subsequent checks showed
all three messages delivered but zero model calls; this was not inference proof.

## Measurements kept separate

| Evaluation | Outcome | What it establishes |
| --- | --- | --- |
| v0.5 local development run | 4/5 structured; 3/5 usable without correction | Earlier failure baseline |
| v0.6 reasoning/selection repair | 8/8 structured; 7/8 semantic | Original exhaustion and role-selection regressions passed repeats; one new unnecessary abstention |
| v0.6.1 offline replay | 8/8 application handling; 2 source fallbacks | Full-source degraded presentation handles empty selections; no new model calls |
| v0.6.1 fresh Linux CLI test | 3/3 application and semantic passes | Actual CLI/worker/report path executes on the local-model host |
| v0.6.1 offline tests | 110/110 | Deterministic positive/negative software checks, not model accuracy |

The repair run had six useful nonempty selections, one appropriate abstention
on sparse data and one inappropriate abstention. The all-eight semantic threshold
was not met. The fallback keeps this failure visible, not regraded as model success.
The later three calls used one saved real xAI article and two repetitions of the
fictional transcription regression. All three selected relevant highlights; no
fallback was triggered. Earlier failures remain valid evidence.

No holdout was used. The repair set included two real saved articles and four
synthetic cases, with repeats making eight attempts. These are development and
regression cases. No broad accuracy estimate, statistical significance or new-news
delivery qualification is claimed. Original facts are source claims, not independently
verified. Grading: deterministic structure/binding/cleanup assertions plus assistant
source comparison; not independent expert or final owner acceptance.

## Model, runtime, permissions

MiniCPM5-2B-Q4_K_M; llama.cpp build 10809/5266f24da; Python 3.14.7; CPU-only,
four threads. Context 8192, output 4096, reasoning_budget_tokens 512, temperature 1.0,
top_p 0.95, min_p 0, repeat_penalty 1.05, thinking enabled. Model SHA256:
`ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd`.
The model gets no tools, credentials or publishing authority. Temporary authenticated
loopback servers and package directories were cleaned up after every attempt.
Existing services stayed healthy and unchanged. No retries or hosted fallback.

Prompt SHA256:`45c6ec8db8380242c8f7c1ec1682cd20d0364c8cc88ebccff6ec40c52d98fb4c`.
Policy SHA256:`e4d258a7f7c54f60f6213d4699dffd33ab077e5ba7db1a57bfb60e79ecee29e9`.
Versioned private receipts retain complete prompts, cases, hashes and raw responses.
They are not distributed here because they include real source archives and private
infrastructure. The public synthetic tests can be rerun; this document is a sanitized
summary, not a fully public reproducibility bundle for the real-article runs.

## Time and cost

Repair run: 8 calls, 452.3s total, 58.6s median; 2,463 prompt + 3,730 completion tokens.
Fresh Linux CLI run: 3 calls, 178.6s total; 60.7s, 58.8s, 59.0s each;
820 prompt + 1,577 completion = 2,397 tokens. Times include setup/checks/cleanup.
All fresh CLI responses finished normally. Returned reasoning retokenized to 511
tokens each, observational evidence that the cap took effect on the tested runtime.

Provider API charges: $0 for local inference. Electricity, hardware and review time
were not measured. There is no controlled hosted-cost comparison or net savings
claim. The earlier v0.5 five-call run took 21m50s; prompt/task changes prevent
attributing the time difference solely to the reasoning cap.

## Historical v0.6.1 limitations and acceptance

Source-protection rules are heuristics. The model may choose irrelevant passages
or abstain unnecessarily; nonempty wrong selections are not universally detected.
Source-only fallback may be longer than a brief. Long documents are held rather
than clipped. Retrieved-page shape, source dates and platform access can change.
Only OpenAI /index/, xAI /news/ and GitHub /changelog/ body adapters are included.
No scheduler, delivery integration, fresh-source holdout or browser/mobile visual
acceptance is bundled or claimed. Use OPERATIONS.md for review and failure intake.

Before scheduled use: representative source holdout, owner acceptance, explicit
schedule/destination/budget, dedupe and delivery receipts, monitoring and rollback.
Publication is a separate owner decision. Previous submitted materials stay intact.
