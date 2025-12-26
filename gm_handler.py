"""Main GM handler that coordinates command parsing, game engine, and AI."""

from typing import Optional, Union

from command_parser import CommandParser
from ai_handler import AIHandler
from chat_bot import BotResponse, ChatEntry


class GMHandler:
    """Main handler for GM chatbot functionality."""

    def __init__(self):
        self.command_parser = CommandParser()
        self.ai_handler = AIHandler()

    def handle_message(self, chat_entry: Union[str, ChatEntry]) -> Optional[Union[str, BotResponse]]:
        """
        Handle an incoming chat message.

        Args:
            chat_entry: ChatEntry object (new format) or string (old format for backward compatibility)

        Returns:
            Response string, BotResponse, or None if no response needed
        """
        # Backward compatibility: accept string
        if isinstance(chat_entry, str):
            message = chat_entry.strip()
            if not message:
                return None
            
            # Ignore bot's own responses (prevent feedback loops)
            if message.startswith("📚") or message.startswith("Error querying AI"):
                return None

            # Check if it's a command (starts with !)
            if message.startswith("!"):
                command = message[1:]  # Remove the !
                response = self.command_parser.parse(command, character_id=None, roll_data=None)
                # Backward compatibility: return as-is (could be string or BotResponse)
                return response

            # Check if it's a question (for AI handler)
            elif self.ai_handler.is_question(message):
                if self.ai_handler.is_available():
                    response = self.ai_handler.query_rules(message)
                    # Backward compatibility: return plain text
                    return f"📚 {response}"
                else:
                    return "AI features are not available. Use !help for command reference."

            return None
        
        # New format: ChatEntry object
        message = chat_entry.message.strip()
        if not message:
            return None

        # Use message_type for filtering (from Roll20 API)
        msg_type = chat_entry.message_type
        
        # Handle rollresult messages
        if msg_type == "rollresult" and chat_entry.roll_data:
            # Roll results are handled separately - could be used for pending commands
            # For now, just ignore them (they're already rolled in Roll20)
            return None

        # Handle command messages (type "command" or starts with !)
        if msg_type == "command" or message.startswith("!"):
            command = message[1:] if message.startswith("!") else message
            response = self.command_parser.parse(
                command, 
                character_id=chat_entry.characterId,
                roll_data=chat_entry.roll_data
            )
            return response

        # Handle question messages (type "question" or looks like a question)
        if msg_type == "question" or self.ai_handler.is_question(message):
            if self.ai_handler.is_available():
                response = self.ai_handler.query_rules(message)
                # Return BotResponse for structured format, but also support plain text
                return BotResponse(
                    type="text",
                    content=f"📚 {response}",
                    metadata={"who": chat_entry.who, "playerid": chat_entry.playerid}
                )
            else:
                return BotResponse(
                    type="text",
                    content="AI features are not available. Use !help for command reference.",
                    metadata={}
                )

        # Otherwise, ignore the message
        return None
