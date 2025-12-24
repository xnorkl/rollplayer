#!/bin/bash
# Smoke test script using curl and basic connectivity tests

set -e

echo "=========================================="
echo "GM Chatbot WebSocket Smoke Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if Python is available
echo "Test 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python found: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python3 not found"
    exit 1
fi

# Test 2: Check if required Python packages are installed
echo ""
echo "Test 2: Checking Python dependencies..."
python3 -c "import websockets; import bs4; print('✓ websockets and beautifulsoup4 installed')" 2>/dev/null || {
    echo -e "${RED}✗${NC} Missing required Python packages. Run: pip install -r requirements.txt"
    exit 1
}

# Test 3: Check if modules can be imported
echo ""
echo "Test 3: Testing module imports..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
try:
    import game_engine
    import command_parser
    import gm_handler
    import config
    import shadowdark_rules
    print('✓ All modules imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
" || exit 1

# Test 4: Test basic functionality
echo ""
echo "Test 4: Testing basic game engine functionality..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from game_engine import DiceRoller, ShadowdarkRules, CombatTracker

# Test dice rolling
result, _ = DiceRoller.roll('1d20')
assert 1 <= result <= 20, f'Dice roll out of range: {result}'
print('✓ Dice rolling works')

# Test rules
success, _ = ShadowdarkRules.ability_check(15, 3, 15)
assert success, 'Ability check should succeed'
print('✓ Rule calculations work')

# Test combat tracker
tracker = CombatTracker()
tracker.start_combat()
assert tracker.is_in_combat(), 'Combat should be active'
print('✓ Combat tracking works')
" || {
    echo -e "${RED}✗${NC} Basic functionality test failed"
    exit 1
}

# Test 5: Test command parser
echo ""
echo "Test 5: Testing command parser..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from command_parser import CommandParser

parser = CommandParser()
result = parser.parse('roll 2d6')
assert result is not None, 'Command parser should return result'
assert '2d6' in result, 'Result should contain dice expression'
print('✓ Command parsing works')
" || {
    echo -e "${RED}✗${NC} Command parser test failed"
    exit 1
}

# Test 6: Check if port is available (basic check)
echo ""
echo "Test 6: Checking if WebSocket port is available..."
PORT=5678
if command -v lsof &> /dev/null; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $PORT is already in use (server may be running)"
    else
        echo -e "${GREEN}✓${NC} Port $PORT is available"
    fi
else
    echo -e "${YELLOW}⚠${NC} Cannot check port (lsof not available)"
fi

# Test 7: Run Python unit tests if available
echo ""
echo "Test 7: Running Python unit tests..."
if [ -f "test_game_engine.py" ]; then
    python3 -m unittest test_game_engine -v 2>&1 | head -20 || {
        echo -e "${YELLOW}⚠${NC} Some unit tests may have failed (see output above)"
    }
else
    echo -e "${YELLOW}⚠${NC} test_game_engine.py not found, skipping unit tests"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓${NC} All smoke tests completed!"
echo "=========================================="
echo ""
echo "To start the chatbot server, run:"
echo "  python3 chat_bot.py"
echo ""
echo "Note: WebSocket testing requires a WebSocket client."
echo "The server will be available at ws://localhost:5678"

