# STACKIT-Whisper-functions

Rebuilds the always-on VM transcription demo from
[`STACKIT-Whisper-open-ai`](../STACKIT-Whisper-open-ai) as a **STACKIT Function**: a
container that only runs while it's handling a request and scales to zero
afterwards, instead of a VM that runs (and costs) 24/7.

## What it does

An HTTP-triggered function (`whisper-fn/`) that, on `POST /transcribe`:

1. downloads a video from an S3 (STACKIT Object Storage) bucket,
2. transcribes it locally with [`openai-whisper`](https://github.com/openai/whisper)
   (the open-weights Whisper model running inside the function — **not** a call
   to OpenAI's paid API),
3. uploads the resulting transcript back to the same bucket,
4. returns a small JSON summary (bucket, keys, model, duration).

`GET /health` returns a plain status check.

## Why it exists

The old solution (`STACKIT-Whisper-open-ai/`) works, but it's a Terraform-provisioned
VM that runs continuously via `cloud-init` and only ever leaves its result on local
disk — nobody stops it, so it costs money the whole time it's not transcribing
anything. STACKIT Functions offered a scale-to-zero, HTTP-triggered alternative, so
this project reimplements the same demo (same input video, same Whisper model
family) as a function instead of a VM, with the transcript written back to S3 so the
result is actually retrievable afterwards.

The old project is intentionally left untouched — it has its own project-boundary
rule (its `CLAUDE.md`) forbidding reuse of its credentials/resources without
explicit permission, which is why this project provisions its own S3 bucket rather
than sharing the old one.

## Project layout

| Path | Purpose |
|---|---|
| `whisper-fn/` | The actual function: `handler.py`, dependencies, STACKIT Functions manifests |
| `whisper-fn/.env.example` | Template for the env vars you need (S3 bucket/credentials, model size) — copy to `whisper-fn/.env`, fill in your own values, never commit it |
| `install-sfn.sh` | Installs the `sfn` CLI (STACKIT Functions CLI) locally |
| `deploy.sh` | Convenience wrapper: build → auth → confirm → deploy, using `whisper-fn/.env` |
| `GETTING-STARTED.md` | Step-by-step setup and deploy instructions |
| `Task.md` | Original design/planning notes (background reading, not required to run this) |
| `Handout.md` | Session log — implementation history and the disk-space blocker that paused the first deploy attempt (background reading, not required to run this) |

## Status

**Deployed and live** at
`https://<function-id>.functions.onstackit.cloud`,
verified end-to-end with a real transcription of `elephants_dream.mp4`
(downloaded from the bucket, transcribed, transcript written back).
Running `WHISPER_MODEL=small`, not the originally planned `large-v3` --
see `DECISIONS.md` for why (short version: no STACKIT Functions plan has
enough memory for `large-v3` or even `medium`). Built via a hand-written
`Dockerfile`, not the default buildpack path -- see `DECISIONS.md` for
that too (buildpack images get rejected by this registry).

## Quick start

```bash
./install-sfn.sh                                  # install/update the sfn CLI (>= 1.7.0 needed)
cp whisper-fn/.env.example whisper-fn/.env         # fill in your own S3 bucket/credentials
./deploy.sh <project-id> <registry-image-ref> <registry-username>
# e.g. ./deploy.sh <your-stackit-project-id> registry.onstackit.cloud/<reg-project>/whisper-fn:0.1.1 'robot$<reg-project>+<robot-name>'
```

See [`GETTING-STARTED.md`](GETTING-STARTED.md) for the full walkthrough --
creating the Object Storage bucket and Container Registry are one-time,
manual (Portal) steps not covered by `deploy.sh`.

## Cost note

This project creates real STACKIT resources once deployed (S3 bucket, a running
function instance while it's warm). Per the standing cost rule: no
`sfn functions deploy`, no bucket creation, without explicit confirmation first —
`deploy.sh` has its own confirmation prompt built in before it deploys.
Installing the CLI, building/running the container locally, and `sfn auth login`
are free and don't need separate sign-off.
