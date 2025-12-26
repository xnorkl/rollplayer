# Using the Roll20 Shadowdark RPG Chatbot

## Introduction

The Roll20 Shadowdark RPG Chatbot is a Game Master assistant that helps manage your Shadowdark RPG sessions on Roll20. It can roll dice, track combat, handle ability checks, manage spells, and answer questions about Shadowdark RPG rules using natural language.

**Key Features:**
- 🎲 Dice rolling with any expression
- ⚔️ Combat tracking (initiative, HP, AC, turn order)
- 📋 Ability checks and attack rolls
- ✨ Spell casting and slot management
- 📚 AI-powered rule clarifications

All commands start with `!` (exclamation mark), or you can ask questions in plain English about the rules.

## Quick Start

1. **Setup** (one-time): Your GM will set up the chatbot. See the [README.md](README.md) for technical setup details.

2. **Using the Chatbot**: Once set up, simply type commands or questions in the Roll20 chat window. The chatbot will automatically respond.

3. **Get Help**: Type `!help` at any time to see all available commands.

## Basic Commands

### Dice Rolling

Roll any dice expression:

```
!roll 2d6+3
!roll 1d20
!roll 3d8-1
!roll d4
```

The bot will show you the individual dice results and the total.

### Ability Checks

Make an ability check against a difficulty class (DC):

```
!check strength 15
!check dex 10
!check wisdom
!check charisma 20
```

- If you don't specify a DC, it defaults to 10 (Normal difficulty)
- You can use full ability names (strength, dexterity) or abbreviations (str, dex)
- The bot rolls a d20 and adds your ability modifier

**DC Reference:**
- Easy: 5
- Normal: 10
- Hard: 15
- Very Hard: 20

### Attack Rolls

Roll an attack against a target:

```
!attack goblin +5
!attack orc +3
!attack dragon
```

- Specify the target name
- Optionally include your attack modifier (defaults to +0)
- The bot checks against the target's AC if they're in combat

### Apply Damage

Apply damage to a target:

```
!damage goblin 2d6
!damage orc 1d8+3
!damage player 5
```

- The bot rolls the damage dice and applies it to the target
- If the target is in combat, their HP is automatically updated

### Help

Get a quick reference of all commands:

```
!help
```

## Combat Commands

### Starting Combat

Begin tracking a combat encounter:

```
!combat start
```

This initializes the combat tracker. You'll need to add participants with initiative rolls.

### Rolling Initiative

Add a participant to combat and roll their initiative:

```
!initiative player1 +2
!initiative goblin -1
!initiative wizard
```

- Specify the participant's name
- Optionally include their Dexterity modifier (defaults to +0)
- Participants are automatically sorted by initiative (highest first)

### Combat Status

View the current state of combat:

```
!combat status
```

Shows:
- All participants with their initiative, HP, and AC
- Current turn order
- Who's turn it is now

### Next Turn

Advance to the next turn in initiative order:

```
!combat next
```

### Setting HP and AC

Set or update a participant's hit points and armor class:

```
!hp goblin 10 15
!hp player1 25
!ac goblin 15
!ac player1 18
```

- `!hp <name> <current> [max]` - Set current HP, optionally set max HP
- `!ac <name> <value>` - Set armor class

### Ending Combat

End the current combat encounter:

```
!combat end
```

This clears all combat participants and turn tracking.

## Spell Commands

### Casting Spells

Cast a spell:

```
!spell magic_missile goblin
!spell cure_wounds player1
!spell fireball
```

- Specify the spell name (use underscores for multi-word spells)
- Optionally specify a target
- The bot tracks spell slot usage (your GM manages spell slots)

**Note:** Spell slot tracking is managed by your GM. If you get an error about spell slots, ask your GM to set them up.

## Natural Language Queries

You can ask questions about Shadowdark RPG rules in plain English! Just type your question in the chat (no `!` needed).

**Examples:**

- "What's the DC for a hard check?"
- "How does initiative work in Shadowdark?"
- "What are the ability modifiers?"
- "How do spell slots work?"
- "What's the difference between an ability check and a saving throw?"
- "What conditions can affect a character?"

The AI will provide answers based on Shadowdark RPG rules. **Note:** AI features require your GM to have set up an OpenAI API key.

## Examples

### Example 1: Starting a Combat Encounter

```
GM: Combat begins! Roll initiative.
Player1: !initiative player1 +2
Chatbot: player1: Initiative 18 (d20: 16, Dex mod: +2)
Player2: !initiative player2 -1
Chatbot: player2: Initiative 12 (d20: 13, Dex mod: -1)
GM: !initiative goblin +1
Chatbot: goblin: Initiative 15 (d20: 14, Dex mod: +1)
GM: !combat status
Chatbot: === Combat Status ===
player1: Initiative 18, HP 0, AC 10
goblin: Initiative 15, HP 0, AC 10
player2: Initiative 12, HP 0, AC 10

Current turn: player1
```

### Example 2: Making Ability Checks During Exploration

```
Player: I want to check for traps on the door.
Player: !check wisdom 15
Chatbot: 📋 Wisdom Check: Success: 17 (d20: 15, mod: +2) vs DC 15
GM: You notice a pressure plate just before the door...
```

### Example 3: Combat Turn Sequence

```
GM: !combat next
Chatbot: Turn: goblin
Player1: I attack the goblin!
Player1: !attack goblin +5
Chatbot: ⚔️ Attack vs goblin: HIT: 18 (d20: 13, mod: +5) vs AC 15
Player1: !damage goblin 1d8+3
Chatbot: 💥 goblin takes 8 damage. HP: 2/10 (1d8+3 = [5] +3 = 8)
GM: !combat next
Chatbot: Turn: player2
```

### Example 4: Asking Rule Questions

```
Player: How does advantage work in Shadowdark?
Chatbot: 📚 In Shadowdark RPG, there isn't a formal "advantage" mechanic like in D&D 5e. Instead, the GM may grant bonuses to rolls or lower the DC based on circumstances. The GM has discretion to adjust difficulty based on player creativity and situation.
```

## Troubleshooting

### Commands Don't Work

- **Check the command syntax**: Make sure you're using `!` at the start of commands
- **Verify connection**: Ask your GM if the chatbot is running and connected
- **Check spelling**: Commands are case-insensitive, but make sure you're using the right command name

### No Response from Chatbot

- The chatbot only responds to:
  - Commands starting with `!`
  - Questions (text ending with `?` or starting with question words)
- Regular chat messages are ignored
- If you're asking a question, make sure it ends with `?` or starts with words like "what", "how", "when", etc.

### AI Questions Not Working

- AI features require your GM to have configured an OpenAI API key
- If you get "AI features are not available", ask your GM to check the setup
- You can still use all the `!` commands even if AI isn't available

### Combat Tracking Issues

- Make sure combat has been started with `!combat start` before using combat commands
- Use `!combat status` to see the current state
- If participants aren't showing up, make sure you've rolled initiative for them

### Need More Help?

- Type `!help` for a quick command reference
- For technical setup issues, see the [README.md](README.md)
- Ask your GM for assistance with game-specific questions

