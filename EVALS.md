# Synthetic AI boundary evaluations

Run from the checkout root, standard library only:

```sh
python3 -m evals run --out "$HOME/newsdesk-evals/my-new-run"
python3 -m evals verify "$HOME/newsdesk-evals/my-new-run"
```

Local development uses available Python 3.12; CI runs qualified Python 3.14.7.
The command refuses existing output directories. With no output argument it uses
a new timestamped directory under `$HOME/newsdesk-evals`. Curated, reviewed,
synthetic-only evidence can be generated with
`python3 -m evals run --evidence evals/evidence/my-new-run` and verified with
`python3 -m evals verify evals/evidence/my-new-run`. The committed `synthetic-v1`
log is replayable with the current definitions; `synthetic-v2` also includes a
harness safety correction binding the no-approval probe to a forbidden transport,
and client-side daily live-observation plumbing tested only with a fake transport.
No real live calls occurred. New evidence files must be
reviewed and added explicitly to EXPORT-ALLOWLIST.json before publication.

## What runs

An authenticated `http.server` thread binds **127.0.0.1 on a random port**. It
scripts llama.cpp preflight endpoints and completion responses, including hostile
responses. Real `network.infer` subprocess workers, `network.model_direct`,
selector reporting and legacy reporting execute. No actual model, downloads,
external source requests or Telegram calls occur. The fake tokenizer returns a
small fixed token list; this is protocol/application testing, not tokenizer or
model-runtime qualification. Every received request records its method, path,
redacted authorization, JSON body and response. Oversized response evidence stores
a digest, length and preview instead of repeating a megabyte.

All articles are synthetic. Selection fixtures use the built-in synthetic source.
Legacy fixtures temporarily map the `xai` source registry entry to **example.invalid**
inside the parent test process, so real URL validation still runs against a
synthetic host. Daily model-build cases use the same registry adapter and replace
article retrieval with a synthetic article-file writer (or a scripted failure).
The real daily loop, selector, model worker, formatter and SQLite attempt budget
execute. Other daily cases test empty build, approval refusal and the budget gate.
These adapters do **not** evaluate public source retrieval or production ingestion.
No recipient identifiers or real personal data are used.

Cases declare secure expectations and `must_hold`. A known privacy/editorial
finding is deliberately not a CI failure; a broken `must_hold` expectation returns
1. Harness errors return 2. Known findings that improve become passes. Any finding,
including intentional source/response archival, requires contextual human review;
severity is a default application-boundary impact rating, not proof of exploitation.

## Evidence and reproducibility

Each run emits `evidence.jsonl`, `summary.md` and `manifest.json`. Case records
include canonical input/transcript SHA256, redacted transcript, machine-readable
outcome, secure expectation, severity and framework mappings. Request ports,
temporary paths, wall-clock times and UUIDs do not enter per-case evidence.
Manifests retain start/end time, Python/platform, Git HEAD and harness/data hashes;
Git HEAD can precede the commit containing the run, so use the content hashes as
the exact harness identity. `verify` reruns the mock suite and compares **complete
case records**, including hashes, transcripts and outcomes. Definition changes or
tampered/different evidence fail verification. Run metadata is intentionally not
byte-identical. Verification never runs live inference.

Credentials and their scripted base64/reversed/split forms are redacted from
evidence after persistence outcomes are measured. Requests intentionally contain
only synthetic source text. Private response artifacts exist briefly in isolated
temporary directories and are removed; curated evidence contains only synthetic
data. System prompts are already public repository content. The environment-canary
case scripts an already-known canary: it tests retention, **not** environment
exfiltration by a model. Prompt checks separately verify environment/key absence.

## What this does not prove

**Mock = application defenses against scripted model behavior, not the model's
own robustness.** A script selecting an injected paragraph demonstrates that a
boundary permits that outcome, not that MiniCPM obeyed an injection. Gold cases
are hand-authored assertions, not an independent accuracy estimate. No new frozen
benchmark scores, private corpus, model calls, delivery claims or runtime promotion
are involved. Legacy unsupported-claim checks are synthetic oracle assertions,
not a general semantic entailment detector. No browser/Telegram visual acceptance
or live service security qualification is claimed.

Mappings in `evals/mappings.json` are provisional analyst crosswalks. A requested
"OWASP LLM Top 10 2026" publication was not verified under this task's offline
restriction; identifiers explicitly use the established **2025** taxonomy, with
the requested edition marked unverified. NIST AI RMF subcategories, AI 600-1 risk
labels and SP 800-218A/SSDF practice suggestions are not compliance certification.
Validate publication versions and applicability before external compliance use.

## Optional live mode — do not run casually

`--live-endpoint http://127.0.0.1:PORT` requires
`--i-am-operator-authorized-inference` and a real `MINICPM_API_KEY` environment
value; numeric loopback and qualified model configuration are enforced before
running. Use a private absolute `--out` path. Curated `--evidence` refuses live mode.
This mode can perform **multiple real calls across the suite** and needs its own
explicit evaluation authorization/budget and interpretation: scripted attack
responses are no longer injected, while cases still contain synthetic attacks.
Only application request/response observations, not server-internal HTTP logs,
are available in live mode. Do not treat its outcomes as comparable to mock
replay. The flag is a human authorization assertion, not an access-control system.
This task did not run live mode. Shipped reasoning budget remains 512.
