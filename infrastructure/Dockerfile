# Use UV base image for faster builds
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY rules/ ./rules/
COPY campaigns/ ./campaigns/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "gm_chatbot.main"]
