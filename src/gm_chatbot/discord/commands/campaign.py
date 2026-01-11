"""Campaign commands for Discord bot."""

import logging

import discord
from discord import app_commands

from ..bot import DiscordBot

logger = logging.getLogger(__name__)


async def _check_can_bind_channel(
    interaction: discord.Interaction,
    campaign_id: str,
    bot: DiscordBot,
) -> bool:
    """
    Check if user can bind campaign to channel.

    Returns True if user has:
    - Server administrator permissions, OR
    - Server owner status, OR
    - Discord role "GM" (case-insensitive), OR
    - Campaign GM membership

    Args:
        interaction: Discord interaction
        campaign_id: Campaign identifier
        bot: Discord bot instance

    Returns:
        True if user can bind channel, False otherwise
    """
    if not interaction.guild:
        return False

    # 1. Check server administrator
    if interaction.user.guild_permissions.administrator:
        return True

    # 2. Check server owner
    if interaction.guild.owner_id == interaction.user.id:
        return True

    # 3. Check Discord role "GM" (case-insensitive)
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if "gm" in user_roles:
        return True

    # 4. Check campaign GM membership
    user_id = str(interaction.user.id)
    has_permission = await bot.context_service.validate_permission(
        user_id, campaign_id, "gm"
    )
    return has_permission


def setup_campaign_commands(bot: DiscordBot) -> None:
    """
    Set up campaign commands.

    Args:
        bot: Discord bot instance
    """
    campaign_group = app_commands.Group(
        name="campaign",
        description="Campaign management commands",
    )

    @campaign_group.command(name="create", description="Create a new campaign")
    @app_commands.describe(
        name="Campaign name",
        system="Game system (e.g., shadowdark, dnd5e)",
        description="Optional campaign description",
    )
    async def create_campaign(
        interaction: discord.Interaction,
        name: str,
        system: str,
        description: str | None = None,
    ) -> None:
        """Create a new campaign."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Resolve player from Discord user
            user_id = str(interaction.user.id)
            player = await bot.linking_service.get_player_by_discord_id(user_id)
            if not player:
                # Auto-link user
                await bot.linking_service.link_discord_user(
                    discord_user_id=user_id,
                    discord_username=str(interaction.user),
                    guild_id=str(interaction.guild.id) if interaction.guild else None,
                    guild_name=interaction.guild.name if interaction.guild else None,
                )
                player = await bot.linking_service.get_player_by_discord_id(user_id)
                if not player:
                    raise ValueError("Failed to create player account")

            # Create campaign
            campaign = await bot.campaign_service.create_campaign(
                name=name,
                rule_system=system,
                description=description,
                created_by=player.metadata.id,
            )

            # Automatically add creator as GM member
            try:
                await bot.campaign_service.add_player(
                    campaign_id=campaign.metadata.id,
                    player_id=player.metadata.id,
                    role="gm",
                )
                logger.info(
                    f"Auto-added campaign creator {player.metadata.id} as GM "
                    f"for campaign {campaign.metadata.id}"
                )
            except ValueError:
                # Already a member (shouldn't happen, but handle gracefully)
                logger.warning(
                    f"Creator {player.metadata.id} already a member of "
                    f"campaign {campaign.metadata.id}"
                )

            embed = discord.Embed(
                title="Campaign Created",
                description=f"Campaign **{campaign.name}** has been created.",
                color=discord.Color.green(),
            )
            embed.add_field(name="Campaign ID", value=campaign.metadata.id, inline=False)
            embed.add_field(name="System", value=campaign.rule_system, inline=True)
            embed.add_field(name="Status", value=campaign.status, inline=True)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in create_campaign: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(name="list", description="List campaigns in this server")
    async def list_campaigns(interaction: discord.Interaction) -> None:
        """List campaigns in the guild."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not interaction.guild:
                embed = discord.Embed(
                    title="Error",
                    description="This command can only be used in a server.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            guild_id = str(interaction.guild.id)
            bindings = await bot.binding_service.list_campaigns_in_guild(guild_id)

            if not bindings:
                embed = discord.Embed(
                    title="No Campaigns",
                    description="No campaigns are bound to channels in this server.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="Campaigns",
                description=f"Found {len(bindings)} campaign(s) in this server:",
                color=discord.Color.blue(),
            )

            for binding in bindings[:10]:  # Limit to 10 campaigns
                try:
                    campaign = await bot.campaign_service.get_campaign(binding.campaign_id)
                    embed.add_field(
                        name=campaign.name,
                        value=f"ID: {campaign.metadata.id}\nChannel: <#{binding.channel_id}>",
                        inline=False,
                    )
                except Exception:
                    continue

            if len(bindings) > 10:
                embed.set_footer(text=f"Showing 10 of {len(bindings)} campaigns")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in list_campaigns: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(name="info", description="Show campaign details")
    @app_commands.describe(
        campaign_id="Campaign ID (optional, uses current channel if not provided)"
    )
    async def campaign_info(
        interaction: discord.Interaction,
        campaign_id: str | None = None,
    ) -> None:
        """Show campaign details."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Resolve campaign
            if not campaign_id:
                if not interaction.guild or not interaction.channel:
                    embed = discord.Embed(
                        title="Error",
                        description="No campaign found. Either provide a campaign ID or use this command in a bound channel.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                channel_id = str(interaction.channel.id)
                campaign_id = await bot.binding_service.get_campaign_by_channel(channel_id)
                if not campaign_id:
                    embed = discord.Embed(
                        title="Error",
                        description="No campaign found. Either provide a campaign ID or use this command in a bound channel.",
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

            campaign = await bot.campaign_service.get_campaign(campaign_id)

            # Get binding if exists
            binding = await bot.binding_service.get_binding(campaign.metadata.id)

            embed = discord.Embed(
                title=campaign.name,
                description=campaign.description or "No description",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Campaign ID", value=campaign.metadata.id, inline=False)
            embed.add_field(name="System", value=campaign.rule_system, inline=True)
            embed.add_field(name="Status", value=campaign.status, inline=True)

            if binding:
                embed.add_field(
                    name="Discord Channel",
                    value=f"<#{binding.channel_id}>",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
        except FileNotFoundError:
            embed = discord.Embed(
                title="Error",
                description=f"Campaign {campaign_id} not found.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in campaign_info: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(
        name="join",
        description="Join a campaign in this server",
    )
    @app_commands.describe(
        campaign_id="Campaign ID (optional, uses current channel if not provided)"
    )
    async def join_campaign(
        interaction: discord.Interaction,
        campaign_id: str | None = None,
    ) -> None:
        """Join a campaign."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not interaction.guild or not interaction.channel:
                embed = discord.Embed(
                    title="Error",
                    description="This command must be used in a server channel.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Resolve campaign
            if not campaign_id:
                channel_id = str(interaction.channel.id)
                campaign_id = await bot.binding_service.get_campaign_by_channel(
                    channel_id
                )
                if not campaign_id:
                    embed = discord.Embed(
                        title="Error",
                        description=(
                            "Channel not bound to a campaign. "
                            "Provide campaign_id or use a bound channel."
                        ),
                        color=discord.Color.red(),
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

            # Resolve player
            user_id = str(interaction.user.id)
            player = await bot.linking_service.get_player_by_discord_id(user_id)
            if not player:
                # Auto-link user
                await bot.linking_service.link_discord_user(
                    discord_user_id=user_id,
                    discord_username=str(interaction.user),
                    guild_id=str(interaction.guild.id),
                    guild_name=interaction.guild.name,
                )
                player = await bot.linking_service.get_player_by_discord_id(user_id)
                if not player:
                    raise ValueError("Failed to create player account")

            # Check if already a member
            existing = await bot.campaign_service.get_membership(
                campaign_id, player.metadata.id
            )
            if existing:
                embed = discord.Embed(
                    title="Already a Member",
                    description="You are already a member of this campaign.",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Add player to campaign
            await bot.campaign_service.add_player(
                campaign_id=campaign_id,
                player_id=player.metadata.id,
                role="player",
            )

            # Get campaign info
            campaign = await bot.campaign_service.get_campaign(campaign_id)

            # Build success embed
            embed = discord.Embed(
                title="Joined Campaign",
                description=f"You have joined **{campaign.name}**!",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Campaign ID", value=campaign.metadata.id, inline=False
            )
            embed.add_field(name="Role", value="Player", inline=True)
            embed.add_field(name="System", value=campaign.rule_system, inline=True)
            embed.set_footer(text="Use /character create to create your character")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            embed = discord.Embed(
                title="Cannot Join Campaign",
                description=str(e),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except FileNotFoundError as e:
            embed = discord.Embed(
                title="Not Found",
                description=str(e),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in join_campaign: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(
        name="set-channel",
        description="Bind campaign to current channel",
    )
    @app_commands.describe(campaign_id="Campaign ID")
    async def set_channel(
        interaction: discord.Interaction,
        campaign_id: str,
    ) -> None:
        """Bind campaign to current channel."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not interaction.guild or not interaction.channel:
                embed = discord.Embed(
                    title="Error",
                    description="This command can only be used in a server channel.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Check permission using enhanced permission check
            if not await _check_can_bind_channel(interaction, campaign_id, bot):
                embed = discord.Embed(
                    title="Error",
                    description=(
                        "You need GM permissions, server administrator role, "
                        "server owner status, or Discord 'GM' role to bind campaigns."
                    ),
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Resolve player
            user_id = str(interaction.user.id)
            player = await bot.linking_service.get_player_by_discord_id(user_id)
            if not player:
                embed = discord.Embed(
                    title="Error",
                    description="Please link your Discord account first.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Create binding
            channel_name = interaction.channel.name if interaction.channel.name else "Unknown"
            binding = await bot.binding_service.bind_campaign_to_channel(
                campaign_id=campaign_id,
                guild_id=str(interaction.guild.id),
                channel_id=str(interaction.channel.id),
                channel_name=channel_name,
                bound_by=player.metadata.id,
            )

            embed = discord.Embed(
                title="Channel Bound",
                description=f"Campaign is now bound to <#{binding.channel_id}>",
                color=discord.Color.green(),
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in set_channel: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(name="archive", description="Archive a campaign")
    @app_commands.describe(campaign_id="Campaign ID")
    async def archive_campaign(
        interaction: discord.Interaction,
        campaign_id: str,
    ) -> None:
        """Archive a campaign."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check permission
            user_id = str(interaction.user.id)
            has_permission = await bot.context_service.validate_permission(
                user_id, campaign_id, "gm"
            )
            if not has_permission:
                embed = discord.Embed(
                    title="Error",
                    description="You need GM permissions to archive campaigns.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            from ...lib.types import CampaignStatus

            campaign = await bot.campaign_service.get_campaign(campaign_id)
            campaign.status = CampaignStatus.ARCHIVED
            await bot.campaign_service.update_campaign(campaign)

            embed = discord.Embed(
                title="Campaign Archived",
                description=f"Campaign **{campaign.name}** has been archived.",
                color=discord.Color.orange(),
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
        except FileNotFoundError:
            embed = discord.Embed(
                title="Error",
                description=f"Campaign {campaign_id} not found.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in archive_campaign: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @campaign_group.command(name="delete", description="Delete a campaign")
    @app_commands.describe(campaign_id="Campaign ID")
    async def delete_campaign(
        interaction: discord.Interaction,
        campaign_id: str,
    ) -> None:
        """Delete a campaign."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check permission
            user_id = str(interaction.user.id)
            has_permission = await bot.context_service.validate_permission(
                user_id, campaign_id, "gm"
            )
            if not has_permission:
                embed = discord.Embed(
                    title="Error",
                    description="You need GM permissions to delete campaigns.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            campaign = await bot.campaign_service.get_campaign(campaign_id)

            # Delete binding if exists
            try:
                await bot.binding_service.unbind_campaign(campaign_id)
            except FileNotFoundError:
                pass

            # Delete campaign
            await bot.campaign_service.delete_campaign(campaign_id)

            embed = discord.Embed(
                title="Campaign Deleted",
                description=f"Campaign **{campaign.name}** has been deleted.",
                color=discord.Color.red(),
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
        except FileNotFoundError:
            embed = discord.Embed(
                title="Error",
                description=f"Campaign {campaign_id} not found.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in delete_campaign: {e}", exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {e!s}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    # Register the group to the bot
    bot.tree.add_command(campaign_group)
