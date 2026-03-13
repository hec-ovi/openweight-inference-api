# OpenWeight Responses API

Production-ready ROCm-first inference gateway for open-weight chat and reasoning models, backed by vLLM and designed for Strix Halo / Ryzen AI Max deployments.

## What ships here

- FastAPI gateway with `POST /v1/responses`, `POST /v1/chat/completions`, `GET /v1/models`, `GET /health/live`, `GET /health/ready`, and `GET /metrics`
- Strict bearer auth, request IDs, JSON logs, request-size limits, CORS, and Prometheus metrics
- Model adapter isolation for `openai/gpt-oss-20b`, `Qwen/Qwen3-4B`, and `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
- ROCm 7.2 stable deployment lane plus a separate ROCm/TheRock 7.11.0 preview lane for gfx1151 validation
- Persistent host-backed model storage rooted at `/var/lib/openweight/models/vllm`
- Static API docs in [`docs/`](./docs)

## Runtime lanes

- Stable production lane: `deploy/compose.yaml` with a pinned ROCm 7.2 vLLM image
- TheRock compatibility lane: `deploy/compose.yaml` plus `deploy/compose.therock.yaml`

Both lanes mount the same persistent cache layout:

- `MODEL_CACHE_DIR=/var/lib/openweight/models/vllm`

The vLLM container derives the official Hugging Face cache directories under that mount:

- `HF_HOME=/models/vllm/hf`
- `HF_HUB_CACHE=/models/vllm/hub`
- `HF_ASSETS_CACHE=/models/vllm/assets`

Weights and caches stay on the host bind mount. They are not baked into the image.

## Required env

Your local `.env` should include at least:

```dotenv
HF_TOKEN=hf_...
API_BEARER_KEYS=replace-with-a-real-long-random-token
MODEL_PROFILE=qwen3-light
```

The full template is in [`.env.template`](./.env.template).

For first-load ROCm smoke tests, you can set `VLLM_ENFORCE_EAGER=1` to skip long initial compile cycles.

## Local run

Stable ROCm lane:

```bash
docker compose --env-file .env -f deploy/compose.yaml up -d --build
```

TheRock compatibility lane:

```bash
docker compose --env-file .env -f deploy/compose.yaml -f deploy/compose.therock.yaml up -d --build
```

Docs are published from [`docs/index.html`](./docs/index.html) and [`docs/redoc.html`](./docs/redoc.html). Refresh `docs/openapi.json` with:

```bash
cd backend
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/export_openapi.py
```

## Backend verification

```bash
cd backend
UV_CACHE_DIR=/tmp/uv-cache uv sync --frozen --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest ../tests
```

## Supported model profiles

- `qwen3-light`
- `deepseek-r1-distill`
- `gpt-oss`

Each deployment serves one active profile at a time. The gateway stays model-agnostic at the public API layer while the adapter isolates reasoning controls, prompt formatting hints, and vLLM launch flags for that profile.
