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


