"""CLI adapter."""

from collections.abc import Awaitable, Callable

from ..adapters.interface import PlatformConfig
from ..models.chat import ChatMessage


class CLIAdapter:
    """CLI adapter for command-line interface."""

    def __init__(self):
        """Initialize CLI adapter."""
        self.message_handler: Callable[[ChatMessage], Awaitable[None]] | None = None

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
        return "cli"

    async def connect(self, config: PlatformConfig) -> None:
        """Establish connection (no-op for CLI)."""
        pass

    async def disconnect(self) -> None:
        """Gracefully disconnect (no-op for CLI)."""
        pass

    async def send_message(self, message: ChatMessage) -> None:
        """Send message to CLI output."""
        print(f"GM: {message.message}")

    async def on_message(
        self,
        callback: Callable[[ChatMessage], Awaitable[None]],
    ) -> None:
        """Register message handler."""
        self.message_handler = callback
