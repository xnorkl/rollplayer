"""Smoke tests for game engine components."""

import unittest
from game_engine import DiceRoller, ShadowdarkRules, CombatTracker, SpellManager, Spell


class TestDiceRoller(unittest.TestCase):
    """Test dice rolling functionality."""

    def test_roll_simple_d20(self):
        """Test rolling a simple d20."""
        result, breakdown = DiceRoller.roll("1d20")
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 20)
        self.assertIn("1d20", breakdown)

    def test_roll_multiple_dice(self):
        """Test rolling multiple dice."""
        result, breakdown = DiceRoller.roll("2d6")
        self.assertGreaterEqual(result, 2)
        self.assertLessEqual(result, 12)
        self.assertIn("2d6", breakdown)

    def test_roll_with_modifier(self):
        """Test rolling dice with modifier."""
        result, breakdown = DiceRoller.roll("1d20+5")
        self.assertGreaterEqual(result, 6)
        self.assertLessEqual(result, 25)
        self.assertIn("+5", breakdown)

    def test_roll_with_negative_modifier(self):
        """Test rolling dice with negative modifier."""
        result, breakdown = DiceRoller.roll("1d20-2")
        self.assertGreaterEqual(result, -1)
        self.assertLessEqual(result, 18)
        self.assertIn("-2", breakdown)

    def test_roll_d4_shorthand(self):
        """Test rolling d4 (without number prefix)."""
        result, breakdown = DiceRoller.roll("d4")
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 4)

    def test_invalid_expression(self):
        """Test invalid dice expression."""
        with self.assertRaises(ValueError):
            DiceRoller.roll("invalid")

    def test_roll_d20_method(self):
        """Test the roll_d20 convenience method."""
        result = DiceRoller.roll_d20()
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 20)


class TestShadowdarkRules(unittest.TestCase):
    """Test Shadowdark RPG rule calculations."""

    def test_ability_check_success(self):
        """Test successful ability check."""
        success, result = ShadowdarkRules.ability_check(
            roll=15, ability_modifier=3, dc=15
        )
        self.assertTrue(success)
        self.assertIn("Success", result)

    def test_ability_check_failure(self):
        """Test failed ability check."""
        success, result = ShadowdarkRules.ability_check(
            roll=5, ability_modifier=1, dc=15
        )
        self.assertFalse(success)
        self.assertIn("Failure", result)

    def test_attack_roll_hit(self):
        """Test successful attack roll."""
        hit, result = ShadowdarkRules.attack_roll(
            roll=18, attack_modifier=5, target_ac=20
        )
        self.assertTrue(hit)
        self.assertIn("HIT", result)

    def test_attack_roll_miss(self):
        """Test missed attack roll."""
        hit, result = ShadowdarkRules.attack_roll(
            roll=10, attack_modifier=2, target_ac=15
        )
        self.assertFalse(hit)
        self.assertIn("MISS", result)

    def test_saving_throw_success(self):
        """Test successful saving throw."""
        success, result = ShadowdarkRules.saving_throw(roll=12, save_modifier=4, dc=15)
        self.assertTrue(success)
        self.assertIn("Success", result)

    def test_saving_throw_failure(self):
        """Test failed saving throw."""
        success, result = ShadowdarkRules.saving_throw(roll=8, save_modifier=1, dc=15)
        self.assertFalse(success)
        self.assertIn("Failure", result)


class TestCombatTracker(unittest.TestCase):
    """Test combat tracking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = CombatTracker()

    def test_start_combat(self):
        """Test starting combat."""
        result = self.tracker.start_combat()
        self.assertTrue(self.tracker.is_in_combat())
        self.assertIn("Combat started", result)

    def test_end_combat(self):
        """Test ending combat."""
        self.tracker.start_combat()
        result = self.tracker.end_combat()
        self.assertFalse(self.tracker.is_in_combat())
        self.assertIn("Combat ended", result)

    def test_add_initiative(self):
        """Test adding initiative."""
        self.tracker.start_combat()
        result = self.tracker.add_initiative("Player1", roll=15, dex_modifier=2)
        self.assertIn("Player1", result)
        self.assertIn("17", result)  # 15 + 2 = 17

    def test_set_hp(self):
        """Test setting HP."""
        self.tracker.start_combat()
        result = self.tracker.set_hp("Goblin", hp=10, max_hp=15)
        self.assertIn("Goblin", result)
        self.assertIn("10/15", result)

    def test_apply_damage(self):
        """Test applying damage."""
        self.tracker.start_combat()
        self.tracker.set_hp("Goblin", hp=10, max_hp=10)
        result = self.tracker.apply_damage("Goblin", 3)
        self.assertIn("takes 3 damage", result)
        self.assertIn("7/10", result)

    def test_apply_damage_death(self):
        """Test applying lethal damage."""
        self.tracker.start_combat()
        self.tracker.set_hp("Goblin", hp=5, max_hp=10)
        result = self.tracker.apply_damage("Goblin", 10)
        self.assertIn("DEAD", result)

    def test_set_ac(self):
        """Test setting AC."""
        self.tracker.start_combat()
        result = self.tracker.set_ac("Goblin", 15)
        self.assertIn("Goblin", result)
        self.assertIn("AC 15", result)

    def test_get_ac(self):
        """Test getting AC."""
        self.tracker.start_combat()
        self.tracker.set_ac("Goblin", 15)
        ac = self.tracker.get_ac("Goblin")
        self.assertEqual(ac, 15)

    def test_combat_status(self):
        """Test getting combat status."""
        self.tracker.start_combat()
        self.tracker.add_initiative("Player1", roll=15, dex_modifier=2)
        self.tracker.set_hp("Player1", hp=20, max_hp=20)
        self.tracker.set_ac("Player1", 16)
        status = self.tracker.get_status()
        self.assertIn("Combat Status", status)
        self.assertIn("Player1", status)

    def test_turn_order(self):
        """Test turn order based on initiative."""
        self.tracker.start_combat()
        self.tracker.add_initiative("Player1", roll=10, dex_modifier=2)  # 12
        self.tracker.add_initiative("Goblin", roll=15, dex_modifier=0)  # 15
        status = self.tracker.get_status()
        # Goblin should come first (higher initiative)
        self.assertLess(status.find("Goblin"), status.find("Player1"))


class TestSpellManager(unittest.TestCase):
    """Test spell management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = SpellManager()
        # Register a test spell
        self.test_spell = Spell(name="Magic Missile", level=1)
        self.manager.register_spell(self.test_spell)

    def test_register_spell(self):
        """Test registering a spell."""
        spell = Spell(name="Fireball", level=3)
        self.manager.register_spell(spell)
        # Should not raise an exception

    def test_set_spell_slots(self):
        """Test setting spell slots."""
        result = self.manager.set_spell_slots("Wizard", level=1, slots=3)
        self.assertIn("Wizard", result)
        self.assertIn("3", result)

    def test_cast_spell_success(self):
        """Test successfully casting a spell."""
        self.manager.set_spell_slots("Wizard", level=1, slots=3)
        result = self.manager.cast_spell("Wizard", "Magic Missile")
        self.assertIn("casts Magic Missile", result)
        self.assertIn("2 remaining", result)  # 3 - 1 = 2

    def test_cast_spell_no_slots(self):
        """Test casting spell without slots."""
        result = self.manager.cast_spell("Wizard", "Magic Missile")
        self.assertIn("no level 1 spell slots", result)

    def test_cast_spell_not_found(self):
        """Test casting unknown spell."""
        self.manager.set_spell_slots("Wizard", level=1, slots=3)
        result = self.manager.cast_spell("Wizard", "Unknown Spell")
        self.assertIn("not found", result)

    def test_get_spell_slots(self):
        """Test getting spell slots."""
        self.manager.set_spell_slots("Wizard", level=1, slots=3)
        self.manager.set_spell_slots("Wizard", level=2, slots=2)
        result = self.manager.get_spell_slots("Wizard")
        self.assertIn("Wizard's Spell Slots", result)
        self.assertIn("Level 1: 3", result)
        self.assertIn("Level 2: 2", result)


if __name__ == "__main__":
    unittest.main()
