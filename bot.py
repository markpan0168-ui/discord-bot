import os
from dotenv import load_dotenv

load_dotenv()
import discord
from discord.ext import commands
from datetime import timedelta
import re
import aiosqlite
import asyncio
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=",", intents=intents)

# ================= CONFIG =================
MOD_ROLE_ID = 1502932574769643550
ADMIN_ROLE_ID = 1502932574769643550

SUSPENDED_ROLE_ID = 1500473776725295134
SUSPENDED_CHANNEL_ID = 1501202781766422641
APPEAL_CHANNEL_ID = 1488471572011290654

# ================= AFK STORAGE =================
afk_users = {}
afk_cooldowns = {}

# ================= DATABASE =================
async def setup_db():
    async with aiosqlite.connect("mod.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            warns INTEGER DEFAULT 0,
            mutes INTEGER DEFAULT 0,
            bans INTEGER DEFAULT 0,
            suspensions INTEGER DEFAULT 0
        )
        """)
        await db.commit()


async def add_stat(user_id, column):
    async with aiosqlite.connect("mod.db") as db:
        await db.execute(f"""
        INSERT INTO stats (user_id, {column})
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET {column} = {column} + 1
        """, (user_id,))
        await db.commit()


# ================= HELPERS =================
def parse_duration(duration: str):
    match = re.match(r"(\d+)(s|m|h|d)", duration)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

    return None


def embed(title, description, color=0x2b2d31):
    return discord.Embed(title=title, description=description, color=color)


# ================= READY =================
@bot.event
async def on_ready():
    await setup_db()
    print(f"Logged in as {bot.user}")


# ================= AFK SYSTEM =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason

    try:
        await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
    except:
        pass

    try:
        await ctx.author.send(f"You are now AFK: {reason}")
    except:
        pass

    await ctx.send(f"{ctx.author.mention} is now AFK")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # AFK RETURN
    if message.author.id in afk_users:
        reason = afk_users.pop(message.author.id)

        now = time.time()

        # anti spam cooldown (5 sec)
        if afk_cooldowns.get(message.author.id, 0) > now:
            return

        afk_cooldowns[message.author.id] = now + 5

        try:
            await message.author.edit(
                nick=message.author.display_name.replace("[AFK] ", "")
            )
        except:
            pass

        await message.channel.send(
            f"Welcome back {message.author.mention} from AFK ({reason})"
        )

    await bot.process_commands(message)


# ================= WARN =================
@bot.command()
@commands.has_role(1502932574769643550)
async def warn(ctx, member: discord.Member, *, reason="No reason"):

    await add_stat(member.id, "warns")

    await ctx.send(embed=embed(
        "Warn Issued",
        f"{member.mention} warned.\nReason: {reason}",
        0xffcc00
    ))

    # AUTO ESCALATION
    async with aiosqlite.connect("mod.db") as db:
        async with db.execute("SELECT warns FROM stats WHERE user_id = ?", (member.id,)) as cur:
            data = await cur.fetchone()

    warns = data[0] if data else 0

    try:
        await member.send(
            f"You have been warned in {ctx.guild.name} for {reason}"
        )
    except:
        pass

    # escalation logic
    if warns >= 3:
        await member.timeout(timedelta(hours=1), reason="Auto-mute after 3 warns")
    if warns >= 5:
        await member.ban(reason="Auto-ban after 5 warns")


# ================= MUTE =================
@bot.command()
@commands.has_role(1502932574769643550)
async def mute(ctx, member: discord.Member, duration, *, reason="No reason"):

    time_delta = parse_duration(duration)
    if not time_delta:
        return await ctx.send(embed=embed("Error", "Use 10m / 2h / 1d", 0xff0000))

    await member.timeout(time_delta, reason=reason)
    await add_stat(member.id, "mutes")

    try:
        await member.send(
            f"You have been muted in {ctx.guild.name} for {duration} due to {reason}"
        )
    except:
        pass

    await ctx.send(embed=embed(
        "User Muted",
        f"{member.mention} muted for {duration}",
        0xff8800
    ))


# ================= UNMUTE =================
@bot.command()
@commands.has_role(1502932574769643550)
async def unmute(ctx, member: discord.Member, *, reason="No reason"):

    try:
        await member.timeout(None, reason=reason)
    except Exception as e:
        return await ctx.send(embed=embed("Error", str(e), 0xff0000))

    await ctx.send(embed=embed(
        "User Unmuted",
        f"{member.mention} unmuted",
        0x00ff88
    ))


# ================= BAN =================
@bot.command()
@commands.has_role(1502932574769643550)
async def ban(ctx, member: discord.Member, *, reason="No reason"):

    await member.ban(reason=reason)
    await add_stat(member.id, "bans")

    await ctx.send(embed=embed(
        "User Banned",
        f"{member.mention} banned",
        0xff0000
    ))


# ================= SUSPEND =================
@bot.command()
@commands.has_role(1502932574769643550)
async def suspend(ctx, member: discord.Member, *, reason="No reason"):

    for role in member.roles:
        if role != ctx.guild.default_role:
            try:
                await member.remove_roles(role)
            except:
                pass

    role = ctx.guild.get_role(1500473776725295134)
    if role:
        await member.add_roles(role)

    await add_stat(member.id, "suspensions")

    try:
        await member.send(
            f"You have been suspended in {ctx.guild.name} for {reason}"
        )
    except:
        pass

    channel = bot.get_channel(1501202781766422641)
    appeal = bot.get_channel(1488471572011290654)

    if channel:
        await channel.send(
            f"🚨 **SUSPENDED**\n\n"
            f"User: {member.mention}\n"
            f"Reason: {reason}\n"
            f"Moderator: {ctx.author.mention}\n"
            f"Appeal: {appeal.mention if appeal else 'N/A'}"
        )

    await ctx.send(embed=embed(
        "User Suspended",
        f"{member.mention} suspended",
        0x8b0000
    ))


# ================= SERVER INFO =================
@bot.command(aliases=["si"])
async def serverinfo(ctx):
    g = ctx.guild

    emb = discord.Embed(title=g.name, color=0x5865f2)
    emb.add_field(name="Members", value=g.member_count)
    emb.add_field(name="Roles", value=len(g.roles))
    emb.set_thumbnail(url=g.icon.url if g.icon else None)

    await ctx.send(embed=emb)


# ================= RUN =================
bot.run(os.getenv("TOKEN"))
