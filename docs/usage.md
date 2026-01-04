# API Usage Guide

Complete guide to using the GM Chatbot API, including REST endpoints, WebSocket connections, CLI usage, and YAML artifacts.

## REST API

### Creating a Campaign

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Campaign",
    "rule_system": "shadowdark",
    "description": "A test campaign"
  }'
```

### Creating a Character

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/{campaign_id}/characters" \
  -H "Content-Type: application/json" \
  -d '{
    "character_type": "player_character",
    "identity": {
      "name": "Theron Blackwood",
      "level": 3
    },
    "abilities": {
      "strength": 16,
      "dexterity": 14
    }
  }'
```

### Rolling Dice

```bash
curl -X POST "http://localhost:8000/api/v1/tools/dice/roll" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "2d6+3",
    "reason": "Damage roll"
  }'
```

### Sending Chat Messages

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/{campaign_id}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should the party do next?",
    "campaign_id": "{campaign_id}"
  }'
```

### Querying Game Rules

```bash
curl "http://localhost:8000/api/v1/rules/shadowdark"
```

## WebSocket Chat

Connect to the WebSocket endpoint for real-time chat:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/campaigns/{campaign_id}/chat');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('GM:', data.content);
};

ws.send('Hello GM!');
```

## CLI Client

The CLI client provides a convenient interface for common operations:

### List Campaigns

```bash
uv run python scripts/cli.py campaigns
```

### Roll Dice

```bash
uv run python scripts/cli.py roll "1d20+5" "Attack roll"
```

### Chat with GM

```bash
uv run python scripts/cli.py chat {campaign_id} "What happens next?"
```

For more CLI commands, see the root [README.md](../README.md) or run:

```bash
uv run python scripts/cli.py --help
```

## YAML Artifacts

Campaigns and characters are stored as validated YAML files in the `campaigns/` directory:

```
campaigns/
  {campaign_id}/
    campaign.yaml           # Campaign metadata
    gm_rules.yaml          # GM-specific rules
    player_rules.yaml      # Player-facing rules
    characters/
      pc_theron.yaml       # Player character
      npc_goblin.yaml      # Non-player character
    modules/
      session_001.yaml      # Session modules
    state/
      combat_state.yaml     # Current combat state
      history.yaml          # Action history
```

All artifacts are validated against Pydantic models before being used by the system.

## Game Rules

Game rules are stored in YAML format in the `rules/` directory:

```
rules/
  shadowdark/
    core.yaml              # Core rule definitions
```

Rules can be:
- Loaded dynamically without code changes
- Queried via the API
- Extended with campaign-specific house rules

See [requirements.md](requirements.md) for detailed information about the rules engine and artifact structure.
