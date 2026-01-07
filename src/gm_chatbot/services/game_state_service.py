"""Game state service for sequential action processing."""

from typing import TYPE_CHECKING

from ..artifacts.store import ArtifactStore
from ..artifacts.validator import ArtifactValidator
from ..models.action import GameAction, StateChange
from ..services.character_service import CharacterService

if TYPE_CHECKING:
    from ..models.character import CharacterSheet


class GameState:
    """Represents current game state."""

    def __init__(self, campaign_id: str):
        """
        Initialize game state.

        Args:
            campaign_id: Campaign identifier
        """
        self.campaign_id = campaign_id
        self.in_combat: bool = False
        self.initiative_order: list[str] = []
        self.current_turn: int = 0
        self.characters: dict[str, CharacterSheet] = {}


class GameStateManager:
    """Manages game state transitions."""

    def __init__(self, store: ArtifactStore | None = None):
        """
        Initialize game state manager.

        Args:
            store: Optional artifact store
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()
        self._states: dict[str, GameState] = {}

    def get_state(self, campaign_id: str) -> GameState:
        """
        Get or create game state for campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Game state instance
        """
        if campaign_id not in self._states:
            self._states[campaign_id] = GameState(campaign_id)
        return self._states[campaign_id]

    async def apply_state_change(self, state_change: StateChange, campaign_id: str) -> None:
        """
        Apply a state change to game state.

        Args:
            state_change: State change to apply
            campaign_id: Campaign identifier
        """
        state = self.get_state(campaign_id)

        # Handle character updates
        if state_change.target in state.characters:
            char = state.characters[state_change.target]
            # Update field using dot notation path
            parts = state_change.field.split(".")
            obj = char
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], state_change.new_value)


class GameStateService:
    """Service for processing game actions and managing state."""

    def __init__(
        self,
        store: ArtifactStore | None = None,
        character_service: CharacterService | None = None,
    ):
        """
        Initialize game state service.

        Args:
            store: Optional artifact store
            character_service: Optional character service
        """
        self.store = store or ArtifactStore()
        self.validator = ArtifactValidator()
        self.character_service = character_service or CharacterService(store)
        self.manager = GameStateManager(store)
        self._action_history: dict[str, list[GameAction]] = {}

    async def apply_action(
        self,
        campaign_id: str,
        action: GameAction,
    ) -> GameAction:
        """
        Apply an action to game state.

        Args:
            campaign_id: Campaign identifier
            action: Action to apply

        Returns:
            Action with outcome populated
        """
        # Validate action
        self.validator.validate_action(action.model_dump())

        # Apply state changes
        for change in action.outcome.state_changes:
            await self.manager.apply_state_change(change, campaign_id)

        # Save to history
        if campaign_id not in self._action_history:
            self._action_history[campaign_id] = []
        self._action_history[campaign_id].append(action)

        # Persist action to YAML
        await self._persist_action(campaign_id, action)

        return action

    async def get_current_state(self, campaign_id: str) -> GameState:
        """
        Get current game state.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Current game state
        """
        return self.manager.get_state(campaign_id)

    async def get_action_history(
        self,
        campaign_id: str,
        limit: int | None = None,
    ) -> list[GameAction]:
        """
        Get action history for campaign.

        Args:
            campaign_id: Campaign identifier
            limit: Optional limit on number of actions

        Returns:
            List of actions
        """
        history = self._action_history.get(campaign_id, [])
        if limit:
            return history[-limit:]
        return history

    async def rollback_action(
        self,
        campaign_id: str,
        action_id: str,
    ) -> GameState:
        """
        Rollback to state before specified action.

        Args:
            campaign_id: Campaign identifier
            action_id: Action ID to rollback to

        Returns:
            Game state after rollback
        """
        history = self._action_history.get(campaign_id, [])
        # Find action index
        action_index = None
        for i, action in enumerate(history):
            if action.action_id == action_id:
                action_index = i
                break

        if action_index is None:
            raise ValueError(f"Action {action_id} not found in history")

        # Remove actions after this one
        self._action_history[campaign_id] = history[: action_index + 1]

        # Rebuild state from remaining actions
        state = GameState(campaign_id)
        for action in self._action_history[campaign_id]:
            for change in action.outcome.state_changes:
                await self.manager.apply_state_change(change, campaign_id)

        self.manager._states[campaign_id] = state
        return state

    async def _persist_action(self, campaign_id: str, action: GameAction) -> None:
        """Persist action to YAML file."""
        state_dir = self.store.get_campaign_dir(campaign_id) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Append to history.yaml
        history_file = state_dir / "history.yaml"
        import yaml

        history_data = {"actions": []}
        if history_file.exists():
            with history_file.open() as f:
                existing = yaml.safe_load(f)
                if existing and "actions" in existing:
                    history_data["actions"] = existing["actions"]

        history_data["actions"].append(action.model_dump(mode="json"))

        with history_file.open("w") as f:
            yaml.safe_dump(history_data, f, default_flow_style=False, allow_unicode=True)
