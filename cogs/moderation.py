from config import *
from cogs.utility import embed, usage_embed, parse_duration, suspend_cache
from cogs.stats import add_stat, add_mod_stat
from discord.ext import commands
import discord
from discord import app_commands
from config import suspend_cache

# assumes these exist somewhere global or imported
# MOD_ROLE_ID, ADMIN_ROLE_ID, SUSPENDED_ROLE_ID, SUSPENDED_CHANNEL_ID, APPEAL_CHANNEL_ID
# suspend_cache, embed, usage_embed, parse_duration, add_stat, add_mod_stat, tree

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= PREFIX MOD COMMANDS =================

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        await add_stat(member.id, "warns")
        await add_mod_stat(ctx.author.id, "warns")

        await ctx.send(embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00))

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def mute(self, ctx, member: discord.Member, duration, *, reason="No reason"):
        time_delta = parse_duration(duration)
        if not time_delta:
            return await ctx.send(embed=embed("Error", "Use 10m / 2h / 1d", 0xff0000))

        await member.timeout(time_delta, reason=reason)

        await add_stat(member.id, "mutes")
        await add_mod_stat(ctx.author.id, "mutes")

        await ctx.send(embed=embed("Muted", f"{member.mention} muted for {duration}", 0xff8800))

    @commands.command()
    @commands.has_role(ADMIN_ROLE_ID)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        await member.ban(reason=reason)

        await add_stat(member.id, "bans")
        await add_mod_stat(ctx.author.id, "bans")

        await ctx.send(embed=embed("Banned", f"{member.mention}", 0xff0000))

    @commands.command()
    @commands.has_role(MOD_ROLE_ID)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason"):
        try:
            await member.timeout(None, reason=reason)
        except Exception as e:
            return await ctx.send(embed=embed("Error", str(e), 0xff0000))

        await add_mod_stat(ctx.author.id, "unmutes")

        await ctx.send(embed=embed("Unmuted", f"{member.mention} unmuted", 0x00ff88))

    @commands.command()
    @commands.has_role(ADMIN_ROLE_ID)
    async def suspend(self, ctx, member: discord.Member, *, reason="No reason"):

        suspend_cache[member.id] = [
            r.id for r in member.roles
            if r != ctx.guild.default_role
        ]

        roles_to_remove = [
            role for role in member.roles
            if role != ctx.guild.default_role
        ]

        try:
            await member.remove_roles(*roles_to_remove)
        except Exception as e:
            print(f"suspend remove_roles error: {e}")

        role = ctx.guild.get_role(SUSPENDED_ROLE_ID)
        if role:
            await member.add_roles(role)

        await add_stat(member.id, "suspensions")
        await add_mod_stat(ctx.author.id, "suspensions")

        channel = self.bot.get_channel(SUSPENDED_CHANNEL_ID)
        appeal = self.bot.get_channel(APPEAL_CHANNEL_ID)

        if channel:
            await channel.send(
                f"🚨 **SUSPENDED**\n"
                f"User: {member.mention}\n"
                f"Reason: {reason}\n"
                f"Moderator: {ctx.author.mention}\n"
                f"Appeal: {appeal.mention if appeal else 'N/A'}"
            )

        await ctx.send(embed=embed("Suspended", f"{member.mention} suspended", 0x8b0000))

    @commands.command()
    @commands.has_role(ADMIN_ROLE_ID)
    async def unsuspend(self, ctx, member: discord.Member = None, *, reason="No reason"):

        if member is None:
            return await ctx.send(embed=usage_embed(
                ",unsuspend",
                ",unsuspend @user [reason]",
                "Unsuspend a user. Removes suspended role and restores access."
            ))

        role = ctx.guild.get_role(SUSPENDED_ROLE_ID)
        if role:
            await member.remove_roles(role)

        roles = suspend_cache.get(member.id, [])
        for role_id in roles:
            r = ctx.guild.get_role(role_id)
            if r:
                try:
                    await member.add_roles(r)
                except:
                    pass

        await add_stat(member.id, "unsuspensions")
        await add_mod_stat(ctx.author.id, "unsuspensions")

        await ctx.send(embed=embed("Unsuspended", f"{member.mention} has been restored", 0x00ff88))


    # ================= SLASH COMMANDS =================

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_role(MOD_ROLE_ID)
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await add_stat(member.id, "warns")
        await add_mod_stat(interaction.user.id, "warns")

        await interaction.response.send_message(
            embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00)
        )

    @app_commands.command(name="mute", description="Mute a user")
    @app_commands.checks.has_role(MOD_ROLE_ID)
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason"):
        time_delta = parse_duration(duration)

        if not time_delta:
            return await interaction.response.send_message(
                embed=embed("Error", "Use 10m / 2h / 1d", 0xff0000),
                ephemeral=True
            )

        await member.timeout(time_delta, reason=reason)

        await add_stat(member.id, "mutes")
        await add_mod_stat(interaction.user.id, "mutes")

        await interaction.response.send_message(
            embed=embed("Muted", f"{member.mention} muted for {duration}", 0xff8800)
        )

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.checks.has_role(ADMIN_ROLE_ID)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await member.ban(reason=reason)

        await add_stat(member.id, "bans")
        await add_mod_stat(interaction.user.id, "bans")

        await interaction.response.send_message(
            embed=embed("Banned", f"{member.mention}", 0xff0000)
        )

    @app_commands.command(name="suspend", description="Suspend a user")
    @app_commands.checks.has_role(ADMIN_ROLE_ID)
    async def suspend_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

        suspend_cache[member.id] = [
            r.id for r in member.roles
            if r != interaction.guild.default_role
        ]

        roles_to_remove = [
            role for role in member.roles
            if role != interaction.guild.default_role
        ]

        try:
            await member.remove_roles(*roles_to_remove)
        except Exception as e:
            print(f"suspend slash remove_roles error: {e}")

        suspended_role = interaction.guild.get_role(SUSPENDED_ROLE_ID)
        if suspended_role:
            await member.add_roles(suspended_role)

        await add_stat(member.id, "suspensions")
        await add_mod_stat(interaction.user.id, "suspensions")

        channel = self.bot.get_channel(SUSPENDED_CHANNEL_ID)
        appeal = self.bot.get_channel(APPEAL_CHANNEL_ID)

        if channel:
            await channel.send(
                f"🚨 **SUSPENDED**\n"
                f"User: {member.mention}\n"
                f"Reason: {reason}\n"
                f"Moderator: {interaction.user.mention}\n"
                f"Appeal: {appeal.mention if appeal else 'N/A'}"
            )

        await interaction.response.send_message(
            embed=embed("Suspended", f"{member.mention} suspended", 0x8b0000)
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
