"""
General Commands Cog — Bot info, ping, stats, help, invite, uptime.
7 Commands: ping, stats, invite, help, info, uptime, vote
"""

import discord
from discord.ext import commands
import datetime
import time
import platform

from utils.helpers import Emojis, format_duration, truncate


class General(commands.Cog):
    """General bot commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    @property
    def uptime(self) -> datetime.timedelta:
        return datetime.datetime.now(datetime.timezone.utc) - self.start_time

    @commands.hybrid_command(name="ping", description="Check bot latency")
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """Show bot latency and WebSocket ping."""
        start = time.perf_counter()
        msg = await ctx.reply(f"{Emojis.PING} Pinging...")
        end = time.perf_counter()

        api_latency = round((end - start) * 1000)
        ws_latency = round(self.bot.latency * 1000)

        embed = discord.Embed(title=f"{Emojis.PING} Pong!", color=0x57F287)
        embed.add_field(name="API Latency", value=f"`{api_latency}ms`", inline=True)
        embed.add_field(name="WebSocket", value=f"`{ws_latency}ms`", inline=True)

        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="stats", description="Bot statistics")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """Show bot statistics."""
        total_guilds = len(self.bot.guilds)
        total_users = sum(g.member_count for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)

        embed = discord.Embed(
            title=f"{Emojis.STATS} Bot Statistics",
            color=0x5865F2,
        )

        embed.add_field(name="Servers", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="Users", value=f"`{total_users}`", inline=True)
        embed.add_field(name="Channels", value=f"`{total_channels}`", inline=True)

        embed.add_field(name="Python", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="discord.py", value=f"`{discord.__version__}}`", inline=True)
        embed.add_field(name="Uptime", value=f"`{format_duration(int(self.uptime.total_seconds() * 1000))}`", inline=True)

        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
        embed.set_footer(text=f"Shard: {ctx.guild.shard_id if hasattr(ctx.guild, 'shard_id') else 'N/A'}")

        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="invite", description="Get bot invite link")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """Generate and show the bot invite link."""
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(
                send_messages=True,
                connect=True,
                speak=True,
                use_voice_activation=True,
                change_nickname=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                add_reactions=True,
                use_external_emojis=True,
                use_external_stickers=True,
                create_instant_invite=True,
            ),
            scopes=["bot", "applications.commands"],
        )

        embed = discord.Embed(
            title=f"{Emojis.INVITE} Invite Me!",
            description=f"Click the link below to add me to your server:\n\n"
                        f"**[🔗 Invite Link]({invite_url})**",
            color=0x57F287,
        )

        embed.add_field(
            name="Required Permissions",
            value="• Send Messages\n• Connect & Speak\n• Embed Links\n"
                  "• Change Nickname *(for name styles)*\n• Use External Emojis",
            inline=False,
        )

        embed.set_footer(text="Thank you for using the bot! ❄️")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="help", description="Show help menu")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def help(self, ctx: commands.Context, category: str = None):
        """Display the help menu with all commands."""
        categories = {
            "music": {
                "emoji": Emojis.MUSIC,
                "commands": [
                    "`/play` — Play a song", `/pause` — Pause", "`/resume` — Resume",
                    "`/skip` — Skip", "`/stop` — Stop & disconnect",
                    "`/loop` — Toggle loop", "`/queue` — View queue",
                    "`/shuffle` — Shuffle queue", "`/remove` — Remove track",
                    "`/clearqueue` — Clear queue", "`/volume` — Set volume",
                    "`/nowplaying` — Current track", "`/seek` — Seek position",
                    "`/restart` — Restart track", "`/join` — Join VC",
                    "`/leave` — Leave VC", "`/autoplay` — Toggle autoplay",
                    "`/lyrics` — Get lyrics", "`/bassboost` — Bass boost",
                    "`/speed` — Playback speed", "`/move` — Move track",
                    "`/save` — Save to DMs", "`/history` — Play history",
                    "`/24-7` — 24/7 mode",
                ],
            },
            "namestyle": {
                "emoji": Emojis.FONT,
                "commands": [
                    "`/namestyle set` — Setup style", `/namestyle reset` — Reset style",
                    "`/namestyle list` — Fonts & effects", "`/namestyle presets` — Presets",
                    "`/namestyle preview` — Preview preset", "`/namestyle current` — Current style",
                    "`/namestyle info` — Rules & limits",
                ],
            },
            "general": {
                "emoji": Emojis.INFO,
                "commands": [
                    "`/ping` — Bot latency", "`/stats` — Statistics",
                    "`/invite` — Invite link", "`/help` — This menu",
                    "`/info` — Bot info", "`/uptime` — Uptime",
                    "`/vote` — Vote link",
                ],
            },
            "fun": {
                "emoji": Emojis.JOKE,
                "commands": [
                    "`/joke` — Random joke", "`/meme` — Random meme",
                    "`/8ball` — Magic 8ball", "`/flip` — Coin flip",
                    "`/roll` — Dice roll", "`/rps` — Rock paper scissors",
                ],
            },
            "utility": {
                "emoji": Emojis.USER,
                "commands": [
                    "`/avatar` — User avatar", "`/banner` — User banner",
                    "`/serverinfo` — Server info", "`/userinfo` — User info",
                    "`/emojiinfo` — Emoji info",
                ],
            },
        }

        if category and category.lower() in categories:
            cat = categories[category.lower()]
            embed = discord.Embed(
                title=f"{cat['emoji']} {category.title()} Commands",
                description="\n".join(cat['commands']),
                color=0x5865F2,
            )
            embed.set_footer(text=f"Use /help for all categories")
            await ctx.reply(embed=embed)
            return

        # Full help menu
        embed = discord.Embed(
            title=f"{Emojis.HELP} Help Menu",
            description=f"**{self.bot.user.name}** — A powerful Discord Music Bot with custom Name Styles!\n"
                        f"Use `/help <category>` for details on a specific category.",
            color=0x5865F2,
        )

        for cat_name, cat_data in categories.items():
            embed.add_field(
                name=f"{cat_data['emoji']} {cat_name.title()} ({len(cat_data['commands'])} commands)",
                value=f"`/help {cat_name}` for details",
                inline=False,
            )

        embed.set_footer(text=f"Total: 48 commands • Prefix: m!")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="info", description="Bot information")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def info(self, ctx: commands.Context):
        """Show detailed bot information."""
        embed = discord.Embed(
            title=f"{Emojis.BOT} About {self.bot.user.name}",
            description="A feature-rich Discord Music Bot with customizable Name Styles, "
                        "40+ slash commands, and a beautiful music controller.",
            color=0x5865F2,
        )

        embed.add_field(name="Developer", value="Shandip", inline=True)
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(
            name="Features",
            value="• YouTube Music Streaming\n• Queue Management\n• Audio Filters (Bass Boost, Speed)\n"
                  "• Custom Name Styles (12 fonts, 6 effects)\n• Interactive Controller\n• 24/7 Mode",
            inline=False,
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="uptime", description="Show bot uptime")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def uptime(self, ctx: commands.Context):
        """Show how long the bot has been online."""
        uptime_delta = self.uptime
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        embed = discord.Embed(
            title=f"{Emojis.UPTIME} Uptime",
            description=f"**{' '.join(parts)}**",
            color=0x57F287,
        )
        embed.add_field(name="Started", value=f"<t:{int(self.start_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Started At", value=f"<t:{int(self.start_time.timestamp())}:F>", inline=True)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="vote", description="Vote for the bot")
    @commands.cooldown(rate=2, per=30, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context):
        """Show vote/support links."""
        embed = discord.Embed(
            title=f"{Emojis.STAR} Support & Vote",
            description="Love the bot? Show your support!",
            color=0xFEE75C,
        )
        embed.add_field(
            name="Links",
            value="• **Vote** — Coming soon on top.gg\n"
                  "• **Invite** — Use `/invite`\n"
                  "• **Support** — Join the support server\n\n"
                  "Thank you for your support! ❤️",
            inline=False,
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
