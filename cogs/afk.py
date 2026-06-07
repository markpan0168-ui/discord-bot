import discord
from discord.ext import commands
import time

from cogs.utility import embed
from cogs.config import *
from cogs.stats import setup_db

afk_users = {}
afk_cooldowns = {}

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def afk(self, ctx, *, reason="AFK"):

        afk_users[ctx.author.id] = reason

        try:
            nick = ctx.author.display_name

            if not nick.startswith("[AFK] "):
                await ctx.author.edit(nick=f"[AFK] {nick}")

        except Exception:
            pass

        await ctx.send(
            embed=embed(
                "AFK Enabled",
                f"{ctx.author.mention} is now AFK.\nReason: {reason}",
                0xffff00
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        # User returns from AFK
        if message.author.id in afk_users:

            reason = afk_users.pop(message.author.id)

            now = time.time()

            if afk_cooldowns.get(message.author.id, 0) <= now:

                afk_cooldowns[message.author.id] = now + 5

                try:
                    await message.author.edit(
                        nick=message.author.display_name.replace("[AFK] ", "")
                    )
                except Exception:
                    pass

                await message.channel.send(
                    embed=embed(
                        "Welcome Back",
                        f"{message.author.mention} is no longer AFK.\nPrevious reason: {reason}",
                        0x00ff88
                    )
                )

        # Check mentioned AFK users
        afk_list = []

        for user in message.mentions:

            if user.bot:
                continue

            if user.id in afk_users:
                afk_list.append(
                    f"{user.mention} - {afk_users[user.id]}"
                )

        if afk_list:
            await message.channel.send(
                embed=embed(
                    "AFK Users",
                    "\n".join(afk_list),
                    0xffcc00
                )
            )

async def setup(bot):
    await bot.add_cog(AFK(bot))
