"""Smoke tests for command parser."""

import unittest
from command_parser import CommandParser


class TestCommandParser(unittest.TestCase):
    """Test command parsing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_roll_command(self):
        """Test !roll command."""
        result = self.parser.parse("roll 2d6")
        self.assertIsNotNone(result)
        self.assertIn("2d6", result)

    def test_roll_command_with_modifier(self):
        """Test !roll command with modifier."""
        result = self.parser.parse("roll 1d20+5")
        self.assertIsNotNone(result)
        self.assertIn("1d20", result)

    def test_check_command(self):
        """Test !check command."""
        result = self.parser.parse("check strength")
        self.assertIsNotNone(result)
        self.assertIn("Strength", result)

    def test_check_command_with_dc(self):
        """Test !check command with DC."""
        result = self.parser.parse("check dex 15")
        self.assertIsNotNone(result)
        self.assertIn("Dexterity", result)
        self.assertIn("DC 15", result)

    def test_attack_command(self):
        """Test !attack command."""
        result = self.parser.parse("attack goblin")
        self.assertIsNotNone(result)
        self.assertIn("goblin", result)

    def test_attack_command_with_modifier(self):
        """Test !attack command with modifier."""
        result = self.parser.parse("attack goblin +5")
        self.assertIsNotNone(result)
        self.assertIn("goblin", result)

    def test_damage_command(self):
        """Test !damage command."""
        result = self.parser.parse("damage goblin 2d6")
        self.assertIsNotNone(result)
        self.assertIn("goblin", result)

    def test_initiative_command(self):
        """Test !initiative command."""
        result = self.parser.parse("initiative player1")
        self.assertIsNotNone(result)
        self.assertIn("player1", result)

    def test_initiative_command_with_modifier(self):
        """Test !initiative command with modifier."""
        result = self.parser.parse("initiative player1 +2")
        self.assertIsNotNone(result)
        self.assertIn("player1", result)

    def test_combat_start_command(self):
        """Test !combat start command."""
        result = self.parser.parse("combat start")
        self.assertIsNotNone(result)
        self.assertIn("Combat started", result)

    def test_combat_status_command(self):
        """Test !combat status command."""
        self.parser.parse("combat start")
        result = self.parser.parse("combat status")
        self.assertIsNotNone(result)

    def test_combat_end_command(self):
        """Test !combat end command."""
        self.parser.parse("combat start")
        result = self.parser.parse("combat end")
        self.assertIsNotNone(result)
        self.assertIn("Combat ended", result)

    def test_hp_command(self):
        """Test !hp command."""
        result = self.parser.parse("hp goblin 10")
        self.assertIsNotNone(result)
        self.assertIn("goblin", result)

    def test_ac_command(self):
        """Test !ac command."""
        result = self.parser.parse("ac goblin 15")
        self.assertIsNotNone(result)
        self.assertIn("goblin", result)
        self.assertIn("AC 15", result)

    def test_help_command(self):
        """Test !help command."""
        result = self.parser.parse("help")
        self.assertIsNotNone(result)
        self.assertIn("Commands", result)

    def test_invalid_command(self):
        """Test invalid command."""
        result = self.parser.parse("invalid_command")
        self.assertIsNone(result)

    def test_empty_command(self):
        """Test empty command."""
        result = self.parser.parse("")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
