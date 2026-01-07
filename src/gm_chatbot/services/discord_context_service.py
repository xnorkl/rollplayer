"""Discord context service for resolving Discord context to game entities."""

from ..artifacts.store import ArtifactStore
from ..models.campaign import Campaign
from ..models.character import CharacterSheet
from ..models.membership import CampaignMembership
from ..models.session import Session
from ..services.campaign_service import CampaignService
from ..services.character_service import CharacterService
from ..services.discord_binding_service import DiscordBindingService
from ..services.discord_linking_service import DiscordLinkingService
from ..services.session_service import SessionService


class DiscordContext:
    """Resolved Discord context."""

    def __init__(
        self,
        campaign: Campaign | None = None,
        session: Session | None = None,
        character: CharacterSheet | None = None,
        membership: CampaignMembership | None = None,
        player_id: str | None = None,
    ):
        """
        Initialize Discord context.

        Args:
            campaign: Resolved campaign
            session: Resolved session
            character: Resolved character
            membership: Resolved membership
            player_id: Resolved player ID
        """
        self.campaign = campaign
        self.session = session
        self.character = character
        self.membership = membership
        self.player_id = player_id


class DiscordContextService:
    """Service for resolving Discord context to game entities."""

    def __init__(self, store: ArtifactStore | None = None):
        """
        Initialize Discord context service.

        Args:
            store: Optional artifact store (creates default if not provided)
        """
        self.store = store or ArtifactStore()
        self.binding_service = DiscordBindingService(self.store)
        self.linking_service = DiscordLinkingService(self.store)
        self.campaign_service = CampaignService(self.store)
        self.session_service = SessionService(self.store)
        self.character_service = CharacterService(self.store)

    async def resolve_context(
        self,
        guild_id: str,
        channel_id: str,
        user_id: str,
    ) -> DiscordContext:
        """
        Resolve Discord context (guild, channel, user) to campaign, session, character.

        Args:
            guild_id: Discord guild ID (snowflake)
            channel_id: Discord channel ID (snowflake)
            user_id: Discord user ID (snowflake)

        Returns:
            DiscordContext with resolved entities
        """
        context = DiscordContext()

        # Resolve player from Discord user ID
        player = await self.linking_service.get_player_by_discord_id(user_id)
        if player:
            context.player_id = player.metadata.id

        # Resolve campaign from channel binding
        campaign_id = await self.binding_service.get_campaign_by_channel(channel_id)
        if campaign_id:
            try:
                context.campaign = await self.campaign_service.get_campaign(campaign_id)
            except FileNotFoundError:
                pass

        # Resolve session if campaign found
        if context.campaign:
            # Get active session for campaign
            context.session = await self.session_service.get_active_session(
                context.campaign.metadata.id
            )

            # Resolve membership and character if player found
            if context.player_id:
                try:
                    context.membership = await self.campaign_service.get_membership(
                        context.campaign.metadata.id, context.player_id
                    )

                    # Resolve character if membership has character_id
                    if context.membership and context.membership.character_id and context.campaign:
                        try:
                            context.character = await self.character_service.get_character(
                                context.campaign.metadata.id,
                                context.membership.character_id,
                            )
                        except FileNotFoundError:
                            pass
                except Exception:
                    pass

        return context

    async def get_active_session_for_channel(self, channel_id: str) -> Session | None:
        """
        Get active session for a Discord channel.

        Args:
            channel_id: Discord channel ID (snowflake)

        Returns:
            Active Session or None if not found
        """
        campaign_id = await self.binding_service.get_campaign_by_channel(channel_id)
        if not campaign_id:
            return None

        return await self.session_service.get_active_session(campaign_id)

    async def validate_permission(
        self,
        user_id: str,
        campaign_id: str,
        required_role: str = "player",
    ) -> bool:
        """
        Validate user has required permission in campaign.

        Args:
            user_id: Discord user ID (snowflake)
            campaign_id: Campaign identifier
            required_role: Required role ("spectator", "player", "gm", "admin")

        Returns:
            True if user has required permission, False otherwise
        """
        # Resolve player from Discord user ID
        player = await self.linking_service.get_player_by_discord_id(user_id)
        if not player:
            return False

        # Get membership
        try:
            membership = await self.campaign_service.get_membership(campaign_id, player.metadata.id)
            if not membership:
                return False

            # Check role hierarchy
            role_hierarchy = {
                "spectator": 0,
                "player": 1,
                "gm": 2,
                "admin": 3,
            }

            user_role_level = role_hierarchy.get(membership.role, 0)
            required_role_level = role_hierarchy.get(required_role, 0)

            return user_role_level >= required_role_level
        except Exception:
            return False
