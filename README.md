# MiniCPM News Desk — 0.6.1 research preview

An experimental local-first news reader powered by MiniCPM5-2B and ordinary
Python. It helps an operator review official announcements with source-linked
passages and explicit access, pricing and setup conditions.

**Experimental public research preview. Review required. No automatic delivery.**
Project code is MIT licensed; see LICENSE. Model/runtime licenses remain separate.

## Quick start — no model required

Tested with Python 3.14.7; standard library only. No pip or npm installation.

```sh
git clone https://github.com/fenner888/minicpm-news-desk.git
cd minicpm-news-desk
python3.14 -m newsdesk demo --out outputs/demo-1
python3.14 -m unittest discover -s tests -v
```

Open outputs/demo-1/index.html. The example is synthetic, uses hand-selected IDs,
and performs zero inference. Each command requires a new output directory.

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
OpenAI direct retrieval failed with HTTP403 on one tested Mac and succeeded on
one Linux host; there is no automatic alternative transport.

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

- Every output requires meaning review. Longer reports preserve context but can
  repeat facts; they are not polished automated newsletters.
- Overview candidates are the first four eligible blocks plus up to three later
  practical-use blocks. Excluded counts are disclosed; full text stays available.
- Budgets: 7,000 source characters, 120 blocks, 2,000 per block; protected text
  5,500 characters/30 blocks; pool 4,000/25; selected text 1,800 characters total.
  Exceeding a limit holds the item instead of silently clipping it.
- English heading/demo heuristics can miss context. Known instruction-like
  patterns hold the item but are not comprehensive injection detection.
- No matching price passage does not mean free, unrestricted or unannounced.
- No accounts, public API, UI dashboard, automatic publishing or delivery.
- Legacy free-prose library functions remain for regression compatibility; the
  CLI uses the ID-only selector. Read SECURITY.md for the trust boundaries.

## Evaluation and distribution

Read EVALUATION.md for outcomes, failures and corrections by version. Offline
tests are not model accuracy. No matched cloud-cost comparison or general
reliability claim is made. API charges for local tests were zero; hardware,
electricity and review time are not zero-cost or measured savings.

Latest evidence: 110 offline tests; the earlier repair produced 7/8 semantic passes,
followed by 8/8 offline saved-response handling checks. A separate fresh Linux CLI
smoke test passed 3/3, including two repeats of the previous abstention case. Those
are separate measurements, not one combined accuracy score.

Source/model archives and credentials are excluded. Synthetic fixtures are
project-authored. Model weights, runtime binaries, third-party articles, images
and music are not bundled. Public release and unattended use are separate
acceptance decisions; this package does not grant authority to change a service.
