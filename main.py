"""
███████╗██╗  ██╗ █████╗ ███╗   ██╗██████╗ ██╗██████╗ 
██╔════╝██║  ██║██╔══██╗████╗  ██║██╔══██╗██║██╔══██╗
███████╗███████║███████║██╔██╗ ██║██║  ██║██║██████╔╝
╚════██║██╔══██║██╔══██║██║╚██╗██║██║  ██║██║██╔═══╝ 
███████║██║  ██║██║  ██║██║ ╚████║██████╔╝██║██║     
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝╚═╝     
                                                       
Shandip's Discord Music Bot — 48 Slash Commands, Music + Name Styles
"""

import discord
from discord.ext import commands
import wavelink
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# ── Load Environment ────────────────────────────────────────────────

load_dotenv()

# ── Logging Setup ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MusicBot")


# ── Bot Class ───────────────────────────────────────────────────────

class MusicBot(commands.Bot):
    """Main bot class with integrated Lavalink (wavelink) support."""

    def __init__(self):
        # Intents — all enabled for maximum compatibility
        intents = discord.Intents.all()

        super().__init__(
            command_prefix="m!",
            intents=intents,
            help_command=None,  # Custom help in General cog
            case_insensitive=True,
            strip_after_prefix=True,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/play | m!play"
            ),
            status=discord.Status.online,
        )

    # ── Startup ─────────────────────────────────────────────────

    async def setup_hook(self):
        """Called when the bot starts — load cogs and connect to Lavalink."""
        logger.info("Starting MusicBot...")

        # ── Load Cogs ────────────────────────────────────────
        cogs = [
            "cogs.music",
            "cogs.namestyle",
            "cogs.general",
            "cogs.fun",
            "cogs.utility",
        ]

        loaded = 0
        failed = 0

        for cog in cogs:
            try:
                await self.load_extension(cog)
                loaded += 1
                logger.info(f"  ✓ Loaded: {cog}")
            except Exception as e:
                failed += 1
                logger.error(f"  ✗ Failed: {cog} — {e}")

        logger.info(f"Cogs: {loaded} loaded, {failed} failed")

        # ── Connect to Lavalink ──────────────────────────────
        lavalink_host = os.getenv("LAVALINK_HOST", "localhost")
        lavalink_port = int(os.getenv("LAVALINK_PORT", "2333"))
        lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
        lavalink_secure = os.getenv("LAVALINK_SECURE", "false").lower() == "true"

        uri = f"{'https' if lavalink_secure else 'http'}://{lavalink_host}:{lavalink_port}"

        try:
            nodes = [
                wavelink.Node(
                    uri=uri,
                    password=lavalink_password,
                )
            ]
            await wavelink.Pool.connect(nodes=nodes, client=self)
            logger.info(f"  ✓ Connected to Lavalink at {uri}")
        except Exception as e:
            logger.error(f"  ✗ Lavalink connection failed: {e}")
            logger.warning("  ⚠ Music features will NOT work until Lavalink is available!")

    async def on_ready(self):
        """Called when the bot is fully ready."""
        logger.info(f"Logged in as: {self.user} (ID: {self.user.id})")
        logger.info(f"Servers: {len(self.guilds)}")
        logger.info(f"Users: {sum(g.member_count for g in self.guilds)}")

        # ── Sync Slash Commands ──────────────────────────────
        try:
            synced = await self.tree.sync()
            logger.info(f"Slash commands synced: {len(synced)} globally")
        except Exception as e:
            logger.error(f"Command sync failed: {e}")

        logger.info("=" * 50)
        logger.info("MusicBot is READY! 🎵")
        logger.info("=" * 50)

    async def on_command_error(self, ctx: commands.Context, error):
        """Global error handler — catch all command errors gracefully."""
        # Ignore some errors
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f"⏳ Slow down! Try again in `{error.retry_after:.1f}s`.",
                delete_after=8,
            )
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌%20You%20don't%20have%20permission.", delete_after=8)
            return
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.reply(f"❌!20I%20need:%20{', '.join(error.missing_permissions)}", delete_after=10)
            return

        # Log unexpected errors
        logger.error(f"Command%20error%20in%20{ctx.command}:%20{error}")
        await ctx.reply(f"❌%20An%20error%20occurred:%20`{error}`", delete_after=10)

    async def on_guild_join(self, guild: discord.Guild):
        """Re-apply saved name style when joining a guild."""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")

        # Re-apply saved name style
        from utils.db import get_namestyle_settings
        from utils.namestyle_data import apply_name_style

        style = get_namestyle_settings(guild.id)
        if style:
            try:
                await apply_name_style(
                    self.http.token,
                    guild.id,
                    style['font_id'],
                    style['effect_id'],
                    style['colors'],
                )
                logger.info(f"  ✓ Re-applied name style for {guild.name}")
            except Exception as e:
                logger.warning(f"  ⚠ Failed to re-apply name style: {e}")


# ── Entry Point ─────────────────────────────────────────────────────

def main():
    """Start the bot."""
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        logger.critical("=" * 50)
        logger.critical("DISCORD_TOKEN not set in .env file!")
        logger.critical("1. Copy .env.example to .env")
        logger.critical("2. Fill in your bot token")
        logger.critical("=" * 50)
        sys.exit(1)

    bot = MusicBot()
    bot.run(token)


if __name__ == "__main__":
    main()
