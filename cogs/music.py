"""
Music Cog — Complete Discord Music System
Adapted from REO Bot's music.py, rewritten for standalone deployment.
Uses wavelink (Lavalink) for audio playback.

Features: Play, Pause, Resume, Skip, Stop, Loop, Queue, Shuffle,
          Remove, Clear, Volume, NowPlaying, Seek, Restart,
          Join, Leave, Autoplay, Lyrics, BassBoost, Speed, Move, Save, History
"""

import discord
from discord.ext import commands
import wavelink
import asyncio
import datetime
import traceback
from typing import Optional, Dict, List, Any

from utils.helpers import (
    Emojis, format_duration, truncate, is_url,
    progress_bar, volume_bar, safe_int
)
from utils.db import get_music_settings, update_music_setting


# ── Music Controller View ───────────────────────────────────────────


class VolumeModal(discord.ui.Modal):
    """Modal for setting precise volume."""

    def __init__(self, cog: "Music", guild_id: int, current_vol: int):
        super().__init__(title="Volume Control")
        self.cog = cog
        self.guild_id = guild_id
        self.vol_input = discord.ui.TextInput(
            label="Volume (0-100)",
            placeholder=str(current_vol),
            default=str(current_vol),
            max_length=3,
            required=True,
        )
        self.add_item(self.vol_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            vol = int(self.vol_input.value)
            if vol < 0 or vol > 100:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("Volume must be 0-100.", ephemeral=True)
            return

        player: wavelink.Player = interaction.guild.voice_client
        if player and isinstance(player, wavelink.Player):
            await player.set_volume(vol)
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(f"Volume: {vol}%", ephemeral=True)
            await self.cog.update_controller(interaction.guild)
        else:
            await interaction.response.send_message("No active player.", ephemeral=True)


class SeekModal(discord.ui.Modal):
    """Modal for seeking to a position."""

    def __init__(self, cog: "Music", guild_id: int, duration: int):
        super().__init__(title="Seek Position")
        self.cog = cog
        self.guild_id = guild_id
        total_sec = duration // 1000 if duration else 0
        mins = total_sec // 60
        secs = total_sec % 60
        self.seek_input = discord.ui.TextInput(
            label=f"Seconds (0-{total_sec}) or mm:ss",
            placeholder="e.g. 90 or 1:30",
            max_length=6,
            required=True,
        )
        self.add_item(self.seek_input)

    async def on_submit(self, interaction: discord.Interaction):
        from utils.helpers import safe_int
        raw = self.seek_input.value.strip()

        # Parse mm:ss or plain seconds
        if ":" in raw:
            parts = raw.split(":")
            try:
                secs = int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                await interaction.response.send_message("Invalid format. Use seconds or mm:ss.", ephemeral=True)
                return
        else:
            secs = safe_int(raw)
            if secs is None:
                await interaction.response.send_message("Enter a valid number.", ephemeral=True)
                return

        player: wavelink.Player = interaction.guild.voice_client
        if not player or not isinstance(player, wavelink.Player):
            await interaction.response.send_message("No active player.", ephemeral=True)
            return

        dur = (player.current.length or 1) // 1000
        if secs < 0 or secs > dur:
            await interaction.response.send_message(f"Must be 0-{dur} seconds.", ephemeral=True)
            return

        await player.seek(secs * 1000)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Seeked to {secs}s", ephemeral=True)
        await self.cog.update_controller(interaction.guild)


class MusicControllerView(discord.ui.View):
    """Interactive music controller with buttons."""

    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    async def _validate(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """Validate that the user can interact with the controller."""
        player: wavelink.Player = interaction.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await interaction.response.send_message(
                f"Player is not active.", ephemeral=True, delete_after=6
            )
            return None

        if not interaction.user.voice:
            await interaction.response.send_message(
                f"Join a voice channel first.",
                ephemeral=True, delete_after=6,
            )
            return None

        if player.channel and interaction.user.voice.channel != player.channel:
            await interaction.response.send_message(
                f"You must be in the same voice channel.",
                ephemeral=True, delete_after=6,
            )
            return None

        return player

    # ── Buttons ─────────────────────────────────────────────────

    @discord.ui.button(label="Pause/Resume", emoji="⏯️", style=discord.ButtonStyle.primary, row=0, custom_id="music_pause_resume")
    async def btn_pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)
        if player.paused:
            await player.pause(False)
            await interaction.followup.send(f"Resumed!", ephemeral=True)
        else:
            await player.pause(True)
            await interaction.followup.send(f"Paused!", ephemeral=True)

        await self.cog.update_controller(interaction.guild)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary, row=0, custom_id="music_skip")
    async def btn_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)

        if player.queue or player.autoplay != wavelink.AutoPlayMode.disabled:
            await player.skip(force=True)
            await interaction.followup.send(f"Skipped!", ephemeral=True)
        else:
            await interaction.followup.send(
                f"Nothing left in queue.", ephemeral=True
            )

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=0, custom_id="music_stop")
    async def btn_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)
        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await self.cog.update_controller(interaction.guild, idle=True)
        await interaction.followup.send(f"Stopped & disconnected.", ephemeral=True)

    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, row=1, custom_id="music_loop")
    async def btn_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            await interaction.followup.send(f"Loop disabled.", ephemeral=True)
        else:
            player.queue.mode = wavelink.QueueMode.loop
            await interaction.followup.send(f"Loop enabled.", ephemeral=True)

        await self.cog.update_controller(interaction.guild)

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1, custom_id="music_shuffle")
    async def btn_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)

        if player.queue:
            import random
            items = list(player.queue)
            random.shuffle(items)
            player.queue.clear()
            for item in items:
                await player.queue.put_wait(item)
            await interaction.followup.send(f"Queue shuffled!", ephemeral=True)
            await self.cog.update_controller(interaction.guild)
        else:
            await interaction.followup.send(f"Queue is empty.", ephemeral=True)

    @discord.ui.button(label="Autoplay", emoji="♾️", style=discord.ButtonStyle.secondary, row=1, custom_id="music_autoplay")
    async def btn_autoplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return

        await interaction.response.defer(ephemeral=True)

        if player.autoplay == wavelink.AutoPlayMode.disabled:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await interaction.followup.send(f"Autoplay enabled.", ephemeral=True)
        else:
            player.autoplay = wavelink.AutoPlayMode.disabled
            await interaction.followup.send(f"Autoplay disabled.", ephemeral=True)

        await self.cog.update_controller(interaction.guild)

    @discord.ui.button(label="Vol+10", emoji="🔊", style=discord.ButtonStyle.secondary, row=2, custom_id="music_vol_up")
    async def btn_vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return
        new_vol = min(player.volume + 10, 100)
        await player.set_volume(new_vol)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Volume: {new_vol}%", ephemeral=True)
        await self.cog.update_controller(interaction.guild)

    @discord.ui.button(label="Vol-10", emoji="🔉", style=discord.ButtonStyle.secondary, row=2, custom_id="music_vol_down")
    async def btn_vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return
        new_vol = max(player.volume - 10, 0)
        await player.set_volume(new_vol)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Volume: {new_vol}%", ephemeral=True)
        await self.cog.update_controller(interaction.guild)

    @discord.ui.button(label="Vol Set", emoji="🎚️", style=discord.ButtonStyle.secondary, row=2, custom_id="music_vol_modal")
    async def btn_vol_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return
        await interaction.response.send_modal(VolumeModal(self.cog, self.guild_id, player.volume))

    @discord.ui.button(label="Seek", emoji="⏩", style=discord.ButtonStyle.secondary, row=2, custom_id="music_seek")
    async def btn_seek(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._validate(interaction)
        if not player:
            return
        dur = player.current.length if player.current else 0
        await interaction.response.send_modal(SeekModal(self.cog, self.guild_id, dur))

    @discord.ui.button(label="Help", emoji="❓", style=discord.ButtonStyle.secondary, row=3, custom_id="music_help")
    async def btn_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        help_text = (
            "**Controls**\n"
            "⏯️ Pause/Resume  •  ⏭️ Skip  •  ⏹️ Stop\n"
            "🔁 Loop toggle  •  🔀 Shuffle queue  •  ♾️ Autoplay\n"
            "🔊 Vol+10  •  🔉 Vol-10  •  🎚️ Set exact volume\n"
            "⏩ Seek position\n\n"
            "**Commands:** `/play` `/pause` `/skip` `/queue` `/volume` `/seek` `/loop` `/nowplaying`"
        )
        await interaction.followup.send(help_text, ephemeral=True)


# ── Music Cog ───────────────────────────────────────────────────────

class Music(commands.Cog):
    """Complete Music System with 23 commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.controller_messages: Dict[int, discord.Message] = {}
        self.play_history: Dict[int, List[wavelink.Playable]] = {}
        self._cooldowns: Dict[int, datetime.datetime] = {}
        self._requesters: Dict[int, str] = {}

    # ── Utility Methods ─────────────────────────────────────────

    def _add_history(self, guild_id: int, track: wavelink.Playable):
        """Add track to play history (max 20)."""
        if guild_id not in self.play_history:
            self.play_history[guild_id] = []
        self.play_history[guild_id].insert(0, track)
        if len(self.play_history[guild_id]) > 20:
            self.play_history[guild_id].pop()

    def _build_queue_preview(self, player: wavelink.Player) -> str:
        """Build a text preview of the queue."""
        if not player or not player.current:
            return "-# No active session."

        lines = [f"**Now** — `{truncate(player.current.title, 48)}`"]

        queue_items = list(player.queue)
        if queue_items:
            for i, track in enumerate(queue_items[:5], start=1):
                lines.append(
                    f"**#{i}** — `{truncate(track.title, 40)}` — `{format_duration(track.length)}`"
                )
            if len(queue_items) > 5:
                lines.append(f"-# +{len(queue_items) - 5} more tracks...")
        else:
            lines.append("-# Queue is empty")

        return "\n".join(lines)

    def build_controller_embed(self, player: Optional[wavelink.Player], guild_id: Optional[int] = None) -> discord.Embed:
        """Build embed matching reference style — clean, bullet points, no bar."""
        GREY = 0x2B2D31

        if not player or not player.current:
            embed = discord.Embed(
                title="Music Controller",
                description="Nothing is playing right now.\nUse `/play <song>` to start a session!",
                color=GREY,
            )
            return embed

        current = player.current
        duration = current.length or 1
        paused = player.paused

        embed = discord.Embed(
            title="Paused" if paused else "Now Playing",
            color=GREY,
        )

        # Description: • bullet style matching reference
        requester = ""
        if guild_id and guild_id in self._requesters:
            requester = f" - (@{self._requesters[guild_id]})"

        embed.description = (
            f"• {truncate(current.title, 50)} - {current.author}\n"
            f"• Duration: {format_duration(duration)}{requester}"
        )

        # Song poster — artwork first, fallback to YT thumbnail
        artwork_url = getattr(current, 'artwork', None)
        if artwork_url and str(artwork_url).startswith("http"):
            embed.set_thumbnail(url=str(artwork_url))
        elif hasattr(current, 'identifier') and current.identifier:
            ytid = str(current.identifier)
            if ytid:
                embed.set_thumbnail(url=f"https://img.youtube.com/vi/{ytid}/mqdefault.jpg")

        # Stats — inline, no emojis
        queue_count = len(player.queue)
        loop_on = player.queue.mode == wavelink.QueueMode.loop
        ap_on = player.autoplay != wavelink.AutoPlayMode.disabled

        embed.add_field(name="Queue", value=f"`{queue_count}`", inline=True)
        embed.add_field(name="Volume", value=f"`{player.volume}%`", inline=True)
        embed.add_field(name="Loop", value="On" if loop_on else "Off", inline=True)
        embed.add_field(name="Auto", value="On" if ap_on else "Off", inline=True)

        # Queue preview
        queue_items = list(player.queue)
        if queue_items:
            lines = []
            for i, t in enumerate(queue_items[:3], 1):
                lines.append(f"`{i}.` {truncate(t.title, 34)}  `{format_duration(t.length)}`")
            if len(queue_items) > 3:
                lines.append(f"... +{len(queue_items) - 3} more")
            embed.add_field(name="Up Next", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="Up Next", value="Queue is empty", inline=False)

        # Footer — clean, no emojis
        now = datetime.datetime.utcnow().strftime("%H:%M")
        footer = f"{format_duration(duration)}  •  {now}"
        if guild_id and guild_id in self._requesters:
            footer += f"  •  {self._requesters[guild_id]}"
        embed.set_footer(text=footer)

        return embed

    async def update_controller(
        self,
        guild: discord.Guild,
        idle: bool = False,
        channel: Optional[discord.TextChannel] = None
    ):
        """Send or update the music controller message."""
        player: Optional[wavelink.Player] = guild.voice_client

        if idle or not player or not player.current:
            view = MusicControllerView(self, guild.id)
            # Disable buttons when idle
            for child in view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            embed = self.build_controller_embed(None, guild.id)

            existing = self.controller_messages.get(guild.id)
            if existing:
                try:
                    await existing.edit(embed=embed, view=view)
                except (discord.NotFound, discord.HTTPException):
                    pass
            elif channel:
                msg = await channel.send(embed=embed, view=view)
                self.controller_messages[guild.id] = msg
            return

        # Active player
        view = MusicControllerView(self, guild.id)
        embed = self.build_controller_embed(player, guild.id)

        existing = self.controller_messages.get(guild.id)
        if existing:
            try:
                await existing.edit(embed=embed, view=view)
            except (discord.NotFound, discord.HTTPException):
                if channel:
                    msg = await channel.send(embed=embed, view=view)
                    self.controller_messages[guild.id] = msg
        elif channel:
            msg = await channel.send(embed=embed, view=view)
            self.controller_messages[guild.id] = msg

    # ── Connection Helper ────────────────────────────────────────

    async def _connect_player(
        self, ctx: commands.Context, search: str
    ) -> Optional[wavelink.Player]:
        """Connect to VC and return player, handling all edge cases."""
        # Check user voice
        if not ctx.author.voice:
            await ctx.reply(f"Join a voice channel first!", delete_after=10)
            return None

        if not ctx.author.voice.channel:
            await ctx.reply(f"Cannot determine your voice channel.", delete_after=10)
            return None

        destination = ctx.author.voice.channel

        if not ctx.guild.voice_client:
            try:
                player: wavelink.Player = await destination.connect(
                    cls=wavelink.Player, timeout=30, self_deaf=True
                )
                player.inactive_timeout = 120  # 2 min auto-disconnect
                player.autoplay = wavelink.AutoPlayMode.disabled
                return player
            except asyncio.TimeoutError:
                await ctx.reply(
                    f"Connection timed out. Try changing the VC region.",
                    delete_after=10,
                )
                return None
            except Exception as e:
                await ctx.reply(f"Failed to connect: {e}", delete_after=10)
                return None
        else:
            player: wavelink.Player = ctx.guild.voice_client

            if not isinstance(player, wavelink.Player):
                await ctx.reply(f"Player type mismatch.", delete_after=10)
                return None

            # If in different VC
            if player.channel and player.channel.id != destination.id:
                if not player.current and not player.queue:
                    await player.move_to(destination)
                else:
                    await ctx.reply(
                        f"Bot is already playing in {player.channel.mention}.",
                        delete_after=10,
                    )
                    return None

            return player

    # ── Wavelink Event Listeners ─────────────────────────────────

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Called when a track starts playing."""
        player = payload.player
        if not player or not player.guild:
            return

        self._add_history(player.guild.id, payload.track)
        try:
            await self.update_controller(player.guild)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Called when a track ends. Handles autoplay recommendations."""
        player = payload.player
        if not player or not player.guild:
            return

        # If track ended normally, queue is empty, and autoplay is on
        if (
            payload.reason == "finished"
            and not player.queue
            and player.autoplay == wavelink.AutoPlayMode.enabled
        ):
            try:
                # Get recommendations based on the ended track
                if payload.track:
                    recommendation = await wavelink.Playable.search(
                        payload.track.title, source=wavelink.TrackSource.YouTubeMusic
                    )
                    if recommendation and len(recommendation) > 1:
                        # Skip the first result (same track), play the second
                        await player.queue.put_wait(recommendation[1])
            except Exception:
                pass

        try:
            await self.update_controller(player.guild)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Handle track playback errors — skip to next if available."""
        player = payload.player
        if not player or not player.guild:
            return

        try:
            if player.queue:
                await player.skip(force=True)
                await self.update_controller(player.guild)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        """Auto-disconnect inactive player."""
        try:
            await player.disconnect()
            if player.guild:
                await self.update_controller(player.guild, idle=True)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes — clean up if bot is alone."""
        if member.id != self.bot.user.id:
            return

        # If bot got disconnected
        if before.channel and not after.channel:
            if member.guild.id in self.controller_messages:
                try:
                    await self.update_controller(member.guild, idle=True)
                except Exception:
                    pass

    # ═══════════════════════════════════════════════════════════════
    # COMMANDS
    # ═══════════════════════════════════════════════════════════════

    # ── /play ────────────────────────────────────────────────────

    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song from YouTube")
    @commands.cooldown(rate=6, per=30, type=commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song. Supports YouTube URLs and search queries."""
        if ctx.interaction:
            await ctx.defer()

        player = await self._connect_player(ctx, query)
        if not player:
            return

        # Search for the track
        try:
            results = await wavelink.Playable.search(query)
        except Exception as e:
            await ctx.reply(
                f"Search failed: `{e}`", delete_after=10
            )
            return

        if not results:
            await ctx.reply(f"No results found for: `{query}`", delete_after=10)
            return

        track = results[0]

        # Play or queue
        if not player.current:
            # Store requester
            requester_name = ctx.author.display_name
            self._requesters[ctx.guild.id] = requester_name

            # Get default volume
            music_settings = get_music_settings(ctx.guild.id)
            default_volume = music_settings.get("default_volume", 80)

            await player.play(track, volume=default_volume)
            await self.update_controller(ctx.guild, channel=ctx.channel)

            # Play embed — reference bullet style
            play_embed = discord.Embed(
                title="Now Playing",
                description=f"• {truncate(track.title, 50)} - {track.author}\n• Duration: {format_duration(track.length)} - (@{requester_name})",
                color=0x2B2D31,
            )
            if hasattr(track, 'artwork') and track.artwork and str(track.artwork).startswith("http"):
                play_embed.set_thumbnail(url=str(track.artwork))
            elif hasattr(track, 'identifier') and track.identifier:
                play_embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/mqdefault.jpg")
            await ctx.reply(embed=play_embed)
        else:
            # Queue limit: 50 tracks
            if len(player.queue) >= 50:
                await ctx.reply(f"Queue is full (max 50 tracks).", delete_after=10)
                return

            await player.queue.put_wait(track)
            await self.update_controller(ctx.guild)

            queue_embed = discord.Embed(
                title="Enqueued Track",
                description=f"Added **{truncate(track.title, 40)}** - **{track.author}** to the queue.\nDuration: {format_duration(track.length)}  •  Requestor: {ctx.author.display_name}  •  Position: {len(player.queue)}",
                color=0x2B2D31,
            )
            if hasattr(track, 'artwork') and track.artwork and str(track.artwork).startswith("http"):
                queue_embed.set_thumbnail(url=str(track.artwork))
            elif hasattr(track, 'identifier') and track.identifier:
                queue_embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/mqdefault.jpg")
            await ctx.reply(embed=queue_embed)

    # ── /pause ───────────────────────────────────────────────────

    @commands.hybrid_command(name="pause", description="Pause playback")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def pause(self, ctx: commands.Context):
        """Pause the current track."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if player.paused:
            await ctx.reply(f"Already paused.", delete_after=10)
            return

        await player.pause(True)
        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Paused** — `/resume` to continue.")

    # ── /resume ──────────────────────────────────────────────────

    @commands.hybrid_command(name="resume", description="Resume playback")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def resume(self, ctx: commands.Context):
        """Resume the paused track."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if not player.paused:
            await ctx.reply(f"Not paused.", delete_after=10)
            return

        await player.pause(False)
        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Resumed!**")

    # ── /skip ────────────────────────────────────────────────────

    @commands.hybrid_command(name="skip", aliases=["s"], description="Skip current track")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def skip(self, ctx: commands.Context):
        """Skip the current track."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if not ctx.author.voice or (player.channel and ctx.author.voice.channel != player.channel):
            await ctx.reply(f"Join the same voice channel first.", delete_after=10)
            return

        if player.queue or player.autoplay != wavelink.AutoPlayMode.disabled:
            await player.skip(force=True)
            await ctx.reply(f"**Skipped!**")
        else:
            await ctx.reply(f"Nothing left to skip to. Use `/stop`.", delete_after=10)

    # ── /stop ────────────────────────────────────────────────────

    @commands.hybrid_command(name="stop", description="Stop playback and disconnect")
    @commands.cooldown(rate=3, per=20, type=commands.BucketType.user)
    async def stop(self, ctx: commands.Context):
        """Stop playback and disconnect from VC."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            # Try forceful disconnect
            if ctx.guild.me.voice:
                await ctx.guild.me.move_to(None)
                await ctx.reply(f"Forcefully disconnected.")
            else:
                await ctx.reply(f"Not connected to any VC.", delete_after=10)
            return

        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await self.update_controller(ctx.guild, idle=True)
        await ctx.reply(f"**Stopped & disconnected.**")

    # ── /loop ────────────────────────────────────────────────────

    @commands.hybrid_command(name="loop", description="Toggle loop mode")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def loop(self, ctx: commands.Context):
        """Toggle loop for the queue."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            await ctx.reply(f"**Loop Disabled**")
        else:
            player.queue.mode = wavelink.QueueMode.loop
            await ctx.reply(f"**Loop Enabled** — queue will repeat.")

        await self.update_controller(ctx.guild)

    # ── /queue ───────────────────────────────────────────────────

    @commands.hybrid_command(name="queue", aliases=["q"], description="Show the queue")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def queue(self, ctx: commands.Context):
        """Display the current queue."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        embed = discord.Embed(
            title="📋 Track Queue",
            color=0x5865F2,
        )

        # Current track
        current = player.current
        embed.description = (
            f"**Now Playing:** [`{truncate(current.title, 55)}`]({getattr(current, 'uri', '')})\n"
            f"by `{truncate(current.author, 45)}` — `{format_duration(current.length)}`\n"
        )

        # Queue items
        queue_list = list(player.queue)
        if queue_list:
            items_text = ""
            for i, track in enumerate(queue_list[:15], start=1):
                items_text += (
                    f"**{i}.** `{truncate(track.title, 42)}` — "
                    f"`{format_duration(track.length)}` — {track.author}\n"
                )
            if len(queue_list) > 15:
                items_text += f"\n*...and {len(queue_list) - 15} more tracks*"
            embed.add_field(name=f"Up Next ({len(queue_list)} tracks)", value=items_text, inline=False)
        else:
            embed.add_field(name="Up Next", value="Queue is empty", inline=False)

        # Stats
        total_time = sum((t.length or 0) for t in queue_list)
        embed.set_footer(
            text=f"Volume: {player.volume}% • Loop: {'On' if player.queue.mode == wavelink.QueueMode.loop else 'Off'} • "
                 f"Total queue time: {format_duration(total_time)}"
        )

        await ctx.reply(embed=embed)

    # ── /shuffle ─────────────────────────────────────────────────

    @commands.hybrid_command(name="shuffle", description="Shuffle the queue")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def shuffle(self, ctx: commands.Context):
        """Shuffle all tracks in the queue."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if not player.queue:
            await ctx.reply(f"Queue is empty to shuffle.", delete_after=10)
            return

        import random
        items = list(player.queue)
        random.shuffle(items)
        player.queue.clear()
        for item in items:
            await player.queue.put_wait(item)

        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Queue shuffled!** ({len(items)} tracks)")

    # ── /remove ──────────────────────────────────────────────────

    @commands.hybrid_command(name="remove", description="Remove a track from queue by position")
    @commands.cooldown(rate=5, per=20, type=commands.BucketType.user)
    async def remove(self, ctx: commands.Context, position: int):
        """Remove a specific track from the queue."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if not player.queue:
            await ctx.reply(f"Queue is empty.", delete_after=10)
            return

        if position < 1 or position > len(player.queue):
            await ctx.reply(
                f"Invalid position. Queue has {len(player.queue)} tracks.",
                delete_after=10,
            )
            return

        # Get track before deleting (0-indexed)
        track_list = list(player.queue)
        removed = track_list[position - 1]

        # Clear and rebuild queue
        player.queue.delete(position - 1)

        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Removed:** `{removed.title}` from queue.")

    # ── /clearqueue ──────────────────────────────────────────────

    @commands.hybrid_command(name="clearqueue", aliases=["cq"], description="Clear the queue")
    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    async def clearqueue(self, ctx: commands.Context):
        """Clear all tracks from the queue."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        count = len(player.queue)
        player.queue.clear()

        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Cleared {count} tracks** from the queue.")

    # ── /volume ──────────────────────────────────────────────────

    @commands.hybrid_command(name="volume", aliases=["vol", "v"], description="Set playback volume (0-100)")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def volume(self, ctx: commands.Context, level: Optional[int] = None):
        """View or set the volume."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if level is None:
            await ctx.reply(f"Current volume: **{player.volume}%**")
            return

        if level < 0 or level > 100:
            await ctx.reply(f"Volume must be 0-100.", delete_after=10)
            return

        await player.set_volume(level)
        bar = volume_bar(level)
        await self.update_controller(ctx.guild)
        await ctx.reply(f"Volume: `{bar}` **{level}%**")

    # ── /nowplaying ──────────────────────────────────────────────

    @commands.hybrid_command(name="nowplaying", aliases=["np", "current"], description="Show current track")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def nowplaying(self, ctx: commands.Context):
        """Show detailed info about the current track."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        current = player.current
        position = getattr(player, 'position', 0) or 0
        duration = current.length or 1
        bar = progress_bar(position, duration, 15)

        embed = discord.Embed(
            color=0xC0392B if not player.paused else 0xD4A017,
        )
        uri = getattr(current, 'uri', None)
        title_text = f"[{truncate(current.title, 55)}]({uri})" if uri else truncate(current.title, 55)
        embed.description = (
            f"**{title_text}**\n"
            f"{current.author}  •  `{format_duration(duration)}`"
        )

        embed.add_field(
            name="",
            value=f"`{format_duration(position)}` │{bar}│ `{format_duration(duration)}`",
            inline=False,
        )

        embed.add_field(name="Volume", value=f"`{player.volume}%`", inline=True)
        embed.add_field(name="Loop", value="On" if player.queue.mode == wavelink.QueueMode.loop else "Off", inline=True)
        embed.add_field(name="Queue", value=f"`{len(player.queue)}` tracks", inline=True)

        if hasattr(current, 'artwork') and current.artwork:
            embed.set_thumbnail(url=current.artwork)

        footer_parts = [format_duration(duration), datetime.datetime.utcnow().strftime("%H:%M")]
        if ctx.guild.id in self._requesters:
            footer_parts.append(self._requesters[ctx.guild.id])
        embed.set_footer(text="  •  ".join(footer_parts))

        await ctx.reply(embed=embed)

    # ── /seek ────────────────────────────────────────────────────

    @commands.hybrid_command(name="seek", description="Seek to a position (seconds)")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def seek(self, ctx: commands.Context, seconds: int):
        """Seek to a specific position in the current track."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if seconds < 0:
            await ctx.reply(f"Seconds must be positive.", delete_after=10)
            return

        position_ms = seconds * 1000
        if position_ms > (player.current.length or 0):
            await ctx.reply(f"Cannot seek beyond track length.", delete_after=10)
            return

        await player.seek(position_ms)
        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Seeked to** `{format_duration(position_ms)}`")

    # ── /restart ─────────────────────────────────────────────────

    @commands.hybrid_command(name="restart", aliases=["replay"], description="Restart current track")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def restart(self, ctx: commands.Context):
        """Restart the current track from the beginning."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        await player.seek(0)
        await self.update_controller(ctx.guild)
        await ctx.reply(f"**Restarted!**")

    # ── /join ────────────────────────────────────────────────────

    @commands.hybrid_command(name="join", description="Join your voice channel")
    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    async def join(self, ctx: commands.Context):
        """Make the bot join your voice channel."""
        if not ctx.author.voice:
            await ctx.reply(f"Join a voice channel first.", delete_after=10)
            return

        destination = ctx.author.voice.channel

        if ctx.guild.voice_client:
            player: wavelink.Player = ctx.guild.voice_client
            if player.channel and player.channel.id == destination.id:
                await ctx.reply(f"Already in your channel.", delete_after=10)
                return
            await player.move_to(destination)
        else:
            try:
                player: wavelink.Player = await destination.connect(
                    cls=wavelink.Player, timeout=15, self_deaf=True
                )
                player.inactive_timeout = 120
                player.autoplay = wavelink.AutoPlayMode.disabled
            except Exception as e:
                await ctx.reply(f"Failed to connect: {e}", delete_after=10)
                return

        await ctx.reply(f"**Joined** {destination.mention}")

    # ── /leave ───────────────────────────────────────────────────

    @commands.hybrid_command(name="leave", aliases=["disconnect"], description="Leave voice channel")
    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    async def leave(self, ctx: commands.Context):
        """Make the bot leave the voice channel."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            if ctx.guild.me.voice:
                await ctx.guild.me.move_to(None)
                await ctx.reply(f"Disconnected.")
            else:
                await ctx.reply(f"Not in a voice channel.", delete_after=10)
            return

        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await self.update_controller(ctx.guild, idle=True)
        await ctx.reply(f"**Disconnected.**")

    # ── /autoplay ────────────────────────────────────────────────

    @commands.hybrid_command(name="autoplay", description="Toggle autoplay mode")
    @commands.cooldown(rate=5, per=15, type=commands.BucketType.user)
    async def autoplay(self, ctx: commands.Context):
        """Toggle autoplay — automatically plays related tracks when queue ends."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if player.autoplay == wavelink.AutoPlayMode.disabled:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await ctx.reply(f"**Autoplay Enabled** — related tracks will play automatically.")
        else:
            player.autoplay = wavelink.AutoPlayMode.disabled
            await ctx.reply(f"**Autoplay Disabled**")

        await self.update_controller(ctx.guild)

    # ── /lyrics ──────────────────────────────────────────────────

    @commands.hybrid_command(name="lyrics", description="Get lyrics for the current song")
    @commands.cooldown(rate=3, per=20, type=commands.BucketType.user)
    async def lyrics(self, ctx: commands.Context):
        """Fetch lyrics for the currently playing song."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        current = player.current
        # Use a simple lyrics search via the web
        query = f"{current.title} {current.author} lyrics"

        embed = discord.Embed(
            title=f"📝 Lyrics: {truncate(current.title, 50)}",
            description=f"Search for lyrics online:\n\n"
                        f"🔗 [Search on Google](https://www.google.com/search?q={query.replace(' ', '+')})\n"
                        f"🔗 [Search on Genius](https://genius.com/search?q={query.replace(' ', '%20')})\n"
                        f"🔗 [Search on Musixmatch](https://www.musixmatch.com/search/{current.title.replace(' ', '%20')})",
            color=0xFFFF00,
        )
        embed.set_footer(text="Click the links above to find lyrics")

        await ctx.reply(embed=embed)

    # ── /bassboost ───────────────────────────────────────────────

    @commands.hybrid_command(name="bassboost", description="Toggle bass boost filter")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def bassboost(self, ctx: commands.Context):
        """Toggle bass boost audio filter."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        # Check if filters are active
        current_filters = getattr(player, 'filters', None)

        try:
            from wavelink import filters
            if current_filters and hasattr(current_filters, 'equalizer'):
                # Remove filters
                await player.set_filters(filters.Equalizer.flat(), seek=True)
                await ctx.reply(f"**Bass Boost Disabled**")
            else:
                # Apply bass boost
                eq = filters.Equalizer()
                # Boost low frequencies
                bands = [
                    (0, 0.2), (1, 0.2), (2, 0.15),
                    (3, 0.1), (4, 0.05), (5, 0.0),
                ]
                for band, gain in bands:
                    eq.set_gain(band, gain)
                await player.set_filters(eq, seek=True)
                await ctx.reply(f"**Bass Boost Enabled** 🎛️")
        except ImportError:
            await ctx.reply(f"Filter system not available.", delete_after=10)
        except Exception as e:
            await ctx.reply(f"Filter error: {e}", delete_after=10)

    # ── /speed ───────────────────────────────────────────────────

    @commands.hybrid_command(name="speed", description="Set playback speed (0.5x - 3.0x)")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def speed(self, ctx: commands.Context, rate: float = 1.0):
        """Change the playback speed."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        if rate < 0.5 or rate > 3.0:
            await ctx.reply(f"Speed must be between 0.5x and 3.0x.", delete_after=10)
            return

        try:
            from wavelink import filters
            timescale = filters.Timescale(speed=rate)
            await player.set_filters(timescale, seek=True)
            label = "Normal" if rate == 1.0 else f"{rate}x"
            await ctx.reply(f"**Speed set to {label}**")
        except ImportError:
            await ctx.reply(f"Filter system not available.", delete_after=10)
        except Exception as e:
            await ctx.reply(f"Speed error: {e}", delete_after=10)

    # ── /move ────────────────────────────────────────────────────

    @commands.hybrid_command(name="move", description="Move a track to a new position in queue")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def move(self, ctx: commands.Context, from_pos: int, to_pos: int):
        """Move a track from one position to another."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        queue_len = len(player.queue)
        if from_pos < 1 or from_pos > queue_len or to_pos < 1 or to_pos > queue_len:
            await ctx.reply(
                f"Positions must be between 1 and {queue_len}.",
                delete_after=10,
            )
            return

        if from_pos == to_pos:
            await ctx.reply(f"Same position, nothing moved.", delete_after=10)
            return

        items = list(player.queue)
        track = items.pop(from_pos - 1)
        items.insert(to_pos - 1, track)

        player.queue.clear()
        for item in items:
            await player.queue.put_wait(item)

        await self.update_controller(ctx.guild)
        await ctx.reply(f"Moved `{track.title}` from #{from_pos} to #{to_pos}.")

    # ── /save ────────────────────────────────────────────────────

    @commands.hybrid_command(name="save", description="Save the current song to your DMs")
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def save(self, ctx: commands.Context):
        """DM the current track info to the user."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player) or not player.current:
            await ctx.reply(f"Nothing is playing.", delete_after=10)
            return

        current = player.current
        uri = getattr(current, 'uri', '') or f"https://www.youtube.com/watch?v={current.identifier}"

        embed = discord.Embed(
            title="💾 Saved Track",
            description=f"**[{current.title}]({uri})**\nby **{current.author}**\nDuration: `{format_duration(current.length)}`",
            color=0x57F287,
        )

        if hasattr(current, 'artwork') and current.artwork:
            embed.set_thumbnail(url=current.artwork)

        embed.set_footer(text=f"Saved from {ctx.guild.name}")

        try:
            await ctx.author.send(embed=embed)
            await ctx.reply(f"**Sent to your DMs!** 📨", ephemeral=True)
        except discord.Forbidden:
            await ctx.reply(f"I can't DM you. Enable DMs from server members.", delete_after=10)

    # ── /history ─────────────────────────────────────────────────

    @commands.hybrid_command(name="history", description="Show recently played tracks")
    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    async def history(self, ctx: commands.Context):
        """Show the play history for this server."""
        history = self.play_history.get(ctx.guild.id, [])

        if not history:
            await ctx.reply(f"No play history yet.", delete_after=10)
            return

        embed = discord.Embed(
            title=f"Recently Played",
            color=0x5865F2,
        )

        items = ""
        for i, track in enumerate(history[:15], start=1):
            items += f"**{i}.** `{truncate(track.title, 42)}` — `{format_duration(track.length)}`\n"

        embed.description = items
        embed.set_footer(text=f"Showing {min(len(history), 15)} of {len(history)} tracks")

        await ctx.reply(embed=embed)

    # ── /24-7 ────────────────────────────────────────────────────

    @commands.hybrid_command(name="24-7", description="Toggle 24/7 mode (bot never disconnects)")
    @commands.cooldown(rate=2, per=30, type=commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def twenty_four_seven(self, ctx: commands.Context):
        """Toggle 24/7 mode — bot stays in VC even when alone."""
        player: wavelink.Player = ctx.guild.voice_client

        if not player or not isinstance(player, wavelink.Player):
            await ctx.reply(f"Not connected to a voice channel.", delete_after=10)
            return

        if player.inactive_timeout == 0:
            player.inactive_timeout = 120
            await ctx.reply(f"**24/7 mode Disabled** — bot will leave after 2 min of inactivity.")
        else:
            player.inactive_timeout = 0
            await ctx.reply(f"**24/7 mode Enabled** — bot will never auto-disconnect.")


# ── Setup Function ─────────────────────────────────────────────────

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
