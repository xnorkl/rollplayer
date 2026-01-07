# Use UV base image with Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies directly in runtime stage (ensures Python interpreter compatibility)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ ./src/

# Create volume mount points for persistent storage
RUN mkdir -p /data/campaigns /data/rules

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "gm_chatbot.main"]
