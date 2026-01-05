"""Dependency injection for FastAPI."""

import os

from ..artifacts.store import ArtifactStore
from ..services.campaign_service import CampaignService
from ..services.character_service import CharacterService
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
