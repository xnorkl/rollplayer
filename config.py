"""Configuration settings for the GM Chatbot."""

import os
from typing import Optional

# LLM Configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = 0.3

# WebSocket Configuration
# Fly.io sets PORT automatically, but we use WS_PORT for consistency
# Support both PORT (Fly.io) and WS_PORT (local) environment variables
WS_ADDRESS: str = os.getenv(
    "WS_ADDRESS", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
)
WS_PORT: int = int(os.getenv("PORT") or os.getenv("WS_PORT", "5678"))

# Shadowdark Rule Constants
DC_EASY: int = 5
DC_NORMAL: int = 10
DC_HARD: int = 15
DC_VERY_HARD: int = 20

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
