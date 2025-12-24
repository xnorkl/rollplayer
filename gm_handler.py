"""Main GM handler that coordinates command parsing, game engine, and AI."""
from typing import Optional

from command_parser import CommandParser
from ai_handler import AIHandler


class GMHandler:
    """Main handler for GM chatbot functionality."""
    
    def __init__(self):
        self.command_parser = CommandParser()
        self.ai_handler = AIHandler()
    
    def handle_message(self, message: str) -> Optional[str]:
        """
        Handle an incoming chat message.
        
        Args:
            message: Chat message text
            
        Returns:
            Response string or None if no response needed
        """
        message = message.strip()
        if not message:
            return None
        
        # Check if it's a command (starts with !)
        if message.startswith("!"):
            command = message[1:]  # Remove the !
            response = self.command_parser.parse(command)
            return response
        
        # Check if it's a question (for AI handler)
        elif self.ai_handler.is_question(message):
            if self.ai_handler.is_available():
                response = self.ai_handler.query_rules(message)
                return f"📚 {response}"
            else:
                return "AI features are not available. Use !help for command reference."
        
        # Otherwise, ignore the message
        return None

