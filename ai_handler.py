"""AI handler for natural language rule queries."""
import os
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE


# Shadowdark RPG rule context for the AI
SHADOWDARK_RULES_CONTEXT = """
Shadowdark RPG is a streamlined fantasy roleplaying game. Key rules:

**Ability Scores & Modifiers:**
- Ability scores range from 1-20
- Modifiers: 1-2: -5, 3-4: -4, 5-6: -3, 7-8: -2, 9-10: -1, 11-12: +0, 13-14: +1, 15-16: +2, 17-18: +3, 19-20: +4

**Difficulty Classes (DC):**
- Easy: 5
- Normal: 10
- Hard: 15
- Very Hard: 20

**Ability Checks:**
- Roll d20 + ability modifier
- Compare total to DC
- Meet or exceed DC to succeed

**Combat:**
- Initiative: Roll d20 + Dexterity modifier (higher goes first)
- Attack: Roll d20 + attack modifier vs target's Armor Class (AC)
- Damage: Roll weapon/spell damage dice
- Armor Class (AC) typically ranges from 10-20

**Saving Throws:**
- Roll d20 + save modifier vs DC
- Used to resist spells, traps, and other effects

**Spellcasting:**
- Characters have spell slots by level
- Casting time is usually 1 action
- Spells may require concentration
- Spell effects vary by spell

**Conditions:**
Common conditions include: blinded, charmed, deafened, frightened, grappled, incapacitated, invisible, paralyzed, petrified, poisoned, prone, restrained, stunned, unconscious

**General Principles:**
- Fast-paced, rules-light gameplay
- Focus on player creativity and quick decisions
- GM has final say on rule interpretations
"""


class AIHandler:
    """Handles AI-powered rule queries."""
    
    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        self._cache: dict = {}
    
    def is_available(self) -> bool:
        """Check if AI handler is available."""
        return self.client is not None
    
    def query_rules(self, question: str) -> str:
        """
        Query AI for rule clarification.
        
        Args:
            question: Natural language question about Shadowdark rules
            
        Returns:
            Answer string
        """
        if not self.is_available():
            return "AI features are not available. Please set OPENAI_API_KEY environment variable."
        
        # Check cache
        question_lower = question.lower().strip()
        if question_lower in self._cache:
            return self._cache[question_lower]
        
        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful Game Master assistant for Shadowdark RPG. Answer questions about the rules clearly and concisely. Here are the key rules:\n\n{SHADOWDARK_RULES_CONTEXT}\n\nKeep answers brief and focused on the specific question asked."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=300
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Cache the answer
            self._cache[question_lower] = answer
            
            return answer
        except Exception as e:
            return f"Error querying AI: {str(e)}"
    
    def is_question(self, text: str) -> bool:
        """
        Determine if text looks like a question.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be a question
        """
        text = text.strip()
        if not text:
            return False
        
        # Check for question marks
        if text.endswith("?"):
            return True
        
        # Check for question words at start
        question_words = ["what", "how", "when", "where", "why", "who", "which", "can", "could", "should", "would", "is", "are", "does", "do", "did"]
        first_word = text.split()[0].lower() if text.split() else ""
        if first_word in question_words:
            return True
        
        return False

