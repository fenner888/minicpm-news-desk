# Daily recap contract

The digest is one daily rolling24-hour recap, not an hourly notification system.
`newsdesk.digest` is standard-library Python with SQLite and IANA `zoneinfo`.
No pip installation, model download, network request or message occurs on import.

## Layout and curation

**☕ Cheryl’s AI & Tech Brief** opens with the weekday, date and “Morning edition”.
The lead targets100–150 words; Worth knowing targets40–70 words per story, with
bold headlines and source links. Quick hits retain one useful source-supported
sentence when available. These are editorial targets, not hard truncation rules:
the current implementation preserves verified passages and important caveats.
No filler, forced jokes or invented practical value. A quiet day can have fewer
stories; the format never requires padding.

One lead plus up to three “Worth knowing” stories use verified full-source cards.
Remaining selected discoveries appear as explicitly labeled publisher excerpts
and links where available. Excerpts are not full-article/model summaries. No forced
“Something to try” section or invented practical benefit.

Ranking is transparent: title keywords for security/privacy, launches/models and
agent/API/workflow tools receive weights; minor/pre-release labels are discounted.
This heuristic is not editorial judgment, a benchmark or proof of importance.
It can miss significant stories. All selected items keep original source links.

Source conditions remain intact; length targets do not override accuracy.
The formatter uses bold section headings, restrained emoji, condition bullets
and numbered parts. Maximum9 stories,4 detailed cards,16 parts. A paragraph that
cannot safely fit requires review rather than being silently clipped.

### Editorial repair in 0.7.1

`reading_card` separates the short reading view from the full report. It removes
standalone list introductions/navigation, field-reference highlights and
unmentioned API definitions, with a reason recorded for each placement. Access,
price, deadlines, directly referenced definitions and unknown qualifications stay
visible. Restrictive unfinished introductions or unfinished selected claims hold
the card as a source link. This heuristic can miss semantic relationships; it is
not a substitute for editorial review. Source wording is never rewritten.

`supporting_report(edition, cards)` returns escaped, script-free HTML containing
the complete extracted article and placement decisions. Save it privately before
sending; it contains third-party source material. Do not publish it by default.
Source links remain the reader's route to the original; there is no new report host.

Whole stories stay together whenever they fit. Oversized stories use named
continuations, and headings stay with their following paragraphs. Preview editions
show preparation time and historical source window, never a false morning label.

### Presentation polish in 0.7.2

Story headlines are plain bold; emojis identify sections rather than every item.
Short related highlights join into one paragraph without changing their words.
One qualification is inline; multiple qualifications retain bullets. Original
HTTPS links use a fixed “Read the source ↗” label with encoded Markdown delimiters.
Normal editions open with “Your last 24 hours in AI & tech.” `live_test=True`
labels an isolated current-data test, distinct from `preview=True` saved replays.
The two modes cannot be combined. Neither flag authorizes fetching or sending.
Quick hits share a source-only disclosure and stay grouped where they fit;
per-item date uncertainty and failures are still visible.

### Quick-hit context in 0.7.3

The optional `descriptions` mapping in `render` adds short publisher text, bound
to each item's source and canonical URL. `newsdesk.quickhits.collect` uses complete
feed sentences first; missing descriptions can be fetched from fixed official
AWS, Google, Vercel, LangChain and LM Studio hosts. These are HTML page descriptions,
not new full-body adapters. No model writes prose or invents practical benefits.
Complete caveats in an accepted excerpt remain; a truncated trailing feed fragment
is never completed. Incomplete, conflicting, generic or oversized page descriptions
are held. These conservative checks can reject useful publisher metadata.

Keep the source description/provenance/hash record privately. An absent description
remains an explicitly labeled headline. Existing source/model failure notices take
precedence. The operator shares its six-fetch daily allowance between full articles
and metadata requests, reserving each attempt before networking; no retry or extra
inference. `collect` takes the remaining fetch budget; it does not manage the
operator's durable reservation ledger. The sample integration below does not fetch
metadata unless the caller explicitly adds this step.

Individual quick hits stay intact while packing, avoiding unnecessary section-wide
page breaks. One message is preferred when the whole edition fits the existing safe
limit; content is never cut solely to force a single message. The latest nine-item
replay used two messages; later detailed editions have needed three. Source text
remains untrusted and inert.

### Date preservation repair in 0.7.4

A real current-data test found that an Ubuntu migration brief omitted its date
range and explicit version-pinning alternative. The source was complete; exact
quotes alone did not guarantee completeness. Protected-block policy v4 now covers
between/through ranges, explicit month/day and ISO dates, roll-out wording, and
migration compatibility/deferral guidance. Pure "To learn more" navigation moves
to the supporting report; access, price, deadline and safety qualifications remain.
These are heuristics, not a guarantee of complete fact recall across every source.
The model, prompt and inference settings are unchanged. Old packets/selection
hashes are not compatible with the new policy; regenerate packets and keep old
artifacts as historical evidence rather than silently rewriting them.

### Qualification retention in 0.7.5

Reading-view filtering now preserves access, price, safety, explicit dates and
migration qualifications even when the model selected them as highlights beginning
with navigation text or an API-field label. Previously a selected block could be
excluded from the separate conditions list and then hidden as navigation. ISO
dates and migration guidance use the existing protected-source rules in both
paths, and background safety warnings remain visible. Ordinary navigation still
moves to the supporting report; incomplete restrictive passages still hold the card.

This is a deterministic formatter correction, not a model/prompt/policy-hash or
timing change. Six additional offline regression tests cover the affected paths.
The subsequent owner-approved deployment passed 203 public plus 74 private tests.
Two fresh local-model briefs and seven source-only quick hits were delivered in
two confirmed Telegram messages on 0.7.5. See [EVALUATION.md](EVALUATION.md) for
measured results and the separate pending scheduled-delivery observation.

### Protection reasons reach the reading view in 0.8.1

`verified_card` carries protected rule names as `highlight_rules` and
`condition_rules`, parallel to `highlights` and `conditions`. Section or exclusion
protection applies whether a block is selected or supplied independently: field
reference filtering cannot hide a protected selected highlight. `reading_card`
keeps a condition in the brief when its rules include a recognized section
(`section:important notes`, `section:requirements`) or an exclusion clause, even
if it defines an API field the highlights never mention; the audit reason is
`protected_section_or_exclusion_retained`. Unmentioned field definitions without
such a tag still move to the report. Navigation lines and unfinished restrictive
introductions are unaffected. Absent rule metadata keeps legacy placement;
explicit metadata must be a parallel list of lists of strings. Malformed data,
including an empty rule list for nonempty passages, is rejected.

Also in 0.8.1: the selector pool excludes blocks shorter than 60 characters
without terminal `.`, `!` or `?` (unrecognized headings, bare table cells), the
GitHub/xAI/OpenAI parser keeps one simple table row per line with ` | ` between
cells, and protection policy v6 covers stated prerequisites (`you’ll need`,
`or later`, `prerequisites`) and rejection clauses (`rejects`, `refuses`). Nested
tables and spanning cells fail closed rather than guess relationships; hidden
markup cannot reset the visible row state. No generic table-context assembly is
implemented, so unfinished list introductions still hold the brief. Policy v6
changes packet hashes; old packets stay historical. These are deterministic
changes identified from private review. Shipped model, prompt, runtime settings
and reasoning budget are unchanged; an isolated budget comparison is recorded
separately in EVALUATION.md.

## Integration example

### September 21 candidate contract

Public-readiness work adds a separate opt-in reference CLI (`newsdesk.daily`).
Its state, collection, build, approval and recovery boundaries are specified in
`specs/2026-09-21-public-readiness/`. No installation starts a schedule or sends.
Technical punctuation must survive display escaping. Licensing and prohibition
clauses are protected, but heuristic completeness still requires source review.
The existing library defaults remain compatible with the private integration.

```python
import time
from newsdesk.digest import Store, render, verified_card, supporting_report

store = Store("private-state.sqlite3")  # protect with OS permissions; never commit
store.initialize(time.time())         # first scheduled edition: next8AM Eastern
store.ingest(validated_source_items, time.time())
edition = store.claim(time.time())
if edition:
    # Supply cards bound to exact source/article/packet/selection data:
    # cards[item_id] = verified_card(article, packet, selection)
    # A blocked or unsupported item stays a link. Do not pass arbitrary model prose.
    parts = render(edition, cards)
    # Persist supporting_report(edition, cards) in protected local storage first.
    store.ready(edition["id"], parts, time.time())
    for index, part in enumerate(parts):
        store.reserve_send(edition["id"], index, part)
        message_id = your_authorized_delivery_adapter(part)
        store.confirm_send(edition["id"], index, message_id)
    store.finish(edition["id"], time.time())
store.close()
```

This is an integration sketch, not a runnable sender. `validated_source_items`,
`cards` and the adapter must be supplied by the operator. Snapshot items require
`source`, `title`, public HTTPS `url`, and numeric `first_seen`; optional fields
are `company`, `excerpt`, `published`, `changed_observed_at`. Times are Unix seconds.
The package does not provide an allowlist for all possible news vendors: validate
collector host/source identity before intake. Full-body fetching retains the
existing three-adapter host restrictions and public-address/TLS checks.

An edition uses the exact86400 seconds ending at08:00 America/New_York. The daily
trigger follows local time across DST; the content window stays24 elapsed hours.
There can therefore be a1-hour overlap/gap between successive windows at DST.
Delivery deduplication handles overlaps; no strict24-hour system can promise both
fixed local delivery and contiguous elapsed windows on clock-change days.

Publication time determines eligibility when known; otherwise discovery time is
used and labeled. A freshly observed revision can qualify as an explicitly labeled
listing update. Future observations are rejected; future publication dates are
held. Late discovery of an old publication does not make it new. A missed edition
does not expand the next day's scope beyond24 hours.

## Delivery and resource boundaries

The caller must hold an exclusive process lock around intake/build/send, protect
the SQLite file, fix the recipient outside source/model data, and validate message
length after the platform's Markdown conversion. This module has no public route,
tenant system or model-owned credentials.

At most4 model reservations are allowed per edition; the private adapter also
caps source fetches at6 and uses no inference retries/hosted fallback. `Store`
does not itself enforce arbitrary callers' network behavior. Treat this as an
integration contract, not an OS sandbox.

Only confirmed delivery of every part marks the selected stories delivered.
Unselected and expired records remain archived. A reserved/ambiguous send cannot
be resent automatically. A failed or partially delivered edition blocks subsequent
editions until the operator reconciles it. If all parts were confirmed but the
process stopped before commit, `reconcile_confirmed(now)` safely commits without
sending again. Do not delete reservation rows to manufacture a successful run.

## Public reference workflow (0.8.0)

The reading layer can retain a `To prepare:` paragraph together with its complete
following source paragraphs, bounded to one reading paragraph. It requires the
full source hash and an unambiguous match, and stops at the next recognized
heading. Missing/truncated/nested/oversized context remains held; other unfinished
restriction lists still require review. This is a narrow English structural rule,
not proof of semantic completeness. The original model selection is unchanged.

`newsdesk.daily` implements a separate fixed-feed reference workflow; see
[REFERENCE-WORKFLOW.md](REFERENCE-WORKFLOW.md). GitHub and OpenAI RSS use the same
public-IP/TLS/no-redirect transport with XML content types and a 45-second worker
limit. Maximum 2 MB and 2,000 items per feed; feed requests are separate from the
six article fetches per edition. Wrong-host/path links are excluded and counted.

The builder uses existing article/selector code, persists full-source reports,
and requests up to four local generations. Source-only quick hits use feed
descriptions without extra fetches. Explicit switches gate network/inference.
Failures remain labeled links and consume reserved attempts.

Private state is owner-only with POSIX locking and fixes title/IANA timezone.
Existing library defaults remain unchanged. Technical punctuation is escaped,
not deleted; `presentation.telegram_html` identifies app-owned formatting before
decoding source entities. Never decode then re-parse source as trusted Markdown.
Licensing policy v5 changes packet hashes; old packets stay historical.

Approval lasts 15 minutes and binds edition, messages, full report, bot identity
and numeric chat. Credentials come only from operator environment. Approval is
consumed before transport, each part reserved before sending, and confirmation
requires a matching-chat provider receipt. No retries. `cancel-unsent` retains
history/day locks and refuses any send reservation. Manual receipt confirmation
is labeled operator-verified. Unknown sends block. No schedule is installed and
no automatic approval is included.

## Public versus private

The repository includes the portable queue/formatter, model selection code,
tests and fictional examples. It excludes private collector paths, scheduler
jobs, Telegram destinations/tokens, SSH configuration, raw third-party articles,
reasoning traces and the machine-specific temporary model supervisor.
The original v0.6.1 synthetic selector samples remain historical fixtures. Their
saved packets are not compatible with the current protection-policy hash; create
a fresh packet from their synthetic article when exercising the current CLI.
The bundled daily example is regenerated for the public package version.
The reference collector/sender are new public code, not the owner's private adapters.
