# Set up MiniCPM News Desk

Start with the offline demo. It shows the output without downloading a model or
creating any accounts. Then follow the local-model steps if you want real article
selection. Run commands from the cloned repository folder.

| What you want | What you need | Start here |
| --- | --- | --- |
| See the briefing layout | Git, Python and timezone data | Step 1 |
| Process a real supported article locally | Above, plus MiniCPM GGUF weights and llama.cpp | Step 2 |
| Receive an automatic Telegram digest | Above, plus your own collector, scheduler and delivery adapter | Step 4 |

The Telegram screenshots show the author's working private integration. Cloning
this repository does **not** connect Telegram or start collecting news. The public
package contains the source-processing, model-selection, archive and digest logic.

## 1. Clone and see the demo

The tested Python version is **3.14.7**. There are no pip or npm dependencies.
Install Git and Python using your operating system's supported installation method
if these commands are missing. Other Python versions are not qualified here.

```sh
git clone https://github.com/fenner888/minicpm-news-desk.git
cd minicpm-news-desk
python3.14 --version
python3.14 -c 'from zoneinfo import ZoneInfo; print(ZoneInfo("America/New_York"))'
python3.14 -m newsdesk.digest demo --out outputs/my-daily-demo
python3.14 -m newsdesk demo --out outputs/my-article-demo
python3.14 -m unittest discover -s tests -v
```

Expected: Python reports 3.14.7, the timezone check prints America/New_York, and
**203 tests pass**. If the timezone check fails, install your OS's IANA timezone
data (commonly called `tzdata`) before continuing. If your Python executable has
a different name, use its full path after checking the version.

Open these files using your file manager:

- `outputs/my-daily-demo/part-1.md`: numbered daily reading view.
- `outputs/my-daily-demo/supporting-report.html`: supporting report in a browser.
- `outputs/my-article-demo/index.html`: a single-article selection example.

These examples are fictional and make **zero model calls**. They neither fetch
news nor send messages. Use a new output folder name each time; existing results
are deliberately not overwritten.

## 2. Prepare the local model

This section uses a Linux/macOS shell. The measured reference machine is Linux,
Intel i5-9400F, 16 GB RAM, CPU-only. Windows model-server setup is not tested here.
The application does not download weights or start a server on your behalf.

### Download the two external components

1. Get **llama.cpp b10809** from its [official release page](https://github.com/ggml-org/llama.cpp/releases/tag/b10809).
   Choose the CPU archive matching your OS and architecture; extract the whole
   archive so required libraries remain beside the executable. For the reference
   Linux x64 machine, use the Ubuntu x64 CPU build if compatible with your system.
   This pinned upstream release is marked pre-release; a newer build needs its
   own validation rather than inheriting these results.
2. Get **MiniCPM5-2B-Q4_K_M.gguf** from OpenBMB's
   [official GGUF repository](https://huggingface.co/openbmb/MiniCPM5-2B-GGUF).
   Use Files and versions to choose that exact quantization. The BF16, SFT, MLX,
   DSpark and other quantizations are not interchangeable with the tested file.
   The [OpenBMB model card](https://huggingface.co/openbmb/MiniCPM5-2B) describes
   the model; this project uses the specific settings below.

Keep runtime binaries and weights outside this Git checkout. Run your downloaded
`llama-server --version`: the tested build identifies `10809` and `5266f24da`.
Compare the GGUF's SHA256 with the evaluated file:

```text
ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd
```

Use `sha256sum /absolute/path/to/MiniCPM5-2B-Q4_K_M.gguf` on Linux or
`shasum -a 256 /absolute/path/to/MiniCPM5-2B-Q4_K_M.gguf` on macOS. A different hash
means you have a different artifact; don't assume this evaluation applies to it.
Model/runtime licenses are separate from this project's MIT code license.

### Create a private local key

This is a key **you generate for your local server**, not a paid provider API key.
The command below saves it privately without printing it. It refuses to overwrite
an existing key; reuse your existing file instead if already configured.

```sh
python3.14 -c 'from pathlib import Path; import os, secrets; os.umask(0o077); p=Path.home()/".config"/"minicpm-news-desk"; p.mkdir(parents=True, exist_ok=True); f=(p/"local-api.key").open("x"); f.write(secrets.token_urlsafe(32)); f.close()'
```

Do not paste the key into a chat, Git, screenshots or logs. Never enable shell
tracing (`set -x`) while loading it.

### Start the server in terminal A

Replace the two `/absolute/path/to/` placeholders with your downloaded paths.
Keep this terminal running while you use News Desk; Ctrl-C stops the server.

```sh
/absolute/path/to/llama-server \
  --model /absolute/path/to/MiniCPM5-2B-Q4_K_M.gguf \
  --alias MiniCPM5-2B-Q4_K_M \
  --host 127.0.0.1 --port 8093 \
  --api-key-file "$HOME/.config/minicpm-news-desk/local-api.key" \
  --no-webui --jinja --ctx-size 8192 --parallel 1 \
  --threads 4 --threads-batch 4 \
  --reasoning on --reasoning-format deepseek --n-gpu-layers 0
```

Leave the host at `127.0.0.1`; do not expose this service to the public internet.
Wait for the model to load before continuing. If port 8093 is occupied, resolve
the conflict deliberately rather than stopping an unrelated service.

### Configure News Desk in terminal B

Change into your cloned `minicpm-news-desk` folder first. The next command copies
the example only if no local config exists; it does not overwrite your settings.

```sh
test -e config.local.json || cp config.example.json config.local.json
export MINICPM_API_KEY="$(python3.14 -c 'from pathlib import Path; print((Path.home()/".config"/"minicpm-news-desk"/"local-api.key").read_text().strip())')"
```

The provided config points to `http://127.0.0.1:8093`, model alias
`MiniCPM5-2B-Q4_K_M`, context 8192 and output limit 4096. It stores the environment
variable's **name**, not the secret. News Desk sends `reasoning_budget_tokens=512`;
generic OpenAI-compatible providers may not implement that control. The client
checks the model alias, context and template before requesting generation, but
does not independently authenticate your downloaded model or runtime binaries.

## 3. Fetch one article and run MiniCPM

Use a public, supported article URL. The following is an explicit network fetch;
individual pages may become unavailable. The `prepare` step does not use a model.

```sh
python3.14 -m newsdesk article --source xai \
  --url https://x.ai/news/grok-build-memory --out outputs/my-article-1
python3.14 -m newsdesk prepare --article outputs/my-article-1/article.json \
  --out outputs/my-source-review-1
```

Open `outputs/my-source-review-1/index.html` and check the extracted source first.
Then explicitly allow **one local inference request**:

```sh
python3.14 -m newsdesk select --article outputs/my-article-1/article.json \
  --config config.local.json --allow-local-inference \
  --out outputs/my-selection-1
```

Open `outputs/my-selection-1/index.html` for the selected passages and qualifications.
Inspect its `manifest.json` for the recorded outcome and attempts. A normal completed
request records one model attempt; a failed preflight may record none. Empty valid
selections display **SOURCE-ONLY FALLBACK**, not a successful model-written brief.
Failures are not retried and never fall back to a hosted model. The outer limit is
480 seconds; don't start another invocation while the first is still running.

Supported full-body adapters cover xAI `/news/`, OpenAI `/index/` and GitHub
`/changelog/`. OpenAI has returned HTTP 403/challenges in testing. Other publishers
need a new reviewed adapter or remain labeled excerpt/headline items; the model
does not browse arbitrary sites. Read [README.md](README.md) for saved HTML and
snapshot input options. Review source context before sharing.

When finished, stop terminal A with Ctrl-C and run `unset MINICPM_API_KEY` in
terminal B. Your protected key file stays available for your next local session.

## 4. Add daily collection and Telegram delivery

**This is a developer integration step, not another built-in CLI command.**
There is no Telegram token field or one-click schedule installer in this package.
To reproduce the author's personal workflow, supply these components:

1. **Collector:** check your chosen official sources hourly and produce validated
   source items with title, URL, source identity and publication/discovery times.
2. **Daily builder:** use the archive and edition logic in `newsdesk.digest` to
   select the previous 24 elapsed hours at 08:00 America/New_York. Obtain supported
   source-bound model cards; clearly label excerpts/headline-only items.
3. **Delivery adapter:** store your own Telegram bot token and fixed destination
   outside Git/model inputs, persist the report, split messages without losing
   text, and record confirmed sends. Do not automatically retry uncertain sends.
4. **Scheduler and validation:** set the repository root as working directory,
   prevent concurrent runs, enforce budgets, test the actual end-to-end path and
   separately check the first scheduled delivery before relying on it.

Use [DIGEST.md](DIGEST.md) for the integration sketch, input schema, DST behavior,
budgets and receipt state machine. It is explicitly a sketch: collector data,
model cards and the sender are supplied by you. [OPERATIONS.md](OPERATIONS.md)
covers source review, failures and rollback. No private collector, credentials,
recipient details or machine-specific service files are distributed here.

## Common setup problems

| Symptom | Check |
| --- | --- |
| Python command missing / timezone error | Step 1 prerequisites and executable version. |
| Cannot import `newsdesk` / `worker_failed` | Run from the repository root, including subprocesses and jobs. Inspect local diagnostics before retrying. |
| Connection refused | Terminal A is still running and listening on numeric loopback port 8093. |
| Authentication / model preflight failure | Both terminals use the same local key; alias, context, runtime and thinking settings match Step 2. Never print the key for debugging. |
| Existing output folder | Choose a new `--out` path; keep prior results for comparison. |
| Source is blocked, too long or unsupported | Keep it a labeled source link. Don't bypass checks or claim it was summarized. |
| No Telegram message | The public CLI does not send one; Step 4 requires your own integration. |

For measured results and remaining limitations, see [EVALUATION.md](EVALUATION.md).
