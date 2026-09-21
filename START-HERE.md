# Start here — MiniCPM News Desk 0.8.1

A local, source-linked AI/technology news review tool. MiniCPM picks useful source
passages; deterministic code preserves restrictions and handles empty results.
Project code: MIT. Review source context before sharing an output.
Repository: https://github.com/fenner888/minicpm-news-desk

1. Follow [SETUP.md](SETUP.md) for prerequisites, demo commands, local-model
   configuration, expected outputs and troubleshooting.
2. Try `python3.14 -m newsdesk.digest demo --out outputs/first-daily-demo`.
   Open preview.html and supporting-report.html. Fictional data; no model, network or credentials are needed.
3. Run `python3.14 -m unittest discover -s tests -v`.
4. Inspect the bundled normal and fallback examples in samples/. Both are
   synthetic demonstrations, not actual model responses.
5. Read DIGEST.md for the daily24-hour recap and integration contract; read
   EVALUATION.md before connecting your own authenticated local model.

Run commands from the cloned repository root. Python 3.14.7 and system timezone
data are the tested prerequisites; the demo needs neither model weights nor keys.

Version 0.8.1 includes 264 offline checks, a documented live acceptance test of
0.8.0, and deterministic repairs from a private frozen benchmark that did not show
a coverage benefit over a no-model baseline. This is not unattended reliability
evidence. The local collection/preview/send path uses separate state
and explicit approval. Windows reference integration is not qualified; Linux/macOS
POSIX file locking is required. Nothing installs a schedule automatically. See
[EVALUATION.md](EVALUATION.md) and [CHANGELOG.md](CHANGELOG.md).

Follow SETUP step 4 to collect from fixed official feeds, build a daily preview
and explicitly send to your own Telegram test chat. Local model and source-only
results remain separately labeled. Review the source before sending.

OPENBMB-UPDATE.md is a message draft, not a sent submission. No model weights,
private infrastructure, real article archives or demo/music files are included.
