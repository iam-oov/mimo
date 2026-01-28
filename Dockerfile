# ============================================
# Stage 1: Builder - Install dependencies with uv
# ============================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first (better cache utilization)
COPY pyproject.toml uv.lock ./

# Install dependencies without dev packages
# --frozen: use exact versions from lockfile
# --no-dev: skip development dependencies
# --no-editable: install as regular packages
RUN uv sync --frozen --no-dev --no-editable

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 mimo && \
  useradd --uid 1000 --gid mimo --shell /bin/bash --create-home mimo

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=mimo:mimo src/ ./src/
COPY --chown=mimo:mimo templates/ ./templates/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER mimo

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
