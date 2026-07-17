"""
Name Style Cog — Apply custom fonts, effects, and colors to the bot's nickname.
Adapted from Bot-NameStyles-main by itsfizys.
Works via Discord REST API PATCH /guilds/{guild_id}/members/@me

7 Slash Commands: set, reset, list, presets, preview, current, info
"""

import discord
from discord.ext import commands
from typing import Optional, List

from utils.helpers import Emojis, truncate
from utils.namestyle_data import (
    FONTS, EFFECTS, PRESETS,
    hex_to_int, is_valid_hex, validate_name_style,
    apply_name_style, reset_name_style, int_to_hex
)
from utils.db import get_namestyle_settings, save_namestyle_settings, clear_namestyle_settings


# ── Name Style Select Menus ────────────────────────────────────────

class FontSelect(discord.ui.Select):
    """Dropdown for selecting a font."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"{data['name']} ({data['label']})",
                value=str(fid),
                description=truncate(data['style'], 50),
            )
            for fid, data in FONTS.items()
        ]
        super().__init__(placeholder="Choose a font...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_font = int(self.values[0])
        await self.view._update_message(interaction)


class EffectSelect(discord.ui.Select):
    """Dropdown for selecting an effect."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"{data['name']}",
                value=str(eid),
                description=data['description'],
            )
            for eid, data in EFFECTS.items()
        ]
        super().__init__(placeholder="Choose an effect...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_effect = int(self.values[0])
        await self.view._update_message(interaction)


class NameStyleSetupView(discord.ui.View):
    """Interactive view for setting up name styles."""
    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.selected_font: Optional[int] = None
        self.selected_effect: Optional[int] = None
        self.color1: Optional[str] = None
        self.color2: Optional[str] = None
        self.font_select = FontSelect()
        self.effect_select = EffectSelect()
        self.add_item(self.font_select)
        self.add_item(self.effect_select)

    async def _update_message(self, interaction: discord.Interaction):
        """Rebuild and update the message with current selections."""
        embed = self._build_embed()
        await interaction.message.edit(embed=embed, view=self)

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{Emojis.FONT} Name Style Setup",
            color=0x5865F2,
        )
        embed.add_field(
            name="Font",
            value=f"{FONTS[self.selected_font]['name']} ({FONTS[self.selected_font]['label']})" if self.selected_font else "Not selected",
            inline=True,
        )
        embed.add_field(
            name="Effect",
            value=f"{self.selected_effect} - {EFFECTS[self.selected_effect]['name']}" if self.selected_effect else "Not selected",
            inline=True,
        )
        embed.add_field(
            name="Color 1",
            value=f"`{self.color1}`" if self.color1 else "Not set — use /namestyle set",
            inline=True,
        )
        embed.add_field(
            name="Color 2",
            value=f"`{self.color2}`" if self.color2 else "Optional",
            inline=True,
        )
        return embed

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.success, row=2)
    async def btn_apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_font or not self.selected_effect:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Select a font and effect first!", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Build colors
        colors: List[int] = []
        if self.color1:
            colors.append(hex_to_int(self.color1))
        else:
            colors.append(16777215)  # Default white
        if self.color2:
            colors.append(hex_to_int(self.color2))

        # Validate
        error = validate_name_style(self.selected_font, self.selected_effect, colors)
        if error:
            await interaction.followup.send(f"{Emojis.ERROR} {error}", ephemeral=True)
            return

        # Apply via REST API
        token = self.cog.bot.http.token
        status, text = await apply_name_style(
            token, interaction.guild_id, self.selected_font, self.selected_effect, colors
        )

        if status == 200:
            # Save to DB
            save_namestyle_settings(interaction.guild_id, {
                "font_id": self.selected_font,
                "effect_id": self.selected_effect,
                "colors": colors,
            })
            await interaction.followup.send(
                f"{Emojis.SUCCESS} **Name style applied!** "
                f"Font: {FONTS[self.selected_font]['name']}, Effect: {EFFECTS[self.selected_effect]['name']}",
                ephemeral=True,
            )
        elif status == 403:
            await interaction.followup.send(
                f"{Emojis.ERROR} Missing **Change Nickname** permission! Grant it and try again.",
                ephemeral=True,
            )
        elif status == 429:
            await interaction.followup.send(
                f"{Emojis.WARNING} Rate limited. Wait a moment and try again.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} API Error ({status}): {truncate(text, 200)}",
                ephemeral=True,
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=2)
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        self.stop()


# ── Name Style Cog ─────────────────────────────────────────────────

class NameStyle(commands.Cog):
    """Custom bot name styles — fonts, effects, and colors per guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /namestyle (Group) ─────────────────────────────────────

    @commands.hybrid_group(
        name="namestyle",
        description="Customize the bot's display name — fonts, effects, and colors",
        with_app_command=True,
        invoke_without_command=True,
    )
    @commands.cooldown(rate=3, per=20, type=commands.BucketType.user)
    async def namestyle(self, ctx: commands.Context):
        """Name style group command — shows available subcommands."""
        embed = discord.Embed(
            title=f"{Emojis.FONT} Name Style Commands",
            description="Customize the bot's display name with fonts, effects, and colors!",
            color=0x5865F2,
        )
        embed.add_field(
            name="Subcommands",
            value="`/namestyle set` — Interactive style setup\n"
                  "`/namestyle reset` — Reset to default\n"
                  "`/namestyle list` — All fonts & effects\n"
                  "`/namestyle presets` — Ready-made styles\n"
                  "`/namestyle preview <preset>` — Preview a style\n"
                  "`/namestyle current` — Show current style\n"
                  "`/namestyle info` — Rules & limits",
            inline=False,
        )
        embed.set_footer(text="Requires Manage Server permission to apply styles")
        await ctx.reply(embed=embed)

    @namestyle.command(name="set", description="Interactive name style setup for this server")
    @commands.cooldown(rate=3, per=20, type=commands.BucketType.user)
    async def namestyle_set(self, ctx: commands.Context):
        """Interactive name style setup."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply(f"{Emojis.ERROR} You need **Manage Server** permission.", delete_after=10, ephemeral=True)
            return

        view = NameStyleSetupView(self, ctx)
        embed = view._build_embed()
        embed.set_footer(text="Select font & effect from dropdowns, then click Apply")
        await ctx.reply(embed=embed, view=view)

    @namestyle.command(name="reset", description="Reset bot name style to default")
    @commands.cooldown(rate=2, per=15, type=commands.BucketType.user)
    async def namestyle_reset(self, ctx: commands.Context):
        """Reset name style to default."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply(f"{Emojis.ERROR} You need **Manage Server** permission.", delete_after=10, ephemeral=True)
            return

        token = self.bot.http.token
        status, text = await reset_name_style(token, ctx.guild.id)

        if status == 200:
            clear_namestyle_settings(ctx.guild.id)
            await ctx.reply(f"{Emojis.SUCCESS} **Name style reset to default!**")
        else:
            await ctx.reply(f"{Emojis.ERROR} API Error ({status}): {truncate(text, 200)}", delete_after=10)

    @namestyle.command(name="list", description="List all available fonts and effects")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def namestyle_list(self, ctx: commands.Context):
        """List all available fonts and effects."""
        embed = discord.Embed(
            title=f"{Emojis.FONT} Available Fonts & Effects",
            color=0x5865F2,
        )

        fonts_text = "\n".join([
            f"**{fid}.** {data['name']} — *{data['label']}* — {data['style']}"
            for fid, data in FONTS.items()
        ])
        embed.add_field(name="📝 Fonts (IDs 1-12)", value=fonts_text, inline=False)

        effects_text = "\n".join([
            f"**{eid}.** {data['name']} — {data['description']}"
            + (" (2 colors required)" if data['colors_needed'] == 2 else "")
            for eid, data in EFFECTS.items()
        ])
        embed.add_field(name="✨ Effects (IDs 1-6)", value=effects_text, inline=False)

        embed.set_footer(text="Use /namestyle set to configure interactively")
        await ctx.reply(embed=embed)

    @namestyle.command(name="presets", description="Show preset name styles")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def namestyle_presets(self, ctx: commands.Context):
        """Show all preset styles."""
        embed = discord.Embed(
            title=f"{Emojis.SPARKLES} Preset Name Styles",
            description="Ready-to-use styles — use `/namestyle set` to apply one!",
            color=0x5865F2,
        )

        for i, (key, data) in enumerate(PRESETS.items(), start=1):
            font_name = FONTS[data['font_id']]['name']
            effect_name = EFFECTS[data['effect_id']]['name']
            colors_display = ", ".join([f"`{int_to_hex(c)}`" for c in data['colors']])
            embed.add_field(
                name=f"{i}. {key}",
                value=f"Font: **{font_name}** | Effect: **{effect_name}** | Colors: {colors_display}",
                inline=False,
            )

        await ctx.reply(embed=embed)

    @namestyle.command(name="preview", description="Preview a preset name style")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def namestyle_preview(self, ctx: commands.Context, preset: str):
        """Preview a preset style."""
        if preset not in PRESETS:
            available = ", ".join(f"`{k}`" for k in PRESETS.keys())
            await ctx.reply(
                f"{Emojis.ERROR} Unknown preset. Available: {available}",
                delete_after=10,
            )
            return

        data = PRESETS[preset]
        font_name = FONTS[data['font_id']]['name']
        effect_name = EFFECTS[data['effect_id']]['name']
        colors_display = ", ".join([f"`{int_to_hex(c)}`" for c in data['colors']])

        embed = discord.Embed(
            title=f"{Emojis.SPARKLES} Preview: {preset}",
            description=f"**Font:** {font_name} (ID: {data['font_id']})\n"
                        f"**Effect:** {effect_name} (ID: {data['effect_id']})\n"
                        f"**Colors:** {colors_display}",
            color=0x5865F2,
        )
        embed.set_footer(text="Use /namestyle set to apply this style")

        await ctx.reply(embed=embed)

    @namestyle.command(name="current", description="Show current name style for this server")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def namestyle_current(self, ctx: commands.Context):
        """Show current name style (from local DB)."""
        style = get_namestyle_settings(ctx.guild.id)

        if not style:
            await ctx.reply(f"{Emojis.INFO} No custom name style is set for this server.")
            return

        font_name = FONTS.get(style['font_id'], {}).get('name', 'Unknown')
        effect_name = EFFECTS.get(style['effect_id'], {}).get('name', 'Unknown')
        colors_display = ", ".join([f"`{int_to_hex(c)}`" for c in style['colors']])

        embed = discord.Embed(
            title=f"{Emojis.FONT} Current Name Style",
            description=f"**Font:** {font_name} (`{style['font_id']}`)\n"
                        f"**Effect:** {effect_name} (`{style['effect_id']}`)\n"
                        f"**Colors:** {colors_display}",
            color=0x57F287,
        )
        embed.set_footer(text="Use /namestyle reset to clear")

        await ctx.reply(embed=embed)

    @namestyle.command(name="info", description="Name style limits and information")
    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    async def namestyle_info(self, ctx: commands.Context):
        """Show name style information and limits."""
        embed = discord.Embed(
            title=f"{Emojis.INFO} Name Style Information",
            description="Name Styles let you customize the bot's display name with fonts, effects, and colors — visible in the member list and chat.",
            color=0xFEE75C,
        )

        embed.add_field(name="Fonts", value="12 fonts (IDs 1-12)", inline=True)
        embed.add_field(name="Effects", value="6 effects (IDs 1-6)", inline=True)
        embed.add_field(name="Colors", value="1 or 2 colors (24-bit integer, 0-16777215)", inline=True)

        embed.add_field(
            name="Requirements",
            value="• **Change Nickname** permission\n"
                  "• Styles are per-server (guild-scoped)\n"
                  "• Reset by passing `null` for all fields",
            inline=False,
        )

        embed.add_field(
            name="Tips",
            value="• Gradient effect requires exactly 2 colors\n"
                  "• Styles don't survive bot restarts — re-applied via DB\n"
                  "• Font 11 (GG Sans) keeps default look but applies effect/colors",
            inline=False,
        )

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(NameStyle(bot))
