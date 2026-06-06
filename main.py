import discord
from discord.ext import commands
import os

from cogs.config import *
from cogs.utility import usage_embed

# if you already moved suspend_cache here later, you're good

print("BOOTING BOT FILE")

intents = discord.Intents.all()

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.afk")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.games")
        await self.load_extension("cogs.stats")

        # sync slash commands here (cleaner than on_ready spam)
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"Slash sync failed: {e}")


bot = MyBot(command_prefix=",", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingRole):
        return await ctx.send("❌ You don't have permission.")

    if isinstance(error, commands.MissingRequiredArgument):
        cmd = ctx.command.name if ctx.command else None

        if cmd == "warn":
            return await ctx.send(embed=usage_embed(
                ",warn",
                ",warn @user [reason]",
                "Warn a user."
            ))

        elif cmd == "mute":
            return await ctx.send(embed=usage_embed(
                ",mute",
                ",mute @user <duration> [reason]",
                "Mute a user. Example: 10m, 2h, 1d"
            ))

        elif cmd == "ban":
            return await ctx.send(embed=usage_embed(
                ",ban",
                ",ban @user [reason]",
                "Ban a user."
            ))

        elif cmd == "suspend":
            return await ctx.send(embed=usage_embed(
                ",suspend",
                ",suspend @user [reason]",
                "Suspend a user by removing roles and applying suspended role."
            ))

        elif cmd == "unsuspend":
            return await ctx.send(embed=usage_embed(
                ",unsuspend",
                ",unsuspend @user [reason]",
                "Restore a suspended user and return their roles."
            ))

    print(error)
    return


token = os.getenv("TOKEN")

if not token:
    print("TOKEN missing in environment")
    exit()

bot.run(token)
