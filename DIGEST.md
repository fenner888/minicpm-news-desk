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
operator's durable reservation ledger. The sample integration above does not fetch
metadata unless the caller explicitly adds this step.

Individual quick hits stay intact while packing, avoiding unnecessary section-wide
page breaks. One message is preferred when the whole edition fits the existing safe
limit; content is never cut solely to force a single message. The latest nine-item
replay still needs two messages. Source text remains untrusted and inert.

## Integration example

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

## Public versus private

The repository includes the portable queue/formatter, model selection code,
tests and fictional examples. It excludes private collector paths, scheduler
jobs, Telegram destinations/tokens, SSH configuration, raw third-party articles,
reasoning traces and the machine-specific temporary model supervisor.
The original v0.6.1 synthetic selector samples remain historical fixtures.
