import discord
import re
from datetime import timedelta
from discord.ext import commands
from discord import app_commands

from cogs.config import MOD_ROLE_ID


# ================= HELPERS =================

def parse_duration(duration: str):
    """
    Supports:
    10s, 10m, 2h, 1d
    also expanded human formats:
    10sec, 10min, 2hours, 1day
    """

    duration = duration.lower().strip()

    match = re.match(r"(\d+)\s*(s|m|h|d|sec|min|hour|hours|day|days)?", duration)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if not unit:
        return None

    if unit in ("s", "sec"):
        return timedelta(seconds=value)
    if unit in ("m", "min"):
        return timedelta(minutes=value)
    if unit in ("h", "hour", "hours"):
        return timedelta(hours=value)
    if unit in ("d", "day", "days"):
        return timedelta(days=value)

    return None


def embed(title, description, color=0x2b2d31):
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )


def usage_embed(command_name, usage, description):
    emb = discord.Embed(
        title=f"Command: {command_name}",
        color=0xffcc00
    )

    emb.add_field(
        name="Usage",
        value=f"`{usage}`",
        inline=False
    )

    emb.add_field(
        name="Description",
        value=description,
        inline=False
    )

    return emb


# ================= COG =================

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- SLASH SERVER INFO ----------

    @app_commands.command(name="serverinfo", description="Show server information")
    async def serverinfo_slash(self, interaction: discord.Interaction):

        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "This command only works in servers.",
                ephemeral=True
            )

        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        emb = discord.Embed(
            title=guild.name,
            color=0x5865F2
        )

        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)

        emb.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        emb.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        emb.add_field(name="Server ID", value=str(guild.id), inline=False)

        emb.add_field(name="Members", value=guild.member_count, inline=True)
        emb.add_field(name="Humans", value=humans, inline=True)
        emb.add_field(name="Bots", value=bots, inline=True)

        emb.add_field(name="Roles", value=len(guild.roles), inline=True)
        emb.add_field(name="Channels", value=len(guild.channels), inline=True)

        emb.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        emb.add_field(name="Boost Tier", value=guild.premium_tier, inline=True)

        emb.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        emb.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)

        await interaction.response.send_message(embed=emb)

    # ---------- EMBED BUILDER ----------

    @app_commands.checks.has_role(MOD_ROLE_ID)
    @app_commands.command(name="embed", description="Create a custom embed")
    async def embed_builder(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str = "2b2d31",
        footer: str = None,
        author: str = None,
        thumbnail: str = None,
        message_link: str = None
    ):

        try:
            color_int = int(color.replace("#", ""), 16)
        except Exception:
            return await interaction.response.send_message(
                "Invalid color format. Use #ff0000",
                ephemeral=True
            )

        emb = discord.Embed(
            title=title,
            description=description,
            color=color_int
        )

        if footer:
            emb.set_footer(text=footer)

        if author:
            emb.set_author(name=author)

        if thumbnail:
            emb.set_thumbnail(url=thumbnail)

        if message_link:
            try:
                match = re.search(r"discord\.com/channels/(\d+)/(\d+)/(\d+)", message_link)

                if match:
                    channel_id = int(match.group(2))
                    message_id = int(match.group(3))

                    channel = self.bot.get_channel(channel_id)
                    if channel is None:
                        channel = await self.bot.fetch_channel(channel_id)

                    msg = await channel.fetch_message(message_id)

                    if msg.attachments:
                        emb.set_image(url=msg.attachments[0].url)

            except Exception as e:
                return await interaction.response.send_message(
                    f"Failed to fetch attachment:\n{e}",
                    ephemeral=True
                )

        await interaction.response.send_message(embed=emb)

    # ---------- PREFIX SERVER INFO ----------

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):

        guild = ctx.guild
        if guild is None:
            return await ctx.send("This command only works in servers.")

        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        emb = discord.Embed(
            title=guild.name,
            color=0x5865F2
        )

        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)

        emb.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        emb.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        emb.add_field(name="Server ID", value=str(guild.id), inline=False)

        emb.add_field(name="Members", value=guild.member_count, inline=True)
        emb.add_field(name="Humans", value=humans, inline=True)
        emb.add_field(name="Bots", value=bots, inline=True)

        emb.add_field(name="Roles", value=len(guild.roles), inline=True)
        emb.add_field(name="Channels", value=len(guild.channels), inline=True)

        emb.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        emb.add_field(name="Boost Tier", value=guild.premium_tier, inline=True)

        emb.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        emb.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)

        await ctx.send(embed=emb)


async def setup(bot):
    await bot.add_cog(Utility(bot))
