"""Player service for player management."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.player import Player


class PlayerService:
    """Service for managing players."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """
        Initialize player service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()

    async def create_player(
        self,
        username: str,
        display_name: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        status: str = "offline",
    ) -> Player:
        """
        Create a new player.

        Args:
            username: Unique username
            display_name: Display name
            email: Optional email
            avatar_url: Optional avatar URL
            status: Player status (default: "offline")

        Returns:
            Created player

        Raises:
            ValueError: If username already exists
        """
        # Check username uniqueness
        if not await self.check_username_unique(username):
            raise ValueError(f"Username '{username}' already exists")

        player_id = str(uuid4())
        player = Player(
            username=username,
            display_name=display_name,
            email=email,
            avatar_url=avatar_url,
            status=status,
        )
        player.metadata.id = player_id

        # Create player directory
        player_dir = self.store.get_player_dir(player_id)
        player_dir.mkdir(parents=True, exist_ok=True)

        # Save player.yaml (use campaign_id as player_id for save_artifact compatibility)
        # We'll need to save directly since players are not in campaigns
        import fcntl
        from pathlib import Path

        file_path = player_dir / "player.yaml"
        temp_path = file_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(player.to_yaml())
                f.flush()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            temp_path.replace(file_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return player

    async def get_player(self, player_id: str) -> Player:
        """
        Get a player by ID.

        Args:
            player_id: Player identifier

        Returns:
            Player instance

        Raises:
            FileNotFoundError: If player not found
        """
        import fcntl
        from pathlib import Path

        player_dir = self.store.get_player_dir(player_id)
        file_path = player_dir / "player.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Player {player_id} not found")

        with file_path.open() as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                content = f.read()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return Player.from_yaml(content)

    async def get_player_by_username(self, username: str) -> Optional[Player]:
        """
        Get a player by username.

        Args:
            username: Username

        Returns:
            Player instance or None if not found
        """
        players_dir = self.store.get_players_dir()
        if not players_dir.exists():
            return None

        for player_dir in players_dir.iterdir():
            if player_dir.is_dir():
                try:
                    player = await self.get_player(player_dir.name)
                    if player.username == username:
                        return player
                except Exception:
                    continue

        return None

    async def update_player(self, player: Player) -> Player:
        """
        Update a player.

        Args:
            player: Updated player instance

        Returns:
            Updated player

        Raises:
            ValueError: If username changed and new username already exists
        """
        # If username changed, check uniqueness
        existing = await self.get_player(player.metadata.id)
        if existing.username != player.username:
            if not await self.check_username_unique(player.username):
                raise ValueError(f"Username '{player.username}' already exists")

        # Update timestamp
        player.metadata.updated_at = datetime.utcnow()

        # Save directly (players are not in campaigns)
        import fcntl
        from pathlib import Path

        player_dir = self.store.get_player_dir(player.metadata.id)
        file_path = player_dir / "player.yaml"
        temp_path = file_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(player.to_yaml())
                f.flush()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            temp_path.replace(file_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return player

    async def delete_player(self, player_id: str) -> None:
        """
        Delete a player.

        Args:
            player_id: Player identifier

        Raises:
            ValueError: If player is in an active session
        """
        # Check if player is in active session
        active_session = await self.get_player_active_session(player_id)
        if active_session is not None:
            raise ValueError(
                f"Cannot delete player {player_id}: player is in active session {active_session.metadata.id}"
            )

        # Delete player directory
        player_dir = self.store.get_player_dir(player_id)
        if player_dir.exists():
            import shutil

            shutil.rmtree(player_dir)

    async def list_players(self) -> list[Player]:
        """
        List all players.

        Returns:
            List of players
        """
        players = []
        players_dir = self.store.get_players_dir()
        if not players_dir.exists():
            return players

        for player_dir in players_dir.iterdir():
            if player_dir.is_dir():
                try:
                    player = await self.get_player(player_dir.name)
                    players.append(player)
                except FileNotFoundError:
                    continue

        return players

    async def check_username_unique(
        self, username: str, exclude_player_id: Optional[str] = None
    ) -> bool:
        """
        Check if username is unique.

        Args:
            username: Username to check
            exclude_player_id: Optional player ID to exclude from check (for updates)

        Returns:
            True if username is unique, False otherwise
        """
        existing = await self.get_player_by_username(username)
        if existing is None:
            return True
        if exclude_player_id and existing.metadata.id == exclude_player_id:
            return True
        return False

    async def get_player_campaigns(self, player_id: str) -> list[dict]:
        """
        List player's campaign memberships.

        Args:
            player_id: Player identifier

        Returns:
            List of membership dictionaries with campaign and role info
        """
        from ..models.membership import CampaignMembership
        from ..models.campaign import Campaign

        memberships = []
        if not self.store.campaigns_dir.exists():
            return memberships

        for campaign_dir in self.store.campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                memberships_dir = self.store.get_memberships_dir(campaign_dir.name)
                if memberships_dir.exists():
                    membership_file = memberships_dir / f"{player_id}.yaml"
                    if membership_file.exists():
                        try:
                            membership = self.store.load_artifact(
                                CampaignMembership,
                                campaign_dir.name,
                                f"memberships/{player_id}.yaml",
                            )
                            campaign = self.store.load_artifact(
                                Campaign, campaign_dir.name, "campaign.yaml"
                            )
                            memberships.append(
                                {
                                    "campaign_id": membership.campaign_id,
                                    "campaign_name": campaign.name,
                                    "role": membership.role,
                                    "character_id": membership.character_id,
                                    "joined_at": membership.joined_at,
                                }
                            )
                        except Exception:
                            continue

        return memberships

    async def get_player_active_session(self, player_id: str):
        """
        Find player's current active session across all campaigns.

        Args:
            player_id: Player identifier

        Returns:
            Session instance if found, None otherwise
        """
        from ..models.session import Session

        if not self.store.campaigns_dir.exists():
            return None

        for campaign_dir in self.store.campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                sessions_dir = self.store.get_sessions_dir(campaign_dir.name)
                if sessions_dir.exists():
                    for session_file in sessions_dir.glob("*.yaml"):
                        try:
                            session = self.store.load_artifact(
                                Session,
                                campaign_dir.name,
                                f"sessions/{session_file.name}",
                            )
                            if session.status in ["active", "paused"]:
                                # Check if player is a participant
                                for participant in session.participants:
                                    if (
                                        participant.player_id == player_id
                                        and participant.left_at is None
                                    ):
                                        return session
                        except Exception:
                            continue

        return None
