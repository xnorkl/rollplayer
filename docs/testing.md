# Testing Guide

Testing procedures for the GM Chatbot REST API and services.

## Test Structure

Tests are organized in the `tests/` directory:

- `tests/integration/` - Integration tests for API endpoints and services
- `tests/conftest.py` - Pytest configuration and fixtures

## Running Tests

### Run All Tests

```bash
uv run pytest tests/ -v
```

### Run with Coverage

```bash
uv run pytest tests/ --cov=gm_chatbot --cov-report=html
```

### Run Specific Test Files

```bash
# Integration tests
uv run pytest tests/integration/test_campaigns.py -v
uv run pytest tests/integration/test_characters.py -v
```

## API Testing

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "gm-chatbot"
}
```

### Readiness Check

```bash
curl http://localhost:8000/ready
```

Expected response:

```json
{
  "status": "ready",
  "service": "gm-chatbot"
}
```

### Interactive API Documentation

Once the server is running, visit:

- **Scalar API Reference**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Test Coverage

### Integration Tests

- Campaign CRUD operations
- Character management
- API endpoint validation
- Error handling

## Continuous Integration

The project uses UV for dependency management. CI/CD should:

```bash
# Install dependencies
uv sync --dev

# Run linting
uv run ruff check src/

# Run type checking
uv run ty check src/

# Run tests with coverage
uv run pytest tests/ --cov=gm_chatbot --cov-report=xml
```

## Manual Testing

### Start the API Server

```bash
uv run python -m gm_chatbot.main
```

The API will be available at `http://localhost:8000`

### Test Campaign Operations

```bash
# Create a campaign
curl -X POST "http://localhost:8000/api/v1/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "rule_system": "shadowdark",
    "description": "A test campaign"
  }'

# List campaigns
curl "http://localhost:8000/api/v1/campaigns"
```

### Test Dice Rolling

```bash
curl -X POST "http://localhost:8000/api/v1/tools/dice/roll" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "2d6+3",
    "reason": "Test roll"
  }'
```

## Troubleshooting

### Import Errors

Ensure you're running tests from the project root and that dependencies are installed:

```bash
cd /path/to/roll20_chatbot
uv sync --dev
uv run pytest tests/
```

### Port Already in Use

If port 8000 is already in use:

- Stop the existing server
- Change the port in the application configuration
- Use environment variable: `PORT=8001 uv run python -m gm_chatbot.main`
