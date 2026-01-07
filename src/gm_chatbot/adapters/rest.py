"""REST API adapter (primary platform)."""

from collections.abc import Awaitable, Callable

from ..adapters.interface import PlatformConfig
from ..models.chat import ChatMessage


class RESTAdapter:
    """REST API adapter - primary platform interface."""

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
        return "rest_api"

    async def connect(self, config: PlatformConfig) -> None:
        """Establish connection (no-op for REST)."""
        pass

    async def disconnect(self) -> None:
        """Gracefully disconnect (no-op for REST)."""
        pass

    async def send_message(self, message: ChatMessage) -> None:
        """Send message (handled by API endpoints)."""
        # REST API handles messages via HTTP endpoints
        pass

    async def on_message(
        self,
        callback: Callable[[ChatMessage], Awaitable[None]],
    ) -> None:
        """Register message handler (handled by API endpoints)."""
        # REST API handles messages via HTTP endpoints
        pass
