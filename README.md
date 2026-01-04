# GM Chatbot

Game Master Assistant for tabletop RPGs - A modular, multi-campaign REST API platform with AI-powered GM assistance.

## Features

- **Multi-Campaign Support**: Manage multiple campaigns with isolated game state
- **REST API**: Full REST API with OpenAPI 3.1 documentation
- **WebSocket Support**: Real-time chat via WebSocket
- **YAML-Based Configuration**: Game rules and campaign artifacts stored as YAML
- **Type-Safe Models**: Pydantic v2 with strict validation
- **External Dice Tools**: Delegated dice rolling for auditability
- **LLM Integration**: Support for OpenAI and Anthropic
- **Platform Adapters**: REST, Roll20, and CLI adapters

## Quick Start

### Prerequisites

- Python 3.12+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
uv sync

# Run the API server
uv run python -m gm_chatbot.main
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:

- **Scalar API Reference**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### CLI Client

```bash
# List campaigns
uv run python scripts/cli.py campaigns

# Roll dice
uv run python scripts/cli.py roll "2d6+3"

# Send chat message
uv run python scripts/cli.py chat <campaign_id> "Hello GM!"
```

## Architecture

The system is built with a modular architecture:

- **Models**: Pydantic models for all data structures
- **Services**: Business logic layer (CampaignService, CharacterService, GameStateService, GMService)
- **API**: FastAPI REST endpoints and WebSocket support
- **Tools**: External integrations (dice tools, LLM providers)
- **Adapters**: Platform-specific integrations (REST, Roll20, CLI)
- **Artifacts**: YAML-based persistence layer

## Configuration

Set environment variables for LLM providers:

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run linting
uv run ruff check .

# Run type checking
uv run ty check

# Run tests
uv run pytest tests/ -v
```

## Deployment

The application is containerized and can be deployed to Fly.io:

```bash
flyctl deploy
```

See `infrastructure/README.md` for detailed deployment instructions.

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Usage Guide](docs/usage.md)** - Complete API usage with examples
- **[Testing Guide](docs/testing.md)** - Testing procedures and CI/CD
- **[Requirements Document](docs/requirements.md)** - Architecture specification and requirements
- **[Documentation Index](docs/README.md)** - Overview of all documentation

## License

See LICENSE file.
