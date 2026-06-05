import os
from dotenv import load_dotenv

load_dotenv()

import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import re
import aiosqlite
import asyncio
import time

# ================= INTENTS =================
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=",", intents=intents)
tree = bot.tree

# ================= CONFIG =================
MOD_ROLE_ID = 1502932574769643550
ADMIN_ROLE_ID = 1488474035997380649

SUSPENDED_ROLE_ID = 1500473776725295134
SUSPENDED_CHANNEL_ID = 1501202781766422641
APPEAL_CHANNEL_ID = 1488471572011290654

# ================= AFK =================
afk_users = {}
afk_cooldowns = {}

# ================= DATABASE =================
async def setup_db():
    async with aiosqlite.connect("mod.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS modstats (
            moderator_id INTEGER PRIMARY KEY,
            warns INTEGER DEFAULT 0,
            mutes INTEGER DEFAULT 0,
            unmutes INTEGER DEFAULT 0,
            bans INTEGER DEFAULT 0,
            suspensions INTEGER DEFAULT 0
        )
        """)

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


async def add_mod_stat(mod_id, column):
    async with aiosqlite.connect("mod.db") as db:
        await db.execute(f"""
        INSERT INTO modstats (moderator_id, {column})
        VALUES (?, 1)
        ON CONFLICT(moderator_id)
        DO UPDATE SET {column} = {column} + 1
        """, (mod_id,))
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

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")


# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason

    try:
        await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
    except:
        pass

    await ctx.send(f"{ctx.author.mention} is now AFK")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        reason = afk_users.pop(message.author.id)
        now = time.time()

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
            f"Welcome back {message.author.mention} ({reason})"
        )

    await bot.process_commands(message)


# ================= PREFIX MOD COMMANDS =================
@bot.command()
@commands.has_role(1502932574769643550)
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    await add_stat(member.id, "warns")
    await add_mod_stat(ctx.author.id, "warns")

    await ctx.send(embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00))


@bot.command()
@commands.has_role(1502932574769643550)
async def mute(ctx, member: discord.Member, duration, *, reason="No reason"):
    time_delta = parse_duration(duration)
    if not time_delta:
        return await ctx.send(embed=embed("Error", "Use 10m / 2h / 1d", 0xff0000))

    await member.timeout(time_delta, reason=reason)

    await add_stat(member.id, "mutes")
    await add_mod_stat(ctx.author.id, "mutes")

    await ctx.send(embed=embed("Muted", f"{member.mention} muted for {duration}", 0xff8800))


@bot.command()
@commands.has_role(1488474035997380649)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)

    await add_stat(member.id, "bans")
    await add_mod_stat(ctx.author.id, "bans")

    await ctx.send(embed=embed("Banned", f"{member.mention}", 0xff0000))


# ================= SLASH WARN =================
@tree.command(name="warn", description="Warn a user")
@app_commands.checks.has_role(1502932574769643550)
async def warn_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await add_stat(member.id, "warns")
    await add_mod_stat(interaction.user.id, "warns")

    await interaction.response.send_message(
        embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00)
    )


# ================= SLASH MUTE =================
@tree.command(name="mute", description="Mute a user")
@app_commands.checks.has_role(1502932574769643550)
async def mute_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason"):
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


# ================= SLASH BAN =================
@tree.command(name="ban", description="Ban a user")
@app_commands.checks.has_role(1488474035997380649)
async def ban_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)

    await add_stat(member.id, "bans")
    await add_mod_stat(interaction.user.id, "bans")

    await interaction.response.send_message(
        embed=embed("Banned", f"{member.mention}", 0xff0000)
    )

@tree.command(name="suspend", description="Suspend a user (remove roles + apply suspended role)")
@app_commands.checks.has_role(1488474035997380649)
async def suspend_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

    # remove roles
    for role in member.roles:
        if role != interaction.guild.default_role:
            try:
                await member.remove_roles(role)
            except:
                pass

    # add suspended role
    role = interaction.guild.get_role(1500473776725295134)
    if role:
        await member.add_roles(role)

    await add_stat(member.id, "suspensions")
    await add_mod_stat(interaction.user.id, "suspensions")

    channel = bot.get_channel(1501202781766422641)
    appeal = bot.get_channel(1488471572011290654)

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

@tree.command(name="serverinfo", description="Show server information")
async def serverinfo_slash(interaction: discord.Interaction):

    guild = interaction.guild

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
    emb.add_field(name="Server ID", value=guild.id, inline=False)

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


@tree.command(name="unmute", description="Remove timeout from a user")
@app_commands.checks.has_role(1502932574769643550)
async def unmute_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

    try:
        await member.timeout(None, reason=reason)
    except Exception as e:
        return await interaction.response.send_message(
            embed=embed("Error", str(e), 0xff0000),
            ephemeral=True
        )

    await add_mod_stat(interaction.user.id, "unmutes")

    await interaction.response.send_message(
        embed=embed("Unmuted", f"{member.mention} unmuted", 0x00ff88)
    )
# ================= EMBED BUILDER =================
@tree.command(name="embed", description="Create a custom embed")
async def embed_builder(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: str = "2b2d31",
    footer: str = None,
    author: str = None,
    thumbnail: str = None
):
    try:
        color_int = int(color.replace("#", ""), 16)
    except:
        return await interaction.response.send_message(
            "Invalid color format. Use hex like #ff0000",
            ephemeral=True
        )

    emb = discord.Embed(title=title, description=description, color=color_int)

    if footer:
        emb.set_footer(text=footer)

    if author:
        emb.set_author(name=author)

    if thumbnail:
        emb.set_thumbnail(url=thumbnail)

    await interaction.response.send_message(embed=emb)

@bot.command(aliases=["si"])
async def serverinfo(ctx):
    guild = ctx.guild

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
    emb.add_field(name="Server ID", value=guild.id, inline=False)

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


@bot.command()
@commands.has_role(1488474035997380649)
async def suspend(ctx, member: discord.Member, *, reason="No reason"):

    # remove all roles except @everyone
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
    await add_mod_stat(ctx.author.id, "suspensions")

    channel = bot.get_channel(1501202781766422641)
    appeal = bot.get_channel(1488471572011290654)

    if channel:
        await channel.send(
            f"🚨 **SUSPENDED**\n"
            f"User: {member.mention}\n"
            f"Reason: {reason}\n"
            f"Moderator: {ctx.author.mention}\n"
            f"Appeal: {appeal.mention if appeal else 'N/A'}"
        )

    await ctx.send(embed=embed(
        "Suspended",
        f"{member.mention} suspended",
        0x8b0000
    ))


@bot.command()
@commands.has_role(1502932574769643550)
async def unmute(ctx, member: discord.Member, *, reason="No reason"):
    try:
        await member.timeout(None, reason=reason)
    except Exception as e:
        return await ctx.send(embed=embed("Error", str(e), 0xff0000))

    await add_mod_stat(ctx.author.id, "unmutes")

    await ctx.send(embed=embed(
        "Unmuted",
        f"{member.mention} unmuted",
        0x00ff88
    ))
# ================= RUN =================
bot.run(os.getenv("TOKEN"))
