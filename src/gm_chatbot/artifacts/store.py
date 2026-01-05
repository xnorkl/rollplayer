"""Artifact store for YAML persistence."""

import fcntl
import os
from pathlib import Path
from typing import Optional

from ..models.base import BaseArtifact


class ArtifactStore:
    """Manages YAML artifact persistence with atomic writes and file locking."""

    def __init__(self, campaigns_dir: Path | str | None = None):
        """
        Initialize artifact store.

        Args:
            campaigns_dir: Base directory for campaign artifacts (defaults to CAMPAIGNS_DIR env var or /data/campaigns)
        """
        if campaigns_dir is None:
            campaigns_dir = os.getenv("CAMPAIGNS_DIR", "/data/campaigns")
        self.campaigns_dir = Path(campaigns_dir)
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        # Players directory (top-level, independent of campaigns)
        players_dir = os.getenv("PLAYERS_DIR", "/data/players")
        self.players_dir = Path(players_dir)
        self.players_dir.mkdir(parents=True, exist_ok=True)

    def get_campaign_dir(self, campaign_id: str) -> Path:
        """
        Get directory path for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Path to campaign directory
        """
        return self.campaigns_dir / campaign_id

    def save_artifact(
        self,
        artifact: BaseArtifact,
        campaign_id: str,
        artifact_type: str,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Save an artifact to YAML file with atomic write.

        Args:
            artifact: Artifact to save
            campaign_id: Campaign identifier
            artifact_type: Type of artifact (e.g., "campaign", "character")
            filename: Optional custom filename (defaults to artifact type)

        Returns:
            Path to saved file
        """
        campaign_dir = self.get_campaign_dir(campaign_id)
        campaign_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"{artifact_type}.yaml"

        file_path = campaign_dir / filename

        # Atomic write: write to temp file, then rename
        temp_path = file_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(artifact.to_yaml())
                f.flush()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            temp_path.replace(file_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return file_path

    def load_artifact(
        self,
        artifact_class: type[BaseArtifact],
        campaign_id: str,
        filename: str,
    ) -> BaseArtifact:
        """
        Load an artifact from YAML file.

        Args:
            artifact_class: Class of artifact to load
            campaign_id: Campaign identifier
            filename: Filename of artifact

        Returns:
            Loaded artifact instance

        Raises:
            FileNotFoundError: If artifact file not found
        """
        file_path = self.get_campaign_dir(campaign_id) / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact not found: {file_path}")

        with file_path.open() as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                content = f.read()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return artifact_class.from_yaml(content)

    def list_artifacts(
        self,
        campaign_id: str,
        artifact_type: Optional[str] = None,
    ) -> list[Path]:
        """
        List artifact files in a campaign.

        Args:
            campaign_id: Campaign identifier
            artifact_type: Optional filter by artifact type (filename prefix)

        Returns:
            List of artifact file paths
        """
        campaign_dir = self.get_campaign_dir(campaign_id)
        if not campaign_dir.exists():
            return []

        pattern = f"{artifact_type}*.yaml" if artifact_type else "*.yaml"
        return sorted(campaign_dir.glob(pattern))

    def delete_artifact(
        self,
        campaign_id: str,
        filename: str,
    ) -> None:
        """
        Delete an artifact file.

        Args:
            campaign_id: Campaign identifier
            filename: Filename of artifact to delete
        """
        file_path = self.get_campaign_dir(campaign_id) / filename
        if file_path.exists():
            file_path.unlink()

    def get_players_dir(self) -> Path:
        """
        Get directory path for players.

        Returns:
            Path to players directory
        """
        return self.players_dir

    def get_player_dir(self, player_id: str) -> Path:
        """
        Get directory path for a specific player.

        Args:
            player_id: Player identifier

        Returns:
            Path to player directory
        """
        return self.players_dir / player_id

    def get_memberships_dir(self, campaign_id: str) -> Path:
        """
        Get directory path for campaign memberships.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Path to memberships directory
        """
        return self.get_campaign_dir(campaign_id) / "memberships"

    def get_sessions_dir(self, campaign_id: str) -> Path:
        """
        Get directory path for campaign sessions.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Path to sessions directory
        """
        return self.get_campaign_dir(campaign_id) / "sessions"
