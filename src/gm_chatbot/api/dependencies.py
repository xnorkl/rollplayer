"""Dependency injection for FastAPI."""

import os

from ..artifacts.store import ArtifactStore
from ..services.campaign_service import CampaignService
from ..services.character_service import CharacterService
from ..services.discord_binding_service import DiscordBindingService
from ..services.discord_context_service import DiscordContextService
from ..services.discord_linking_service import DiscordLinkingService
from ..services.game_state_service import GameStateService
from ..services.player_service import PlayerService
from ..services.session_service import SessionService
from ..tools.registry import DiceToolRegistry


# Global instances (singleton pattern)
_store: ArtifactStore | None = None
_campaign_service: CampaignService | None = None
_character_service: CharacterService | None = None
_game_state_service: GameStateService | None = None
_player_service: PlayerService | None = None
_session_service: SessionService | None = None
_dice_tool_registry: DiceToolRegistry | None = None
_discord_linking_service: DiscordLinkingService | None = None
_discord_binding_service: DiscordBindingService | None = None
_discord_context_service: DiscordContextService | None = None


def get_artifact_store() -> ArtifactStore:
    """Get artifact store instance."""
    global _store
    if _store is None:
        campaigns_dir = os.getenv("CAMPAIGNS_DIR", "/data/campaigns")
        _store = ArtifactStore(campaigns_dir=campaigns_dir)
    return _store


def get_campaign_service() -> CampaignService:
    """Get campaign service instance."""
    global _campaign_service
    if _campaign_service is None:
        _campaign_service = CampaignService(get_artifact_store())
    return _campaign_service


def get_character_service() -> CharacterService:
    """Get character service instance."""
    global _character_service
    if _character_service is None:
        _character_service = CharacterService(get_artifact_store())
    return _character_service


def get_game_state_service() -> GameStateService:
    """Get game state service instance."""
    global _game_state_service
    if _game_state_service is None:
        _game_state_service = GameStateService(
            get_artifact_store(),
            get_character_service(),
        )
    return _game_state_service


def get_dice_tool_registry() -> DiceToolRegistry:
    """Get dice tool registry instance."""
    global _dice_tool_registry
    if _dice_tool_registry is None:
        _dice_tool_registry = DiceToolRegistry()
    return _dice_tool_registry


def get_player_service() -> PlayerService:
    """Get player service instance."""
    global _player_service
    if _player_service is None:
        _player_service = PlayerService(get_artifact_store())
    return _player_service


def get_session_service() -> SessionService:
    """Get session service instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(get_artifact_store())
    return _session_service


def get_discord_linking_service() -> DiscordLinkingService:
    """Get Discord linking service instance."""
    global _discord_linking_service
    if _discord_linking_service is None:
        _discord_linking_service = DiscordLinkingService(get_artifact_store())
    return _discord_linking_service


def get_discord_binding_service() -> DiscordBindingService:
    """Get Discord binding service instance."""
    global _discord_binding_service
    if _discord_binding_service is None:
        _discord_binding_service = DiscordBindingService(get_artifact_store())
    return _discord_binding_service


def get_discord_context_service() -> DiscordContextService:
    """Get Discord context service instance."""
    global _discord_context_service
    if _discord_context_service is None:
        _discord_context_service = DiscordContextService(get_artifact_store())
    return _discord_context_service


def reset_dependencies():
    """Reset all global dependencies (for testing only)."""
    global _store, _campaign_service, _character_service, _game_state_service
    global _player_service, _session_service, _dice_tool_registry
    global _discord_linking_service, _discord_binding_service, _discord_context_service
    _store = None
    _campaign_service = None
    _character_service = None
    _game_state_service = None
    _player_service = None
    _session_service = None
    _dice_tool_registry = None
    _discord_linking_service = None
    _discord_binding_service = None
    _discord_context_service = None