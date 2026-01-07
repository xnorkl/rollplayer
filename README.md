# GM Chatbot

[![codecov](https://codecov.io/gh/xnorkl/Roll20_Shadowdark_GM/branch/main/graph/badge.svg)](https://codecov.io/gh/xnorkl/Roll20_Shadowdark_GM)

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

This project uses [`just`](https://github.com/casey/just) as a task runner for standardized local development. Install it with:

```bash
# macOS
brew install just

# Or via cargo
cargo install just
```

### Common Tasks

```bash
# Run all tests
just test

# Run unit tests only
just test-unit

# Run integration tests only
just test-integration

# Run tests with coverage
just test-cov

# Run linting
just lint

# Auto-fix linting issues
just lint-fix

# Format code
just format

# Run type checking
just typecheck

# Run all quality checks (format, lint, typecheck, test)
just check

# Start development server
just dev

# Interactive smoke testing shell
just shell

# Start development server with debug logging
just dev-debug

# Clean build artifacts
just clean

# Show all available commands
just --list
```

### Smoke Testing

The project includes a fast smoke testing framework for validating critical business logic paths during development. Smoke tests complete in under 10 seconds and require no external dependencies.

```bash
# Run all smoke tests
just smoke

# Run smoke tests with verbose output
just smoke-v

# Run specific test suite
just smoke-only player
just smoke-only campaign
just smoke-only session
just smoke-only integration

# List available test suites
just smoke-list

# Run pytest smoke tests
just test-smoke

# Quick local validation (smoke + unit tests)
just validate

# Pre-commit checks (format-check + lint + smoke)
just pre-commit

# Pre-push checks (full CI parity)
just pre-push
```

**Interactive Shell**: Use `just shell` to launch an interactive Python REPL with pre-configured services, models, and helper functions for ad-hoc exploration and manual testing.

**Workflow Examples**:

- Quick sanity check: `just smoke` (~5s)
- Before committing: `just pre-commit` (~15s)
- Before pushing: `just pre-push` (~60s)
- Interactive exploration: `just shell`

### Manual Commands

If you don't have `just` installed, you can use these commands directly:

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
