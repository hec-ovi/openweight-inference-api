# BACKEND RULES (Python + FastAPI)

## Stack

- Python 3.12+
- FastAPI (latest 0.128.x) for API framework
- Pydantic v2 (latest 2.12.x) for validation and serialization
- `uv` for all dependency management (replaces pip entirely)
- Docker containerized (multi-stage, slim images)

---

## Architecture Pattern

Strict three-layer architecture. Each layer has a single responsibility and never bleeds into another:

```
Route (HTTP only) → Service (business logic) → Tool (isolated unit)
```

- **Routes (`/routes/`)** handle HTTP concerns only: parse request via Pydantic models, call service, return response with status codes and headers. Delegate ALL business logic to services.
- **Services (`/services/`)** contain ALL business logic: pure Python, no FastAPI imports, stateless, reusable across different routes. All context received via parameters.
- **Tools (`/tools/`)** are isolated, reusable units: no knowledge of FastAPI, agents, or business context. Framework-agnostic, single-responsibility, stateless. Any service can use any tool.

**Pattern Example:**
```python
# routes/user.py — HTTP only
@router.post("/users", tags=["Users"])
async def create_user(data: UserCreateDTO) -> UserResponse:
    """Create a new user account."""
    return await user_service.create(data)

# services/user_service.py — business logic only
async def create(data: UserCreateDTO) -> UserResponse:
    # Business logic here
    pass
```

---

## File Organization

```
backend/
  Dockerfile
  pyproject.toml
  uv.lock
  src/
    main.py              # FastAPI app entry point
    /routes/             # HTTP route handlers (API endpoints)
    /services/           # Business logic services
    /models/             # Pydantic models (DTOs, entities)
    /tools/              # Isolated, reusable tool classes
    /prompts/            # AI prompts as .md files
    /core/               # Config, database, exceptions, dependencies
    /lib/                # Utilities, helpers
```

**Rules:**
- One file per domain in each folder (`user.py`, `auth.py`, `chat.py`)
- Never import from routes into services (only the reverse)
- Tools are completely isolated — no FastAPI dependencies, no service imports
- Never dump all files loose in `/backend/src/`

---

## UV Workflow

UV replaces pip, venv, pip-tools, and poetry. It is Rust-based, 10-100x faster, and handles everything from project init to production Docker builds.

**Project Setup:**
```bash
uv init backend                    # Create project with pyproject.toml
uv add "fastapi[standard]"        # Add FastAPI + uvicorn + pydantic
uv add sqlalchemy httpx            # Add dependencies
uv add --dev pytest ruff           # Add dev-only dependencies
```

**Running (Docker-first):**
```bash
# Development / verification
docker compose up backend

# One-off run with reload inside the backend container
docker compose run --rm --service-ports backend \
  uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src

# Production
docker compose up -d backend
```

**Key Files:**
- `pyproject.toml` — project metadata and dependencies (replaces `requirements.txt`)
- `uv.lock` — deterministic lock file (always commit this)

**Search the internet for the latest UV version and commands before configuring.** UV evolves fast — always verify against `https://docs.astral.sh/uv/`.

---

## Async & Streaming

- Use `async def` for **all** routes, services, and tools that do I/O (database, HTTP, LLM calls).
- For LLM streaming responses, use **Server-Sent Events (SSE)** via `StreamingResponse`.
- Streaming follows the same three-layer architecture:
  - **Route** creates the `StreamingResponse`
  - **Service** yields chunks (business logic, formatting)
  - **Tool** handles the raw LLM connection
- WebSockets are acceptable for bidirectional real-time features, but **prefer SSE for one-way streams** like LLM output.

---

## Type Safety (100% Pydantic)

- **NO untyped dictionaries** anywhere in the codebase.
- Every function parameter and return type must be typed.
- Use Pydantic models for ALL data structures.
- Use `|` union syntax (Python 3.10+), not `Optional` or `Union`.
- Use `Annotated` for dependency injection and field metadata.

```python
from typing import Annotated
from fastapi import Depends
from pydantic import BaseModel, Field

# Pydantic model with Annotated fields
class UserCreateDTO(BaseModel):
    email: Annotated[str, Field(description="User's email address")]
    name: Annotated[str, Field(description="User's full name")]

# Dependency injection with Annotated
async def get_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    pass

# Union syntax — never use Optional
def find_user(user_id: str) -> User | None:
    pass
```

---

## Error Handling

- Use **custom exception classes** in `/core/exceptions.py`.
- **Services** raise domain exceptions.
- **Routes** catch domain exceptions and convert to HTTP responses.
- Never return `None` for errors — raise exceptions.

```python
# core/exceptions.py
class UserNotFoundError(Exception):
    pass

# services/user_service.py
if not user:
    raise UserNotFoundError(f"User {user_id} not found")

# routes/user.py
try:
    user = await user_service.get(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail="User not found")
```

---

## Dependency Injection

- Use FastAPI's `Depends()` with `Annotated` for shared resources.
- Database connections, config, external clients — all injected.

```python
from typing import Annotated
from fastapi import Depends

DBSession = Annotated[AsyncSession, Depends(get_db)]

@router.get("/users/{id}", tags=["Users"])
async def get_user(id: str, db: DBSession) -> UserResponse:
    """Retrieve a user by ID."""
    pass
```

---

## API Design & OpenAPI

**Every endpoint MUST be documented via OpenAPI.** FastAPI auto-generates OpenAPI from Pydantic models and return type annotations.

```python
from pydantic import BaseModel, Field
from typing import Annotated

class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    email: Annotated[str, Field(description="User's email address")]
    name: Annotated[str, Field(description="User's full name")]

class UserResponse(BaseModel):
    """User data response."""
    id: Annotated[str, Field(description="Unique user identifier")]
    email: Annotated[str, Field(description="User's email address")]
    created_at: Annotated[datetime, Field(description="Account creation timestamp")]

# Use return type annotation — NOT response_model= (avoids double validation)
@app.post("/users", tags=["Users"])
async def create_user(data: CreateUserRequest) -> UserResponse:
    """Create a new user account."""
    pass
```

**Requirements:**
- Every route has Pydantic request/response models with `Field(description=...)`
- Use **return type annotations** for response models, not `response_model=` in the decorator (avoids double Pydantic validation)
- All routes have docstrings and tags
- OpenAPI docs available at `/docs` and `/openapi.json`

---

## Docstrings

Mandatory for every public method and class. Google-style, concise:

```python
async def create_user(data: UserCreateDTO) -> UserResponse:
    """Create a new user in the system.

    Args:
        data: User creation data including email and password.

    Returns:
        UserResponse with created user details.

    Raises:
        UserAlreadyExistsError: If email is already registered.
    """
```

---

## Backend Dockerfile (UV + Multi-Stage)

All backend containers use UV with multi-stage builds for minimal image size. **Search the internet for the latest UV Docker patterns before building.**

```dockerfile
# === Build Stage ===
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Install project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# === Runtime Stage ===
FROM python:3.12-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=build /app /app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key flags:**
- `--locked` — ensures lock file matches `pyproject.toml` (stricter than `--frozen`, better for deploys)
- `--no-install-project` — first pass installs only dependencies (better Docker layer caching)
- `--no-dev` — excludes dev dependencies from production image
- `UV_COMPILE_BYTECODE=1` — pre-compiles `.pyc` for faster startup
- `UV_LINK_MODE=copy` — avoids hardlink warnings in containers

Add `.venv` to `.dockerignore` — the venv is platform-dependent and must be created fresh in the image.

---

## Agentic Patterns (LangGraph)

For agentic AI workflows, **LangGraph 1.0** is the production standard (GA, stable API, no breaking changes until 2.0).

**When to use what:**

| Complexity | Framework | Use Case |
|---|---|---|
| Simple linear chains (RAG, chatbot) | LangChain | Quick setup, minimal orchestration |
| Stateful multi-step agents | **LangGraph** | Branching, loops, tool-calling, human-in-the-loop |
| Role-based multi-agent teams | CrewAI | Collaborative agents with defined roles |

**LangGraph Production Best Practices:**
- **State must be small, typed, and validated.** Use `TypedDict` with `Annotated` reducers. Never dump everything into state — only what nodes need to pass between each other.
- **Bound all cycles.** Agentic loops (retry, tool-call) need hard stops: `max_steps` counter, exponential backoff, explicit exit conditions for "no progress."
- **Use Postgres checkpointing** (`PostgresSaver`) for production persistence. `MemorySaver` is for tutorials only — it is in-memory and does not survive restarts.
- **Streaming:** Choose deliberately between streaming messages, updates, values, or custom events based on UX needs.
- **Error boundaries at every level:** node-level, graph-level, and app-level. Graceful degradation over hard crashes.
- **Tools follow the same isolation rules** as the rest of the backend — each tool in its own file in `/tools/`, stateless, framework-agnostic. LangGraph nodes import tools, tools never know about LangGraph.

---

## Prompt Engineering for Tools & Agents

**CRITICAL: Prompts are the most under-engineered part of most agentic systems.** A vague, generic prompt produces vague, generic output. Production prompts are precision instruments.

All prompts live as `.md` files in `/prompts/`, loaded at runtime. Never hardcode prompts in Python strings.

**Production Prompt Structure (mandatory for every tool/agent prompt):**

```markdown
ROLE: [1-2 lines — who/what, domain expertise]

OBJECTIVE: [The single task or narrow mission]

CONSTRAINTS:
- [Positive framing: "Only do X" not "Don't do Y"]
- [Scope limits, safety rules, operational boundaries]

INPUT: [What the agent receives — schema, field descriptions]

OUTPUT FORMAT:
- [Explicit schema: JSON, markdown template, structured format]
- [The model must know exactly what shape to return]

EXAMPLES: [1-3 input→output pairs, covering happy path + edge case]
```

**Anti-patterns that produce bad output:**
- Vague role ("You are a helpful assistant") — be specific about domain and expertise level
- No output contract — always define the exact schema or template
- No examples — even 1 few-shot example dramatically improves consistency
- Overloaded prompts — one prompt = one job. Decompose multi-task workflows
- Negative framing ("don't do X") — reframe positively ("only do X")
- No success criteria — define what "correct" looks like before writing the prompt

**Treat prompts as code:** version-controlled in `/prompts/`, tested, iterated. The first version is never production-ready.

---

## Backend Reinforcement

These rules reinforce the general best practices from `instructions.md` for the specific context where Python backends most commonly fail:

**Monolithic Prevention:** Python backends are the #1 place where code collapses into monolithic files. An agent service is NOT a 500-line file with tools, prompts, and business logic inlined. Route files contain only HTTP handling. Service files contain only business logic. Tool files contain only the tool. One class per file. No exceptions.

**Code Quality:** Python is permissive — enforce discipline. No untyped `dict` returns. No `Any` types. No bare `except`. No mutable default arguments. Every public function has a return type. Simplify relentlessly — if a function exceeds reasonable scope, split it.

**Prompts as Files:** Never `prompt = "You are a..."` in Python code. Every prompt is a `.md` file in `/prompts/`, loaded with `Path("prompts/name.md").read_text()`. This makes prompts diffable, reviewable, and iterable without touching Python.

**Schemas as Contracts:** Input/output schemas for tools and agents are Pydantic models in `/models/`, not inline dictionaries. Schemas are shared contracts — tools, services, and routes all reference the same models.
