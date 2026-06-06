from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Moderation(bot))

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

# save roles
suspend_cache[member.id] = [
    r.id for r in member.roles
    if r != interaction.guild.default_role
]

# remove roles
roles_to_remove = [
    role for role in member.roles
    if role != interaction.guild.default_role
]

await member.remove_roles(*roles_to_remove)

# add suspended role
suspended_role = interaction.guild.get_role(SUSPENDED_ROLE_ID)

if suspended_role:
    await member.add_roles(suspended_role)

    await add_stat(member.id, "suspensions")
    await add_mod_stat(interaction.user.id, "suspensions")

    channel = bot.get_channel(SUSPENDED_CHANNEL_ID)
    appeal = bot.get_channel(APPEAL_CHANNEL_ID)

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

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def suspend(ctx, member: discord.Member, *, reason="No reason"):

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


@tree.command(name="unmute", description="Remove a timeout from a user")
@app_commands.checks.has_role(MOD_ROLE_ID)
async def unmute_slash(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason"
):
    try:
        await member.timeout(None, reason=reason)
    except Exception as e:
        return await interaction.response.send_message(
            embed=embed("Error", str(e), 0xff0000),
            ephemeral=True
        )

    await add_mod_stat(interaction.user.id, "unmutes")

    await interaction.response.send_message(
        embed=embed(
            "Unmuted",
            f"{member.mention} unmuted",
            0x00ff88
        )
    )

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
                "Removes all roles and gives the Suspended role."
            ))

        elif cmd == "unmute":
            return await ctx.send(embed=usage_embed(
                ",unmute",
                ",unmute @user [reason]",
                "Remove a user's timeout."
            ))

        elif cmd == "unsuspend":
            return await ctx.send(embed=usage_embed(
                ",unsuspend @user [reason]",
                ",unsuspend @user [reason]",
                "Restore a suspended user's roles."
            ))

    raise error
