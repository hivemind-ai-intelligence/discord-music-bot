"""
Fun Commands Cog — Jokes, memes, 8ball, coin flip, dice, rock paper scissors.
6 Commands: joke, meme, 8ball, flip, roll, rps
"""

import discord
from discord.ext import commands
import random
import asyncio
import aiohttp

from utils.helpers import Emojis


class Fun(commands.Cog):
    """Fun and entertainment commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /joke ────────────────────────────────────────────────────

    @commands.hybrid_command(name="joke", description="Get a random joke")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def joke(self, ctx: commands.Context):
        """Fetch a random joke from the API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://official-joke-api.appspot.com/random_joke",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(
                            title=f"Random Joke",
                            description=f"**{data['setup']}**\n\n||{data['punchline']}||",
                            color=0xFEE75C,
                        )
                        await ctx.reply(embed=embed)
                        return
        except Exception:
            pass

        # Fallback jokes
        jokes = [
            ("Why don't scientists trust atoms?", "Because they make up everything!"),
            ("What do you call a fake noodle?", "An impasta!"),
            ("Why did the scarecrow win an award?", "Because he was outstanding in his field!"),
            ("What do you call cheese that isn't yours?", "Nacho cheese!"),
            ("Why don't eggs tell jokes?", "They'd crack each other up!"),
            ("What's brown and sticky?", "A stick!"),
            ("Why did the bicycle fall over?", "Because it was two-tired!"),
            ("What do you call a bear with no teeth?", "A gummy bear!"),
            ("Why can't a nose be 12 inches long?", "Because then it would be a foot!"),
            ("What time is it when an elephant sits on your fence?", "Time to get a new fence!"),
        ]

        setup, punchline = random.choice(jokes)
        embed = discord.Embed(
            title=f"Random Joke",
            description=f"**{setup}**\n\n||{punchline}||",
            color=0xFEE75C,
        )
        await ctx.reply(embed=embed)

    # ── /meme ────────────────────────────────────────────────────

    @commands.hybrid_command(name="meme", description="Get a random meme")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def meme(self, ctx: commands.Context):
        """Fetch a random meme from Reddit."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://meme-api.com/gimme",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(
                            title=data.get('title', 'Random Meme'),
                            color=0x5865F2,
                        )
                        embed.set_image(url=data.get('url', ''))
                        embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', 'memes')}")
                        await ctx.reply(embed=embed)
                        return
        except Exception:
            pass

        await ctx.reply(f"Couldn't fetch a meme right now. Try again!", delete_after=10)

    # ── /8ball ───────────────────────────────────────────────────

    EIGHTBALL_RESPONSES = [
        "🎱 It is certain.", "🎱 It is decidedly so.", "🎱 Without a doubt.",
        "🎱 Yes — definitely.", "🎱 You may rely on it.", "🎱 As I see it, yes.",
        "🎱 Most likely.", "🎱 Outlook good.", "🎱 Yes.",
        "🎱 Signs point to yes.", "🎱 Reply hazy, try again.", "🎱 Ask again later.",
        "🎱 Better not tell you now.", "🎱 Cannot predict now.", "🎱 Concentrate and ask again.",
        "🎱 Don't count on it.", "🎱 My reply is no.", "🎱 My sources say no.",
        "🎱 Outlook not so good.", "🎱 Very doubtful.",
    ]

    @commands.hybrid_command(name="8ball", description="Ask the magic 8ball a question")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def eightball(self, ctx: commands.Context, *, question: str):
        """Ask the magic 8ball a yes/no question."""
        response = random.choice(self.EIGHTBALL_RESPONSES)
        embed = discord.Embed(
            title=f"Magic 8Ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=0x2B2D31,
        )
        await ctx.reply(embed=embed)

    # ── /flip ────────────────────────────────────────────────────

    @commands.hybrid_command(name="flip", aliases=["coinflip"], description="Flip a coin")
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.user)
    async def flip(self, ctx: commands.Context):
        """Flip a coin — heads or tails."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        embed = discord.Embed(
            title=f"Coin Flip",
            description=f"🪙 The coin lands on... **{result}**!",
            color=0xFEE75C if result == "Heads" else 0x5865F2,
        )
        await ctx.reply(embed=embed)

    # ── /roll ────────────────────────────────────────────────────

    @commands.hybrid_command(name="roll", aliases=["dice"], description="Roll a dice")
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.user)
    async def roll(self, ctx: commands.Context, sides: int = 6):
        """Roll a dice with specified number of sides (default 6)."""
        if sides < 2 or sides > 100:
            await ctx.reply(f"Choose between 2 and 100 sides.", delete_after=10)
            return

        result = random.randint(1, sides)
        embed = discord.Embed(
            title=f"Dice Roll (d{sides})",
            description=f"🎲 You rolled: **{result}**",
            color=0x57F287,
        )
        await ctx.reply(embed=embed)

    # ── /rps ─────────────────────────────────────────────────────

    RPS_CHOICES = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

    class RPSView(discord.ui.View):
        def __init__(self, author_id: int):
            super().__init__(timeout=30)
            self.author_id = author_id
            self.choice = None

        @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.primary)
        async def btn_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Not your game!", ephemeral=True)
                return
            self.choice = "rock"
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.success)
        async def btn_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Not your game!", ephemeral=True)
                return
            self.choice = "paper"
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.danger)
        async def btn_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Not your game!", ephemeral=True)
                return
            self.choice = "scissors"
            await interaction.response.defer()
            self.stop()

    @commands.hybrid_command(name="rps", description="Play Rock Paper Scissors")
    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    async def rps(self, ctx: commands.Context):
        """Play Rock Paper Scissors against the bot."""
        embed = discord.Embed(
            title=f"Rock Paper Scissors",
            description="Choose your move!",
            color=0x5865F2,
        )

        view = self.RPSView(ctx.author.id)
        msg = await ctx.reply(embed=embed, view=view)

        await view.wait()

        if view.choice is None:
            await msg.edit(content="Game timed out!", embed=None, view=None)
            return

        user_choice = view.choice
        bot_choice = random.choice(list(self.RPS_CHOICES.keys()))
        user_emoji = self.RPS_CHOICES[user_choice]
        bot_emoji = self.RPS_CHOICES[bot_choice]

        # Determine winner
        if user_choice == bot_choice:
            result = "It's a **tie**! 🤝"
            color = 0xFEE75C
        elif (
            (user_choice == "rock" and bot_choice == "scissors")
            or (user_choice == "paper" and bot_choice == "rock")
            or (user_choice == "scissors" and bot_choice == "paper")
        ):
            result = f"**{ctx.author.name} wins**! 🎉"
            color = 0x57F287
        else:
            result = "**Bot wins**! 🤖"
            color = 0xED4245

        embed = discord.Embed(
            title=f"Rock Paper Scissors",
            description=f"{ctx.author.mention}: {user_emoji} **vs** {bot_emoji} :Bot\n\n{result}",
            color=color,
        )

        for child in view.children:
            child.disabled = True

        await msg.edit(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
