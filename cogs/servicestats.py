import discord
import aiosqlite
from discord.ext import commands, tasks

from cogs.config import SERVICE_ROLE_ID, ADMIN_ROLE_ID
from cogs.utility import embed

DB_NAME = "mod.db"


# ================= HELPERS =================

def short_number(num: int):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.0f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.0f}M"
    if num >= 1_000:
        return f"{num / 1_000:.0f}K"
    return str(num)


def parse_amount(amount: str):
    amount = amount.upper().replace(",", "").strip()

    if amount.endswith("B"):
        return int(float(amount[:-1]) * 1_000_000_000)

    if amount.endswith("M"):
        return int(float(amount[:-1]) * 1_000_000)

    if amount.isdigit():
        return int(amount)

    return None


# ================= DB =================

async def setup_service_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS servicestats (
            user_id INTEGER PRIMARY KEY,
            vouches INTEGER DEFAULT 0,
            obtained INTEGER DEFAULT 0,
            tax_paid INTEGER DEFAULT 0
        )
        """)
        await db.commit()


async def ensure_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR IGNORE INTO servicestats (user_id)
        VALUES (?)
        """, (user_id,))
        await db.commit()


async def fetch_user(user_id: int):
    await ensure_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
        SELECT vouches, obtained, tax_paid
        FROM servicestats
        WHERE user_id = ?
        """, (user_id,)) as cursor:
            return await cursor.fetchone()


async def add_vouch_db(user_id: int, amount: int):
    await ensure_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE servicestats
        SET vouches = vouches + 1,
            obtained = obtained + ?
        WHERE user_id = ?
        """, (amount, user_id))
        await db.commit()


async def set_tax_paid(user_id: int):
    await ensure_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE servicestats
        SET tax_paid = 1
        WHERE user_id = ?
        """, (user_id,))
        await db.commit()


async def reset_tax():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE servicestats
        SET tax_paid = 0
        """)
        await db.commit()


# ================= LEADERBOARDS =================

async def fetch_top_vouches(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
        SELECT user_id, vouches
        FROM servicestats
        ORDER BY vouches DESC
        LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()


async def fetch_top_obtained(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
        SELECT user_id, obtained
        FROM servicestats
        ORDER BY obtained DESC
        LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()


# ================= COG =================

class ServiceStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tax_reset_task.start()

    def cog_unload(self):
        self.tax_reset_task.cancel()

    # ================= SERVICE STATS =================

    @commands.command(name="servicestats")
    async def servicestats(self, ctx, member: discord.Member = None):

        if SERVICE_ROLE_ID not in [r.id for r in ctx.author.roles]:
            return await ctx.send(embed=embed(
                "No Permission",
                "You cannot use this command.",
                0xff0000
            ))

        member = member or ctx.author

        vouches, obtained, tax = await fetch_user(member.id)

        emb = discord.Embed(
            title="Service Statistics",
            color=0x5865F2
        )

        emb.set_thumbnail(url=member.display_avatar.url)

        emb.description = (
            f"**User:** {member.mention}\n"
            f"**User ID:** `{member.id}`\n\n"
            f"**Vouches:** {vouches}\n"
            f"**Obtained:** {short_number(obtained)}\n"
            f"**Tax:** {'Paid✅' if tax else 'Not paid❌'}"
        )

        await ctx.send(embed=emb)

    # ================= VOUCH =================

    @commands.command()
    async def vouch(self, ctx, member: discord.Member, amount: str):

        if ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
            return await ctx.send(embed=embed(
                "No Permission",
                "You cannot use this command.",
                0xff0000
            ))

        parsed = parse_amount(amount)

        if not parsed or parsed < 1_000_000 or parsed > 10_000_000_000:
            return await ctx.send(embed=embed(
                "Invalid Amount",
                "Amount must be between **1M and 10B**.",
                0xff0000
            ))

        await add_vouch_db(member.id, parsed)

        await ctx.send(embed=embed(
            "Vouch Added",
            f"{member.mention}\n\n**+1 Vouch**\n**+{short_number(parsed)} Obtained**",
            0x00ff88
        ))

    # ================= TAX =================

    @commands.command()
    async def taxpass(self, ctx, member: discord.Member):

        if ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
            return await ctx.send(embed=embed(
                "No Permission",
                "You cannot use this command.",
                0xff0000
            ))

        await set_tax_paid(member.id)

        await ctx.send(embed=embed(
            "Tax Updated",
            f"{member.mention} is now marked as **Paid✅**",
            0x00ff88
        ))

    # ================= LEADERBOARD COMMANDS =================

    @commands.command(name="vouchlb")
    async def vouchlb(self, ctx):

        data = await fetch_top_vouches()

        desc = ""

        for i, (uid, v) in enumerate(data, start=1):
            user = self.bot.get_user(uid)
            name = user.mention if user else f"`{uid}`"
            desc += f"**{i}.** {name} — `{v}` vouches\n"

        emb = discord.Embed(
            title="🏆 Vouch Leaderboard",
            description=desc or "No data yet.",
            color=0x5865F2
        )

        await ctx.send(embed=emb)

    @commands.command(name="obtainedlb")
    async def obtainedlb(self, ctx):

        data = await fetch_top_obtained()

        desc = ""

        for i, (uid, amt) in enumerate(data, start=1):
            user = self.bot.get_user(uid)
            name = user.mention if user else f"`{uid}`"
            desc += f"**{i}.** {name} — `{short_number(amt)}`\n"

        emb = discord.Embed(
            title="💰 Obtained Leaderboard",
            description=desc or "No data yet.",
            color=0x00ff88
        )

        await ctx.send(embed=emb)

    # ================= TAX RESET =================

    @tasks.loop(hours=1)
    async def tax_reset_task(self):

        now = discord.utils.utcnow()

        # Sunday 8PM GMT+8 (UTC 12PM)
        if now.weekday() == 6 and now.hour == 12:
            await reset_tax()

    @tax_reset_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await setup_service_db()
    await bot.add_cog(ServiceStats(bot))
