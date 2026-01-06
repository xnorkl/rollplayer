"""Discord pagination system."""

import discord
from discord.ui import Button, View


class PaginatedView(View):
    """Paginated view for long embeds."""

    def __init__(self, pages: list[discord.Embed], timeout: int = 300):
        """
        Initialize paginated view.

        Args:
            pages: List of embeds (pages)
            timeout: View timeout in seconds
        """
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: Button) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button) -> None:
        """Go to next page."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()
