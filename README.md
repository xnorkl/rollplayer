# Roll20 GM Chatbot for Shadowdark RPG

A Game Master chatbot for Roll20 that understands Shadowdark RPG rules, handles dice rolls, manages combat, and provides rule clarifications using AI.

## Features

- **Dice Rolling**: Parse and execute dice expressions (e.g., `2d6+3`, `1d20`)
- **Ability Checks**: Perform ability checks with DC calculations
- **Combat Tracking**: Manage initiative, turn order, HP, AC, and status effects
- **Spell Management**: Track spell slots and handle spell casting
- **AI-Powered Rules**: Answer natural language questions about Shadowdark RPG rules
- **Command-Based Actions**: Quick commands for common game actions

## Setup

### Prerequisites

1. Python 3.8 or higher
2. [Tampermonkey](https://www.tampermonkey.net/) browser extension
3. (Optional) OpenAI API key for AI features

### Local Installation

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install Tampermonkey in your browser

3. Add the `chat_connector.js` script to Tampermonkey:

   - Open Tampermonkey dashboard
   - Create a new script
   - Copy and paste the contents of `chat_connector.js`
   - Save the script

4. (Optional) Set up OpenAI API key for AI features:

   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

5. Start the chatbot server:

   ```bash
   python3 chat_bot.py
   ```

6. Connect to your Roll20 game - the chatbot will automatically connect via WebSocket

### Fly.io Deployment (Production)

For production hosting on Fly.io with GitOps:

1. **Install Fly.io CLI**:

   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Authenticate**:

   ```bash
   flyctl auth login
   ```

3. **Create app and deploy**:

   ```bash
   flyctl apps create roll20-chatbot
   flyctl secrets set OPENAI_API_KEY=your-api-key-here
   # Copy fly.toml to project root (build context must be project root)
   cp infrastructure/fly.toml fly.toml
   flyctl deploy
   ```

4. **Update client configuration**:

   - Get your app URL: `flyctl status --app roll20-chatbot`
   - Update `chat_connector.js` WebSocket URL to `wss://your-app.fly.dev`
   - Or configure at runtime: `localStorage.setItem('roll20_chatbot_ws_url', 'wss://your-app.fly.dev')`

5. **GitOps (Automatic deployments)**:
   - Set `FLY_API_TOKEN` secret in GitHub Actions
   - Push to `main` branch to trigger automatic deployment

See [infrastructure/README.md](infrastructure/README.md) for detailed deployment documentation.

## Configuration

Edit `config.py` or set environment variables to customize:

- `OPENAI_API_KEY`: Your OpenAI API key (optional, for AI features)
- `LLM_MODEL`: Model to use (default: `gpt-4o-mini`)
- `WS_ADDRESS`: WebSocket address (default: `127.0.0.1`)
- `WS_PORT`: WebSocket port (default: `5678`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Usage

### Commands

All commands start with `!`:

#### Dice & Rolls

- `!roll <expression>` - Roll dice
  - Example: `!roll 2d6+3`, `!roll 1d20`
- `!check <ability> [DC]` - Ability check
  - Example: `!check strength 15`, `!check dex`
- `!attack <target> [modifier]` - Attack roll
  - Example: `!attack goblin +5`
- `!damage <target> <expression>` - Apply damage
  - Example: `!damage goblin 2d6`

#### Combat Management

- `!combat start` - Start combat tracking
- `!combat end` - End combat
- `!combat status` - Show current combat status
- `!combat next` - Advance to next turn
- `!initiative <name> [dex_modifier]` - Roll initiative
  - Example: `!initiative player1 +2`
- `!hp <target> <value> [max]` - Set HP
  - Example: `!hp goblin 10 15`
- `!ac <target> <value>` - Set AC
  - Example: `!ac goblin 15`

#### Spells

- `!spell <spell_name> [target]` - Cast spell
  - Example: `!spell magic_missile goblin`

#### Help

- `!help` - Show command reference

### Natural Language Queries

Ask questions in plain English for rule clarifications:

- "What's the DC for a hard check?"
- "How does initiative work in Shadowdark?"
- "What are the ability modifiers?"
- "How do spell slots work?"

The AI will provide answers based on Shadowdark RPG rules.

## Shadowdark RPG Rules

The chatbot implements key Shadowdark mechanics:

- **Ability Checks**: d20 + ability modifier vs DC

  - Easy: DC 5
  - Normal: DC 10
  - Hard: DC 15
  - Very Hard: DC 20

- **Combat**:

  - Initiative: d20 + Dexterity modifier
  - Attack: d20 + modifier vs AC
  - Damage: Roll weapon/spell damage dice

- **Ability Modifiers**: Based on ability scores (1-20 range)

## Architecture

The chatbot uses a WebSocket bridge architecture:

1. **chat_connector.js** (Tampermonkey script) - Monitors Roll20 chat and forwards messages
2. **chat_bot.py** - WebSocket server that receives messages
3. **gm_handler.py** - Main handler that coordinates responses
4. **command_parser.py** - Parses and executes game commands
5. **game_engine.py** - Core game mechanics (dice, combat, spells)
6. **ai_handler.py** - AI integration for rule queries

## Development

### Project Structure

```
roll20_chatbot/
├── infrastructure/          # Infrastructure as Code
│   ├── Dockerfile          # Container image
│   ├── fly.toml            # Fly.io configuration
│   └── README.md           # Deployment docs
├── .github/
│   └── workflows/
│       └── deploy-fly.yml  # GitOps workflow
├── chat_bot.py             # WebSocket server
├── chat_connector.js       # Tampermonkey script
├── game_engine.py          # Core game mechanics
├── command_parser.py       # Command parsing
├── ai_handler.py           # LLM integration
├── gm_handler.py           # Main GM handler
├── config.py               # Configuration
├── shadowdark_rules.py     # Shadowdark rule definitions
├── requirements.txt        # Dependencies
└── README.md               # This file
```

### Testing

Run smoke tests:

```bash
python3 smoke_test.py
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## License

See LICENSE file for details.
