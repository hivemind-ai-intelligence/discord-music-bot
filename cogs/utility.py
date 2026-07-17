"""
Utility Commands Cog — Avatar, banner, server info, user info, emoji info.
5 Commands: avatar, banner, serverinfo, userinfo, emojiinfo
"""

import discord
from discord.ext import commands
import datetime

from utils.helpers import Emojis, truncate, format_duration


class Utility(commands.Cog):
    """Utility and information commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /avatar ──────────────────────────────────────────────────

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"], description="Show user avatar")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """Display a user's avatar in full resolution."""
        target = user or ctx.author

        embed = discord.Embed(
            title=f"{target.display_name}'s Avatar",
            color=target.accent_color if hasattr(target, 'accent_color') and target.accent_color else 0x5865F2,
            url=target.display_avatar.url if target.display_avatar else None,
        )

        if target.display_avatar:
            embed.set_image(url=target.display_avatar.url)
        else:
            embed.description = "No avatar set."

        # Add avatar URLs
        if target.display_avatar:
            embed.add_field(
                name="Download",
                value=f"[PNG]({target.display_avatar.with_format('png').url}) • "
                      f"[JPG]({target.display_avatar.with_format('jpg').url}) • "
                      f"[WEBP]({target.display_avatar.with_format('webp').url})",
                inline=False,
            )

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    # ── /banner ──────────────────────────────────────────────────

    @commands.hybrid_command(name="banner", description="Show user banner")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        """Display a user's profile banner."""
        target = user or ctx.author

        # Fetch user to get banner
        try:
            fetched = await self.bot.fetch_user(target.id)
        except Exception:
            fetched = target

        banner = getattr(fetched, 'banner', None)

        if not banner:
            accent_color = getattr(target, 'accent_color', None)
            if accent_color:
                embed = discord.Embed(
                    title=f"{target.display_name}'s Banner",
                    description=f"No banner set. Accent color: `{accent_color}`",
                    color=accent_color,
                )
            else:
                embed = discord.Embed(
                    title=f"{target.display_name}'s Banner",
                    description="No banner set.",
                    color=0x2B2D31,
                )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.reply(embed=embed)
            return

        embed = discord.Embed(
            title=f"{target.display_name}'s Banner",
            color=getattr(target, 'accent_color', None) or 0x5865F2,
        )

        embed.set_image(url=banner.url)
        embed.add_field(
            name="Download",
            value=f"[PNG]({banner.with_format('png').url}) • "
                  f"[JPG]({banner.with_format('jpg').url}) • "
                  f"[WEBP]({banner.with_format('webp').url})",
            inline=False,
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    # ── /serverinfo ──────────────────────────────────────────────

    @commands.hybrid_command(name="serverinfo", aliases=["guildinfo", "si"], description="Show server info")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        """Display detailed information about the current server."""
        guild = ctx.guild

        # Basic info
        created_at = int(guild.created_at.timestamp())
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles_count = len(guild.roles)

        embed = discord.Embed(
            title=f"{guild.name}",
            color=0x5865F2,
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Created", value=f"<t:{created_at}:R>\n<t:{created_at}:D>", inline=True)

        embed.add_field(name="Members", value=f"👥 {total_members} total\n🟢 {online_members} online", inline=True)
        embed.add_field(
            name="Channels",
            value=f"💬 {text_channels} text\n🔊 {voice_channels} voice",
            inline=True,
        )
        embed.add_field(name="Roles", value=str(roles_count), inline=True)

        # Boosts
        if guild.premium_tier > 0:
            embed.add_field(name="Boosts", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)

        # Verification level
        embed.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    # ── /userinfo ────────────────────────────────────────────────

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"], description="Show user info")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def userinfo(self, ctx: commands.Context, user: discord.Member = None):
        """Display detailed information about a user."""
        target = user or ctx.author

        created_at = int(target.created_at.timestamp())
        joined_at = int(target.joined_at.timestamp()) if target.joined_at else None

        embed = discord.Embed(
            title=f"{target.display_name}",
            color=target.color if target.color.value else 0x5865F2,
        )

        if target.display_avatar:
            embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(name="Username", value=str(target), inline=True)
        embed.add_field(name="User ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Nickname", value=target.nick or "None", inline=True)

        embed.add_field(name="Account Created", value=f"<t:{created_at}:R>\n<t:{created_at}:D>", inline=True)

        if joined_at:
            embed.add_field(name="Joined Server", value=f"<t:{joined_at}:R>\n<t:{joined_at}:D>", inline=True)

        # Status
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫",
        }
        embed.add_field(name="Status", value=f"{status_emoji.get(target.status, '⚫')} {target.status}", inline=True)

        # Activity
        if target.activity:
            activity_type = str(target.activity.type).replace("ActivityType.", "").title()
            embed.add_field(name="Activity", value=f"{activity_type}: {target.activity.name}", inline=True)

        # Roles
        roles = [role.mention for role in reversed(target.roles) if role != ctx.guild.default_role]
        if roles:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                inline=False,
            )

        # Badges
        badges = []
        if target.public_flags:
            flags = target.public_flags
            flag_map = {
                'hypesquad_bravery': "🦁 HypeSquad Bravery",
                'hypesquad_brilliance': "🧠 HypeSquad Brilliance",
                'hypesquad_balance': "⚖️ HypeSquad Balance",
                'early_supporter': "🏅 Early Supporter",
                'bug_hunter_level_1': "🐛 Bug Hunter",
                'bug_hunter_level_2': "🐛 Bug Hunter Lv2",
                'verified_bot_developer': "👑 Early Verified Developer",
                'active_developer': "💻 Active Developer",
                'staff': "🔧 Discord Staff",
                'partner': "🤝 Partner",
            }
            for flag_name, label in flag_map.items():
                if getattr(flags, flag_name, False):
                    badges.append(label)

        if badges:
            embed.add_field(name="Badges", value="\n".join(badges), inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    # ── /emojiinfo ───────────────────────────────────────────────

    @commands.hybrid_command(name="emojiinfo", description="Show information about an emoji")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def emojiinfo(self, ctx: commands.Context, emoji: str):
        """Display info about a custom emoji."""
        # Try to extract emoji ID
        emoji_id = None
        animated = False

        # Parse custom emoji format: <a?:name:id>
        if emoji.startswith("<") and emoji.endswith(">"):
            parts = emoji.strip("<>").split(":")
            if len(parts) >= 3:
                animated = parts[0].lower() == "a"
                emoji_name = parts[1]
                try:
                    emoji_id = int(parts[2])
                except ValueError:
                    pass
        else:
            await ctx.reply(
                f"Please provide a custom emoji (e.g., `:emoji:`).",
                delete_after=10,
            )
            return

        if emoji_id:
            ext = "gif" if animated else "png"
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"

            embed = discord.Embed(
                title=f"Emoji: {emoji_name}",
                color=0x5865F2,
            )
            embed.set_thumbnail(url=emoji_url)
            embed.add_field(name="Name", value=f"`{emoji_name}`", inline=True)
            embed.add_field(name="ID", value=f"`{emoji_id}`", inline=True)
            embed.add_field(name="Animated", value="Yes" if animated else "No", inline=True)
            embed.add_field(name="Mention", value=f"`{emoji}`", inline=True)
            embed.add_field(name="URL", value=f"[{ext.upper()} Link]({emoji_url})", inline=True)

            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
