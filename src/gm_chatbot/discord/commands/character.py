"""
Character management Discord commands.

This module serves as the PRIMARY ADAPTER for character operations,
translating between Discord interactions and domain services.

Architecture Notes:
- This layer handles Discord-specific concerns (embeds, interactions)
- All business logic delegated to CharacterService
- No direct file I/O; all persistence through services
- Domain models translated to Discord embeds here
"""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


def setup_character_commands(bot: DiscordBot) -> None:
    """
    Register character commands with the Discord bot.

    Args:
        bot: DiscordBot instance with initialized services
    """
    character_group = app_commands.Group(
        name="character",
        description="Character management commands",
    )

    @character_group.command(
        name="create", description="Create a new character in the current campaign"
    )
    @app_commands.describe(name="Character name (1-100 characters)")
    async def create_character(
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        """
        Create a new player character.

        Flow:
        1. Resolve Discord context → domain identifiers
        2. Validate via domain services
        3. Create character via CharacterService
        4. Link to membership via CampaignService
        5. Translate result to Discord embed
        """
        await interaction.response.defer(ephemeral=True)

        try:
            # ─────────────────────────────────────────────────────
            # ADAPTER LAYER: Extract Discord primitives
            # ─────────────────────────────────────────────────────
            name = name.strip()
            if not name or len(name) > 100:
                raise ValueError("Character name must be 1-100 characters")

            if not interaction.guild or not interaction.channel:
                raise ValueError("This command must be used in a server channel")

            # Convert Discord types to domain primitives (strings)
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)
            guild_id = str(interaction.guild.id)
            discord_username = str(interaction.user)
            guild_name = interaction.guild.name

            # ─────────────────────────────────────────────────────
            # SERVICE LAYER: Resolve context
            # ─────────────────────────────────────────────────────
            player = await bot.linking_service.get_player_by_discord_id(user_id)
            if not player:
                # Auto-link new Discord user
                await bot.linking_service.link_discord_user(
                    discord_user_id=user_id,
                    discord_username=discord_username,
                    guild_id=guild_id,
                    guild_name=guild_name,
                )
                player = await bot.linking_service.get_player_by_discord_id(user_id)
                if not player:
                    raise ValueError("Failed to create player account")

            # Resolve campaign from channel binding
            campaign_id = await bot.binding_service.get_campaign_by_channel(channel_id)
            if not campaign_id:
                raise ValueError(
                    "This channel is not bound to a campaign. "
                    "Ask a GM to run `/campaign set-channel` first."
                )

            # ─────────────────────────────────────────────────────
            # SERVICE LAYER: Check membership and auto-join if needed
            # ─────────────────────────────────────────────────────
            membership = await bot.campaign_service.get_membership(
                campaign_id, player.metadata.id
            )
            if not membership:
                # Auto-join user to campaign
                try:
                    membership = await bot.campaign_service.add_player(
                        campaign_id=campaign_id,
                        player_id=player.metadata.id,
                        role="player",
                    )
                    logger.info(
                        f"Auto-joined player {player.metadata.id} to campaign {campaign_id}"
                    )
                except ValueError as e:
                    # Handle edge case (shouldn't happen, but handle gracefully)
                    raise ValueError(f"Failed to join campaign: {e}")

            # Check for existing character (business rule)
            if membership.character_id:
                raise ValueError(
                    "You already have a character in this campaign. "
                    "Use `/character view` to see your character sheet."
                )

            # ─────────────────────────────────────────────────────
            # SERVICE LAYER: Create character (domain operation)
            # ─────────────────────────────────────────────────────
            character = await bot.character_service.create_character(
                campaign_id=campaign_id,
                character_type="player_character",
                name=name,
                identity={"player_name": discord_username},
            )

            # Link character to membership
            await bot.campaign_service.update_membership(
                campaign_id=campaign_id,
                player_id=player.metadata.id,
                character_id=character.metadata.id,
            )

            # ─────────────────────────────────────────────────────
            # ADAPTER LAYER: Translate to Discord embed
            # ─────────────────────────────────────────────────────
            embed = _build_character_created_embed(character)
            await interaction.followup.send(embed=embed, ephemeral=True)

            logger.info(
                f"Character created: {character.identity.name} "
                f"(id={character.metadata.id}) for player {player.metadata.id} "
                f"in campaign {campaign_id}"
            )

        except ValueError as e:
            embed = _build_error_embed("Cannot Create Character", str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

        except FileNotFoundError as e:
            embed = _build_error_embed("Not Found", str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in create_character: {e}", exc_info=True)
            embed = _build_error_embed(
                "Error", "An unexpected error occurred. Please try again later."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @character_group.command(name="view", description="View a character sheet")
    @app_commands.describe(player="Player to view (GMs only, defaults to yourself)")
    async def view_character(
        interaction: discord.Interaction,
        player: discord.Member | None = None,
    ) -> None:
        """
        View a character sheet.

        Players can view their own character.
        GMs can view any player's character.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            if not interaction.guild or not interaction.channel:
                raise ValueError("This command must be used in a server channel")

            channel_id = str(interaction.channel.id)
            user_id = str(interaction.user.id)

            # Resolve campaign from channel
            campaign_id = await bot.binding_service.get_campaign_by_channel(channel_id)
            if not campaign_id:
                raise ValueError("This channel is not bound to a campaign")

            # Resolve requesting player
            requesting_player = await bot.linking_service.get_player_by_discord_id(
                user_id
            )
            if not requesting_player:
                raise ValueError("You don't have a player account")

            # Determine target player and validate permissions
            if player and player.id != interaction.user.id:
                # Viewing another player - require GM role
                from ...lib.types import MembershipRole

                requesting_membership = await bot.campaign_service.get_membership(
                    campaign_id, requesting_player.metadata.id
                )
                if (
                    not requesting_membership
                    or requesting_membership.role != MembershipRole.GM
                ):
                    raise ValueError("Only GMs can view other players' characters")

                target_player = await bot.linking_service.get_player_by_discord_id(
                    str(player.id)
                )
                if not target_player:
                    raise ValueError(
                        f"{player.display_name} doesn't have a player account"
                    )
            else:
                target_player = requesting_player

            # Get target's membership and character
            membership = await bot.campaign_service.get_membership(
                campaign_id, target_player.metadata.id
            )
            if not membership:
                raise ValueError("Player is not a member of this campaign")

            if not membership.character_id:
                raise ValueError(
                    "No character found. Use `/character create` to create one."
                )

            # Load character via service
            character = await bot.character_service.get_character(
                campaign_id, membership.character_id
            )

            # Build and send embed
            embed = _build_character_sheet_embed(character)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            embed = _build_error_embed("Error", str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

        except FileNotFoundError as e:
            embed = _build_error_embed("Not Found", str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in view_character: {e}", exc_info=True)
            embed = _build_error_embed("Error", "An unexpected error occurred.")
            await interaction.followup.send(embed=embed, ephemeral=True)

    @character_group.command(name="list", description="List characters in campaign")
    async def list_characters(interaction: discord.Interaction) -> None:
        """List characters in campaign."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Character listing will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @character_group.command(name="sheet", description="Display character sheet")
    @app_commands.describe(character_id="Character ID (optional)")
    async def character_sheet(
        interaction: discord.Interaction,
        character_id: str | None = None,
    ) -> None:
        """Display character sheet."""
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Not Implemented",
            description="Character sheet display will be implemented in a future update.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    bot.tree.add_command(character_group)


# ─────────────────────────────────────────────────────────────────
# EMBED BUILDERS: Translate domain models to Discord embeds
# ─────────────────────────────────────────────────────────────────


def _build_character_created_embed(character) -> discord.Embed:
    """
    Build embed for successful character creation.

    Args:
        character: CharacterSheet domain model

    Returns:
        Discord Embed
    """
    embed = discord.Embed(
        title="✅ Character Created",
        description=f"**{character.identity.name}** is ready for adventure!",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Character ID", value=f"`{character.metadata.id}`", inline=False
    )
    embed.add_field(name="Type", value="Player Character", inline=True)
    embed.add_field(name="Level", value=str(character.identity.level), inline=True)
    embed.set_footer(text="Use /character view to see your full character sheet")
    return embed


def _build_character_sheet_embed(character) -> discord.Embed:
    """
    Build detailed character sheet embed.

    Args:
        character: CharacterSheet domain model

    Returns:
        Discord Embed with full character details
    """
    embed = discord.Embed(
        title=f"📜 {character.identity.name}",
        color=discord.Color.blue(),
    )

    # Identity section
    identity = character.identity
    identity_lines = []
    if identity.ancestry:
        identity_lines.append(f"**Ancestry:** {identity.ancestry}")
    if identity.class_name:
        identity_lines.append(f"**Class:** {identity.class_name}")
    identity_lines.append(f"**Level:** {identity.level}")
    if identity.alignment:
        identity_lines.append(f"**Alignment:** {identity.alignment}")
    if identity.player_name:
        identity_lines.append(f"**Player:** {identity.player_name}")

    embed.add_field(
        name="Identity",
        value="\n".join(identity_lines) if identity_lines else "No details",
        inline=False,
    )

    # Combat section
    combat = character.combat
    hp = combat.hit_points
    combat_lines = [
        f"**HP:** {hp.current}/{hp.maximum}",
        f"**AC:** {combat.armor_class}",
        f"**Attack Bonus:** {combat.attack_bonus:+d}",
    ]
    embed.add_field(name="Combat", value="\n".join(combat_lines), inline=True)

    # Abilities section
    if character.abilities:
        ability_lines = [
            f"**{abbr}:** {score}" for abbr, score in character.abilities.items()
        ]
        embed.add_field(
            name="Abilities",
            value="\n".join(ability_lines),
            inline=True,
        )

    # Inventory section (first 5 items)
    if character.inventory:
        inventory_lines = []
        for item in character.inventory[:5]:
            equipped = "⚔️ " if item.equipped else ""
            qty = f"(x{item.quantity})" if item.quantity > 1 else ""
            inventory_lines.append(f"{equipped}{item.item} {qty}")
        if len(character.inventory) > 5:
            inventory_lines.append(f"... and {len(character.inventory) - 5} more")
        embed.add_field(
            name="Inventory",
            value="\n".join(inventory_lines),
            inline=False,
        )

    # Conditions
    if character.conditions:
        embed.add_field(
            name="Conditions",
            value=", ".join(character.conditions),
            inline=False,
        )

    # Notes (truncated)
    if character.notes:
        notes_display = character.notes[:200]
        if len(character.notes) > 200:
            notes_display += "..."
        embed.add_field(name="Notes", value=notes_display, inline=False)

    embed.set_footer(text=f"ID: {character.metadata.id}")

    return embed


def _build_error_embed(title: str, description: str) -> discord.Embed:
    """
    Build error embed.

    Args:
        title: Error title
        description: Error description

    Returns:
        Discord Embed styled as error
    """
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red(),
    )
