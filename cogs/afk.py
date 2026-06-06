from discord.ext import commands

# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):

    afk_users[ctx.author.id] = reason

    try:
        nick = ctx.author.display_name

if not nick.startswith("[AFK] "):
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

afk_list = []

for user in message.mentions:
    if user.bot:
        continue

    if user.id in afk_users:
        afk_list.append(
            f"{user.mention} - {afk_users[user.id]}"
        )

if afk_list:
    await message.channel.send(
        embed=embed(
            "AFK Users",
            "\n".join(afk_list),
            0xffcc00
        )
    )

# stores user roles before suspension
suspend_cache = {}
