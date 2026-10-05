# STACKIT-Whisper-functions

**Stack:** Python 3.11, STACKIT Functions (Knative-based FaaS), openai-whisper, boto3 (S3)

## What

A scale-to-zero [STACKIT Function](https://docs.functions.onstackit.cloud/) that
transcribes audio/video with OpenAI's open-weights Whisper model (not the paid
OpenAI API). On `POST /transcribe` it downloads a file from an S3-compatible
bucket (STACKIT Object Storage), transcribes it locally inside the container,
and writes the transcript back to the same bucket.

## COST-SAFETY NOTE — READ FIRST

Deploying this project creates **real, billable STACKIT resources**:
a Container Registry push, an Object Storage bucket, and a running function
instance while it is warm. **Never run `./deploy.sh`, create a bucket, or push
a registry image without the user's explicit confirmation first.**
`setup.sh` only installs the local CLI and prepares config files — it does
not deploy or create anything. `deploy.sh` has its own interactive
confirmation prompt before the actual `sfn functions deploy` call; do not
bypass it.

## Quick Start

```bash
./setup.sh                                          # one-time local bootstrap (no cloud resources)
cp whisper-fn/.env.example whisper-fn/.env           # fill in your S3 bucket/credentials
cd whisper-fn && python3 test_handler_local.py       # pure-logic test, no Docker/S3 needed
```

Deploying further (creates billable resources, requires explicit confirmation):

```bash
./deploy.sh <project-id> <registry-image-ref> <registry-username>
```

See [GETTING-STARTED.md](GETTING-STARTED.md) for the full walkthrough, including
the one-time manual Portal steps (bucket, Container Registry) that can't be
scripted.

## Commands

```bash
# Local setup
./install-sfn.sh                         # install/update the sfn CLI (>= 1.7.0)
cp whisper-fn/.env.example whisper-fn/.env

# Build & run locally (Docker)
cd whisper-fn
docker build --platform linux/amd64 -t whisper-fn:local .
docker run -d --platform linux/amd64 -p 8080:8080 -e PORT=8080 \
  --env-file .env --name whisper-fn-local whisper-fn:local
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/transcribe
docker rm -f whisper-fn-local

# Test (no Docker, no S3 — stubs boto3/whisper/imageio_ffmpeg)
python3 whisper-fn/test_handler_local.py

# Deploy (billable — requires explicit user confirmation, see above)
./deploy.sh <project-id> <registry-image-ref> <registry-username>
```

## Architecture

```
whisper-fn/
├── handler.py                    # Function entrypoint: S3 download -> whisper transcribe -> S3 upload
├── asgi.py                       # Hand-rolled ASGI lifespan wrapper (serves via uvicorn)
├── Dockerfile                    # Custom build (NOT buildpacks — see DECISIONS.md), bakes in `small` model
├── pyproject.toml                # Dependencies: boto3, openai-whisper, imageio-ffmpeg, uvicorn
├── .env.example                  # Template: S3 bucket/credentials, WHISPER_MODEL
├── test_handler_local.py         # Logic-only test, stubs external deps
└── .stackit-functions/           # STACKIT Functions manifests (function.yaml, project.yaml, revision.yaml)
install-sfn.sh                    # Installs the `sfn` CLI locally
deploy.sh                         # build -> push -> auth -> confirm -> deploy wrapper
```

**Request flow (`handler.py`):** `POST /transcribe` downloads the configured
object (`S3_INPUT_KEY`) from `S3_BUCKET` into a temp dir, runs
`whisper.load_model(WHISPER_MODEL).transcribe()` on it off the event loop
(CPU-bound, ~90-150s for `small`), writes the resulting text to a temp file,
and uploads it back to the bucket as `S3_OUTPUT_KEY`. `GET /health` returns
`{"status": "ok", "model": ...}` without touching S3. The model is loaded
once at container warm-up (`Function.start()`), not per request.

## Key Files

```
whisper-fn/handler.py            — all application logic (S3 + whisper + routing)
whisper-fn/Dockerfile            — custom image build, see inline comments for why
whisper-fn/.stackit-functions/revision.yaml — plan/memory/image/concurrency for deploy
whisper-fn/.env.example          — required env vars, copy to .env (gitignored)
deploy.sh                        — the only script that actually deploys (asks for confirmation)
install-sfn.sh                   — installs the sfn CLI binary from GitHub releases
DECISIONS.md                     — why `small` model, custom Dockerfile, plan f6, SemVer tags
GETTING-STARTED.md               — full step-by-step setup/deploy walkthrough
```

## Configuration

All configuration is via environment variables in `whisper-fn/.env`
(copy from `whisper-fn/.env.example`, never commit the real file):

| Variable | Required | Description |
|----------|----------|--------------|
| `S3_BUCKET` | yes | Object Storage bucket holding the input file and receiving the transcript |
| `S3_ACCESS_KEY` | yes | S3 access key for that bucket |
| `S3_SECRET_KEY` | yes | S3 secret key for that bucket |
| `S3_ENDPOINT_URL` | yes | STACKIT Object Storage endpoint for your region |
| `S3_REGION` | no (default `eu01`) | STACKIT region |
| `S3_INPUT_KEY` | no (default `elephants_dream.mp4`) | Object key to download and transcribe |
| `S3_OUTPUT_KEY` | no (default `elephants_dream.txt`) | Object key to write the transcript to |
| `WHISPER_MODEL` | no (default `small`) | Whisper model size — keep `small`; `medium`/`large-v3` OOM-kill on every available STACKIT Functions plan (see DECISIONS.md) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
