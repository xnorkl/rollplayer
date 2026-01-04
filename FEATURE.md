# Feature Requirements Document: GM Chatbot Architecture Redesign

**Document Version:** 1.1 (DRAFT)  
**Date:** January 4, 2026  
**Status:** Draft for Review  
**Author:** Architecture Team

**Revision History:**
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-04 | Initial draft |
| 1.1 | 2026-01-04 | Added Scalar API Reference integration (§7.1); Added terminology clarifications for session/campaign/game state (§1.0, Appendix C) |

---

## Executive Summary

This document specifies the requirements for a comprehensive architectural redesign of the Roll20 GM Chatbot system. The redesign transitions from a tightly-coupled, single-game architecture to a modular, multi-campaign platform with loosely-coupled game rules, type-safe artifact management, and a REST API-first design.

The key objectives are:

1. Decouple game rules from the core engine via YAML configuration
2. Enable multi-campaign tracking with validated YAML artifacts
3. Enforce type safety across all data models
4. Externalize dice rolling and calculations to dedicated tools
5. Provide a REST API that conforms to OpenAPI 3.1
6. Abstract platform integrations (Roll20, Discord, CLI, etc.)
7. Modernize the Python toolchain (UV, Ruff, ty)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Architecture Requirements](#5-architecture-requirements)
6. [Data Model Requirements](#6-data-model-requirements)
7. [API Requirements](#7-api-requirements)
8. [Tooling and Infrastructure Requirements](#8-tooling-and-infrastructure-requirements)
9. [Migration Strategy](#9-migration-strategy)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Appendices](#11-appendices)

---

## 1. Current State Analysis

### 1.0 Terminology

Before proceeding, this section establishes key terminology used throughout this document to describe game state and system concepts:

**Campaign vs. Session**: A _campaign_ is the persistent collection of game artifacts (rules, characters, modules, history) that defines a game world. A _session_ is a runtime instance of a campaign representing a single play period. When players gather to play, the system loads the campaign state into a session. Actions taken during the session modify game state, and those changes persist back to the campaign when the session ends.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CAMPAIGN                                │
│  (Persistent: rules, characters, modules, accumulated history)  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              ┌─────▼─────┐               ┌─────▼─────┐
              │ Session 1 │               │ Session 2 │   ...
              │ (Jan 4)   │               │ (Jan 11)  │
              └─────┬─────┘               └─────┬─────┘
                    │                           │
                    ▼                           ▼
              Actions processed           Actions processed
              State persisted             State persisted
              to Campaign                 to Campaign
```

**Module**: A prepared adventure or encounter content. Campaigns contain many modules, but only one module can be _active_ during a session.

**Game State**: The complete current condition of a session, including all character statuses (HP, conditions), combat state (initiative, turn order), and environmental factors. Game state is modified by sequential _actions_ from players and the GM.

**Action**: A discrete game event (attack, movement, spell cast, etc.) that transitions game state from one valid state to another. All actions are logged for audit, replay, and rollback capabilities.

See [Appendix C: Glossary](#appendix-c-glossary) for complete terminology definitions.

### 1.1 Existing Architecture Overview

The current system implements a WebSocket bridge architecture connecting Roll20's web interface to a Python backend:

| Component            | Current Implementation                   | Limitations                          |
| -------------------- | ---------------------------------------- | ------------------------------------ |
| Game Rules           | Hardcoded in `shadowdark_rules.py`       | Tightly coupled to Shadowdark RPG    |
| Campaign State       | In-memory, single instance               | No persistence, single campaign only |
| Dice Rolling         | Direct calculation in `DiceRoller` class | Logic embedded in application code   |
| Platform Integration | Roll20-specific via Tampermonkey         | Cannot support other platforms       |
| API                  | WebSocket only                           | No REST API, limited client options  |
| Type Safety          | Minimal                                  | No comprehensive validation          |
| Package Management   | pip + requirements.txt                   | No modern tooling                    |

### 1.2 Key Pain Points

1. **Tight Coupling**: Game rules are embedded in Python code, requiring code changes for any rule modification or new game system support.

2. **Single Campaign**: The architecture assumes one active game session per server instance with no persistence.

3. **Platform Lock-in**: The Roll20 integration via Tampermonkey userscript is the only supported interface.

4. **Embedded Calculations**: Dice rolling and game mechanics are calculated directly rather than through verifiable, auditable tools.

5. **No Validation Layer**: Artifacts and game state lack comprehensive type safety and validation.

6. **WebSocket-Only**: No REST API prevents easy development of alternative clients.

---

## 2. Goals and Non-Goals

### 2.1 Goals

| ID  | Goal                                                                 | Priority |
| --- | -------------------------------------------------------------------- | -------- |
| G1  | Decouple game rules into YAML-based configuration files              | P0       |
| G2  | Support multiple concurrent campaigns with persistent YAML artifacts | P0       |
| G3  | Implement comprehensive type safety with Pydantic models             | P0       |
| G4  | Chatbot receives only validated artifacts                            | P0       |
| G5  | Chatbot generates artifacts that must pass validation before storage | P0       |
| G6  | Externalize all dice rolling and calculations to dedicated tools     | P0       |
| G7  | Implement sequential game state updates via player/GM actions        | P0       |
| G8  | Abstract platform integration to support multiple VTTs               | P1       |
| G9  | Provide REST API conforming to OpenAPI 3.1                           | P0       |
| G10 | Adopt UV, Ruff, and ty for modern Python tooling                     | P0       |
| G11 | Enable rapid CLI client development with Typer                       | P1       |

### 2.2 Non-Goals

| ID  | Non-Goal                                    | Rationale                                     |
| --- | ------------------------------------------- | --------------------------------------------- |
| NG1 | Real-time multiplayer state synchronization | Out of scope; sequential updates sufficient   |
| NG2 | Built-in character sheet rendering/UI       | Clients responsible for presentation          |
| NG3 | Direct database integration                 | YAML artifacts provide sufficient persistence |
| NG4 | Authentication/authorization system         | Defer to future iteration                     |
| NG5 | Automated game balancing or AI-driven NPCs  | Separate feature set                          |

---

## 3. Functional Requirements

### 3.1 Game Rules Engine

#### FR-3.1.1: YAML-Based Rule Definitions

The system SHALL support game rules defined in YAML format with the following structure:

```yaml
# Example: rules/shadowdark/core.yaml
metadata:
  system_name: "Shadowdark RPG"
  version: "1.0"
  author: "The Arcane Library"

abilities:
  - name: "strength"
    abbreviation: "STR"
    description: "Physical power and melee combat"
  - name: "dexterity"
    abbreviation: "DEX"
    description: "Agility, reflexes, and ranged combat"
  # ...

ability_modifiers:
  range_mapping:
    - range: [1, 3]
      modifier: -4
    - range: [4, 5]
      modifier: -3
    # ...

difficulty_classes:
  easy: 9
  normal: 12
  hard: 15
  extreme: 18

dice_expressions:
  ability_check: "1d20 + {ability_modifier}"
  attack_roll: "1d20 + {attack_bonus}"
  damage_roll: "{weapon_damage} + {strength_modifier}"
```

**Acceptance Criteria:**

- [ ] Rules can be loaded from YAML files without code changes
- [ ] Multiple game systems can coexist (e.g., Shadowdark, D&D 5e, Pathfinder)
- [ ] Rules are validated against a schema on load
- [ ] Invalid rules produce clear error messages with line numbers

#### FR-3.1.2: Rule Validation Schema

The system SHALL validate all rule definitions against a JSON Schema or Pydantic model:

```python
class AbilityDefinition(BaseModel):
    name: str = Field(..., min_length=1)
    abbreviation: str = Field(..., pattern=r"^[A-Z]{2,3}$")
    description: str

class RuleSet(BaseModel):
    metadata: RuleMetadata
    abilities: list[AbilityDefinition]
    ability_modifiers: AbilityModifierConfig
    difficulty_classes: dict[str, int]
    dice_expressions: dict[str, str]
```

### 3.2 Campaign Artifact Management

#### FR-3.2.1: Campaign Structure

A campaign SHALL comprise the following artifact types, all stored as validated YAML:

| Artifact Type         | Description                                       | Cardinality                  |
| --------------------- | ------------------------------------------------- | ---------------------------- |
| `gm_rules.yaml`       | GM-specific rules, house rules, campaign settings | 1 per campaign               |
| `player_rules.yaml`   | Player-facing rules subset                        | 1 per campaign               |
| `characters/*.yaml`   | Character sheets (PC and NPC)                     | Many per campaign            |
| `modules/*.yaml`      | Session modules (adventures, encounters)          | Many per campaign (1 active) |
| `campaign_state.yaml` | Current game state, history                       | 1 per campaign               |

#### FR-3.2.2: Campaign Directory Structure

```
campaigns/
└── {campaign_id}/
    ├── campaign.yaml           # Campaign metadata
    ├── gm_rules.yaml           # GM rules and settings
    ├── player_rules.yaml       # Player-visible rules
    ├── characters/
    │   ├── pc_aragorn.yaml     # Player character
    │   ├── pc_legolas.yaml     # Player character
    │   ├── npc_gandalf.yaml    # Non-player character
    │   └── npc_sauron.yaml     # Non-player character
    ├── modules/
    │   ├── session_001.yaml    # Completed session
    │   ├── session_002.yaml    # Current active module
    │   └── session_003.yaml    # Prepared future session
    └── state/
        ├── combat_state.yaml   # Current combat (if any)
        ├── initiative.yaml     # Initiative order
        └── history.yaml        # Action history log
```

#### FR-3.2.3: Character Sheet Model

```yaml
# characters/pc_theron.yaml
metadata:
  id: "pc_theron_001"
  type: "player_character" # or "non_player_character"
  created_at: "2026-01-04T10:00:00Z"
  updated_at: "2026-01-04T14:30:00Z"

identity:
  name: "Theron Blackwood"
  player_name: "Alice" # null for NPCs
  ancestry: "Human"
  class: "Fighter"
  level: 3
  alignment: "Lawful Good"

abilities:
  strength: 16
  dexterity: 14
  constitution: 15
  intelligence: 10
  wisdom: 12
  charisma: 8

combat:
  hit_points:
    current: 24
    maximum: 28
  armor_class: 16
  attack_bonus: 5

inventory:
  - item: "Longsword"
    quantity: 1
    equipped: true
  - item: "Chain Mail"
    quantity: 1
    equipped: true

conditions: []

notes: |
  Theron is seeking revenge for his destroyed village.
```

#### FR-3.2.4: Module (Session) Model

```yaml
# modules/session_002.yaml
metadata:
  id: "session_002"
  title: "The Goblin Warrens"
  status: "active" # draft | active | completed
  session_date: "2026-01-04"

scenes:
  - id: "scene_001"
    name: "Entrance to the Caves"
    description: |
      A dark cave mouth yawns before you...
    encounters:
      - type: "combat"
        enemies:
          - npc_id: "npc_goblin_scout"
            quantity: 3
        difficulty: "normal"

npcs_introduced:
  - "npc_goblin_chief"
  - "npc_captured_merchant"

loot:
  - item: "Gold Pieces"
    quantity: 50
  - item: "Potion of Healing"
    quantity: 2

session_notes: []
```

### 3.3 Artifact Validation

#### FR-3.3.1: Input Validation

The system SHALL validate all artifacts before they are provided to the chatbot:

```python
class ArtifactValidator:
    def validate_character(self, data: dict) -> CharacterSheet:
        """Raises ValidationError if invalid"""

    def validate_module(self, data: dict) -> SessionModule:
        """Raises ValidationError if invalid"""

    def validate_campaign(self, campaign_id: str) -> Campaign:
        """Validates entire campaign structure"""
```

**Acceptance Criteria:**

- [ ] Invalid artifacts are rejected with detailed error messages
- [ ] Partial artifacts can be validated in draft mode
- [ ] Cross-references between artifacts are validated (e.g., character IDs exist)

#### FR-3.3.2: Output Validation

When the chatbot generates or modifies artifacts, the system SHALL:

1. Validate the generated artifact against its schema
2. Reject invalid artifacts with error feedback to the chatbot
3. Only persist artifacts that pass validation
4. Log validation failures for debugging

```python
class ArtifactPersistence:
    async def save_artifact(
        self,
        artifact: BaseArtifact,
        campaign_id: str
    ) -> SaveResult:
        """
        Validates and saves artifact.
        Returns SaveResult with success/failure and any errors.
        """
```

### 3.4 Dice Rolling and Calculations

#### FR-3.4.1: External Dice Tool

The chatbot SHALL NOT perform direct dice calculations. All randomization and mathematical operations SHALL be delegated to external tools.

**Tool Interface:**

```python
class DiceToolInterface(Protocol):
    async def roll(self, expression: str) -> DiceResult:
        """
        Roll dice expression (e.g., '2d6+3', '1d20').
        Returns structured result with breakdown.
        """

    async def evaluate(self, expression: str, context: dict) -> int:
        """
        Evaluate mathematical expression with context variables.
        """
```

**DiceResult Model:**

```python
class DiceResult(BaseModel):
    expression: str           # Original expression
    total: int               # Final result
    rolls: list[int]         # Individual die rolls
    modifier: int            # Applied modifier
    breakdown: str           # Human-readable breakdown
    timestamp: datetime
    seed: Optional[str]      # For reproducibility
```

#### FR-3.4.2: Tool Registration

The system SHALL support multiple dice tool implementations:

| Tool Type     | Implementation        | Use Case              |
| ------------- | --------------------- | --------------------- |
| Local CLI     | `dice-cli` subprocess | Development, offline  |
| REST API      | External dice service | Production, auditable |
| Deterministic | Seeded RNG            | Testing               |

```python
class DiceToolRegistry:
    def register(self, name: str, tool: DiceToolInterface) -> None: ...
    def get_default(self) -> DiceToolInterface: ...
    def get(self, name: str) -> DiceToolInterface: ...
```

#### FR-3.4.3: Chatbot Tool Binding

The chatbot (LLM) SHALL access dice rolling through function calling / tool use:

```python
DICE_TOOL_SCHEMA = {
    "name": "roll_dice",
    "description": "Roll dice using standard notation (e.g., 2d6+3, 1d20)",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Dice expression in standard notation"
            },
            "reason": {
                "type": "string",
                "description": "Why this roll is being made"
            }
        },
        "required": ["expression"]
    }
}
```

### 3.5 Game State Management

#### FR-3.5.1: Sequential State Updates

Game state SHALL be updated sequentially through discrete actions:

```python
class GameAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str           # Character or GM identifier
    actor_type: Literal["player", "gm"]
    action_type: str        # "attack", "move", "cast_spell", etc.
    target_ids: list[str]   # Target character IDs
    parameters: dict        # Action-specific parameters
    dice_results: list[DiceResult]  # Associated rolls
    outcome: ActionOutcome  # Result of the action

class ActionOutcome(BaseModel):
    success: bool
    description: str
    state_changes: list[StateChange]
    narrative: str          # Flavor text for the action
```

#### FR-3.5.2: State Transitions

```python
class GameStateManager:
    async def apply_action(
        self,
        campaign_id: str,
        action: GameAction
    ) -> GameStateTransition:
        """
        Apply action to game state.
        Returns transition with before/after state.
        """

    async def get_current_state(self, campaign_id: str) -> GameState:
        """Get current game state for campaign."""

    async def rollback_action(
        self,
        campaign_id: str,
        action_id: str
    ) -> GameState:
        """Rollback to state before specified action."""
```

#### FR-3.5.3: Action History

All actions SHALL be logged to enable:

- Audit trail of game events
- Rollback/undo capabilities
- Session replay
- Analytics

```yaml
# state/history.yaml
actions:
  - action_id: "act_001"
    timestamp: "2026-01-04T14:30:00Z"
    actor_id: "pc_theron_001"
    actor_type: "player"
    action_type: "attack"
    target_ids: ["npc_goblin_001"]
    parameters:
      weapon: "longsword"
    dice_results:
      - expression: "1d20+5"
        total: 18
        rolls: [13]
        modifier: 5
    outcome:
      success: true
      description: "Hit for 8 damage"
      state_changes:
        - target: "npc_goblin_001"
          field: "combat.hit_points.current"
          old_value: 7
          new_value: 0
```

### 3.6 Platform Integration Abstraction

#### FR-3.6.1: Platform Adapter Interface

The system SHALL define a platform-agnostic adapter interface:

```python
class PlatformAdapter(Protocol):
    """Interface for VTT/chat platform integration."""

    async def connect(self, config: PlatformConfig) -> None:
        """Establish connection to platform."""

    async def disconnect(self) -> None:
        """Gracefully disconnect from platform."""

    async def send_message(self, message: ChatMessage) -> None:
        """Send message to platform chat."""

    async def on_message(
        self,
        callback: Callable[[ChatMessage], Awaitable[None]]
    ) -> None:
        """Register message handler."""

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
```

#### FR-3.6.2: Supported Platforms

| Platform | Adapter                     | Priority     |
| -------- | --------------------------- | ------------ |
| REST API | `RESTAdapter`               | P0 (Primary) |
| Roll20   | `Roll20Adapter` (WebSocket) | P1           |
| Discord  | `DiscordAdapter`            | P2           |
| CLI      | `CLIAdapter`                | P1           |

#### FR-3.6.3: Platform Configuration

```yaml
# config/platforms.yaml
platforms:
  rest_api:
    enabled: true
    host: "0.0.0.0"
    port: 8000

  roll20:
    enabled: true
    websocket_url: "wss://gm-chatbot.fly.dev/ws/roll20"

  discord:
    enabled: false
    bot_token: "${DISCORD_BOT_TOKEN}"
    guild_ids: []

  cli:
    enabled: true
    prompt: "GM> "
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID        | Requirement                    | Target  |
| --------- | ------------------------------ | ------- |
| NFR-4.1.1 | API response time (p95)        | < 200ms |
| NFR-4.1.2 | Artifact validation time       | < 50ms  |
| NFR-4.1.3 | Dice roll execution            | < 10ms  |
| NFR-4.1.4 | LLM response time              | < 5s    |
| NFR-4.1.5 | Concurrent campaigns supported | ≥ 100   |

### 4.2 Reliability

| ID        | Requirement                 | Target                  |
| --------- | --------------------------- | ----------------------- |
| NFR-4.2.1 | API availability            | 99.5%                   |
| NFR-4.2.2 | Data durability (artifacts) | No data loss on restart |
| NFR-4.2.3 | Graceful degradation        | Function without LLM    |

### 4.3 Security

| ID        | Requirement                                        |
| --------- | -------------------------------------------------- |
| NFR-4.3.1 | All API endpoints SHALL validate input             |
| NFR-4.3.2 | YAML parsing SHALL use safe loaders only           |
| NFR-4.3.3 | File paths SHALL be sanitized to prevent traversal |
| NFR-4.3.4 | API keys SHALL not be logged or exposed            |

### 4.4 Maintainability

| ID        | Requirement                           |
| --------- | ------------------------------------- |
| NFR-4.4.1 | Code coverage ≥ 80%                   |
| NFR-4.4.2 | All public APIs documented            |
| NFR-4.4.3 | Type hints on all function signatures |
| NFR-4.4.4 | Linting passes with zero errors       |

---

## 5. Architecture Requirements

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
├─────────────────┬─────────────────┬─────────────────┬──────────────────────┤
│   Typer CLI     │   Roll20 WS     │   Discord Bot   │   Web Client         │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬───────────┘
         │                 │                 │                   │
         └────────────────┬┴─────────────────┴───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REST API Layer (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Campaigns   │  │  Characters  │  │   Actions    │  │    Chat/GM       │ │
│  │   Router     │  │    Router    │  │    Router    │  │     Router       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Campaign    │  │  Character   │  │ Game State   │  │   GM/Chat        │ │
│  │   Service    │  │   Service    │  │   Service    │  │    Service       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌──────────────────┐         ┌────────────────────┐
│  Rules Engine   │         │  Artifact Store  │         │   Tool Registry    │
│                 │         │                  │         │                    │
│ ┌─────────────┐ │         │ ┌──────────────┐ │         │ ┌────────────────┐ │
│ │ Rule Loader │ │         │ │  Validator   │ │         │ │  Dice Tool     │ │
│ └─────────────┘ │         │ └──────────────┘ │         │ └────────────────┘ │
│ ┌─────────────┐ │         │ ┌──────────────┐ │         │ ┌────────────────┐ │
│ │ Rule Cache  │ │         │ │ YAML Store   │ │         │ │  Math Tool     │ │
│ └─────────────┘ │         │ └──────────────┘ │         │ └────────────────┘ │
└─────────────────┘         └──────────────────┘         └────────────────────┘
         │                             │                             │
         └──────────────────┬──────────┴──────────────┬──────────────┘
                            │                         │
                            ▼                         ▼
                  ┌──────────────────┐       ┌──────────────────┐
                  │   File System    │       │   External APIs  │
                  │ (YAML Artifacts) │       │  (LLM, Dice)     │
                  └──────────────────┘       └──────────────────┘
```

### 5.2 Component Responsibilities

| Component          | Responsibility                                 |
| ------------------ | ---------------------------------------------- |
| REST API Layer     | HTTP routing, request validation, OpenAPI spec |
| Campaign Service   | CRUD operations on campaigns                   |
| Character Service  | Character sheet management                     |
| Game State Service | Action processing, state transitions           |
| GM/Chat Service    | LLM integration, message handling              |
| Rules Engine       | Load, cache, and query game rules              |
| Artifact Store     | Validate, persist, retrieve YAML artifacts     |
| Tool Registry      | Manage external tool integrations              |

### 5.3 Directory Structure

```
gm-chatbot/
├── pyproject.toml           # UV project configuration
├── uv.lock                  # Dependency lock file
├── ruff.toml                # Ruff linter configuration
├── src/
│   └── gm_chatbot/
│       ├── __init__.py
│       ├── main.py          # FastAPI application entry point
│       │
│       ├── api/             # REST API layer
│       │   ├── __init__.py
│       │   ├── app.py       # FastAPI app factory
│       │   ├── dependencies.py
│       │   └── routers/
│       │       ├── campaigns.py
│       │       ├── characters.py
│       │       ├── actions.py
│       │       ├── chat.py
│       │       └── health.py
│       │
│       ├── models/          # Pydantic models
│       │   ├── __init__.py
│       │   ├── campaign.py
│       │   ├── character.py
│       │   ├── action.py
│       │   ├── rules.py
│       │   ├── dice.py
│       │   └── chat.py
│       │
│       ├── services/        # Business logic
│       │   ├── __init__.py
│       │   ├── campaign_service.py
│       │   ├── character_service.py
│       │   ├── game_state_service.py
│       │   └── gm_service.py
│       │
│       ├── rules/           # Rules engine
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── loader.py
│       │   └── schemas/
│       │       └── rule_schema.json
│       │
│       ├── artifacts/       # Artifact management
│       │   ├── __init__.py
│       │   ├── store.py
│       │   ├── validator.py
│       │   └── schemas/
│       │
│       ├── tools/           # External tool integrations
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── dice/
│       │   │   ├── __init__.py
│       │   │   ├── interface.py
│       │   │   ├── cli_tool.py
│       │   │   └── api_tool.py
│       │   └── llm/
│       │       ├── __init__.py
│       │       ├── interface.py
│       │       ├── openai_provider.py
│       │       └── anthropic_provider.py
│       │
│       ├── adapters/        # Platform adapters
│       │   ├── __init__.py
│       │   ├── interface.py
│       │   ├── roll20.py
│       │   ├── discord.py
│       │   └── cli.py
│       │
│       └── config/          # Configuration
│           ├── __init__.py
│           └── settings.py
│
├── rules/                   # Game rule definitions
│   ├── shadowdark/
│   │   ├── core.yaml
│   │   ├── classes.yaml
│   │   └── spells.yaml
│   └── dnd5e/
│       └── core.yaml
│
├── campaigns/               # Campaign data (gitignored)
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
│   └── cli.py              # Typer CLI application
│
└── infrastructure/
    ├── Dockerfile
    └── fly.toml
```

---

## 6. Data Model Requirements

### 6.1 Core Models

All models SHALL be defined using Pydantic v2 with strict validation:

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Literal
from uuid import uuid4

class BaseArtifact(BaseModel):
    """Base class for all YAML artifacts."""
    model_config = ConfigDict(
        strict=True,
        validate_assignment=True,
        extra="forbid"
    )

class ArtifactMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, ge=1)
    schema_version: str = Field(default="1.0")
```

### 6.2 Validation Requirements

| Requirement            | Implementation                           |
| ---------------------- | ---------------------------------------- |
| Type checking          | Pydantic strict mode                     |
| Required fields        | Field(...) with no default               |
| Optional fields        | Optional[T] or Field(default=...)        |
| Constraints            | Field validators (ge, le, pattern, etc.) |
| Cross-field validation | model_validator                          |
| Custom types           | Annotated types with validators          |

### 6.3 YAML Serialization

```python
import yaml
from pydantic import BaseModel

class YAMLMixin:
    """Mixin for YAML serialization."""

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            default_flow_style=False,
            allow_unicode=True
        )

    @classmethod
    def from_yaml(cls, content: str) -> "YAMLMixin":
        data = yaml.safe_load(content)
        return cls.model_validate(data)
```

---

## 7. API Requirements

### 7.1 OpenAPI 3.1 Compliance

The API SHALL conform to OpenAPI 3.1.0 specification with Scalar API Reference documentation.

#### 7.1.1 FastAPI Application Configuration

```python
from fastapi import FastAPI

app = FastAPI(
    title="GM Chatbot API",
    version="2.0.0",
    openapi_version="3.1.0",
    description="Game Master Assistant API for tabletop RPGs",
    servers=[
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://gm-chatbot.fly.dev", "description": "Production"}
    ],
    docs_url=None,      # Disable default Swagger UI
    redoc_url=None,     # Disable default ReDoc
)
```

#### 7.1.2 Scalar API Reference Integration

The system SHALL use `scalar-fastapi` for interactive API documentation.

**Installation:**

```bash
uv add scalar-fastapi
```

**Implementation:**

```python
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference, Layout, Theme, SearchHotKey

app = FastAPI(
    title="GM Chatbot API",
    version="2.0.0",
    openapi_version="3.1.0",
    description="Game Master Assistant API for tabletop RPGs",
    servers=[
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://gm-chatbot.fly.dev", "description": "Production"}
    ],
    docs_url=None,
    redoc_url=None,
)


@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    """Serve Scalar API Reference documentation."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="GM Chatbot API",
        layout=Layout.MODERN,
        dark_mode=True,
        hide_dark_mode_toggle=False,
        show_sidebar=True,
        search_hot_key=SearchHotKey.K,
        default_open_all_tags=False,
        hide_download_button=False,
        persist_auth=True,
    )
```

#### 7.1.3 Scalar Configuration Options

| Option                 | Value            | Rationale                                 |
| ---------------------- | ---------------- | ----------------------------------------- |
| `layout`               | `Layout.MODERN`  | Clean, modern documentation UI            |
| `dark_mode`            | `True`           | Developer-friendly default                |
| `show_sidebar`         | `True`           | Easy navigation between endpoints         |
| `search_hot_key`       | `SearchHotKey.K` | Quick search with `Cmd/Ctrl+K`            |
| `persist_auth`         | `True`           | Preserve API keys during testing          |
| `hide_download_button` | `False`          | Allow spec download for client generation |

### 7.2 API Endpoints

#### Campaigns

| Method | Path                                     | Description          |
| ------ | ---------------------------------------- | -------------------- |
| GET    | `/api/v1/campaigns`                      | List all campaigns   |
| POST   | `/api/v1/campaigns`                      | Create new campaign  |
| GET    | `/api/v1/campaigns/{id}`                 | Get campaign details |
| PUT    | `/api/v1/campaigns/{id}`                 | Update campaign      |
| DELETE | `/api/v1/campaigns/{id}`                 | Delete campaign      |
| POST   | `/api/v1/campaigns/{id}/activate-module` | Set active module    |

#### Characters

| Method | Path                                          | Description              |
| ------ | --------------------------------------------- | ------------------------ |
| GET    | `/api/v1/campaigns/{id}/characters`           | List campaign characters |
| POST   | `/api/v1/campaigns/{id}/characters`           | Create character         |
| GET    | `/api/v1/campaigns/{id}/characters/{char_id}` | Get character            |
| PUT    | `/api/v1/campaigns/{id}/characters/{char_id}` | Update character         |
| DELETE | `/api/v1/campaigns/{id}/characters/{char_id}` | Delete character         |

#### Actions

| Method | Path                                          | Description            |
| ------ | --------------------------------------------- | ---------------------- |
| GET    | `/api/v1/campaigns/{id}/actions`              | List action history    |
| POST   | `/api/v1/campaigns/{id}/actions`              | Submit new action      |
| GET    | `/api/v1/campaigns/{id}/state`                | Get current game state |
| POST   | `/api/v1/campaigns/{id}/rollback/{action_id}` | Rollback to action     |

#### Chat / GM

| Method    | Path                                  | Description               |
| --------- | ------------------------------------- | ------------------------- |
| POST      | `/api/v1/campaigns/{id}/chat`         | Send message to GM        |
| GET       | `/api/v1/campaigns/{id}/chat/history` | Get chat history          |
| WebSocket | `/ws/campaigns/{id}/chat`             | Real-time chat connection |

#### Tools

| Method | Path                          | Description          |
| ------ | ----------------------------- | -------------------- |
| POST   | `/api/v1/tools/dice/roll`     | Roll dice expression |
| POST   | `/api/v1/tools/dice/evaluate` | Evaluate expression  |
| GET    | `/api/v1/rules/{system}`      | Get rule definitions |

#### Health

| Method | Path      | Description     |
| ------ | --------- | --------------- |
| GET    | `/health` | Health check    |
| GET    | `/ready`  | Readiness check |

### 7.3 Request/Response Models

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta | None = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None

class ResponseMeta(BaseModel):
    request_id: str
    timestamp: datetime
    processing_time_ms: float

# Example endpoint
@router.post("/campaigns", response_model=APIResponse[Campaign])
async def create_campaign(
    request: CreateCampaignRequest,
    service: CampaignService = Depends(get_campaign_service)
) -> APIResponse[Campaign]:
    campaign = await service.create(request)
    return APIResponse(success=True, data=campaign)
```

### 7.4 Error Handling

```python
from fastapi import HTTPException, status

class APIError(HTTPException):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details
            }
        )

# Standard error codes
class ErrorCodes:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    CAMPAIGN_NOT_FOUND = "CAMPAIGN_NOT_FOUND"
    CHARACTER_NOT_FOUND = "CHARACTER_NOT_FOUND"
    DICE_EXPRESSION_INVALID = "DICE_EXPRESSION_INVALID"
    LLM_ERROR = "LLM_ERROR"
```

---

## 8. Tooling and Infrastructure Requirements

### 8.1 Python Toolchain

#### 8.1.1 UV Package Manager

```toml
# pyproject.toml
[project]
name = "gm-chatbot"
version = "2.0.0"
description = "Game Master Assistant for tabletop RPGs"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pyyaml>=6.0",
    "openai>=1.50.0",
    "anthropic>=0.40.0",
    "httpx>=0.27.0",
    "typer>=0.13.0",
    "structlog>=24.0.0",
    "scalar-fastapi>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.8.0",
    "ty>=0.2.0",
    "pre-commit>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
]
```

#### 8.1.2 Ruff Configuration

```toml
# ruff.toml
target-version = "py312"
line-length = 100

[lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "RUF",    # Ruff-specific rules
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[lint.isort]
known-first-party = ["gm_chatbot"]

[format]
quote-style = "double"
indent-style = "space"
```

#### 8.1.3 Type Checking with ty

```toml
# pyproject.toml (continued)
[tool.ty]
python-version = "3.12"
strict = true
warn-unreachable = true
```

### 8.2 Development Workflow

```bash
# Setup
uv sync                          # Install dependencies
uv sync --dev                    # Install with dev dependencies

# Running
uv run python -m gm_chatbot      # Run application
uv run uvicorn gm_chatbot.api.app:app --reload  # Development server

# Quality checks
uv run ruff check src/           # Lint
uv run ruff format src/          # Format
uv run ty check src/             # Type check

# Testing
uv run pytest                    # Run tests
uv run pytest --cov=gm_chatbot   # With coverage

# CLI
uv run python scripts/cli.py --help  # Typer CLI
```

### 8.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --dev

      - name: Lint
        run: uv run ruff check src/

      - name: Format check
        run: uv run ruff format --check src/

      - name: Type check
        run: uv run ty check src/

      - name: Test
        run: uv run pytest --cov=gm_chatbot --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### 8.4 Docker Configuration

```dockerfile
# infrastructure/Dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ src/
COPY rules/ rules/

# Create campaigns directory
RUN mkdir -p campaigns

ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "gm_chatbot.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. Migration Strategy

### 9.1 Phase 1: Foundation (Weeks 1-2)

| Task | Description                   | Deliverable                           |
| ---- | ----------------------------- | ------------------------------------- |
| M1.1 | Set up UV project structure   | `pyproject.toml`, directory structure |
| M1.2 | Configure Ruff and ty         | `ruff.toml`, type checking config     |
| M1.3 | Define core Pydantic models   | `src/gm_chatbot/models/`              |
| M1.4 | Implement artifact validation | `src/gm_chatbot/artifacts/`           |
| M1.5 | Create rule loader            | `src/gm_chatbot/rules/`               |

### 9.2 Phase 2: Core Services (Weeks 3-4)

| Task | Description                  | Deliverable                  |
| ---- | ---------------------------- | ---------------------------- |
| M2.1 | Implement Campaign Service   | Campaign CRUD operations     |
| M2.2 | Implement Character Service  | Character management         |
| M2.3 | Implement Game State Service | Action processing            |
| M2.4 | Create Dice Tool interface   | `src/gm_chatbot/tools/dice/` |
| M2.5 | Implement CLI dice tool      | Subprocess wrapper           |

### 9.3 Phase 3: API Layer (Weeks 5-6)

| Task | Description                | Deliverable                 |
| ---- | -------------------------- | --------------------------- |
| M3.1 | Create FastAPI application | `src/gm_chatbot/api/app.py` |
| M3.2 | Implement REST endpoints   | All routers                 |
| M3.3 | Add WebSocket support      | Real-time chat              |
| M3.4 | Generate OpenAPI spec      | Validated 3.1 spec          |
| M3.5 | Create Typer CLI client    | `scripts/cli.py`            |

### 9.4 Phase 4: Integration (Weeks 7-8)

| Task | Description                      | Deliverable               |
| ---- | -------------------------------- | ------------------------- |
| M4.1 | Integrate LLM providers          | OpenAI/Anthropic handlers |
| M4.2 | Connect GM service to tools      | Tool binding for chatbot  |
| M4.3 | Implement Roll20 adapter         | WebSocket bridge          |
| M4.4 | Convert Shadowdark rules to YAML | `rules/shadowdark/`       |
| M4.5 | End-to-end testing               | Integration test suite    |

### 9.5 Phase 5: Deployment (Week 9)

| Task | Description                 | Deliverable      |
| ---- | --------------------------- | ---------------- |
| M5.1 | Update Docker configuration | New Dockerfile   |
| M5.2 | Update Fly.io configuration | `fly.toml`       |
| M5.3 | CI/CD pipeline              | GitHub Actions   |
| M5.4 | Documentation               | API docs, README |
| M5.5 | Production deployment       | Live system      |

---

## 10. Acceptance Criteria

### 10.1 Functional Acceptance

| ID    | Criterion                                      | Verification Method               |
| ----- | ---------------------------------------------- | --------------------------------- |
| AC-F1 | Game rules load from YAML without code changes | Load 2+ different rule systems    |
| AC-F2 | Multiple campaigns can be created and tracked  | Create 3 concurrent campaigns     |
| AC-F3 | All artifacts pass Pydantic validation         | 100% validation coverage          |
| AC-F4 | Chatbot receives only validated artifacts      | Invalid artifact rejection test   |
| AC-F5 | Chatbot-generated artifacts are validated      | Generation validation test        |
| AC-F6 | Dice rolls use external tool only              | No direct random calls in chatbot |
| AC-F7 | Game state updates are sequential              | Concurrent action ordering test   |
| AC-F8 | REST API conforms to OpenAPI 3.1               | Spectral linting passes           |
| AC-F9 | Typer CLI can perform all operations           | CLI test suite passes             |

### 10.2 Non-Functional Acceptance

| ID     | Criterion                             | Verification Method       |
| ------ | ------------------------------------- | ------------------------- |
| AC-NF1 | API p95 latency < 200ms               | Load testing with k6      |
| AC-NF2 | Type checking passes with zero errors | `ty check` in CI          |
| AC-NF3 | Linting passes with zero errors       | `ruff check` in CI        |
| AC-NF4 | Test coverage ≥ 80%                   | pytest-cov report         |
| AC-NF5 | All public APIs documented            | OpenAPI spec completeness |

### 10.3 Definition of Done

A feature is considered complete when:

1. [ ] Code is implemented and passes all tests
2. [ ] Type hints present on all function signatures
3. [ ] Ruff linting passes with zero errors
4. [ ] ty type checking passes with zero errors
5. [ ] Unit tests written with ≥ 80% coverage
6. [ ] Integration tests pass
7. [ ] API endpoints documented in OpenAPI spec
8. [ ] Code reviewed and approved
9. [ ] Documentation updated

---

## 11. Appendices

### Appendix A: Example Rule Definitions

```yaml
# rules/shadowdark/core.yaml
metadata:
  system_name: "Shadowdark RPG"
  version: "1.0.0"
  license: "Used with permission"

abilities:
  - name: "strength"
    abbreviation: "STR"
    description: "Physical power, melee attacks, carrying capacity"
  - name: "dexterity"
    abbreviation: "DEX"
    description: "Agility, ranged attacks, armor class bonus"
  - name: "constitution"
    abbreviation: "CON"
    description: "Health, stamina, hit points"
  - name: "intelligence"
    abbreviation: "INT"
    description: "Learning, memory, wizard spellcasting"
  - name: "wisdom"
    abbreviation: "WIS"
    description: "Perception, insight, priest spellcasting"
  - name: "charisma"
    abbreviation: "CHA"
    description: "Leadership, persuasion, social interaction"

ability_modifiers:
  description: "Modifier based on ability score"
  mapping:
    - scores: [1, 2, 3]
      modifier: -4
    - scores: [4, 5]
      modifier: -3
    - scores: [6, 7]
      modifier: -2
    - scores: [8, 9]
      modifier: -1
    - scores: [10, 11]
      modifier: 0
    - scores: [12, 13]
      modifier: 1
    - scores: [14, 15]
      modifier: 2
    - scores: [16, 17]
      modifier: 3
    - scores: [18]
      modifier: 4

difficulty_classes:
  easy: 9
  normal: 12
  hard: 15
  extreme: 18

dice_expressions:
  ability_check:
    expression: "1d20 + {modifier}"
    description: "Roll d20, add ability modifier, compare to DC"
  attack_roll:
    expression: "1d20 + {attack_bonus}"
    description: "Roll d20, add attack bonus, compare to AC"
  saving_throw:
    expression: "1d20 + {modifier}"
    description: "Roll d20, add relevant modifier, compare to DC"

conditions:
  - name: "blinded"
    effects:
      - "Automatically fail checks requiring sight"
      - "Attacks against you have advantage"
      - "Your attacks have disadvantage"
  - name: "charmed"
    effects:
      - "Cannot attack the charmer"
      - "Charmer has advantage on social checks"
  - name: "frightened"
    effects:
      - "Disadvantage on checks while source visible"
      - "Cannot willingly move closer to source"
```

### Appendix B: Typer CLI Example

```python
# scripts/cli.py
import typer
import httpx
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="GM Chatbot CLI")
console = Console()
BASE_URL = "http://localhost:8000/api/v1"


@app.command()
def campaigns():
    """List all campaigns."""
    response = httpx.get(f"{BASE_URL}/campaigns")
    data = response.json()

    table = Table(title="Campaigns")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("System")
    table.add_column("Status")

    for campaign in data["data"]:
        table.add_row(
            campaign["id"],
            campaign["name"],
            campaign["rule_system"],
            campaign["status"]
        )

    console.print(table)


@app.command()
def roll(expression: str, reason: str = ""):
    """Roll dice using the dice tool."""
    response = httpx.post(
        f"{BASE_URL}/tools/dice/roll",
        json={"expression": expression, "reason": reason}
    )
    result = response.json()["data"]

    console.print(f"🎲 [bold]{expression}[/bold] → [green]{result['total']}[/green]")
    console.print(f"   Rolls: {result['rolls']} + {result['modifier']}")


@app.command()
def chat(campaign_id: str, message: str):
    """Send a message to the GM."""
    response = httpx.post(
        f"{BASE_URL}/campaigns/{campaign_id}/chat",
        json={"message": message}
    )
    result = response.json()["data"]

    console.print(f"[bold]GM:[/bold] {result['response']}")


if __name__ == "__main__":
    app()
```

### Appendix C: Glossary

#### Core Concepts

| Term         | Definition                                                                                                                                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Artifact** | A YAML file representing campaign data (characters, modules, state). All artifacts are validated against Pydantic models before use.                                                                                       |
| **Campaign** | The persistent definition of a game world, including its rules, characters, modules, and accumulated history. A campaign exists across multiple play sessions.                                                             |
| **Session**  | A runtime instance of a campaign representing a single play period. When players gather to play, the system creates a session from the campaign's current state. Multiple sessions over time advance the campaign's state. |
| **Module**   | A prepared adventure or encounter content within a campaign. Only one module can be active per session. Modules contain scenes, NPCs, encounters, and loot.                                                                |

#### Actors

| Term                           | Definition                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **GM (Game Master)**           | The person (or AI chatbot) running the game, controlling NPCs, adjudicating rules, and narrating the story. |
| **Player**                     | A human participant who controls a Player Character.                                                        |
| **PC (Player Character)**      | A character controlled by a player.                                                                         |
| **NPC (Non-Player Character)** | A character controlled by the GM, including allies, enemies, and neutral parties.                           |

#### Game State

| Term                 | Definition                                                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Game State**       | The complete current condition of a session, including character statuses, combat state, initiative order, and environmental conditions.          |
| **Action**           | A discrete game event performed by a player or GM that may modify game state. Actions are processed sequentially and logged for history/rollback. |
| **Action History**   | A chronological log of all actions taken during a campaign, enabling audit trails, rollback, and session replay.                                  |
| **Combat State**     | A subset of game state tracking active combat: initiative order, combatant HP/AC, conditions, and turn progression.                               |
| **State Transition** | The transformation of game state from one valid state to another as the result of an action.                                                      |

#### Technical Terms

| Term                       | Definition                                                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **VTT (Virtual Tabletop)** | Digital platforms for playing tabletop RPGs online, such as Roll20, Foundry VTT, or Fantasy Grounds.                            |
| **Platform Adapter**       | An abstraction layer that enables the GM Chatbot to communicate with different VTTs or interfaces (Roll20, Discord, CLI, etc.). |
| **Rules Engine**           | The component responsible for loading, validating, and querying game rules from YAML definitions.                               |
| **Dice Tool**              | An external service or CLI used by the chatbot to perform dice rolls and mathematical calculations, ensuring auditability.      |

#### Relationship Diagram

```
Campaign (persistent)
├── Contains: Rules, Characters, Modules, History
├── Spawns: Session (runtime instance)
│
Session (runtime)
├── Loads from: Campaign state
├── Has one active: Module
├── Maintains: Game State
├── Processes: Actions (sequential)
└── Persists changes to: Campaign
```

---

**Document End**

_This document is a living specification and will be updated as requirements are refined._
