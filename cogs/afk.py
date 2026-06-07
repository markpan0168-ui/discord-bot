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

        afk_users[ctx.author.id] = {
            "reason": reason,
            "since": time.time()
        }

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

        ctx = await self.bot.get_context(message)

        # AFK autoresponder
        for user in message.mentions:

            if user.bot:
                continue

            if user.id in afk_users:

                afk_data = afk_users[user.id]

                minutes = int(
                    (time.time() - afk_data["since"]) / 60
                )

                await message.channel.send(
                    embed=embed(
                        "User is AFK",
                        f"{user.mention} is currently AFK.\n"
                        f"Reason: {afk_data['reason']}\n"
                        f"AFK for: {minutes} minute(s)",
                        0xffcc00
                    )
                )

        # Prevent commands from removing AFK
        if ctx.valid:
            return

        # Remove AFK when user sends a normal message
        if message.author.id in afk_users:

            afk_data = afk_users.pop(message.author.id)

            now = time.time()

            if afk_cooldowns.get(message.author.id, 0) <= now:

                afk_cooldowns[message.author.id] = now + 5

                try:
                    nick = message.author.display_name

                    if nick.startswith("[AFK] "):
                        await message.author.edit(
                            nick=nick.replace("[AFK] ", "", 1)
                        )

                except Exception:
                    pass

                await message.channel.send(
                    embed=embed(
                        "Welcome Back",
                        f"{message.author.mention} is no longer AFK.\n"
                        f"Previous reason: {afk_data['reason']}",
                        0x00ff88
                    )
                )

async def setup(bot):
    await bot.add_cog(AFK(bot))
