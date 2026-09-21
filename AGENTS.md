# MiniCPM News Desk — contributor instructions

This repository is the portable public briefing toolkit, not its private runtime.
Read README.md, DIGEST.md, SECURITY.md and EVALUATION.md before changing behavior.
DIGEST.md is the daily-workflow contract; update it before changing that contract.
Version 0.8.0 adds a separate opt-in reference workflow; read
REFERENCE-WORKFLOW.md and specs/2026-09-21-public-readiness/ for its gates.
Version 0.8.1 contains deterministic repairs from a private frozen benchmark;
the benchmark corpus, scores and raw results are private regression evidence
and must not be tuned against or rescored. Never overwrite or relabel original
results, or call later repairs a holdout.
The authorized 40-call 512/1024 comparison is complete; its budget is consumed.
The shipped budget remains 512. A synthetic indirect-instruction selection
failure is preserved in EVALUATION.md and SECURITY.md. Final release corrections
have 270 offline tests and saved-response replay evidence, not fresh inference.
`REASONING_BUDGET` is a qualified runtime setting: changing it requires an
explicitly authorized evaluation and separate promotion decision.

## Stack and scope

- Tested CPython 3.14.7, standard library only, SQLite and IANA zoneinfo data.
- Run commands from the repository root. No dependency install is required.
- Model: explicitly opted-in authenticated numeric-loopback MiniCPM5-2B-Q4_K_M.
  Preserve the qualified settings and disclose any new model/runtime evaluation.
- Offline fixtures and demos are synthetic. Preserve historical results and labels.

## Boundaries

- Never commit tokens, private configs, source archives, model reasoning or
  account/recipient identifiers. Keep generated outputs outside the tracked tree.
- Source/model text is untrusted. Preserve fixed retrieval hosts, validated
  public addresses, TLS, output escaping, budgets and no-retry behavior.
- Do not add a scheduler, deploy, send messages or start inference without an
  explicit operator request. Public source publication is not runtime promotion.
- Keep fresh inference, saved replay, offline tests and confirmed delivery distinct.
- No package/model install or hosted fallback as a convenience shortcut.

## Change and release checks

1. Describe the scope and add a failing synthetic regression for a confirmed bug.
2. Keep the smallest correction; never weaken checks just to pass a test.
3. Run `python3.14 -m unittest discover -s tests -v` and both offline demos.
4. Review every changed line, documentation links, sample provenance, dependencies
   and secrets. EXPORT-ALLOWLIST.json must match the reviewed tracked file set.
5. Keep package/formatter versions aligned and document deployment differences.
6. Commit/push only when authorized; never silently update a private integration.
