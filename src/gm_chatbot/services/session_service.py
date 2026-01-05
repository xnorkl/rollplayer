"""Session service for session management."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.session import Session, SessionParticipant
from ..models.membership import CampaignMembership


class SessionService:
    """Service for managing game sessions."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """
        Initialize session service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()

    async def create_session(
        self,
        campaign_id: str,
        started_by: str,
        name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Session:
        """
        Create a new session for a campaign.

        Args:
            campaign_id: Campaign identifier
            started_by: Player ID who started the session
            name: Optional session name
            notes: Optional session notes

        Returns:
            Created session

        Raises:
            ValueError: If campaign already has an active or paused session
        """
        # Check for existing active/paused session
        existing = await self.get_active_session(campaign_id)
        if existing is not None:
            raise ValueError(
                f"Campaign {campaign_id} already has an active/paused session: {existing.metadata.id}"
            )

        # Calculate session number
        sessions = await self.list_sessions(campaign_id)
        session_number = 1
        if sessions:
            session_number = max(s.session_number for s in sessions) + 1

        session_id = str(uuid4())
        session = Session(
            campaign_id=campaign_id,
            session_number=session_number,
            name=name,
            status="active",
            started_at=datetime.utcnow(),
            started_by=started_by,
            notes=notes,
            participants=[],
        )
        session.metadata.id = session_id

        # Save session
        filename = f"session_{session_number:03d}.yaml"
        self.store.save_artifact(
            session, campaign_id, "session", f"sessions/{filename}"
        )

        return session

    async def get_session(self, campaign_id: str, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier

        Returns:
            Session instance

        Raises:
            FileNotFoundError: If session not found
        """
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        if not sessions_dir.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        for session_file in sessions_dir.glob("*.yaml"):
            try:
                session = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if session.metadata.id == session_id:
                    return session
            except Exception:
                continue

        raise FileNotFoundError(f"Session {session_id} not found")

    async def update_session(self, campaign_id: str, session: Session) -> Session:
        """
        Update a session.

        Args:
            campaign_id: Campaign identifier
            session: Updated session instance

        Returns:
            Updated session

        Raises:
            ValueError: If session is ended (immutable)
        """
        if session.status == "ended":
            raise ValueError("Cannot modify an ended session")

        # Update timestamp
        session.metadata.updated_at = datetime.utcnow()

        # Find existing file to preserve filename
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        for session_file in sessions_dir.glob("*.yaml"):
            try:
                existing = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if existing.metadata.id == session.metadata.id:
                    self.store.save_artifact(
                        session, campaign_id, "session", f"sessions/{session_file.name}"
                    )
                    return session
            except Exception:
                continue

        raise FileNotFoundError(f"Session {session.metadata.id} not found")

    async def end_session(self, campaign_id: str, session_id: str) -> Session:
        """
        End a session.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier

        Returns:
            Ended session
        """
        session = await self.get_session(campaign_id, session_id)

        if session.status == "ended":
            return session

        # Mark all active participants as left
        for participant in session.participants:
            if participant.left_at is None:
                participant.left_at = datetime.utcnow()

        session.status = "ended"
        session.ended_at = datetime.utcnow()
        session.metadata.updated_at = datetime.utcnow()

        # Save
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        for session_file in sessions_dir.glob("*.yaml"):
            try:
                existing = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if existing.metadata.id == session_id:
                    self.store.save_artifact(
                        session, campaign_id, "session", f"sessions/{session_file.name}"
                    )
                    return session
            except Exception:
                continue

        raise FileNotFoundError(f"Session {session_id} not found")

    async def delete_session(self, campaign_id: str, session_id: str) -> None:
        """
        Delete an ended session.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier

        Raises:
            ValueError: If session is not ended
        """
        session = await self.get_session(campaign_id, session_id)

        if session.status != "ended":
            raise ValueError(f"Cannot delete active/paused session {session_id}")

        # Find and delete session file
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        for session_file in sessions_dir.glob("*.yaml"):
            try:
                existing = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if existing.metadata.id == session_id:
                    session_file.unlink()
                    return
            except Exception:
                continue

        raise FileNotFoundError(f"Session {session_id} not found")

    async def list_sessions(
        self, campaign_id: str, status: Optional[str] = None
    ) -> list[Session]:
        """
        List sessions for a campaign.

        Args:
            campaign_id: Campaign identifier
            status: Optional status filter

        Returns:
            List of sessions
        """
        sessions = []
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        if not sessions_dir.exists():
            return sessions

        for session_file in sessions_dir.glob("*.yaml"):
            try:
                session = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if status is None or session.status == status:
                    sessions.append(session)
            except Exception:
                continue

        return sorted(sessions, key=lambda s: s.session_number)

    async def get_active_session(self, campaign_id: str) -> Optional[Session]:
        """
        Get current active or paused session for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Active/paused session or None
        """
        sessions = await self.list_sessions(campaign_id)
        for session in sessions:
            if session.status in ["active", "paused"]:
                return session
        return None

    async def join_session(
        self,
        campaign_id: str,
        session_id: str,
        player_id: str,
        character_id: Optional[str] = None,
        is_gm: bool = False,
    ) -> Session:
        """
        Add a participant to a session.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier
            player_id: Player identifier
            character_id: Optional character ID (required for non-GM players)
            is_gm: Whether participant is GM

        Returns:
            Updated session

        Raises:
            ValueError: If constraints are violated
        """
        # Validate session is active
        session = await self.get_session(campaign_id, session_id)
        if session.status != "active":
            raise ValueError(f"Cannot join session {session_id}: session is not active")

        # Check if player is already in another active session
        from ..services.player_service import PlayerService

        player_service = PlayerService(self.store)
        active_session = await player_service.get_player_active_session(player_id)
        if active_session is not None and active_session.metadata.id != session_id:
            raise ValueError(
                f"Player {player_id} is already in active session {active_session.metadata.id}"
            )

        # Check campaign membership
        membership = await self._get_membership(campaign_id, player_id)
        if membership is None:
            raise ValueError(
                f"Player {player_id} is not a member of campaign {campaign_id}"
            )

        # Validate character ownership (if character specified)
        if character_id and not is_gm:
            if membership.character_id != character_id:
                # Check if character is assigned to player
                raise ValueError(
                    f"Character {character_id} is not assigned to player {player_id}"
                )

        # Use default character if not specified and not GM
        if not character_id and not is_gm:
            character_id = membership.character_id
            if not character_id:
                raise ValueError(
                    f"Player {player_id} has no default character assigned"
                )

        # Check if already a participant
        for participant in session.participants:
            if participant.player_id == player_id and participant.left_at is None:
                return session  # Already participating

        # Add participant
        participant = SessionParticipant(
            player_id=player_id,
            character_id=character_id,
            joined_at=datetime.utcnow(),
            is_gm=is_gm,
        )
        session.participants.append(participant)
        session.metadata.updated_at = datetime.utcnow()

        # Save
        sessions_dir = self.store.get_sessions_dir(campaign_id)
        for session_file in sessions_dir.glob("*.yaml"):
            try:
                existing = self.store.load_artifact(
                    Session, campaign_id, f"sessions/{session_file.name}"
                )
                if existing.metadata.id == session_id:
                    self.store.save_artifact(
                        session, campaign_id, "session", f"sessions/{session_file.name}"
                    )
                    return session
            except Exception:
                continue

        raise FileNotFoundError(f"Session {session_id} not found")

    async def leave_session(
        self, campaign_id: str, session_id: str, player_id: str
    ) -> Session:
        """
        Remove a participant from a session.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier
            player_id: Player identifier

        Returns:
            Updated session
        """
        session = await self.get_session(campaign_id, session_id)

        # Find and mark participant as left
        for participant in session.participants:
            if participant.player_id == player_id and participant.left_at is None:
                participant.left_at = datetime.utcnow()
                session.metadata.updated_at = datetime.utcnow()

                # Save
                sessions_dir = self.store.get_sessions_dir(campaign_id)
                for session_file in sessions_dir.glob("*.yaml"):
                    try:
                        existing = self.store.load_artifact(
                            Session, campaign_id, f"sessions/{session_file.name}"
                        )
                        if existing.metadata.id == session_id:
                            self.store.save_artifact(
                                session,
                                campaign_id,
                                "session",
                                f"sessions/{session_file.name}",
                            )
                            return session
                    except Exception:
                        continue

        raise ValueError(
            f"Player {player_id} is not an active participant in session {session_id}"
        )

    async def get_participants(
        self, campaign_id: str, session_id: str
    ) -> list[SessionParticipant]:
        """
        List session participants.

        Args:
            campaign_id: Campaign identifier
            session_id: Session identifier

        Returns:
            List of participants
        """
        session = await self.get_session(campaign_id, session_id)
        return [p for p in session.participants if p.left_at is None]

    async def _get_membership(
        self, campaign_id: str, player_id: str
    ) -> Optional[CampaignMembership]:
        """Get campaign membership for a player."""
        memberships_dir = self.store.get_memberships_dir(campaign_id)
        membership_file = memberships_dir / f"{player_id}.yaml"
        if membership_file.exists():
            try:
                return self.store.load_artifact(
                    CampaignMembership, campaign_id, f"memberships/{player_id}.yaml"
                )
            except Exception:
                return None
        return None
