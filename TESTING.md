# Testing Guide for GM Chatbot

This document describes the smoke tests and testing procedures for the GM Chatbot.

## Test Files

- `test_game_engine.py` - Unit tests for game engine components
- `test_command_parser.py` - Unit tests for command parsing
- `test_gm_handler.py` - Unit tests for GM handler
- `smoke_test.py` - Comprehensive smoke test runner
- `test_websocket.sh` - Bash script for basic connectivity tests
- `health_check.py` - HTTP health check server for curl testing

## Running Tests

### Python Unit Tests

Run all unit tests:

```bash
python3 -m unittest discover -v
```

Run specific test file:

```bash
python3 -m unittest test_game_engine -v
python3 -m unittest test_command_parser -v
python3 -m unittest test_gm_handler -v
```

### Comprehensive Smoke Test

Run the comprehensive smoke test script:

```bash
python3 smoke_test.py
```

This will:

1. Test module imports
2. Test basic functionality
3. Run all unit tests
4. Provide a summary

### Bash Smoke Tests (curl-compatible)

Run the bash smoke test script:

```bash
./test_websocket.sh
```

This script tests:

- Python installation
- Required dependencies
- Module imports
- Basic functionality
- Port availability

### HTTP Health Check (curl testing)

Start the health check server:

```bash
python3 health_check.py
```

In another terminal, test with curl:

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{
  "status": "healthy",
  "checks": {
    "game_engine": "ok",
    "command_parser": "ok",
    "gm_handler": "ok",
    "dice_rolling": "ok"
  }
}
```

## Test Coverage

### Game Engine Tests

- Dice rolling (simple, multiple dice, modifiers)
- Shadowdark rules (ability checks, attacks, saves)
- Combat tracking (initiative, HP, AC, conditions)
- Spell management (casting, slots)

### Command Parser Tests

- All command types (!roll, !check, !attack, etc.)
- Command validation
- Error handling

### GM Handler Tests

- Command handling
- Question handling (with/without AI)
- Message routing

## Continuous Integration

To integrate into CI/CD:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python3 smoke_test.py

# Check exit code (0 = success, 1 = failure)
echo $?
```

## Manual Testing

For manual testing of the full system:

1. Start the chatbot server:

   ```bash
   python3 chat_bot.py
   ```

2. Install the Tampermonkey script (`chat_connector.js`)

3. Connect to a Roll20 game

4. Test commands in chat:
   - `!roll 2d6`
   - `!check strength 15`
   - `!combat start`
   - `!help`

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running tests from the project root:

```bash
cd /path/to/roll20_chatbot
python3 smoke_test.py
```

### Missing Dependencies

Install all dependencies:

```bash
pip install -r requirements.txt
```

### Port Already in Use

If port 5678 is already in use, either:

- Stop the existing server
- Change the port in `config.py`
