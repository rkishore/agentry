# syntax=docker/dockerfile:1

# --- builder: resolve and install dependencies into a venv ---
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev

# --- runtime: copy the venv and source, run the CLI ---
FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY tests/fixtures ./tests/fixtures

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "agentry.entrypoints.cli"]
CMD ["--help"]
