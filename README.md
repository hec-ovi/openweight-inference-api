<h1 align="center">openweight-inference-api</h1>

<p align="center">
  <strong>ROCm-first vLLM gateway for open-weight inference. One active model, one clean contract, host-backed weights, no image-baked surprises.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Working-brightgreen" alt="Status" />
  <img src="https://img.shields.io/badge/AMD-ROCm-ED1C24?logo=amd&logoColor=white" alt="ROCm" />
  <img src="https://img.shields.io/badge/vLLM-Stable_lane-4B2E83" alt="vLLM" />
  <img src="https://img.shields.io/badge/API-OpenAI_Responses-000" alt="OpenAI Responses" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License" />
</p>

---

## 🟢 Why This Repo Exists

This repo turns a ROCm box into a production-minded OpenAI-style inference gateway with:

- `POST /v1/chat/completions`
- `POST /v1/responses`
- `GET /v1/models`
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`

It is intentionally conservative:

- one active model profile at a time
- host-backed model storage
- strict bearer auth
- no deprecated Hugging Face cache variables
- fail-closed behavior when a model/runtime combination is not clean enough to support

The tracked default is:

- `MODEL_PROFILE=gpt-oss`

That is the cleanest production profile on the current stable ROCm/vLLM lane.

## 🔵 What Ships Here

- FastAPI gateway with request IDs, JSON logs, CORS, request-size limits, and Prometheus metrics
- Stable ROCm deployment lane in [`deploy/compose.yaml`](./deploy/compose.yaml)
- Optional TheRock lane in [`deploy/compose.therock.yaml`](./deploy/compose.therock.yaml)
- Static API docs in [`docs/`](./docs)
- Three model profiles:
  - `gpt-oss`
  - `deepseek-r1-distill`
  - `qwen3-light`

## 🟠 The Fun Part: What Surprised Us

The strangest result in the whole project was not model quality. It was memory behavior.

- `Qwen/Qwen3-4B` loaded about `7.5894 GiB` of weights.
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` loaded about `14.3492 GiB` of weights.
- `openai/gpt-oss-20b` loaded about `14.2905 GiB` of weights on this runtime because the current lane uses quantized GPT-OSS.

And yet, on a `116 GiB` ROCm-visible card, total observed VRAM still hovered around `104-105 GiB` for different models.

That looked wrong at first. It was not multiple models loading. It was not duplicate engines. It was vLLM doing exactly what it was configured to do:

- `VLLM_GPU_MEMORY_UTILIZATION=0.9`
- `VLLM_MAX_MODEL_LEN=32768`

So the card was being filled mostly by KV cache reservation and runtime workspace, not just weights. The split changed. The total target barely did.

The second surprise was speed versus obedience:

- Qwen was the most obedient plain-chat model in the fixed-output test.
- GPT-OSS and DeepSeek pushed more raw decode throughput in several runs, but they also burned output budget on hidden reasoning or intermediate output.
- In other words: fastest token generation did not automatically mean cleanest visible answer.

## 🔴 What We Intentionally Left Out

This repo does not try to do everything.

- No multi-model serving or multiplexing in one stack.
- No baking model weights into the images.
- No deprecated Hugging Face env names.
- No brittle regex-heavy normalization layer to force every reasoning model into one fake-perfect shape.
- No pretending that unstable modes are production-ready.

What is intentionally left out of scope for this pass:

- concurrency and load benchmarks
- long-context stress and OOM characterization
- tool-calling validation across every profile
- live TheRock benchmark pass

## 🟡 Profile Matrix

### `gpt-oss`

- Backing model: `openai/gpt-oss-20b` (`20B` parameters)
- Status: primary production profile
- Live verified:
  - `chat/completions` plain mode
  - `chat/completions` reasoning mode
  - `responses` plain mode
  - streaming

### `deepseek-r1-distill`

- Backing model: `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` (`7B` parameters)
- Live verified:
  - `chat/completions` plain mode
  - `chat/completions` reasoning mode
- Current limitation on the stable runtime:
  - `responses` plain mode can still spend the entire output budget upstream on hidden reasoning and may return no visible message
- Recommendation:
  - use `chat/completions` for DeepSeek production traffic on this lane

### `qwen3-light`

- Backing model: `Qwen/Qwen3-4B` (`4B` parameters)
- Live verified:
  - plain chat mode
  - streaming
- Support intentionally reduced on the stable runtime:
  - normalized reasoning is disabled
  - `responses` is disabled
  - `/v1/models` advertises `reasoning=false` and `responses=false` for Qwen on this lane
- Recommendation:
  - use Qwen as the lightweight plain-chat alternate profile

## 🟣 Benchmark Method

Benchmarks below were run on the stable ROCm lane after rebuilding the images and switching one active profile at a time. They use `POST /v1/chat/completions`.

Metric precision:

- `seconds` is client-side wall-clock time around the HTTP request, not a native vLLM latency field
- `completion tokens` comes from the API `usage.completion_tokens` field
- `tokens/s` is `completion tokens / seconds`
- `reasoning tokens` and `answer tokens` are counted by sending extracted text back through the active tokenizer at `/tokenize`
- unsupported modes are shown as `X`

Important caveat:

- On this stable lane, vLLM logs that the top-level chat `reasoning` request field is ignored for GPT-OSS and DeepSeek.
- End-to-end latency and total token counts are still real.
- Reasoning-vs-answer subtotals are only exact when the returned payload exposes those pieces cleanly.
- Hidden reasoning can still consume budget even when visible reasoning is not surfaced.

## 🔵 Fixed-Output Speed Benchmark

Prompt instruction:

```text
Return exactly this sentence and nothing else: "The little analytical chatbot crossed the private net of my rig and returned these tokens intact, with borrowed dignity."
```

| Profile | Reasoning | Seconds | Tokens/s | Completion Tokens | Reasoning Tokens | Answer Tokens | Exact Match | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-oss | off | 21.33 | 6.85 | 146 | 0 | 21 | yes |  |
| gpt-oss | on | 10.73 | 8.95 | 96 | 93 | 0 | no | exact mismatch; hit max_tokens |
| deepseek-r1-distill | off | 17.23 | 11.14 | 192 | 0 | 0 | no | exact mismatch; hit max_tokens |
| deepseek-r1-distill | on | 7.48 | 12.84 | 96 | 96 | 0 | no | exact mismatch; hit max_tokens |
| qwen3-light | off | 3.75 | 6.14 | 23 | 0 | 22 | yes |  |
| qwen3-light | on | X | X | X | X | X | X | X |

Read of the table:

- Qwen plain chat was the cleanest exact-output follower.
- GPT-OSS plain chat did eventually return the exact sentence, but more slowly and with a much larger completion budget.
- GPT-OSS and DeepSeek reasoning-on runs used the tested budget on reasoning-heavy output rather than landing the exact visible sentence.

## 🟠 Trick-Reasoning Benchmark

Prompt:

```text
A room has 99 murderers. I walk into the room and murder 3 of them. How many murderers are in the room right now? Count dead murderers too. Explain briefly, then end with `Final: <number>`.
```

| Profile | Reasoning | Seconds | Tokens/s | Completion Tokens | Reasoning Tokens | Answer Tokens | Answer | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-oss | off | 29.3 | 10.92 | 320 | 0 | 0 |  | hit max_tokens |
| gpt-oss | on | 14.74 | 10.86 | 160 | 157 | 0 |  | hit max_tokens |
| deepseek-r1-distill | off | 24.93 | 12.84 | 320 | 0 | 0 |  | hit max_tokens |
| deepseek-r1-distill | on | 12.47 | 12.83 | 160 | 160 | 0 |  | hit max_tokens |
| qwen3-light | off | 7.24 | 16.03 | 116 | 0 | 115 | Final: 99 |  |
| qwen3-light | on | X | X | X | X | X | X | X |

Read of the table:

- Qwen plain chat answered the riddle cleanly under the tested budget.
- GPT-OSS and DeepSeek again spent the chosen budget on hidden reasoning or intermediate output on this lane.
- Qwen reasoning rows are `X` by design because the gateway now rejects that unstable contract instead of patching around it.

## 🟢 Small Conclusion

If you want the cleanest plug-and-play production path here, use GPT-OSS as the default profile and treat it as the primary contract surface. If you want the fastest lightweight plain-chat alternate, use Qwen. If you want DeepSeek, keep it on `chat/completions` and accept that plain-mode economics are still distorted by hidden reasoning on the current stable runtime.

This is the honest summary:

- ROCm works
- host-backed model caching works
- one-model-at-a-time orchestration works
- streaming works
- GPT-OSS is the best default production choice
- Qwen is the best lightweight plain-chat choice
- forcing every reasoning model into one perfectly uniform contract would have made the code worse, so the repo now refuses the unstable parts instead

## 🟠 Model Storage

Weights are stored on the host, not inside the images.

- `MODEL_CACHE_DIR=/var/lib/openweight/models/vllm`
- `HF_HOME=/models/vllm/hf`
- `HF_HUB_CACHE=/models/vllm/hub`
- `HF_ASSETS_CACHE=/models/vllm/assets`

Tracked files only use the current official Hugging Face cache variables.

## 🔵 Required Env

Your local `.env` should include at least:

```dotenv
HF_TOKEN=hf_...
API_BEARER_KEYS=replace-with-a-real-long-random-token
MODEL_PROFILE=gpt-oss
```

The full template is in [`.env.template`](./.env.template).

## 🟡 Run

Stable ROCm lane:

```bash
docker compose --env-file .env -f deploy/compose.yaml up -d --build
```

TheRock lane:

```bash
docker compose --env-file .env -f deploy/compose.yaml -f deploy/compose.therock.yaml up -d --build
```

Refresh the generated OpenAPI docs with:

```bash
cd backend
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/export_openapi.py
```

## 🟢 Verification

Backend tests:

```bash
cd backend
UV_CACHE_DIR=/tmp/uv-cache uv sync --frozen --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest ../tests
```

Current automated status:

- `21` tests passing

Live ROCm validation performed on the stable lane:

- `openai/gpt-oss-20b`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
- `Qwen/Qwen3-4B`

## 🔴 API Auth

Clients must send your gateway bearer key:

```http
Authorization: Bearer your-secret-key
```

`HF_TOKEN` is only for downloading model weights from Hugging Face. It is not your inference API key.

---

## License

[MIT](LICENSE).
