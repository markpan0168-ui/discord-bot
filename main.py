bot = commands.Bot(
    command_prefix=",",
    intents=discord.Intents.all()
)

async def load_cogs():
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.afk")
    await bot.load_extension("cogs.utility")
    await bot.load_extension("cogs.games")
    await bot.load_extension("cogs.stats")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

asyncio.run(load_cogs())
bot.run(TOKEN)
