FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY app ./app
COPY scripts ./scripts

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

COPY --from=build /app /app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

