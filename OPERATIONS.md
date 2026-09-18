# Using the research candidate responsibly

This release does not enable an unattended service. Review one item at a time
before sharing it. Keep extraction, model selection, reader acceptance and
delivery as separate decisions.

## Daily recap integration

The intended cadence is one 08:00 America/New_York recap of the preceding 24 hours.
Collection can run hourly without hourly digest notifications. No breaking-alert
stream. See DIGEST.md for the durable state machine and delivery adapter contract.

The private reference integration is separate from this portable repository.
It reuses an existing collector, caps each edition at4 local attempts/6 fetches,
uses the existing approved Telegram destination and preserves the original radar.
The repository does not install its schedule or distribute its machine configuration.

Run module commands and integration processes with the repository root as their
working directory. Fetch/model worker subprocesses import `newsdesk` using that
environment. A private test launched elsewhere failed before article retrieval;
correcting its launch location enabled the subsequent real-model delivery test.
Do not misclassify `worker_failed` as a remote outage or automatically retry it.
Keep diagnostic stderr private if inspecting a custom integration.

The public 0.7.5 formatter update is not automatically installed into an existing
private integration. Back up state, verify code/version hashes, run its integration
tests and review a bounded output before promoting a new version. Do not claim
0.7.4 live-delivery evidence as 0.7.5 live qualification.

Observe first scheduled delivery separately from a preview send. Review source
failures, the number of full-source cards versus links, overflow, date coverage
and reading quality. Empty/blocked intervals are not model successes. Pause only
the digest integration for rollback; preserve archive and delivery receipts.
Never automatically retry an ambiguous send. Reconcile complete confirmed parts
without resending; unresolved preparation/partial delivery requires operator review.

## Review checklist

1. Does the title/link identify the actual original source?
2. Is the release date known? Do not mistake discovery time for publication.
3. Does the overview communicate a concrete change, rather than generic marketing?
4. Are intended users and practical uses supported by the quoted passages?
5. Are numbers, pricing, regions, rollout dates, approvals and setup requirements
   preserved with their conditions?
6. Are source claims clearly attributed, rather than presented as independently
   demonstrated results?
7. Does full source context change the meaning? Are omitted facts material?
8. Is the reading length useful? Keep manual edits separate from raw output and
   label the result reviewed if you correct it.

## Failure and feedback record

Retain the version, source hash, request/packet hash, raw response, failure stage,
elapsed time and token usage. Never log credentials. An unknown or missing field
stays unknown. Stop on transport/preflight failures; do not add unlimited retries.

For an incorrect or incomplete report, record expected vs observed meaning and
the material correction. Turn it into a synthetic regression where feasible,
then rerun tests. Freeze a new version before changing prompts or rules. Do not
reuse a tuned development case as an untouched release holdout.

## Before any future scheduled integration

Obtain owner approval for schedule, destination and inference limits. Require a
representative source holdout, deduplication ledger, reliable source timestamps,
an explicit read-only collector contract and confirmed delivery receipts. Monitor
source failures, no-new-item outcomes, model failures, latency and corrections
separately. Do not equate job completion with message delivery.

Rollback means disabling only the newly approved briefing integration and
returning to the existing collector/source-only workflow. Do not stop unrelated
services. For this package no integration is active, so there is nothing to
disable and no private service name or remote address is bundled.

Human acceptance and a later operational pilot are required before unattended
use; passing a small evaluation alone does not satisfy those gates.
