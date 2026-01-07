#!/usr/bin/env python
"""Structured smoke tests for GM Chatbot critical paths.

Usage:
    just smoke                    # Run all smoke tests
    just smoke --verbose          # Show full tracebacks
    just smoke --only player      # Run single suite
    just smoke --list             # List available suites

Exit Codes:
    0 - All tests passed
    1 - One or more tests failed
    2 - Invalid arguments

Design Principles:
    - No pytest dependency (standalone execution)
    - Fast execution (< 10 seconds total)
    - Isolated (uses temp directories)
    - Self-documenting (clear output)
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TypeAlias

# ============================================================================
# Framework
# ============================================================================

TestFn: TypeAlias = Callable[[], None]


@dataclass
class SmokeResult:
    """Result of a single smoke test."""

    name: str
    passed: bool
    duration_ms: float
    error: str | None = None
    traceback: str | None = None


@dataclass
class SmokeSuite:
    """Collection of related smoke tests."""

    name: str
    description: str = ""
    tests: list[TestFn] = field(default_factory=list)
    results: list[SmokeResult] = field(default_factory=list)

    def test(self, fn: TestFn) -> TestFn:
        """Decorator to register a smoke test function."""
        self.tests.append(fn)
        return fn

    def run(self, *, verbose: bool = False) -> bool:
        """
        Execute all tests in suite.

        Args:
            verbose: Show full tracebacks on failure

        Returns:
            True if all tests passed
        """
        self.results.clear()

        print(f"\n{'─' * 60}")
        print(f"  {self.name}")
        if self.description:
            print(f"  {self.description}")
        print(f"{'─' * 60}\n")

        for test_fn in self.tests:
            result = self._run_single(test_fn, verbose=verbose)
            self.results.append(result)
            self._print_result(result, verbose=verbose)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        status = "✓" if passed == total else "✗"

        print(f"\n  {status} {passed}/{total} passed\n")

        return passed == total

    def _run_single(self, fn: TestFn, *, verbose: bool) -> SmokeResult:
        """Run a single test function."""
        name = fn.__name__
        start = time.perf_counter()

        try:
            fn()
            duration = (time.perf_counter() - start) * 1000
            return SmokeResult(name=name, passed=True, duration_ms=duration)

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            tb = traceback.format_exc() if verbose else None
            return SmokeResult(
                name=name,
                passed=False,
                duration_ms=duration,
                error=f"{type(e).__name__}: {e}",
                traceback=tb,
            )

    def _print_result(self, result: SmokeResult, *, verbose: bool) -> None:
        """Print single test result."""
        icon = "✓" if result.passed else "✗"
        status = "PASS" if result.passed else "FAIL"

        print(f"  {icon} {result.name} ({result.duration_ms:.1f}ms) [{status}]")

        if not result.passed:
            print(f"    └─ {result.error}")
            if verbose and result.traceback:
                for line in result.traceback.split("\n"):
                    print(f"       {line}")


# ============================================================================
# Test Environment
# ============================================================================

class TestEnvironment:
    """Isolated test environment with temp directories."""

    def __init__(self):
        self._temp_dir: Path | None = None
        self._services: dict | None = None

    def setup(self) -> None:
        """Initialize temp directory and services."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="gm_smoke_"))
        self._services = None  # Lazy load

    def teardown(self) -> None:
        """Clean up temp directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._services = None

    @property
    def services(self) -> dict:
        """Get or create service instances."""
        if self._services is None:
            self._services = self._create_services()
        return self._services

    def _create_services(self) -> dict:
        """Create fresh service instances."""
        from gm_chatbot.artifacts.store import ArtifactStore
        from gm_chatbot.services.campaign_service import CampaignService
        from gm_chatbot.services.player_service import PlayerService
        from gm_chatbot.services.session_service import SessionService

        if self._temp_dir is None:
            raise RuntimeError("TestEnvironment not set up")

        store = ArtifactStore(
            campaigns_dir=self._temp_dir / "campaigns",
            players_dir=self._temp_dir / "players",
        )

        return {
            "store": store,
            "campaign": CampaignService(store),
            "player": PlayerService(store),
            "session": SessionService(store),
        }

    def fresh_services(self) -> dict:
        """Get fresh service instances (new directories)."""
        self._services = None
        return self.services


# Global test environment
env = TestEnvironment()


def get_svc(name: str):
    """Shorthand to get a service."""
    return env.services[name]


# ============================================================================
# Test Suites
# ============================================================================

# --- Player Suite ---

player_suite = SmokeSuite(
    name="Player Service",
    description="Core player CRUD operations",
)


@player_suite.test
def player_create_valid():
    """Create player with valid data."""
    svc = get_svc("player")
    player = asyncio.run(svc.create_player(username="smoke_user", display_name="Smoke User"))

    assert player.metadata.id, "Player must have ID"
    assert player.username == "smoke_user", "Username must match"
    assert player.metadata.created_at is not None, "Must have created_at"


@player_suite.test
def player_create_validates_empty_username():
    """Reject empty username."""
    svc = get_svc("player")

    try:
        asyncio.run(svc.create_player(username="", display_name="Bad User"))
        raise AssertionError("Should reject empty username")
    except (ValueError, ValidationError):
        pass  # Expected


@player_suite.test
def player_create_validates_whitespace_username():
    """Reject whitespace-only username."""
    svc = get_svc("player")

    try:
        asyncio.run(svc.create_player(username="   ", display_name="Bad User"))
        raise AssertionError("Should reject whitespace username")
    except (ValueError, ValidationError):
        pass  # Expected


@player_suite.test
def player_retrieve_existing():
    """Retrieve existing player by ID."""
    svc = get_svc("player")
    created = asyncio.run(svc.create_player("retrieval_test", "Retrieval Test"))

    loaded = asyncio.run(svc.get_player(created.metadata.id))

    assert loaded is not None, "Must find existing player"
    assert loaded.metadata.id == created.metadata.id, "IDs must match"
    assert loaded.username == created.username, "Username must match"


@player_suite.test
def player_retrieve_nonexistent():
    """Return None for non-existent player."""
    svc = get_svc("player")

    try:
        asyncio.run(svc.get_player("nonexistent-player-id-12345"))
        raise AssertionError("Should raise FileNotFoundError for missing player")
    except FileNotFoundError:
        pass  # Expected


@player_suite.test
def player_roundtrip_preserves_timestamps():
    """Timestamps survive save/load cycle."""
    from datetime import timezone

    svc = get_svc("player")
    created = asyncio.run(svc.create_player("timestamp_test", "Timestamp Test"))

    loaded = asyncio.run(svc.get_player(created.metadata.id))

    assert loaded is not None
    assert loaded.metadata.created_at == created.metadata.created_at, "created_at must match"
    assert loaded.metadata.created_at.tzinfo == timezone.utc, "Must be UTC"


# --- Campaign Suite ---

campaign_suite = SmokeSuite(
    name="Campaign Service",
    description="Campaign CRUD and membership operations",
)


@campaign_suite.test
def campaign_create_valid():
    """Create campaign with valid data."""
    svc = get_svc("campaign")
    campaign = asyncio.run(svc.create_campaign(name="Smoke Quest", rule_system="dnd5e"))

    assert campaign.metadata.id, "Campaign must have ID"
    assert campaign.name == "Smoke Quest"
    assert campaign.rule_system == "dnd5e"
    assert campaign.status == "draft", "New campaigns start as draft"


@campaign_suite.test
def campaign_add_player():
    """Add player to campaign."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")

    player = asyncio.run(player_svc.create_player("party_member", "Party Member"))
    campaign = asyncio.run(campaign_svc.create_campaign("Party Quest", "dnd5e"))

    membership = asyncio.run(campaign_svc.add_player(campaign.metadata.id, player.metadata.id))

    assert membership.player_id == player.metadata.id
    assert membership.campaign_id == campaign.metadata.id
    assert membership.role == "player"  # Default role


@campaign_suite.test
def campaign_add_player_as_gm():
    """Add player to campaign with GM role."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")

    gm = asyncio.run(player_svc.create_player("game_master", "Game Master"))
    campaign = asyncio.run(campaign_svc.create_campaign("GM Quest", "dnd5e"))

    membership = asyncio.run(campaign_svc.add_player(campaign.metadata.id, gm.metadata.id, role="gm"))

    assert membership.role == "gm"


@campaign_suite.test
def campaign_list_members():
    """List all members of a campaign."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")

    campaign = asyncio.run(campaign_svc.create_campaign("Full Party", "dnd5e"))

    # Add multiple players
    for i in range(3):
        player = asyncio.run(player_svc.create_player(f"member_{i}", f"Member {i}"))
        asyncio.run(campaign_svc.add_player(campaign.metadata.id, player.metadata.id))

    members = asyncio.run(campaign_svc.list_members(campaign.metadata.id))

    assert len(members) == 3, f"Expected 3 members, got {len(members)}"


@campaign_suite.test
def campaign_prevent_duplicate_membership():
    """Prevent adding same player twice."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")

    player = asyncio.run(player_svc.create_player("duplicate_test", "Duplicate Test"))
    campaign = asyncio.run(campaign_svc.create_campaign("No Dupes", "dnd5e"))

    asyncio.run(campaign_svc.add_player(campaign.metadata.id, player.metadata.id))

    try:
        asyncio.run(campaign_svc.add_player(campaign.metadata.id, player.metadata.id))
        raise AssertionError("Should reject duplicate membership")
    except ValueError:
        pass  # Expected


# --- Session Suite ---

session_suite = SmokeSuite(
    name="Session Service",
    description="Game session lifecycle management",
)


@session_suite.test
def session_create():
    """Start a new session."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    gm = asyncio.run(player_svc.create_player("session_gm", "Session GM"))
    campaign = asyncio.run(campaign_svc.create_campaign("Session Test", "dnd5e"))

    session = asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))

    assert session.campaign_id == campaign.metadata.id
    assert session.status == "active"
    assert session.session_number == 1


@session_suite.test
def session_prevent_multiple_active():
    """Only one active session per campaign."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    gm = asyncio.run(player_svc.create_player("multi_session_gm", "Multi Session GM"))
    campaign = asyncio.run(campaign_svc.create_campaign("One At A Time", "dnd5e"))

    asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))

    try:
        asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))
        raise AssertionError("Should reject second active session")
    except ValueError:
        pass  # Expected


@session_suite.test
def session_end():
    """End an active session."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    gm = asyncio.run(player_svc.create_player("end_session_gm", "End Session GM"))
    campaign = asyncio.run(campaign_svc.create_campaign("Ending Quest", "dnd5e"))
    session = asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))

    ended = asyncio.run(session_svc.end_session(campaign.metadata.id, session.metadata.id))

    assert ended.status == "ended"
    assert ended.ended_at is not None


@session_suite.test
def session_increment_number():
    """Session numbers increment correctly."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    gm = asyncio.run(player_svc.create_player("increment_gm", "Increment GM"))
    campaign = asyncio.run(campaign_svc.create_campaign("Counting Quest", "dnd5e"))

    session1 = asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))
    asyncio.run(session_svc.end_session(campaign.metadata.id, session1.metadata.id))

    session2 = asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))

    assert session1.session_number == 1
    assert session2.session_number == 2


# --- Integration Suite ---

integration_suite = SmokeSuite(
    name="Integration (Critical Paths)",
    description="End-to-end workflows that must never break",
)


@integration_suite.test
def integration_full_game_setup():
    """Complete game setup: campaign, GM, players, session."""
    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    # Create GM and players
    gm = asyncio.run(player_svc.create_player("dm", "Dungeon Master"))
    player1 = asyncio.run(player_svc.create_player("fighter", "Brave Fighter"))
    player2 = asyncio.run(player_svc.create_player("wizard", "Wise Wizard"))

    # Create campaign
    campaign = asyncio.run(
        campaign_svc.create_campaign(
            name="Epic Integration Quest",
            rule_system="dnd5e",
            created_by=gm.metadata.id,
        )
    )

    # Add participants
    asyncio.run(campaign_svc.add_player(campaign.metadata.id, gm.metadata.id, role="gm"))
    asyncio.run(campaign_svc.add_player(campaign.metadata.id, player1.metadata.id))
    asyncio.run(campaign_svc.add_player(campaign.metadata.id, player2.metadata.id))

    # Verify membership
    members = asyncio.run(campaign_svc.list_members(campaign.metadata.id))
    assert len(members) == 3

    # Start session
    session = asyncio.run(session_svc.create_session(campaign.metadata.id, gm.metadata.id))
    assert session.status == "active"

    # End session
    ended = asyncio.run(session_svc.end_session(campaign.metadata.id, session.metadata.id))
    assert ended.status == "ended"


@integration_suite.test
def integration_datetime_consistency():
    """All timestamps are UTC throughout the system."""
    from datetime import timezone

    campaign_svc = get_svc("campaign")
    player_svc = get_svc("player")
    session_svc = get_svc("session")

    # Create entities
    player = asyncio.run(player_svc.create_player("tz_test", "Timezone Test"))
    campaign = asyncio.run(campaign_svc.create_campaign("UTC Quest", "dnd5e"))
    asyncio.run(campaign_svc.add_player(campaign.metadata.id, player.metadata.id))
    session = asyncio.run(session_svc.create_session(campaign.metadata.id, player.metadata.id))

    # Verify all timestamps are UTC
    assert player.metadata.created_at.tzinfo == timezone.utc
    assert campaign.metadata.created_at.tzinfo == timezone.utc
    assert session.started_at.tzinfo == timezone.utc

    # Verify after reload
    loaded_player = asyncio.run(player_svc.get_player(player.metadata.id))
    assert loaded_player.metadata.created_at.tzinfo == timezone.utc
    assert loaded_player.metadata.created_at == player.metadata.created_at


@integration_suite.test
def integration_data_isolation():
    """Services use isolated data directories."""
    store = get_svc("store")

    # Verify we're using temp directory
    campaigns_dir = store.campaigns_dir

    assert "gm_smoke_" in str(campaigns_dir), "Must use temp directory"
    assert campaigns_dir.exists(), "Directory must exist"


# ============================================================================
# Test Registry
# ============================================================================

ALL_SUITES: dict[str, SmokeSuite] = {
    "player": player_suite,
    "campaign": campaign_suite,
    "session": session_suite,
    "integration": integration_suite,
}


# ============================================================================
# CLI
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run smoke tests for GM Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/smoke_test.py              # Run all suites
    python scripts/smoke_test.py --verbose    # Show tracebacks
    python scripts/smoke_test.py --only player
    python scripts/smoke_test.py --list
        """,
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full tracebacks on failure",
    )

    parser.add_argument(
        "--only",
        choices=list(ALL_SUITES.keys()),
        help="Run only specified suite",
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        dest="list_suites",
        help="List available suites and exit",
    )

    return parser.parse_args()


def list_suites() -> None:
    """Print available suites."""
    print("\nAvailable smoke test suites:\n")
    for name, suite in ALL_SUITES.items():
        test_count = len(suite.tests)
        print(f"  {name:15} {test_count:2} tests  {suite.description}")
    print()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = failure, 2 = error)
    """
    args = parse_args()

    if args.list_suites:
        list_suites()
        return 0

    # Select suites
    if args.only:
        suites = [ALL_SUITES[args.only]]
    else:
        suites = list(ALL_SUITES.values())

    # Setup
    env.setup()

    try:
        # Run suites
        all_passed = True
        total_tests = 0
        total_passed = 0

        for suite in suites:
            # Fresh services for each suite
            env.fresh_services()

            if not suite.run(verbose=args.verbose):
                all_passed = False

            total_tests += len(suite.results)
            total_passed += sum(1 for r in suite.results if r.passed)

        # Summary
        print("=" * 60)
        status = "PASSED" if all_passed else "FAILED"
        icon = "✓" if all_passed else "✗"
        print(f"  {icon} SMOKE TESTS {status}: {total_passed}/{total_tests}")
        print("=" * 60)
        print()

        return 0 if all_passed else 1

    finally:
        env.teardown()


# Handle pydantic import for validation errors
try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = ValueError  # type: ignore


if __name__ == "__main__":
    sys.exit(main())
