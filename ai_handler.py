"""AI handler for natural language rule queries."""

import json
import logging
import os
import sys
from typing import Optional

LOG = logging.getLogger(__name__)

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    LLM_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    LLM_TEMPERATURE,
)


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
        self.provider = AI_PROVIDER.lower()
        self.client = None

        if self.provider == "openai":
            if OPENAI_AVAILABLE and OPENAI_API_KEY:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == "claude":
            if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

        self._cache: dict = {}

    def is_available(self) -> bool:
        """Check if AI handler is available."""
        if self.provider == "openai":
            return self.client is not None and OPENAI_API_KEY is not None
        elif self.provider == "claude":
            return self.client is not None and ANTHROPIC_API_KEY is not None
        return False

    def query_rules(self, question: str) -> str:
        """
        Query AI for rule clarification.

        Args:
            question: Natural language question about Shadowdark rules

        Returns:
            Answer string
        """
        # #region agent log
        try:
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "location": "ai_handler.py:99",
                "message": "query_rules entry",
                "data": {
                    "provider": self.provider,
                    "hasClient": self.client is not None,
                    "isAvailable": self.is_available(),
                    "questionLength": len(question),
                    "model": (
                        LLM_MODEL if self.provider == "openai" else ANTHROPIC_MODEL
                    ),
                    "hasOpenAIKey": (
                        OPENAI_API_KEY is not None and len(OPENAI_API_KEY) > 0
                        if OPENAI_API_KEY
                        else False
                    ),
                    "hasAnthropicKey": (
                        ANTHROPIC_API_KEY is not None and len(ANTHROPIC_API_KEY) > 0
                        if ANTHROPIC_API_KEY
                        else False
                    ),
                },
                "timestamp": int(__import__("time").time() * 1000),
                "hypothesisId": "A",
            }
            with open(
                "/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log",
                "a",
            ) as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        if not self.is_available():
            if self.provider == "openai":
                return "AI features are not available. Please set OPENAI_API_KEY environment variable."
            elif self.provider == "claude":
                return "AI features are not available. Please set ANTHROPIC_API_KEY environment variable."
            else:
                return (
                    f"AI features are not available. Invalid provider: {self.provider}"
                )

        # Check cache
        question_lower = question.lower().strip()
        if question_lower in self._cache:
            return self._cache[question_lower]

        # #region agent log
        try:
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "location": "ai_handler.py:122",
                "message": "Before API call",
                "data": {
                    "provider": self.provider,
                    "model": (
                        LLM_MODEL if self.provider == "openai" else ANTHROPIC_MODEL
                    ),
                    "temperature": LLM_TEMPERATURE,
                },
                "timestamp": int(__import__("time").time() * 1000),
                "hypothesisId": "B",
            }
            log_json = json.dumps(log_data)
            try:
                with open(
                    "/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log",
                    "a",
                ) as f:
                    f.write(log_json + "\n")
            except:
                pass
            LOG.info(f"[DEBUG] {log_json}")
        except:
            pass
        # #endregion
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a helpful Game Master assistant for Shadowdark RPG. Answer questions about the rules clearly and concisely. Here are the key rules:\n\n{SHADOWDARK_RULES_CONTEXT}\n\nKeep answers brief and focused on the specific question asked.",
                        },
                        {"role": "user", "content": question},
                    ],
                    temperature=LLM_TEMPERATURE,
                    max_tokens=300,
                )
                answer = response.choices[0].message.content.strip()
            elif self.provider == "claude":
                response = self.client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=300,
                    temperature=LLM_TEMPERATURE,
                    system=f"You are a helpful Game Master assistant for Shadowdark RPG. Answer questions about the rules clearly and concisely. Here are the key rules:\n\n{SHADOWDARK_RULES_CONTEXT}\n\nKeep answers brief and focused on the specific question asked.",
                    messages=[
                        {"role": "user", "content": question},
                    ],
                )
                answer = response.content[0].text.strip()
            else:
                return f"Unsupported AI provider: {self.provider}"

            # Cache the answer
            self._cache[question_lower] = answer

            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "location": "ai_handler.py:154",
                    "message": "API call success",
                    "data": {"answerLength": len(answer)},
                    "timestamp": int(__import__("time").time() * 1000),
                    "hypothesisId": "C",
                }
                log_json = json.dumps(log_data)
                try:
                    with open(
                        "/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log",
                        "a",
                    ) as f:
                        f.write(log_json + "\n")
                except:
                    pass
                LOG.info(f"[DEBUG] {log_json}")
            except:
                pass
            # #endregion
            return answer
        except Exception as e:
            # #region agent log
            try:
                error_type = type(e).__name__
                error_str = str(e)
                error_repr = repr(e)
                error_args = str(e.args) if hasattr(e, "args") else None
                error_attrs = {}
                if hasattr(e, "status_code"):
                    error_attrs["status_code"] = e.status_code
                if hasattr(e, "response"):
                    try:
                        error_attrs["response"] = str(e.response)[:200]
                    except:
                        pass
                if hasattr(e, "body"):
                    try:
                        error_attrs["body"] = str(e.body)[:200]
                    except:
                        pass
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "location": "ai_handler.py:155",
                    "message": "API call exception",
                    "data": {
                        "errorType": error_type,
                        "errorStr": error_str,
                        "errorStrFull": error_str[:500],
                        "errorRepr": error_repr[:500],
                        "errorArgs": error_args,
                        "errorAttrs": error_attrs,
                        "provider": self.provider,
                        "model": (
                            LLM_MODEL if self.provider == "openai" else ANTHROPIC_MODEL
                        ),
                    },
                    "timestamp": int(__import__("time").time() * 1000),
                    "hypothesisId": "D",
                }
                log_json = json.dumps(log_data)
                try:
                    with open(
                        "/Users/thomasgordon/Engagements/Etc/roll20_chatbot/.cursor/debug.log",
                        "a",
                    ) as f:
                        f.write(log_json + "\n")
                except:
                    pass
                LOG.error(f"[DEBUG] {log_json}")
            except:
                pass
            # #endregion
            error_str = str(e)

            # Try to extract the actual error message from the API response
            api_error_message = None
            try:
                # For Anthropic errors, the message is nested in the error dict
                if "'message':" in error_str:
                    import re

                    # Extract message from pattern like: 'message': 'Your credit balance...'
                    match = re.search(r"'message':\s*'([^']+)'", error_str)
                    if match:
                        api_error_message = match.group(1)
                # For OpenAI errors, check if there's a response body
                if hasattr(e, "response") and hasattr(e.response, "json"):
                    try:
                        error_body = e.response.json()
                        if isinstance(error_body, dict):
                            if "error" in error_body and isinstance(
                                error_body["error"], dict
                            ):
                                api_error_message = error_body["error"].get("message")
                            elif "message" in error_body:
                                api_error_message = error_body["message"]
                    except:
                        pass
            except:
                pass

            # Use extracted message if available, otherwise use the string representation
            display_message = api_error_message if api_error_message else error_str

            # Provide user-friendly error messages for both providers
            error_lower = display_message.lower()

            # Check for credit balance issues
            if (
                "credit balance" in error_lower
                or "credit" in error_lower
                and ("low" in error_lower or "insufficient" in error_lower)
            ):
                if self.provider == "openai":
                    return "AI service error: Your OpenAI account has insufficient credits. Please add credits to your account to continue using AI features."
                else:
                    return "AI service error: Your Anthropic account has insufficient credits. Please go to Plans & Billing to upgrade or purchase credits."
            # Check for rate limits and quota
            elif (
                "429" in error_str
                or "insufficient_quota" in error_lower
                or "rate_limit" in error_lower
                or "quota" in error_lower
            ):
                if self.provider == "openai":
                    return "AI service quota exceeded. Please check your OpenAI account billing."
                else:
                    return "AI service quota exceeded. Please check your Anthropic account billing."
            # Check for authentication errors
            elif (
                "401" in error_str
                or "invalid_api_key" in error_lower
                or "authentication" in error_lower
                or "unauthorized" in error_lower
            ):
                if self.provider == "openai":
                    return "AI service authentication failed. Please check your OpenAI API key."
                else:
                    return "AI service authentication failed. Please check your Anthropic API key."
            # For other errors, show the extracted message or a reasonable portion
            else:
                if api_error_message:
                    return f"AI service error: {api_error_message}"
                else:
                    # Show more of the error (up to 200 chars) if we couldn't extract a message
                    return f"AI service error: {error_str[:200]}"

    def is_question(self, text: str) -> bool:
        """
        Determine if text looks like a question or request for information.

        Args:
            text: Text to check

        Returns:
            True if text appears to be a question or information request
        """
        text = text.strip()
        if not text:
            return False

        # Check for question marks
        if text.endswith("?"):
            return True

        # Check for question words at start
        question_words = [
            "what",
            "how",
            "when",
            "where",
            "why",
            "who",
            "which",
            "can",
            "could",
            "should",
            "would",
            "will",
            "is",
            "are",
            "does",
            "do",
            "did",
            "was",
            "were",
            "explain",
            "describe",
            "tell",
            "show",
            "help",
        ]
        first_word = text.split()[0].lower() if text.split() else ""
        if first_word in question_words:
            return True

        # Check for question-like patterns (imperative requests for information)
        question_patterns = [
            "explain",
            "describe",
            "tell me",
            "what is",
            "what are",
            "how does",
            "how do",
            "help with",
            "help me",
        ]
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in question_patterns):
            return True

        return False
