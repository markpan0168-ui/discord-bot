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
