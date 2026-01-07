"""Discord binding service for managing campaign to channel bindings."""

import fcntl
from datetime import UTC, datetime

from ..artifacts.store import ArtifactStore
from ..models.discord_binding import DiscordBinding


class DiscordBindingService:
    """Service for managing Discord campaign to channel bindings."""

    def __init__(self, store: ArtifactStore | None = None):
        """
        Initialize Discord binding service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()

    async def bind_campaign_to_channel(
        self,
        campaign_id: str,
        guild_id: str,
        channel_id: str,
        channel_name: str,
        bound_by: str,
        settings: dict | None = None,
    ) -> DiscordBinding:
        """
        Bind a campaign to a Discord channel.

        Args:
            campaign_id: Campaign identifier
            guild_id: Discord guild ID (snowflake)
            channel_id: Discord channel ID (snowflake)
            channel_name: Discord channel name
            bound_by: Player ID who created the binding
            settings: Optional settings dict

        Returns:
            Created or updated DiscordBinding

        Raises:
            ValueError: If channel is already bound to another campaign
        """
        # Check if channel is already bound to another campaign
        existing_binding = await self.get_binding_by_channel(channel_id)
        if existing_binding and existing_binding.campaign_id != campaign_id:
            raise ValueError(
                f"Channel {channel_id} is already bound to campaign {existing_binding.campaign_id}"
            )

        # Check if campaign already has a binding
        existing = await self.get_binding(campaign_id)
        if existing:
            # Update existing binding
            existing.guild_id = guild_id
            existing.channel_id = channel_id
            existing.channel_name = channel_name
            existing.bound_by = bound_by
            existing.metadata.updated_at = datetime.now(UTC)
            if settings is not None:
                existing.settings.update(settings)

            await self._save_binding(existing)
            return existing

        # Create new binding
        binding = DiscordBinding(
            campaign_id=campaign_id,
            guild_id=guild_id,
            channel_id=channel_id,
            channel_name=channel_name,
            bound_at=datetime.now(UTC),
            bound_by=bound_by,
        )
        if settings is not None:
            binding.settings.update(settings)

        binding.metadata.id = str(campaign_id)  # Use campaign_id as binding ID

        await self._save_binding(binding)
        return binding

    async def get_campaign_by_channel(self, channel_id: str) -> str | None:
        """
        Get campaign ID bound to a Discord channel.

        Args:
            channel_id: Discord channel ID (snowflake)

        Returns:
            Campaign ID or None if not bound
        """
        binding = await self.get_binding_by_channel(channel_id)
        return binding.campaign_id if binding else None

    async def get_binding(self, campaign_id: str) -> DiscordBinding | None:
        """
        Get Discord binding for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            DiscordBinding instance or None if not bound
        """
        binding_path = self.store.get_discord_binding_path(campaign_id)
        if not binding_path.exists():
            return None

        try:
            with binding_path.open() as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return DiscordBinding.from_yaml(content)  # type: ignore[return-value]
        except Exception:
            return None

    async def get_binding_by_channel(self, channel_id: str) -> DiscordBinding | None:
        """
        Get Discord binding by channel ID.

        Args:
            channel_id: Discord channel ID (snowflake)

        Returns:
            DiscordBinding instance or None if not found
        """
        campaigns_dir = self.store.campaigns_dir
        if not campaigns_dir.exists():
            return None

        for campaign_dir in campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                binding_path = campaign_dir / "discord_binding.yaml"
                if binding_path.exists():
                    try:
                        with binding_path.open() as f:
                            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                            try:
                                content = f.read()
                            finally:
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                        binding = DiscordBinding.from_yaml(content)
                        if binding.channel_id == channel_id:
                            return binding
                    except Exception:
                        continue

        return None

    async def unbind_campaign(self, campaign_id: str) -> None:
        """
        Remove Discord binding for a campaign.

        Args:
            campaign_id: Campaign identifier

        Raises:
            FileNotFoundError: If binding not found
        """
        binding_path = self.store.get_discord_binding_path(campaign_id)
        if not binding_path.exists():
            raise FileNotFoundError(f"Discord binding not found for campaign {campaign_id}")

        binding_path.unlink()

    async def list_campaigns_in_guild(self, guild_id: str) -> list[DiscordBinding]:
        """
        List all campaigns bound in a Discord guild.

        Args:
            guild_id: Discord guild ID (snowflake)

        Returns:
            List of DiscordBinding instances
        """
        bindings = []
        campaigns_dir = self.store.campaigns_dir
        if not campaigns_dir.exists():
            return bindings

        for campaign_dir in campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                binding_path = campaign_dir / "discord_binding.yaml"
                if binding_path.exists():
                    try:
                        with binding_path.open() as f:
                            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                            try:
                                content = f.read()
                            finally:
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                        binding = DiscordBinding.from_yaml(content)
                        if binding.guild_id == guild_id:
                            bindings.append(binding)
                    except Exception:
                        continue

        return bindings

    async def _save_binding(self, binding: DiscordBinding) -> None:
        """
        Save Discord binding to file.

        Args:
            binding: DiscordBinding instance to save
        """
        binding_path = self.store.get_discord_binding_path(binding.campaign_id)
        binding_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = binding_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(binding.to_yaml())
                f.flush()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            temp_path.replace(binding_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
