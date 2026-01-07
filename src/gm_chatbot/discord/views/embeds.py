"""Discord embed builders."""

import discord

from ...models.campaign import Campaign
from ...models.character import CharacterSheet
from ...models.session import Session


def build_campaign_embed(campaign: Campaign) -> discord.Embed:
    """
    Build campaign info embed.

    Args:
        campaign: Campaign instance

    Returns:
        Discord embed
    """
    embed = discord.Embed(
        title=campaign.name,
        description=campaign.description or "No description",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Campaign ID", value=campaign.metadata.id, inline=False)
    embed.add_field(name="System", value=campaign.rule_system, inline=True)
    embed.add_field(name="Status", value=campaign.status, inline=True)
    return embed


def build_character_sheet_embed(character: CharacterSheet) -> discord.Embed:
    """
    Build character sheet embed.

    Args:
        character: CharacterSheet instance

    Returns:
        Discord embed
    """
    embed = discord.Embed(
        title=character.identity.name if character.identity else "Unknown Character",
        color=discord.Color.green(),
    )
    # Add character details
    if character.identity:
        embed.add_field(name="Name", value=character.identity.name, inline=True)
    return embed


def build_session_status_embed(session: Session) -> discord.Embed:
    """
    Build session status embed.

    Args:
        session: Session instance

    Returns:
        Discord embed
    """
    embed = discord.Embed(
        title=f"Session {session.session_number}",
        description=session.name or "No name",
        color=discord.Color.purple(),
    )
    embed.add_field(name="Status", value=session.status, inline=True)
    embed.add_field(
        name="Started",
        value=session.started_at.isoformat() if session.started_at else "Unknown",
        inline=True,
    )
    return embed


def build_dice_roll_embed(roll_result: dict, user: str, reason: str | None = None) -> discord.Embed:
    """
    Build dice roll result embed.

    Args:
        roll_result: Dice roll result dictionary
        user: User who rolled
        reason: Optional reason for roll

    Returns:
        Discord embed
    """
    embed = discord.Embed(
        title="Dice Roll",
        description=f"{user} rolled: {roll_result.get('result', 'N/A')}",
        color=discord.Color.gold(),
    )
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    return embed


def build_error_embed(error_message: str) -> discord.Embed:
    """
    Build error message embed.

    Args:
        error_message: Error message

    Returns:
        Discord embed
    """
    return discord.Embed(
        title="Error",
        description=error_message,
        color=discord.Color.red(),
    )
