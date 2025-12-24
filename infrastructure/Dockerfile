# Dockerfile for GM Chatbot on Fly.io
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY shadowdark_rules.py ./

# Expose WebSocket port
EXPOSE 5678

# Health check (optional, Fly.io will use its own)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.connect(('localhost', 5678)); s.close()" || exit 1

# Run the application
CMD ["python3", "chat_bot.py"]

