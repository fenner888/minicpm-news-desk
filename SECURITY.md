# Security boundaries and operator responsibilities

This is a local, single-operator experimental CLI. There are no public HTTP
routes, user roles, browser login tokens or multi-tenant storage. Local OS/file
permissions protect saved artifacts. Do not expose a generated report server
or model endpoint publicly based on this package's tests.

## Trust boundaries

- Article text and model responses are untrusted data, not executable commands.
- The model receives no tools, credentials, browser, shell or delivery authority.
- Selection accepts only allowed IDs; application code binds them to the verified
  source/policy packet for the request. Saved imports require an explicit packet
  digest and are labeled unverified-origin. The
  application resolves exact source text; this does not prove relevance or truth.
- Rule-preserved conditions can be incomplete. Always inspect original context.
- Known instruction-like patterns hold the item; this is not complete injection
  detection. Markup is escaped and reports use a restrictive CSP.
- Retrieval permits fixed public hosts/paths, refuses redirects and non-public
  DNS results, checks TLS names, connects to the checked address and caps time/bytes.
- Model transport uses authenticated numeric loopback, no proxies or redirects,
  and explicit output/context limits. There are no retries or hosted fallbacks.
- An empty valid selection shows the full escaped source with an explicit
  fallback label. This is not a generated summary and does not bypass validation.
- Each CLI invocation is one attempt, not an account-wide spending controller.
  Do not wrap it in unlimited retries. Failed requests remain recorded.

## Credentials and outputs

Use the documented environment-variable secret mechanism. Never commit keys,
local configs, model outputs or private input. Tests use obviously synthetic
credential strings. Outputs can contain third-party copyrighted source material;
keep them private unless separately reviewed for redistribution rights.

## Operational limits

No scheduler, notifications or production model-server manager is included.
The package cannot establish that your own server is configured securely. Keep
the server authenticated and loopback-only, review resource use, and stop on
preflight or cleanup failure. The original test lifecycle is private infrastructure
and is not required for the offline demo.

The legacy free-prose workflow functions remain for regression compatibility;
the v0.6.1 CLI uses the ID selector. Their presence is disclosed, not presented
as new model functionality. No remote package installation or external scanner
was used for this standard-library candidate.

This document is a boundary review, not a security certification. Public
publication and unattended operation require separate acceptance.
