# Open-Weight Inference API Brief

## Recommended Project Names

- `openweight-responses-api` (recommended)
- `rocm-reasoning-api`
- `openweight-model-gateway`
- `strix-inference-api`
- `vllm-responses-gateway`

## Recommended Git Description

`Production-ready ROCm Responses API for open-weight reasoning models, with adapter-based support for multiple model families.`

## Product Goal

Build a production-ready, ROCm-first inference gateway for open-weight chat and reasoning models using vLLM.

The project must:

- target AMD ROCm platforms, especially Strix Halo / Ryzen AI Max
- be containerized from day 1
- be deployable locally, with Docker Compose, and on Kubernetes
- expose a modern API that is compatible with OpenAI-style clients
- support reasoning / thinking for multiple model families
- remain model-agnostic at the product layer without pretending all models behave the same
- stay strictly inference-only: no agents, no RAG, no business workflows

## Core Product Rules

- The service is a production inference API, not a demo and not an agent middleware.
- Keep the public API stable and clean.
- Keep the internal architecture extensible through model adapters.
- Support multiple model families in the codebase.
- Each running deployment serves one selected model profile at a time.
- Never hardcode behavior that only works for one model family into the public API handlers.

## Public API Contract

The public API must be modern and broadly compatible.

Required endpoints:

- `POST /v1/responses` as the primary modern endpoint
- `POST /v1/chat/completions` as the compatibility endpoint
- `GET /v1/models`
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`

Required behaviors:

- bearer auth
- SSE streaming where supported
- structured error responses
- strict request validation
- request IDs on every request
- OpenAPI 3.1 schema
- predictable JSON response shapes

Compatibility goals:

- work with OpenAI SDK-style clients
- work with n8n OpenAI-style integrations
- work with simple HTTP clients and SSE consumers

Do not make these the core product surface:

- legacy `POST /v1/completions`
- Anthropic Messages API as the primary contract
- tool execution as part of the default inference path
- embeddings, RAG, or orchestration APIs in this repo

Anthropic compatibility can be added later as a thin facade if needed, but it must not distort the core architecture.

## Model Strategy

The product must be model-agnostic at the API level, but not naive at the protocol level.

Use a model adapter registry.

Each supported model family must have its own isolated adapter/profile that defines:

- public model ID
- Hugging Face model ID
- vLLM launch arguments
- reasoning parser configuration
- prompt formatting strategy
- chat template / template kwargs
- request normalization logic
- response normalization logic
- streaming event normalization logic
- capability flags
- safe defaults for context, generation, and reasoning controls

Minimum required starter profiles:

- `openai/gpt-oss-20b`
- `Qwen/Qwen3.5-4B`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`

These are not just three model IDs.
They must be three separate adapter implementations.

Starter profile roles:

- `openai/gpt-oss-20b` = reasoning-capable OpenAI open-weight profile with a dedicated Harmony-based adapter
- `Qwen/Qwen3.5-4B` = lightweight common profile that defaults to normal non-CoT behavior
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` = separate reasoning-capable profile with its own DeepSeek-specific adapter path

Why this starter set:

- it gives one modern OpenAI-open model path
- it gives one very lightweight Qwen path
- it gives one second reasoning model from a different family
- it forces the codebase to prove real adapter isolation early

Good later additions after the core is stable:

- `Qwen/Qwen3.5-9B`
- `Qwen/Qwen3.5-27B`
- `deepseek-ai/DeepSeek-R1-0528`

Important rule:

- one product API
- many adapter implementations

Do not expose raw model quirks directly to the client if they can be normalized safely.

## Thinking / Reasoning Support

Reasoning support is mandatory.

The service must:

- support reasoning / thinking when the selected model supports it
- expose reasoning controls in a stable public way
- map reasoning controls to model-specific behavior inside the adapter layer
- return clear validation errors when a client requests a reasoning feature a model does not support
- stream reasoning-compatible outputs when the model and endpoint support it
- ship with at least two reasoning-capable starter profiles
- ship with at least one starter profile that defaults to normal non-thinking output

Reasoning normalization requirements:

- normalize reasoning effort levels per model family
- normalize reasoning output structure as much as possible
- do not invent fake reasoning support for models that do not provide it
- do not silently drop reasoning fields without telling the client

## Per-Model Isolation Layer

Every supported model must have its own isolated adapter layer.

This is not an embeddings feature.
It is a model protocol and normalization layer.

Requirements:

- do not share one generic prompt formatter across all models
- do not treat all reasoning models as if they use the same protocol
- keep shared request handlers thin and generic
- push model-specific quirks into the adapter layer
- keep the public API stable while adapters translate model-specific behavior internally

Mandatory starter adapters:

- `gpt-oss` adapter
- `qwen3.5-light` adapter
- `deepseek-r1-distill` adapter

Adapter-specific requirements:

- `gpt-oss` adapter:
  - use Harmony-compatible input formatting and output parsing
  - keep Harmony isolated inside the `gpt-oss` path
  - treat `gpt-oss` as its own protocol family
- `qwen3.5-light` adapter:
  - target `Qwen/Qwen3.5-4B`
  - default to normal non-CoT behavior
  - keep thinking disabled by default for this lightweight profile unless explicitly requested and supported
  - own its Qwen-specific template and generation normalization
- `deepseek-r1-distill` adapter:
  - target `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
  - support explicit reasoning / thinking behavior
  - own its DeepSeek-specific reasoning normalization
  - keep its parser and response handling separate from the Qwen and `gpt-oss` paths

This pattern should generalize:

- if another reasoning model family needs its own formatting or parser layer, implement it as another adapter
- keep model-specific protocol logic out of the shared request handlers

## ROCm / Strix Halo / TheRock Strategy

Primary hardware target:

- Strix Halo / Ryzen AI Max on ROCm

Runtime policy:

- use a pinned stable ROCm production lane as the default production target
- maintain a separate latest TheRock compatibility lane for forward-looking Strix Halo validation
- never make preview-only runtime assumptions the only supported path

Important:

- TheRock is valuable and should be supported
- TheRock must not be the only production story while it remains preview

The project should explicitly support:

- ROCm stable runtime for production
- latest TheRock runtime for compatibility and testing
- other ROCm-capable AMD targets where feasible, without weakening the Strix Halo focus

## Persistent Model Storage

Persistent model storage is mandatory.

Do not bake model weights into the image.
Do not rely on ephemeral container-only downloads.

Requirements:

- all model weights and caches must live on persistent host or PVC-backed storage
- local default host path should be `/home/hector/models/ollama/vllm`
- container runtime must mount a persistent model directory
- Hugging Face cache directories must also be persistent
- restarts must reuse cached weights instead of redownloading

Recommended env/config shape:

- `MODEL_CACHE_DIR`
- `HF_HOME`
- `HUGGINGFACE_HUB_CACHE`
- `VLLM_ASSETS_CACHE`
- `MODEL_ID`
- `MODEL_PROFILE`

Each deployment must declare exactly which model profile it serves and where persistent weights live.

## Architecture

Keep the architecture thin and explicit.

Recommended structure:

- `backend/` for the API gateway and adapter layer
- `backend/app/` for HTTP handlers, config, auth, health, metrics, schemas
- `backend/app/adapters/` for model-family adapters
- `backend/app/services/` for vLLM upstream integration only
- `docs/` for static API docs
- `deploy/` for Docker Compose, Kubernetes manifests, and Helm values
- `tests/` for unit, integration, contract, and smoke tests

Gateway responsibilities:

- authentication
- request validation
- capability checks
- adapter selection
- proxying to vLLM
- health and readiness
- metrics
- structured logging
- request tracing / correlation IDs
- OpenAPI generation

Gateway non-responsibilities:

- agent logic
- web search
- tool orchestration
- prompt engineering pipelines
- RAG
- business workflow logic
- embeddings API

## Backend Stack

Recommended stack:

- Python 3.12
- FastAPI for the external API contract
- Pydantic v2
- `uv` for Python package management
- `httpx` for upstream HTTP calls
- Prometheus metrics
- JSON structured logging

Quality expectations:

- typed code
- pinned dependencies
- clean configuration layer
- no hidden magic in request handlers
- no fake auth

## Frontend / Docs

This project does not need a product dashboard.

The only frontend required is static API documentation.

Requirements:

- plain HTML, CSS, and vanilla JavaScript only
- GitHub Pages friendly
- no React
- no Vite requirement for the docs site
- no SPA complexity

Required docs outputs:

- `docs/openapi.json`
- `docs/index.html` for OpenAPI UI
- `docs/redoc.html` for ReDoc

Nice-to-have:

- `docs/examples.html` with curl and JavaScript fetch examples
- `docs/streaming.html` showing SSE usage

The docs must be self-explanatory for enterprise users integrating the API.

## Security

Production security is required from the beginning.

Requirements:

- bearer token auth
- secrets only from env vars or secret mounts
- explicit CORS policy
- request size limits
- upstream timeouts
- no placeholder auth logic
- no permissive "any non-empty token works" behavior

Design for future additions:

- key rotation
- multiple API keys
- OIDC or enterprise auth in front of the service
- rate limiting at ingress or gateway

## Observability

The service must be operable under production load.

Required:

- JSON logs
- request IDs
- model ID / model profile in logs
- startup logs for model loading
- clear errors when model load fails
- Prometheus metrics
- liveness and readiness separation

Track useful metrics such as:

- request count
- latency
- stream duration
- error count
- upstream failure count
- readiness status

## Docker and Kubernetes

Docker-first is required.

Requirements:

- pinned images only, never floating `latest`
- Compose for local and staging smoke tests
- Kubernetes manifests or Helm values for deployment
- health probes
- resource requests and limits
- secret/config separation
- AMD GPU scheduling support

Kubernetes expectations:

- one deployment serves one model profile
- horizontal scaling by adding more serving pods
- keep the service stateless except for persistent model cache mounts
- support node selectors / tolerations / runtime settings needed for AMD GPU nodes

## Testing

The project must ship with serious tests.

Required test layers:

- unit tests for config, auth, schemas, and adapter logic
- integration tests for gateway to vLLM behavior
- contract tests for OpenAPI correctness
- streaming tests
- reasoning tests per supported model family
- smoke tests for Docker Compose
- deployment validation for Kubernetes manifests or Helm templates

Test goals:

- verify `Responses` and `Chat Completions` behavior
- verify `GET /v1/models`
- verify health and readiness behavior during cold start
- verify adapter-specific reasoning logic
- verify `gpt-oss` Harmony path separately from generic chat-template models

## Non-Goals

Do not add these unless explicitly requested later:

- RAG
- vector databases
- agent loops
- web search
- tool servers as a default feature
- multi-model routing inside one live deployment
- billing systems
- admin dashboards

## Definition of Done

The project is done when all of the following are true:

- a pinned ROCm deployment works on the target AMD platform
- Strix Halo is a first-class supported target
- a TheRock compatibility lane exists
- one selected model profile serves real traffic reliably
- multiple model families are supported through adapters in the codebase
- the starter set includes `openai/gpt-oss-20b`, `Qwen/Qwen3.5-4B`, and `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
- each starter model has its own isolated adapter implementation
- reasoning works for supported models
- `gpt-oss` has its own dedicated protocol layer
- `Qwen/Qwen3.5-4B` works as the lightweight default normal-output profile
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` works as a second reasoning profile
- `Responses` works
- `Chat Completions` compatibility works
- streaming works
- persistent model storage works
- OpenAPI docs and ReDoc static pages exist in plain HTML/JS
- Docker Compose works
- Kubernetes deployment artifacts exist
- tests pass
- the repo reads like a production system, not a toy experiment

## Build Priorities

Recommended order of work:

1. establish the API contract and adapter abstractions
2. implement `Qwen/Qwen3.5-4B` as the lightweight baseline profile
3. implement `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` as the second reasoning adapter
4. implement `openai/gpt-oss-20b` with its Harmony-specific adapter path
5. implement auth, health, readiness, metrics, and structured errors
6. add static docs and generated OpenAPI output
7. add Docker Compose and Kubernetes deployment artifacts