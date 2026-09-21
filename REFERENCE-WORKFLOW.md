# Your first real digest

Prerequisites: finish [SETUP](SETUP.md) steps 1–3, use Linux/macOS, and run all
commands from the checkout root. This public reference integration is separate
from the author's private deployment. No credentials or source archives are bundled.

## 1. Create isolated test state and collect

Initialization refuses to overwrite an existing directory. Choose your IANA
timezone and display title; these settings belong to the state directory.

```sh
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" init \
  --title "My AI & Tech Brief" --timezone America/New_York
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" collect \
  --sources github openai --allow-network
```

Collection reports accepted/rejected item counts and failures per feed. Rejected
links fall outside the supported source/article paths. An HTTP success is not
coverage of every announcement. Each invocation attempts at most the two selected
registered feeds once, bounded to 2 MB and 2,000 listed items per feed. XML entities
and DTD declarations are rejected; HTML inside ordinary RSS text is inert.
Historical items stay archived, not falsely dated as new. Future publications are
held out of the current window. Collection makes no model calls or Telegram sends.

## 2. Build and review

Keep the local server and `MINICPM_API_KEY` from setup available:

```sh
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" build \
  --current-window --allow-network --allow-local-inference --config config.local.json
```

The command prints an edition UUID and `preview.html` path. Open that file and
the adjacent `supporting-report.html`. Inspect `manifest.json`: attempts, usable
model cards and source-only items are separate counts. The model is asked only
for passage IDs; software resolves source text and qualifications. Source/model
failures stay labeled links. At most six article fetches/four local attempts per
edition; zero retries and no hosted fallback. No metadata fetches are added here.

Omit both `--config` and `--allow-local-inference` for an offline source-only build.
That is useful for testing layout but **does not test MiniCPM**.

`--current-window` creates a labeled test edition ending now. Normal builds use
the preceding 24 elapsed hours ending at 08:00 in the configured timezone, starting
the morning after initialization. At most one edition per local date, including
cancelled editions. A quiet day can produce no eligible stories; do not widen the
window silently. Use a new isolated state for a separately authorized repeat test,
not an automatic retry loop.

## 3. Connect your own Telegram test chat

Create a bot with official [BotFather](https://t.me/BotFather), open a private chat
with it and send `/start`. Obtain your numeric chat ID using Telegram's official
[getUpdates API](https://core.telegram.org/bots/api#getupdates) or trusted existing
bot tooling. Do not paste the token into a third-party ID lookup site, browser
history, Git, chat or screenshot. If the bot already has a webhook, do not disable
it for this test; use a separate test bot.

Read credentials privately into the environment in Bash or zsh. Paste the token
after the first command and press Enter (typing is hidden). Paste the numeric
chat ID after the second command. Do not enable shell tracing (`set -x`).

```sh
read -r -s NEWSDESK_TELEGRAM_TOKEN
read -r NEWSDESK_TELEGRAM_CHAT_ID
export NEWSDESK_TELEGRAM_TOKEN NEWSDESK_TELEGRAM_CHAT_ID
```

Replace `EDITION_UUID` with the build's exact UUID after reviewing its source and
preview. Approval sends nothing:

```sh
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" approve \
  --edition EDITION_UUID
```

Copy the returned approval hash into this command:

```sh
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" send \
  --edition EDITION_UUID --approval APPROVAL_HASH --allow-send
python3.14 -m newsdesk.daily --state "$HOME/.local/state/newsdesk-test" status
```

Approval expires in 15 minutes and is consumed once. It binds the exact message
parts, full supporting report, bot identity and numeric chat. Changing them
invalidates approval. Every part requires a confirmed provider message ID in the
configured chat. Check actual Telegram rendering yourself; offline tests cannot
establish delivery. The build manifest stays `not_sent` as a historical build
record; `status` and the receipt ledger track later delivery.

The sender uses Telegram HTML with source text escaped, disables link previews,
and never follows redirects or uses environment proxies for the bot request.
Failure logs omit credentials, URLs containing tokens and raw provider errors.
Finish with `unset NEWSDESK_TELEGRAM_TOKEN NEWSDESK_TELEGRAM_CHAT_ID`.

## 4. Recover safely

Use `status` first. A failed/unfinished edition blocks later builds deliberately.

- **Known unsent preparation or ready edition:** `cancel-unsent --edition UUID`
  retains its history and daily budget lock but permits the next day's edition.
  Any send reservation makes cancellation fail.
- **Every part already confirmed, process stopped before completion:** `reconcile`
  finishes the edition without a network request.
- **Ambiguous send:** verify the actual message in your configured chat first.
  `confirm-observed --edition UUID --part 0 --message-id REAL_ID` records your
  observation. Parts are zero-based. Never invent an ID or infer non-delivery
  from a timeout. Unknown outcomes remain blocked.
- **Some confirmed, other parts never reserved:** after reconciliation, approve
  again and send only the remaining never-reserved parts. Confirmed ones are skipped.

Prefix each command with `python3.14 -m newsdesk.daily --state /absolute/private/state`.
Do not delete reservations or edit SQLite to bypass these protections. Unsent
cancellation is deliberate abandonment, not automatic resumption or another model
budget. Keep the original output directory for diagnosis.

## 5. Optional scheduling, after manual acceptance

Create a separate normal state directory when ready. The disabled
[cron example](examples/schedule.cron.example) illustrates hourly collection and
daily preparation. All entries are commented out. It **does not automate approval
or Telegram sending**; unattended sending requires a separately reviewed policy.

Use an absolute Python executable and checkout working directory. Keep the local
server available and load the model key via a private scheduler environment—not
the example file or public logs. Match the scheduler timezone to the state setting;
`CRON_TZ` is not portable across cron implementations. Observe the first scheduled
build separately. Track command exit status, failed sources and pending editions.

The public integration does not activate or modify the author's existing jobs.
See [DIGEST](DIGEST.md) for DST window tradeoffs and [OPERATIONS](OPERATIONS.md)
for rollback and source-review requirements.
