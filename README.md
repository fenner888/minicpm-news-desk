# MiniCPM News Desk — 0.7.5 daily recap preview

An experimental local-first news reader powered by MiniCPM5-2B and ordinary
Python. It helps an operator review official announcements with source-linked
passages and explicit access, pricing and setup conditions.

**Experimental public research preview. Review required.** The portable package
does not connect a Telegram account or install a schedule. A separate private
integration runs the daily workflow; bring your own collector and delivery adapter.
Project code is MIT licensed; see LICENSE. Model/runtime licenses remain separate.

The original personal setup uses an Intel Core i5-9400F Linux desktop with 16 GB
RAM and CPU-only MiniCPM inference. An existing private collector checks official
sources hourly; the private integration is configured to send one Telegram recap
of the previous 24 hours. This repository shares the reusable briefing logic,
not the owner's collector, Telegram account or machine-specific configuration.
That distinction also applies to screenshots of the actual Telegram test output.

## Current evidence

- **Public package 0.7.5:** 203 offline tests; includes a conservative fix for
  qualified passages being mistaken for navigation or background text.
- **Latest real-model delivery test, on 0.7.4:** one fresh local MiniCPM brief
  plus eight source-only items, delivered as two confirmed Telegram messages.
  The local request took 40.57 seconds. The test required recovery from an
  operator working-directory error; it was not a clean unattended run.
- The public 0.7.5 formatter has **not** been deployed or live-model tested.
  The first scheduled morning delivery remains unobserved as of September 18.

See [EVALUATION.md](EVALUATION.md) for evidence and limitations, and
[CHANGELOG.md](CHANGELOG.md) for the differences between versions.

## One daily recap, not another hourly feed

The target is an approachable morning reading experience: a lead story, a few
updates worth knowing, and smaller quick hits, all linked to original sources.

- Deliver around **8 AM America/New_York**; exactly the preceding **24 hours**.
- Collect independently throughout the day. No hourly MiniCPM messages or
  breaking-news alerts.
- Use source publication dates when available; otherwise label discovery time.
  Older articles are not recycled as fresh news. Listing revisions are updates.
- Up to nine items total: one lead and at most three additional detailed stories;
  remaining selected items appear as source links when no verified brief exists.
- Deduplicate canonical URLs and same-source identical headline/day events.
  This is deterministic editorial ranking, not comprehensive semantic clustering.
- Preserve material conditions. Word counts are soft targets, not truncation
  rules. Long editions split at paragraph boundaries into numbered messages.
- Keep overflow in a local archive; include it later only while it still meets
  the 24-hour window. Display the omitted count.

MiniCPM selects **exact source passages**, rather than generating free-form
newsletter prose. A deterministic editorial layer retains relevant qualifications
in the brief and moves navigation, unrelated field definitions and background
detail into a private supporting report. Unknown conditions stay visible. These
are English heuristics, not a guarantee of semantic completeness; review is still
required. Full extracted sources and placement reasons remain in the report.
No affiliation with Morning Brew.

Try the fictional daily layout without a model or network:

```sh
python3.14 -m newsdesk.digest demo --out outputs/daily-demo-1
```

Open the generated part-1.md and supporting-report.html (additional parts are numbered). All content is
fictional and hand-authored; the manifest records zero model calls. A shareable
example is in [samples/daily-recap](samples/daily-recap).

Read [DIGEST.md](DIGEST.md) for the queue, time-window and integration contract.

## Quick start — no model required

Tested with Python 3.14.7; standard library only. No pip or npm installation.
Use a Python build with IANA timezone data available: the daily formatter needs
`America/New_York`. Other Python versions/platforms have not been qualified.
If `python3.14` is not your executable name, use the path to your Python 3.14
installation rather than assuming the system `python3` is the tested version.

```sh
git clone https://github.com/fenner888/minicpm-news-desk.git
cd minicpm-news-desk
python3.14 -m newsdesk demo --out outputs/demo-1
python3.14 -m unittest discover -s tests -v
```

Open outputs/demo-1/index.html. The example is synthetic, uses hand-selected IDs,
and performs zero inference. Commands that write reports require a new output
directory. Run all module commands from the cloned repository root, including
when configuring an external job: subprocess workers must be able to import
`newsdesk`. An import-path failure is not a model or source-provider failure.

## How it works

1. Import a discovery snapshot or explicitly retrieve a supported article.
2. Preserve exact source text, identity, dates, hashes and offsets.
3. Retain condition-related passages using deterministic rules.
4. Optionally ask a local MiniCPM server to select up to two highlight IDs.
5. Resolve IDs to exact quotations and review the report against the source.

The model cannot rewrite claims, choose new destinations, call tools or send
messages. It can still choose irrelevant passages or omit useful ones. The rules
can miss conditions. Quoting a source is not independent verification of its claims.

If a valid model response selects nothing, the report explicitly displays the
full source as **SOURCE-ONLY FALLBACK**. This is unranked original text, not an AI
summary or a model-quality success. The manifest records `empty_source_fallback`.
Incomplete/invalid responses and held sources still fail closed.

Bundled `samples/synthetic-demo/index.html` shows ordinary selection;
`samples/synthetic-fallback/index.html` shows degraded handling. Both are fictional,
hand-constructed offline demonstrations with zero model calls. Their manifests
record provenance. They do not represent news or fresh inference results.

## Source preparation

```sh
python3.14 -m newsdesk article --source xai \
  --url https://x.ai/news/grok-build-memory --out outputs/article-1
python3.14 -m newsdesk prepare --article outputs/article-1/article.json \
  --out outputs/review-1
```

Article retrieval is an explicit network operation. Supported main-body adapters
cover xAI /news/, OpenAI /index/ and GitHub /changelog/. Individual pages can fail.
OpenAI retrieval has returned HTTP403/challenge on both tested hosts, including
the latest private check. No challenge bypass or automatic alternate transport
is implemented. Blocked/unsupported sources stay clearly labeled links.

Article also accepts --html path.html for an operator-saved document and
--snapshot snapshot.json for exactly matched discovery metadata. Imported HTML
origin is labeled unauthenticated. Never supply private account pages.

An existing collector can supply --input to the snapshot command. Snapshot JSON:

```json
{"version":1,"items":[{"source":"xai","title":"Example discovery","url":"https://x.ai/news/example","excerpt":"An illustrative excerpt, not a real release.","published":null,"first_seen":null}]}
```

Dates are Unix seconds or null. Unknown release dates stay unknown. Snapshots
are excerpt baselines, not full-article summaries. This package does not bundle
the original private collector, scheduler, SSH access or Telegram integration.
The new digest module supplies the portable archive, selection and delivery-state
primitives for an integrator; it does not infer that a prepared message was sent.

## Optional local model selection

Bring your own authenticated, already-running numeric-loopback server. This
package neither installs weights nor starts/reconfigures a server. The evaluated
identity is MiniCPM5-2B-Q4_K_M, llama.cpp b10809/5266f24da, thinking mode,
context 8192 and 4096 output tokens. Requests include `reasoning_budget_tokens=512`.
Use that qualified runtime: generic OpenAI-compatible servers may not implement
this control. Preflight checks model alias, context and template; it does not
cryptographically verify your external server's runtime or weights. Those were
verified separately in the original local tests.
See EVALUATION.md before deciding whether the measured latency suits your use.

Copy config.example.json to a private local config and provide MINICPM_API_KEY
through your secret mechanism. Never place the key in the config or Git.

```sh
python3.14 -m newsdesk select --article outputs/article-1/article.json \
  --config config.local.json --allow-local-inference --out outputs/selection-1
```

One explicit generation per invocation, 480-second outer deadline, no retry or
hosted-model fallback. Empty selections use the source-only presentation above.
Manifest reservation precedes transport. This is not a global
spending limiter. Raw responses remain separate from rendered selections.

apply-selection can validate a saved response offline with --article, --config,
--response, --packet-sha256 and --out. Its origin is labeled unverified.

## Deliberate limits

- Every output requires meaning review. The daily layout is implemented, but
  extractive wording may repeat context or preserve awkward source transitions.
- Overview candidates are the first four eligible blocks plus up to three later
  practical-use blocks. Excluded counts are disclosed; full text stays available.
- Budgets: 7,000 source characters, 120 blocks, 2,000 per block; protected text
  5,500 characters/30 blocks; pool 4,000/25; selected text 1,800 characters total.
  Exceeding a limit holds the item instead of silently clipping it.
- English heading/demo heuristics can miss context. Known instruction-like
  patterns hold the item but are not comprehensive injection detection.
- No matching price passage does not mean free, unrestricted or unannounced.
- No accounts, public API, UI dashboard or built-in messaging credentials. The
  digest engine is local; live scheduling/delivery remain integration concerns.
- Legacy free-prose library functions remain for regression compatibility; the
  CLI uses the ID-only selector. Read SECURITY.md for the trust boundaries.

## Evaluation and distribution

Read EVALUATION.md for outcomes, failures and corrections by version. Offline
tests are not model accuracy. No matched cloud-cost comparison or general
reliability claim is made. API charges for local tests were zero; hardware,
electricity and review time are not zero-cost or measured savings.

Historical selector evidence: 110 offline tests; the earlier repair produced 7/8 semantic passes,
followed by 8/8 offline saved-response handling checks. A separate fresh Linux CLI
smoke test passed 3/3, including two repeats of the previous abstention case. Those
are separate measurements, not one combined accuracy score.

The v0.7 digest adds rolling-window, DST, deduplication, archive, bounded selection,
numbered delivery and failure-reconciliation tests. Saved real model results were
replayed for presentation; they are not new model generations. See EVALUATION.md
for current counts and the distinction between public code and private delivery.

Source/model archives and credentials are excluded. Synthetic fixtures are
project-authored. Model weights, runtime binaries, third-party articles, images
and music are not bundled. Public release and unattended use are separate
acceptance decisions; this package does not grant authority to change a service.
