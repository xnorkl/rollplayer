# GM Chatbot Usage Guide

## API Usage

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
curl -X POST "http://localhost:8000/api/v1/tools/dice/roll?expression=2d6+3"
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

## CLI Usage

### List Campaigns

```bash
uv run python scripts/cli.py campaigns
```

### Roll Dice

```bash
uv run python scripts/cli.py roll "1d20+5" "Attack roll"
```

### Chat

```bash
uv run python scripts/cli.py chat {campaign_id} "What happens next?"
```

## YAML Artifacts

Campaigns and characters are stored as YAML files in the `campaigns/` directory:

```
campaigns/
  {campaign_id}/
    campaign.yaml
    characters/
      pc_theron.yaml
      npc_goblin.yaml
    state/
      history.yaml
```

## Game Rules

Game rules are stored in YAML format in the `rules/` directory:

```
rules/
  shadowdark/
    core.yaml
```

Rules can be queried via the API:

```bash
curl "http://localhost:8000/api/v1/rules/shadowdark"
```
