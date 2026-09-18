# Evaluation — 0.7.2 daily recap preview

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
source publication as an experimental local package on September 17, 2026.
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

## Remaining limitations and acceptance

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
