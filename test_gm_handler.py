"""Smoke tests for GM handler."""

import unittest
from unittest.mock import patch, MagicMock
from gm_handler import GMHandler


class TestGMHandler(unittest.TestCase):
    """Test GM handler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = GMHandler()

    def test_handle_command_roll(self):
        """Test handling roll command."""
        result = self.handler.handle_message("!roll 2d6")
        self.assertIsNotNone(result)
        self.assertIn("2d6", result)

    def test_handle_command_check(self):
        """Test handling check command."""
        result = self.handler.handle_message("!check strength")
        self.assertIsNotNone(result)
        self.assertIn("Strength", result)

    def test_handle_command_help(self):
        """Test handling help command."""
        result = self.handler.handle_message("!help")
        self.assertIsNotNone(result)
        self.assertIn("Commands", result)

    def test_handle_question_without_ai(self):
        """Test handling question when AI is not available."""
        # Mock AI handler to not be available
        with patch.object(self.handler.ai_handler, "is_available", return_value=False):
            result = self.handler.handle_message("What is the DC for a hard check?")
            self.assertIsNotNone(result)
            self.assertIn("not available", result)

    @patch("ai_handler.OpenAI")
    def test_handle_question_with_ai(self, mock_openai):
        """Test handling question when AI is available."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The DC for a hard check is 15."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Create new handler with mocked AI
        with patch("ai_handler.OPENAI_API_KEY", "test-key"):
            handler = GMHandler()
            handler.ai_handler.client = mock_client
            handler.ai_handler._cache = {}

            result = handler.handle_message("What is the DC for a hard check?")
            self.assertIsNotNone(result)
            self.assertIn("DC", result)

    def test_handle_regular_message(self):
        """Test handling regular message (not command or question)."""
        result = self.handler.handle_message("This is a regular message")
        self.assertIsNone(result)

    def test_handle_empty_message(self):
        """Test handling empty message."""
        result = self.handler.handle_message("")
        self.assertIsNone(result)

    def test_handle_whitespace_message(self):
        """Test handling whitespace-only message."""
        result = self.handler.handle_message("   ")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
