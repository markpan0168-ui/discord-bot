import discord
import aiosqlite
from discord.ext import commands
from discord import app_commands

from cogs.config import MOD_ROLE_ID


DB_NAME = "mod.db"


# ================= DB SETUP =================

async def setup_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS modstats (
            moderator_id INTEGER PRIMARY KEY,
            warns INTEGER DEFAULT 0,
            mutes INTEGER DEFAULT 0,
            unmutes INTEGER DEFAULT 0,
            bans INTEGER DEFAULT 0,
            suspensions INTEGER DEFAULT 0,
            unsuspensions INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            warns INTEGER DEFAULT 0,
            mutes INTEGER DEFAULT 0,
            bans INTEGER DEFAULT 0,
            suspensions INTEGER DEFAULT 0,
            unsuspensions INTEGER DEFAULT 0
        )
        """)

        await db.commit()


# ================= HELPERS =================

async def ensure_mod_row(mod_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR IGNORE INTO modstats (moderator_id)
        VALUES (?)
        """, (mod_id,))
        await db.commit()


async def ensure_user_row(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR IGNORE INTO stats (user_id)
        VALUES (?)
        """, (user_id,))
        await db.commit()


async def add_mod_stat(mod_id: int, column: str):
    await ensure_mod_row(mod_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"""
        UPDATE modstats
        SET {column} = {column} + 1
        WHERE moderator_id = ?
        """, (mod_id,))
        await db.commit()


async def add_stat(user_id: int, column: str):
    await ensure_user_row(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"""
        UPDATE stats
        SET {column} = {column} + 1
        WHERE user_id = ?
        """, (user_id,))
        await db.commit()


async def fetch_mod_stats(mod_id: int):
    await ensure_mod_row(mod_id)

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
        SELECT warns, mutes, unmutes, bans, suspensions, unsuspensions
        FROM modstats
        WHERE moderator_id = ?
        """, (mod_id,)) as cursor:
            return await cursor.fetchone()


# ================= COG =================

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= PREFIX =================

    @commands.command(aliases=["moderationstatistics"])
    @commands.has_role(MOD_ROLE_ID)
    async def ms(self, ctx, moderator: discord.Member):

        data = await fetch_mod_stats(moderator.id)

        warns, mutes, unmutes, bans, suspensions, unsuspensions = data

        emb = discord.Embed(
            title=f"Moderation Statistics - {moderator}",
            color=0x5865F2
        )

        emb.add_field(name="Warns", value=warns, inline=True)
        emb.add_field(name="Mutes", value=mutes, inline=True)
        emb.add_field(name="Unmutes", value=unmutes, inline=True)
        emb.add_field(name="Bans", value=bans, inline=True)
        emb.add_field(name="Suspensions", value=suspensions, inline=True)
        emb.add_field(name="Unsuspensions", value=unsuspensions, inline=True)

        emb.set_thumbnail(url=moderator.display_avatar.url)

        await ctx.send(embed=emb)

    # ================= SLASH =================

    @app_commands.command(name="modstats", description="View moderator statistics")
    @app_commands.checks.has_role(MOD_ROLE_ID)
    async def modstats_slash(self, interaction: discord.Interaction, moderator: discord.Member):

        data = await fetch_mod_stats(moderator.id)

        warns, mutes, unmutes, bans, suspensions, unsuspensions = data

        emb = discord.Embed(
            title=f"Moderation Statistics - {moderator}",
            color=0x5865F2
        )

        emb.add_field(name="Warns", value=warns, inline=True)
        emb.add_field(name="Mutes", value=mutes, inline=True)
        emb.add_field(name="Unmutes", value=unmutes, inline=True)
        emb.add_field(name="Bans", value=bans, inline=True)
        emb.add_field(name="Suspensions", value=suspensions, inline=True)
        emb.add_field(name="Unsuspensions", value=unsuspensions, inline=True)

        emb.set_thumbnail(url=moderator.display_avatar.url)

        await interaction.response.send_message(embed=emb)


async def setup(bot):
    await bot.add_cog(Stats(bot))
    await setup_db()
