# Start here — MiniCPM News Desk 0.7.5

A local, source-linked AI/technology news review tool. MiniCPM picks useful source
passages; deterministic code preserves restrictions and handles empty results.
Project code: MIT. Status: public research preview, review required.
Repository: https://github.com/fenner888/minicpm-news-desk

1. Read README.md for capabilities, limits and setup.
2. Try `python3.14 -m newsdesk.digest demo --out outputs/first-daily-demo`.
   Read part-1.md and supporting-report.html. Fictional data; no model, network or credentials are needed.
3. Run `python3.14 -m unittest discover -s tests -v` — 203 offline tests.
4. Inspect the bundled normal and fallback examples in samples/. Both are
   synthetic demonstrations, not actual model responses.
5. Read DIGEST.md for the daily24-hour recap and integration contract; read
   EVALUATION.md before connecting your own authenticated local model.

Run commands from the cloned repository root. Python 3.14.7 and system timezone
data are the tested prerequisites; the demo needs neither model weights nor keys.

The latest private delivery test used 0.7.4: one fresh local-model brief plus eight
source-only items reached Telegram in two messages after an operator launch-path
correction. The 0.7.5 formatter correction is offline-tested only. Older 3/3 results
are separate historical tests, not a current general success rate. See
[EVALUATION.md](EVALUATION.md) and [CHANGELOG.md](CHANGELOG.md).

This package does not collect news on a schedule or send Telegram messages.
Supply your own snapshot or explicitly fetch one supported article using the CLI.

OPENBMB-UPDATE.md is a message draft, not a sent submission. No model weights,
private infrastructure, real article archives or demo/music files are included.
