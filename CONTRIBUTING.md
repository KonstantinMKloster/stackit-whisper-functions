# Contributing

Thanks for your interest in improving STACKIT-Whisper-functions.

## Development setup

```bash
git clone https://github.com/<your-github-username>/stackit-whisper-functions.git
cd stackit-whisper-functions
./setup.sh                                   # installs sfn CLI, prepares whisper-fn/.env
```

Fill in `whisper-fn/.env` with your own STACKIT Object Storage bucket and
credentials (see `whisper-fn/.env.example`). Running the pure-logic test
needs neither Docker nor a real S3 connection:

```bash
cd whisper-fn
python3 test_handler_local.py
```

To build and run the full function locally with Docker:

```bash
cd whisper-fn
docker build --platform linux/amd64 -t whisper-fn:local .
docker run -d --platform linux/amd64 -p 8080:8080 -e PORT=8080 \
  --env-file .env --name whisper-fn-local whisper-fn:local
curl http://127.0.0.1:8080/health
docker rm -f whisper-fn-local
```

See [GETTING-STARTED.md](GETTING-STARTED.md) for the complete walkthrough,
including deploying to STACKIT.

## Cost-safety rule

This project can create real, billable STACKIT resources (Object Storage
bucket, Container Registry image, a running function instance). **Never run
`./deploy.sh`, push a registry image, or create a bucket without explicit
confirmation from whoever owns the STACKIT project/credentials you're
using.** `./setup.sh` and local Docker builds/tests never touch the cloud
and are always safe to run.

## Branch / PR workflow

1. Fork the repository and create a feature branch off `main`.
2. Make your change, keeping commits focused and the commit message
   describing the "why" as well as the "what".
3. Run the local test suite (`python3 whisper-fn/test_handler_local.py`) and,
   where applicable, a local Docker smoke test before opening a PR.
4. Open a pull request against `main` with a clear description of the
   change and, if relevant, a test plan.

## Code style

- Keep `handler.py` dependency-light and framework-free — it is a raw ASGI
  app, not a web framework handler, by design (see `asgi.py`).
- Document non-trivial choices (model size, build approach, plan/memory
  limits, etc.) in `DECISIONS.md` rather than only in code comments —
  follow the existing "Was / Warum / Alternative verworfen" format.
- Never commit real credentials, bucket names, or project IDs. Use the
  placeholder conventions already used in `.env.example`, `README.md`, and
  `GETTING-STARTED.md` (e.g. `<your-stackit-project-id>`,
  `<your-registry-project>`).

## Reporting issues

Please use the issue templates under `.github/ISSUE_TEMPLATE/` for bug
reports and feature requests, and include enough detail (STACKIT Functions
plan, model size, logs/error output) to reproduce the problem.

## Using Claude Code

This repository ships a [`CLAUDE.md`](CLAUDE.md) with condensed
architecture and command context, including the cost-safety rule above.
Running `claude` in this directory picks it up automatically.
