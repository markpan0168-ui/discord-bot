import random
import discord
from discord.ext import commands


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
    "Have you ever kissed someone?"
]

dare_bloxfruit = [
    "Go into PvP and fight using only sword",
    "Drop your current fruit if someone is nearby",
    "Spin a random fruit and use it for 10 minutes",
    "Let someone else choose your build",
    "Go help a random player",
    "Use a weak fruit in PvP",
    "Join a raid and don’t use abilities",
    "Give away a rare item if you lose a fight",
    "Use only basic attacks for 5 minutes",
    "Let someone control your movement for 1 minute",
    "Farm with no accessories",
    "Switch to random fighting style",
    "Help a beginner grind",
    "Let enemy hit you first",
    "Stand still in PvP zone for 30 seconds"
]

dare_general = [
    "Text your last chat and say 'I miss you'",
    "Send a random emoji to your crush",
    "Call someone and stay silent for 10 seconds",
    "Type your last search in chat",
    "Compliment the next person who messages you",
    "Send 'I like you' to a random friend",
    "Change your nickname for 10 mins",
    "Spam a random emoji 10 times",
    "React to every message for 5 minutes",
    "Say something smooth in chat",
    "Confess a fake crush in chat",
    "Send a voice note saying hi",
    "Type your most embarrassing thought",
    "Say something cheesy like romance movie dialogue",
    "Flirt lightly (keep it safe)"
]


# ================= VIEW =================

class TDView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_truth(self):
        return random.choice(truth_bloxfruit + truth_general)

    def get_dare(self):
        return random.choice(dare_bloxfruit + dare_general)

    def get_random(self):
        return random.choice(
            truth_bloxfruit + truth_general + dare_bloxfruit + dare_general
        )

    async def send_result(self, interaction, title, desc, color):
        await interaction.response.send_message(
            embed=discord.Embed(
                title=title,
                description=desc,
                color=color
            ),
            ephemeral=False
        )

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary, custom_id="td_truth")
    async def truth_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_result(interaction, "Truth", self.get_truth(), 0x00ffcc)

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.danger, custom_id="td_dare")
    async def dare_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_result(interaction, "Dare", self.get_dare(), 0xff4444)

    @discord.ui.button(label="Random", style=discord.ButtonStyle.success, custom_id="td_random")
    async def random_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_result(interaction, "Random Challenge", self.get_random(), 0xf1c40f)


# ================= COG =================

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TDView())

    # ONLY ONE COMMAND (FIXED DUPLICATE ISSUE)
    @commands.hybrid_command(name="tod", description="Truth or Dare game")
    async def tod(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎮 Truth or Dare",
            description="Click a button to get a challenge.",
            color=0x2b2d31
        )

        await ctx.send(embed=embed, view=TDView())


async def setup(bot):
    await bot.add_cog(Games(bot))
