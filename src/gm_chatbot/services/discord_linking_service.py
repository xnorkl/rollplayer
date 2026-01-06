"""Discord linking service for managing Discord user to player links."""

import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..models.discord_link import DiscordLink, GuildInfo
from ..models.player import Player
from ..services.player_service import PlayerService


class DiscordLinkingService:
    """Service for managing Discord user to player links."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """
        Initialize Discord linking service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.player_service = PlayerService(self.store)

    async def link_discord_user(
        self,
        discord_user_id: str,
        discord_username: str,
        player_id: Optional[str] = None,
        guild_id: Optional[str] = None,
        guild_name: Optional[str] = None,
    ) -> DiscordLink:
        """
        Create or update a Discord link for a user.

        If player_id is not provided, a new player will be auto-created.

        Args:
            discord_user_id: Discord user ID (snowflake)
            discord_username: Discord username
            player_id: Optional existing player ID (creates new player if not provided)
            guild_id: Optional guild ID to add to guilds list
            guild_name: Optional guild name (required if guild_id provided)

        Returns:
            Created or updated DiscordLink
        """
        # Check if link already exists
        existing_link = await self.get_discord_link_by_user_id(discord_user_id)
        if existing_link:
            # Update existing link
            if player_id and existing_link.player_id != player_id:
                # Update player_id if provided and different
                existing_link.player_id = player_id
            existing_link.discord_username = discord_username
            existing_link.metadata.updated_at = datetime.now(timezone.utc)

            # Add guild if provided
            if guild_id and guild_name:
                # Check if guild already in list
                guild_exists = any(g.guild_id == guild_id for g in existing_link.guilds)
                if not guild_exists:
                    existing_link.guilds.append(
                        GuildInfo(
                            guild_id=guild_id,
                            guild_name=guild_name,
                            joined_at=datetime.now(timezone.utc),
                        )
                    )

            await self._save_discord_link(existing_link)
            return existing_link

        # Create new link
        if not player_id:
            # Auto-create player
            player = await self.player_service.create_player(
                username=f"discord_{discord_user_id}",
                display_name=discord_username,
                status="offline",
            )
            player_id = player.metadata.id

        # Verify player exists
        await self.player_service.get_player(player_id)

        # Create Discord link
        link = DiscordLink(
            player_id=player_id,
            discord_user_id=discord_user_id,
            discord_username=discord_username,
            linked_at=datetime.now(timezone.utc),
        )
        link.metadata.id = str(uuid4())

        # Add guild if provided
        if guild_id and guild_name:
            link.guilds.append(
                GuildInfo(
                    guild_id=guild_id,
                    guild_name=guild_name,
                    joined_at=datetime.now(timezone.utc),
                )
            )

        await self._save_discord_link(link)
        return link

    async def get_player_by_discord_id(self, discord_user_id: str) -> Optional[Player]:
        """
        Get player by Discord user ID.

        Args:
            discord_user_id: Discord user ID (snowflake)

        Returns:
            Player instance or None if not linked
        """
        link = await self.get_discord_link_by_user_id(discord_user_id)
        if link is None:
            return None

        try:
            return await self.player_service.get_player(link.player_id)
        except FileNotFoundError:
            return None

    async def unlink_discord_user(self, discord_user_id: str) -> None:
        """
        Remove Discord link for a user.

        Args:
            discord_user_id: Discord user ID (snowflake)

        Raises:
            FileNotFoundError: If link not found
        """
        link = await self.get_discord_link_by_user_id(discord_user_id)
        if link is None:
            raise FileNotFoundError(
                f"Discord link not found for user {discord_user_id}"
            )

        # Delete link file
        link_path = self.store.get_discord_link_path(link.player_id)
        if link_path.exists():
            link_path.unlink()

    async def get_discord_link(self, player_id: str) -> Optional[DiscordLink]:
        """
        Get Discord link for a player.

        Args:
            player_id: Player identifier

        Returns:
            DiscordLink instance or None if not linked
        """
        link_path = self.store.get_discord_link_path(player_id)
        if not link_path.exists():
            return None

        try:
            with link_path.open() as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return DiscordLink.from_yaml(content)
        except Exception:
            return None

    async def get_discord_link_by_user_id(
        self, discord_user_id: str
    ) -> Optional[DiscordLink]:
        """
        Get Discord link by Discord user ID.

        Args:
            discord_user_id: Discord user ID (snowflake)

        Returns:
            DiscordLink instance or None if not found
        """
        players_dir = self.store.get_players_dir()
        if not players_dir.exists():
            return None

        for player_dir in players_dir.iterdir():
            if player_dir.is_dir():
                link_path = player_dir / "discord_link.yaml"
                if link_path.exists():
                    try:
                        with link_path.open() as f:
                            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                            try:
                                content = f.read()
                            finally:
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                        link = DiscordLink.from_yaml(content)
                        if link.discord_user_id == discord_user_id:
                            return link
                    except Exception:
                        continue

        return None

    async def _save_discord_link(self, link: DiscordLink) -> None:
        """
        Save Discord link to file.

        Args:
            link: DiscordLink instance to save
        """
        link_path = self.store.get_discord_link_path(link.player_id)
        link_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = link_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(link.to_yaml())
                f.flush()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            temp_path.replace(link_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
