"""Command parser for GM chatbot commands."""

import re
from typing import Optional, Tuple, Union

from game_engine import DiceRoller, ShadowdarkRules, _combat_tracker, _spell_manager
from shadowdark_rules import normalize_ability_name, DC_NORMAL
from chat_bot import BotResponse


class CommandParser:
    """Parses and executes game commands."""

    def __init__(self):
        self.dice_roller = DiceRoller()
        self.rules = ShadowdarkRules()

    def parse(
        self, 
        command: str, 
        character_id: Optional[str] = None,
        roll_data: Optional[dict] = None
    ) -> Optional[Union[str, BotResponse]]:
        """
        Parse and execute a command.

        Args:
            command: Command string (without the '!' prefix)
            character_id: Character ID from Roll20 (e.g., "char:abc123")
            roll_data: Pre-rolled dice data from Roll20 (if available)

        Returns:
            Response string, BotResponse, or None if command not recognized
        """
        command = command.strip()
        if not command:
            return None

        parts = command.split()
        if not parts:
            return None

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Route to appropriate handler
        if cmd == "roll":
            return self._handle_roll(args, roll_data)
        elif cmd == "check":
            return self._handle_check(args, character_id, roll_data)
        elif cmd == "attack":
            return self._handle_attack(args, character_id, roll_data)
        elif cmd == "damage":
            return self._handle_damage(args, roll_data)
        elif cmd == "initiative":
            return self._handle_initiative(args, roll_data)
        elif cmd == "spell":
            return self._handle_spell(args)
        elif cmd == "combat":
            return self._handle_combat(args)
        elif cmd == "hp":
            return self._handle_hp(args)
        elif cmd == "ac":
            return self._handle_ac(args)
        elif cmd == "help":
            return self._handle_help()
        else:
            return None

    def _handle_roll(self, args: list, roll_data: Optional[dict] = None) -> Union[str, BotResponse]:
        """Handle !roll command."""
        if not args:
            return "Usage: !roll <dice_expression> (e.g., !roll 2d6+3)"

        expression = "".join(args)
        
        # If we have pre-rolled data from Roll20, use it
        if roll_data and roll_data.get("expr") == expression:
            # Extract dice expression and modifier
            dice_expr = roll_data.get("expr", expression)
            modifier = roll_data.get("modifier", 0)
            
            return BotResponse(
                type="rollresult",
                content="",  # Content handled by Roll20
                metadata={
                    "dice": dice_expr,
                    "modifier": modifier,
                    "description": f"Roll: {dice_expr}"
                }
            )
        
        # Otherwise, return roll instruction for Roll20 to execute
        try:
            # Parse expression to extract dice and modifier
            match = re.match(r"(\d*)d(\d+)([+-]\d+)?", expression.lower().replace(" ", ""))
            if match:
                dice_expr = f"{match.group(1) or '1'}d{match.group(2)}"
                modifier = int(match.group(3)) if match.group(3) else 0
                
                return BotResponse(
                    type="rollresult",
                    content="",
                    metadata={
                        "dice": dice_expr,
                        "modifier": modifier,
                        "description": f"Roll: {expression}"
                    }
                )
            else:
                return f"Error: Invalid dice expression: {expression}"
        except Exception as e:
            return f"Error: {e}"

    def _handle_check(
        self, 
        args: list, 
        character_id: Optional[str] = None,
        roll_data: Optional[dict] = None
    ) -> Union[str, BotResponse]:
        """Handle !check command."""
        if not args:
            return "Usage: !check <ability> [DC] (e.g., !check strength 15)"

        ability_name = normalize_ability_name(args[0])
        dc = int(args[1]) if len(args) > 1 else DC_NORMAL

        # Get ability modifier from character sheet if available
        # Note: character_id lookup would need to be done in the API script
        # For now, we'll return a roll instruction and let the API script
        # look up the modifier and apply it
        
        # If we have a pre-rolled d20, use it
        if roll_data and roll_data.get("dice") and len(roll_data.get("dice", [])) == 1:
            roll = roll_data["dice"][0]
            # Ability modifier should be looked up by API script
            # For now, return instruction to roll with modifier lookup needed
            return BotResponse(
                type="rollresult",
                content="",
                metadata={
                    "dice": "1d20",
                    "modifier": 0,  # Will be looked up by API script
                    "description": f"{ability_name.capitalize()} Check (DC {dc})",
                    "ability": ability_name,
                    "dc": dc,
                    "character_id": character_id
                }
            )
        
        # Return roll instruction
        return BotResponse(
            type="rollresult",
            content="",
            metadata={
                "dice": "1d20",
                "modifier": 0,  # Will be looked up by API script
                "description": f"{ability_name.capitalize()} Check (DC {dc})",
                "ability": ability_name,
                "dc": dc,
                "character_id": character_id
            }
        )

    def _handle_attack(
        self, 
        args: list, 
        character_id: Optional[str] = None,
        roll_data: Optional[dict] = None
    ) -> Union[str, BotResponse]:
        """Handle !attack command."""
        if not args:
            return "Usage: !attack <target> [modifier] (e.g., !attack goblin +5)"

        target = args[0]
        modifier = int(args[1]) if len(args) > 1 else 0

        # Get target AC from combat tracker
        target_ac = 10  # Default
        if _combat_tracker.is_in_combat():
            ac = _combat_tracker.get_ac(target)
            if ac is not None:
                target_ac = ac

        # Return roll instruction (modifier can be enhanced with character sheet lookup)
        return BotResponse(
            type="rollresult",
            content="",
            metadata={
                "dice": "1d20",
                "modifier": modifier,
                "description": f"Attack vs {target} (AC {target_ac})",
                "target": target,
                "target_ac": target_ac,
                "character_id": character_id
            }
        )

    def _handle_damage(self, args: list, roll_data: Optional[dict] = None) -> Union[str, BotResponse]:
        """Handle !damage command."""
        if len(args) < 2:
            return (
                "Usage: !damage <target> <dice_expression> (e.g., !damage goblin 2d6)"
            )

        target = args[0]
        expression = "".join(args[1:])

        # Parse expression to extract dice and modifier
        match = re.match(r"(\d*)d(\d+)([+-]\d+)?", expression.lower().replace(" ", ""))
        if not match:
            return f"Error: Invalid dice expression: {expression}"
        
        dice_expr = f"{match.group(1) or '1'}d{match.group(2)}"
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # If we have pre-rolled data, use it for damage calculation
        if roll_data and roll_data.get("expr") == expression:
            damage = roll_data.get("total", 0)
            if _combat_tracker.is_in_combat():
                result = _combat_tracker.apply_damage(target, damage)
                return f"💥 {result}"
            else:
                return f"💥 {target} takes {damage} damage"
        
        # Return roll instruction
        return BotResponse(
            type="rollresult",
            content="",
            metadata={
                "dice": dice_expr,
                "modifier": modifier,
                "description": f"Damage to {target}",
                "target": target,
                "apply_damage": True
            }
        )

    def _handle_initiative(self, args: list, roll_data: Optional[dict] = None) -> Union[str, BotResponse]:
        """Handle !initiative command."""
        if not args:
            return "Usage: !initiative <name> [dex_modifier] (e.g., !initiative player1 +2)"

        name = args[0]
        dex_mod = int(args[1]) if len(args) > 1 else 0

        # If we have a pre-rolled d20, use it
        if roll_data and roll_data.get("dice") and len(roll_data.get("dice", [])) == 1:
            roll = roll_data["dice"][0]
            return _combat_tracker.add_initiative(name, roll, dex_mod)
        
        # Return roll instruction
        return BotResponse(
            type="rollresult",
            content="",
            metadata={
                "dice": "1d20",
                "modifier": dex_mod,
                "description": f"Initiative for {name}",
                "name": name,
                "initiative": True
            }
        )

    def _handle_spell(self, args: list) -> str:
        """Handle !spell command."""
        if not args:
            return "Usage: !spell <spell_name> [target] (e.g., !spell magic_missile goblin)"

        spell_name = args[0]
        target = args[1] if len(args) > 1 else None

        # For now, use sender name as caster (could be enhanced)
        caster = "Player"
        return _spell_manager.cast_spell(caster, spell_name, target)

    def _handle_combat(self, args: list) -> str:
        """Handle !combat command."""
        if not args:
            return "Usage: !combat <start|end|status|next>"

        subcmd = args[0].lower()

        if subcmd == "start":
            return _combat_tracker.start_combat()
        elif subcmd == "end":
            return _combat_tracker.end_combat()
        elif subcmd == "status":
            return _combat_tracker.get_status()
        elif subcmd == "next":
            return _combat_tracker.next_turn()
        else:
            return f"Unknown combat command: {subcmd}. Use: start, end, status, or next"

    def _handle_hp(self, args: list) -> str:
        """Handle !hp command."""
        if len(args) < 2:
            return "Usage: !hp <target> <value> [max] (e.g., !hp goblin 10 15)"

        target = args[0]
        try:
            hp = int(args[1])
            max_hp = int(args[2]) if len(args) > 2 else None
            return _combat_tracker.set_hp(target, hp, max_hp)
        except ValueError:
            return "Error: HP values must be numbers"

    def _handle_ac(self, args: list) -> str:
        """Handle !ac command."""
        if len(args) < 2:
            return "Usage: !ac <target> <value> (e.g., !ac goblin 15)"

        target = args[0]
        try:
            ac = int(args[1])
            return _combat_tracker.set_ac(target, ac)
        except ValueError:
            return "Error: AC must be a number"

    def _handle_help(self) -> str:
        """Handle !help command."""
        return """🎮 GM Chatbot Commands:
        
**Dice & Rolls:**
  !roll <expression> - Roll dice (e.g., !roll 2d6+3)
  !check <ability> [DC] - Ability check (e.g., !check strength 15)
  !attack <target> [mod] - Attack roll (e.g., !attack goblin +5)
  !damage <target> <expression> - Apply damage (e.g., !damage goblin 2d6)

**Combat:**
  !combat start - Start combat tracking
  !combat end - End combat
  !combat status - Show combat status
  !combat next - Advance to next turn
  !initiative <name> [dex_mod] - Roll initiative
  !hp <target> <value> [max] - Set HP
  !ac <target> <value> - Set AC

**Spells:**
  !spell <spell_name> [target] - Cast spell

**Help:**
  !help - Show this help message

Ask questions in plain English for rule clarifications!"""
