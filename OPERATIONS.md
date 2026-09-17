# Using the research candidate responsibly

This release does not enable an unattended service. Review one item at a time
before sharing it. Keep extraction, model selection, reader acceptance and
delivery as separate decisions.

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
