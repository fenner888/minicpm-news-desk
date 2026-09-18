# Start here — MiniCPM News Desk 0.7.0

A local, source-linked AI/technology news review tool. MiniCPM picks useful source
passages; deterministic code preserves restrictions and handles empty results.
Project code: MIT. Status: public research preview, review required.
Repository: https://github.com/fenner888/minicpm-news-desk

1. Read README.md for capabilities, limits and setup.
2. Try `python3.14 -m newsdesk.digest demo --out outputs/first-daily-demo`.
   Read part-1.md. Fictional data; no model, network or credentials are needed.
3. Run `python3.14 -m unittest discover -s tests -v` —147 tests.
4. Inspect the bundled normal and fallback examples in samples/. Both are
   synthetic demonstrations, not actual model responses.
5. Read DIGEST.md for the daily24-hour recap and integration contract; read
   EVALUATION.md before connecting your own authenticated local model.

The measured fresh Linux test passed 3/3. An earlier unnecessary abstention is
still disclosed, and source-only fallback is tested separately. This package
does not collect news on a schedule or send Telegram messages. Supply your own
snapshot or explicitly fetch one supported article using the documented CLI.

OPENBMB-UPDATE.md is a message draft, not a sent submission. No model weights,
private infrastructure, real article archives or demo/music files are included.
