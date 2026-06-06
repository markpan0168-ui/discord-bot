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
# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):

    afk_users[ctx.author.id] = reason

    try:
        nick = ctx.author.display_name.replace("[AFK] ", "")
        await ctx.author.edit(nick=f"[AFK] {nick}")
    except:
        pass

    await ctx.send(
        embed=embed(
            "AFK Enabled",
            f"{ctx.author.mention} is now AFK.\nReason: {reason}",
            0xffff00
        )
    )


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # AFK RETURN
    if message.author.id in afk_users:

        reason = afk_users.pop(message.author.id)

        now = time.time()

        if afk_cooldowns.get(message.author.id, 0) <= now:

            afk_cooldowns[message.author.id] = now + 5

            try:
                await message.author.edit(
                    nick=message.author.display_name.replace("[AFK] ", "")
                )
            except:
                pass

            await message.channel.send(
                embed=embed(
                    "Welcome Back",
                    f"{message.author.mention} is no longer AFK.\nPrevious reason: {reason}",
                    0x00ff88
                )
            )

    # AFK MENTION CHECK
    for user in message.mentions:

        if user.bot:
            continue

        if user.id in afk_users:

            await message.channel.send(
                embed=embed(
                    "User AFK",
                    f"{user.mention} is AFK.\nReason: {afk_users[user.id]}",
                    0xffcc00
                )
            )

    await bot.process_commands(message)

# stores user roles before suspension
suspend_cache = {}

# ================= PREFIX MOD COMMANDS =================
@bot.command()
@commands.has_role(MOD_ROLE_ID)
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    await add_stat(member.id, "warns")
    await add_mod_stat(ctx.author.id, "warns")

    await ctx.send(embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00))


@bot.command()
@commands.has_role(MOD_ROLE_ID)
async def mute(ctx, member: discord.Member, duration, *, reason="No reason"):
    time_delta = parse_duration(duration)
    if not time_delta:
        return await ctx.send(embed=embed("Error", "Use 10m / 2h / 1d", 0xff0000))

    await member.timeout(time_delta, reason=reason)

    await add_stat(member.id, "mutes")
    await add_mod_stat(ctx.author.id, "mutes")

    await ctx.send(embed=embed("Muted", f"{member.mention} muted for {duration}", 0xff8800))


@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)

    await add_stat(member.id, "bans")
    await add_mod_stat(ctx.author.id, "bans")

    await ctx.send(embed=embed("Banned", f"{member.mention}", 0xff0000))


# ================= SLASH WARN =================
@tree.command(name="warn", description="Warn a user")
@app_commands.checks.has_role(MOD_ROLE_ID)
async def warn_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await add_stat(member.id, "warns")
    await add_mod_stat(interaction.user.id, "warns")

    await interaction.response.send_message(
        embed=embed("Warn", f"{member.mention} warned: {reason}", 0xffcc00)
    )


# ================= SLASH MUTE =================
@tree.command(name="mute", description="Mute a user")
@app_commands.checks.has_role(MOD_ROLE_ID)
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
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def ban_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)

    await add_stat(member.id, "bans")
    await add_mod_stat(interaction.user.id, "bans")

    await interaction.response.send_message(
        embed=embed("Banned", f"{member.mention}", 0xff0000)
    )

@tree.command(name="suspend", description="Suspend a user (remove roles + apply suspended role)")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def suspend_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

# save roles before removing
suspend_cache[member.id] = [r.id for r in member.roles if r != interaction.guild.default_role]

    # remove roles
    for role in member.roles:
        if role != interaction.guild.default_role:
            try:
                await member.remove_roles(role)
            except:
                pass

    # add suspended role
    role = interaction.guild.get_role(SUSPENDED_ROLE_ID)
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

  ync def unmute_slash(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):

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
@app_commands.checks.has_role(MOD_ROLE_ID)
@tree.command(name="embed", description="Create a custom embed")
async def embed_builder(
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
    except:
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

    # Attachment from message link
    if message_link:

        try:
            match = re.search(
                r"discord\.com/channels/(\d+)/(\d+)/(\d+)",
                message_link
            )

            if match:

                guild_id = int(match.group(1))
                channel_id = int(match.group(2))
                message_id = int(match.group(3))

                channel = bot.get_channel(channel_id)

                if channel is None:
                    channel = await bot.fetch_channel(channel_id)

                msg = await channel.fetch_message(message_id)

                if msg.attachments:
                    emb.set_image(url=msg.attachments[0].url)

        except Exception as e:
            return await interaction.response.send_message(
                f"Failed to fetch attachment:\n{e}",
                ephemeral=True
            )

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
@commands.has_role(ADMIN_ROLE_ID)
async def suspend(ctx, member: discord.Member, *, reason="No reason"):

suspend_cache[member.id] = [r.id for r in member.roles if r != ctx.guild.default_role]

    # remove all roles except @everyone
    for role in member.roles:
        if role != ctx.guild.default_role:
            try:
                await member.remove_roles(role)
            except:
                pass

    role = ctx.guild.get_role(SUSPENDED_ROLE_ID)
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
@commands.has_role(MOD_ROLE_ID)
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

# ================= MOD STATS =================
@bot.command(aliases=["moderationstatistics"])
@commands.has_role(MOD_ROLE_ID)
async def ms(ctx, moderator: discord.Member):

    async with aiosqlite.connect("mod.db") as db:
        async with db.execute("""
        SELECT warns, mutes, unmutes, bans, suspensions
        FROM modstats
        WHERE moderator_id = ?
        """, (moderator.id,)) as cursor:
            data = await cursor.fetchone()

    if not data:
        return await ctx.send(
            embed=discord.Embed(
                title="Moderation Statistics",
                description=f"No moderation data found for {moderator.mention}",
                color=0xff0000
            )
        )

    warns, mutes, unmutes, bans, suspensions = data

    emb = discord.Embed(
        title=f"Moderation Statistics - {moderator}",
        color=0x5865F2
    )

    emb.add_field(name="Warns", value=warns, inline=True)
    emb.add_field(name="Mutes", value=mutes, inline=True)
    emb.add_field(name="Unmutes", value=unmutes, inline=True)
    emb.add_field(name="Bans", value=bans, inline=True)
    emb.add_field(name="Suspensions", value=suspensions, inline=True)

    emb.set_thumbnail(url=moderator.display_avatar.url)

    await ctx.send(embed=emb)


@tree.command(name="modstats", description="View moderator statistics")
@app_commands.checks.has_role(MOD_ROLE_ID)
async def modstats_slash(
    interaction: discord.Interaction,
    moderator: discord.Member
):

    async with aiosqlite.connect("mod.db") as db:
        async with db.execute("""
        SELECT warns, mutes, unmutes, bans, suspensions
        FROM modstats
        WHERE moderator_id = ?
        """, (moderator.id,)) as cursor:
            data = await cursor.fetchone()

    if not data:
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="Moderation Statistics",
                description=f"No moderation data found for {moderator.mention}",
                color=0xff0000
            ),
            ephemeral=True
        )

    warns, mutes, unmutes, bans, suspensions = data

    emb = discord.Embed(
        title=f"Moderation Statistics - {moderator}",
        color=0x5865F2
    )

    emb.add_field(name="Warns", value=warns, inline=True)
    emb.add_field(name="Mutes", value=mutes, inline=True)
    emb.add_field(name="Unmutes", value=unmutes, inline=True)
    emb.add_field(name="Bans", value=bans, inline=True)
    emb.add_field(name="Suspensions", value=suspensions, inline=True)

    emb.set_thumbnail(url=moderator.display_avatar.url)

    await interaction.response.send_message(embed=emb)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ You don't have permission.")


@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingRole):
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ You don't have permission.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingRole):
        return await ctx.send("❌ You don't have permission.")

    if isinstance(error, commands.MissingRequiredArgument):

        cmd = ctx.command.name

        if cmd == "warn":
            return await ctx.send(
                embed=usage_embed(
                    ",warn",
                    ",warn @user [reason]",
                    "Warn a user."
                )
            )

        elif cmd == "mute":
            return await ctx.send(
                embed=usage_embed(
                    ",mute",
                    ",mute @user <duration> [reason]",
                    "Mute a user. Example: 10m, 2h, 1d"
                )
            )

        elif cmd == "ban":
            return await ctx.send(
                embed=usage_embed(
                    ",ban",
                    "suspend":
            return await ctx.send(
                embed=usage_embed(
                    ",suspend",
                    ",suspend @user [reason]",
                    "Removes all roles and gives the Suspended role."
                )
            )

        elif cmd == "unmute":
            return await ctx.send(
                embed=usage_embed(
                    ",unmute",
                    ",unmute @user [reason]",
                    "Remove a user's timeout."
                )
            )

    raise error


bot.run(os.getenv("TOKEN"))",ban @user [reason]",
                    "Ban a user."
                )
            )

        elif cmd == "suspend":
            return await ctx.send(
                embed=usage_embed(
                    ",suspend",
                    ",suspend @user [reason]",
                    "Removes all roles and gives the Suspended role."
                )
            )

        elif cmd == "unmute":
            return await ctx.send(
                embed=usage_embed(
                    ",unmute",
                    ",unmute @user [reason]",
                    "Remove a user's timeout."
                )
            )

    raise error


bot.run(os.getenv("TOKEN"))  emb = discord.Embed(
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
@app_commands.checks.has_role(MOD_ROLE_ID)
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
@app_commands.checks.has_role(MOD_ROLE_ID)
@tree.command(name="embed", description="Create a custom embed")
async def embed_builder(
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
    except:
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

    # Attachment from message link
    if message_link:

        try:
            match = re.search(
                r"discord\.com/channels/(\d+)/(\d+)/(\d+)",
                message_link
            )

            if match:

                guild_id = int(match.group(1))
                channel_id = int(match.group(2))
                message_id = int(match.group(3))

                channel = bot.get_channel(channel_id)

                if channel is None:
                    channel = await bot.fetch_channel(channel_id)

                msg = await channel.fetch_message(message_id)

                if msg.attachments:
                    emb.set_image(url=msg.attachments[0].url)

        except Exception as e:
            return await interaction.response.send_message(
                f"Failed to fetch attachment:\n{e}",
                ephemeral=True
            )

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
@commands.has_role(ADMIN_ROLE_ID)
async def suspend(ctx, member: discord.Member, *, reason="No reason"):

    # remove all roles except @everyone
    for role in member.roles:
        if role != ctx.guild.default_role:
            try:
                await member.remove_roles(role)
            except:
                pass

    role = ctx.guild.get_role(SUSPENDED_ROLE_ID)
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
@commands.has_role(MOD_ROLE_ID)
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

# ================= MOD STATS =================
@bot.command(aliases=["moderationstatistics"])
@commands.has_role(MOD_ROLE_ID)
async def ms(ctx, moderator: discord.Member):

    async with aiosqlite.connect("mod.db") as db:
        async with db.execute("""
        SELECT warns, mutes, unmutes, bans, suspensions
        FROM modstats
        WHERE moderator_id = ?
        """, (moderator.id,)) as cursor:
            data = await cursor.fetchone()

    if not data:
        return await ctx.send(
            embed=discord.Embed(
                title="Moderation Statistics",
                description=f"No moderation data found for {moderator.mention}",
                color=0xff0000
            )
        )

    warns, mutes, unmutes, bans, suspensions = data

    emb = discord.Embed(
        title=f"Moderation Statistics - {moderator}",
        color=0x5865F2
    )

    emb.add_field(name="Warns", value=warns, inline=True)
    emb.add_field(name="Mutes", value=mutes, inline=True)
    emb.add_field(name="Unmutes", value=unmutes, inline=True)
    emb.add_field(name="Bans", value=bans, inline=True)
    emb.add_field(name="Suspensions", value=suspensions, inline=True)

    emb.set_thumbnail(url=moderator.display_avatar.url)

    await ctx.send(embed=emb)


@tree.command(name="modstats", description="View moderator statistics")
@app_commands.checks.has_role(MOD_ROLE_ID)
async def modstats_slash(
    interaction: discord.Interaction,
    moderator: discord.Member
):

    async with aiosqlite.connect("mod.db") as db:
        async with db.execute("""
        SELECT warns, mutes, unmutes, bans, suspensions
        FROM modstats
        WHERE moderator_id = ?
        """, (moderator.id,)) as cursor:
            data = await cursor.fetchone()

    if not data:
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="Moderation Statistics",
                description=f"No moderation data found for {moderator.mention}",
                color=0xff0000
            ),
            ephemeral=True
        )

    warns, mutes, unmutes, bans, suspensions = data

    emb = discord.Embed(
        title=f"Moderation Statistics - {moderator}",
        color=0x5865F2
    )

    emb.add_field(name="Warns", value=warns, inline=True)
    emb.add_field(name="Mutes", value=mutes, inline=True)
    emb.add_field(name="Unmutes", value=unmutes, inline=True)
    emb.add_field(name="Bans", value=bans, inline=True)
    emb.add_field(name="Suspensions", value=suspensions, inline=True)

    emb.set_thumbnail(url=moderator.display_avatar.url)

    await interaction.response.send_message(embed=emb)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ You don't have permission.")


@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingRole):
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ You don't have permission.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ You don't have permission.",
                ephemeral=True
            )


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingRole):
        return await ctx.send("❌ You don't have permission.")

    if isinstance(error, commands.MissingRequiredArgument):

        cmd = ctx.command.name

        if cmd == "warn":
            return await ctx.send(
                embed=usage_embed(
                    ",warn",
                    ",warn @user [reason]",
                    "Warn a user."
                )
            )

        elif cmd == "mute":
            return await ctx.send(
                embed=usage_embed(
                    ",mute",
                    ",mute @user <duration> [reason]",
                    "Mute a user. Example: 10m, 2h, 1d"
                )
            )

        elif cmd == "ban":
            return await ctx.send(
                embed=usage_embed(
                    ",ban",
                    "suspend":
            return await ctx.send(
                embed=usage_embed(
                    ",suspend",
                    ",suspend @user [reason]",
                    "Removes all roles and gives the Suspended role."
                )
            )

        elif cmd == "unmute":
            return await ctx.send(
                embed=usage_embed(
                    ",unmute",
                    ",unmute @user [reason]",
                    "Remove a user's timeout."
                )
            )

    raise error


bot.run(os.getenv("TOKEN"))",ban @user [reason]",
                    "Ban a user."
                )
            )

        elif cmd == "suspend":
            return await ctx.send(
                embed=usage_embed(
                    ",suspend",
                    ",suspend @user [reason]",
                    "Removes all roles and gives the Suspended role."
                )
            )

        elif cmd == "unmute":
            return await ctx.send(
                embed=usage_embed(
                    ",unmute",
                    ",unmute @user [reason]",
                    "Remove a user's timeout."
                )
            )

    raise error

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def unsuspend(ctx, member: discord.Member = None, *, reason="No reason"):

    # if user not provided → show usage embed
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

    await ctx.send(embed=embed(
        "Unsuspended",
        f"{member.mention} has been restored",
        0x00ff88
    ))


@tree.command(name="unsuspend", description="Remove suspension and restore user roles")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def unsuspend_slash(
    interaction: discord.Interaction,
    member: discord.Member = None,
    reason: str = "No reason"
):

    if member is None:
        return await interaction.response.send_message(
            embed=usage_embed(
                "/unsuspend",
                "/unsuspend user:[user] reason:[reason]",
                "Unsuspend a user. Restores roles and removes suspension."
            ),
            ephemeral=True
        )

    role = interaction.guild.get_role(SUSPENDED_ROLE_ID)
    if role:
        await member.remove_roles(role)

    roles = suspend_cache.get(member.id, [])
    for role_id in roles:
        r = interaction.guild.get_role(role_id)
        if r:
            try:
                await member.add_roles(r)
            except:
                pass

    await add_stat(member.id, "unsuspensions")
    await add_mod_stat(interaction.user.id, "unsuspensions")

    await interaction.response.send_message(
        embed=embed(
            "Unsuspended",
            f"{member.mention} restored",
            0x00ff88
        )
    )


import random
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=",", intents=discord.Intents.all())

# ================= POOLS =================

truth_bloxfruit = [
    "What’s your highest bounty in Blox Fruits?",
    "Have you ever scammed a trade in Blox Fruits?",
    "What fruit do you secretly want but don’t have?",
    "Have you ever lost a PvP and blamed lag?",
    "What’s your worst fruit roll ever?",
    "Do you prefer sword mains or fruit mains?",
    "Have you ever rage quit after dying in PvP?",
    "What’s your most OP fruit you’ve used?",
    "Have you ever begged someone for a fruit?",
    "What level are you in Blox Fruits right now?",
    "Have you ever been spawn killed repeatedly?",
    "What’s your dream fruit combo?",
    "Have you ever used auto clickers?",
    "What’s the most toxic player you met?",
    "Have you ever lied about your level?"
]

truth_general = [
    "Who was your last crush?",
    "Have you ever had a secret you never told anyone?",
    "What’s the most embarrassing thing you’ve done in public?",
    "Have you ever pretended to be busy to avoid someone?",
    "Who do you stalk the most on social media?",
    "Have you ever lied to your best friend?",
    "What’s your biggest insecurity?",
    "Have you ever cried watching a movie?",
    "Who was your first crush?",
    "Have you ever been rejected?",
    "What’s your most awkward moment?",
    "Have you ever sent a risky text?",
    "Have you ever liked someone who didn’t like you back?",
    "What’s a secret you would never tell your parents?",
    "Have you ever kissed someone? (if no, who would you want to?)"
]

dare_bloxfruit = [
    "Go into PvP and fight someone using only sword",
    "Drop your current fruit if someone is nearby",
    "Spin a random fruit and must use it for 10 minutes",
    "Let someone else choose your build",
    "Go to sea 2 and help a random player",
    "Use a weak fruit in PvP and try to win",
    "Join a raid and don’t use abilities",
    "Give away 1 rare item if you lose a fight",
    "Use only basic attacks for 5 minutes",
    "Let someone else control your movement for 1 minute",
    "Go farm with no accessories",
    "Switch to random fighting style",
    "Help a beginner grind for 10 minutes",
    "Let your enemy hit you first in PvP",
    "Stand still in a PvP zone for 30 seconds"
]

dare_general = [
    "Text your last chat and say 'I miss you'",
    "Send a random emoji to your crush",
    "Call someone and stay silent for 10 seconds",
    "Type your last search in chat",
    "Compliment the next person who messages you",
    "Send 'I like you' to a random friend",
    "Change your nickname to something funny for 10 mins",
    "Spam a random emoji 10 times",
    "React to every message for 5 minutes",
    "Say something smooth in chat",
    "Confess a fake crush in chat",
    "Send a voice note saying hi (if possible)",
    "Type your most embarrassing thought",
    "Say something cheesy like you're in a romance movie",
    "Flirt lightly with someone in chat (no explicit content)"
]

# ================= VIEW =================

class TDView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_random(self):
        return random.choice(
            truth_bloxfruit + truth_general + dare_bloxfruit + dare_general
        )

    def get_truth(self):
        return random.choice(truth_bloxfruit + truth_general)

    def get_dare(self):
        return random.choice(dare_bloxfruit + dare_general)

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary)
    async def truth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Truth",
                description=self.get_truth(),
                color=0x00ffcc
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.danger)
    async def dare_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Dare",
                description=self.get_dare(),
                color=0xff4444
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Random", style=discord.ButtonStyle.success)
    async def random_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.get_random()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Random Challenge",
                description=result,
                color=0xf1c40f
            ),
            ephemeral=True
        )

# ================= COMMAND =================

@bot.command()
async def truthdare(ctx):
    embed = discord.Embed(
        title="🎮 Truth or Dare",
        description="Press a button to get your challenge.",
        color=0x2b2d31
    )

    await ctx.send(embed=embed, view=TDView())
bot.run(os.getenv("TOKEN"))
