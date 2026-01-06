"""Discord interactive components."""

import discord
from discord.ui import Button, Select, Modal, TextInput


class CharacterSheetView(discord.ui.View):
    """View for character sheet interactions."""

    def __init__(self):
        """Initialize character sheet view."""
        super().__init__(timeout=300)  # 5 minute timeout

    @discord.ui.button(label="View Details", style=discord.ButtonStyle.primary)
    async def view_details(self, interaction: discord.Interaction, button: Button) -> None:
        """View character details."""
        await interaction.response.send_message("Character details will be shown here.", ephemeral=True)
