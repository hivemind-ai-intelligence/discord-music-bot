"""
Discord Name Styles — Font, Effect, Color data + REST API calls.
Adapted from Bot-NameStyles-main by itsfizys.
Uses Discord REST API PATCH /guilds/{guild_id}/members/@me
"""

import aiohttp
from typing import List, Optional, Dict, Any, Tuple


# ── Font Reference (12 fonts, IDs 1-12) ────────────────────────────

FONTS: Dict[int, Dict[str, str]] = {
    1:  {"name": "Bangers",        "label": "Bold Comic",     "style": "Thick, comic-book lettering"},
    2:  {"name": "BioRhyme",       "label": "Elegant Serif",  "style": "Classic serif, refined look"},
    3:  {"name": "Cherry Bomb",    "label": "Sakura",         "style": "Playful bubble-style characters"},
    4:  {"name": "Chicle",         "label": "Jellybean",      "style": "Rounded, soft and bubbly"},
    5:  {"name": "Compagnon",      "label": "Display",        "style": "Stylish mixed-weight display font"},
    6:  {"name": "MuseoModerno",   "label": "Modern",         "style": "Clean, geometric, modern feel"},
    7:  {"name": "Neo-Castel",     "label": "Medieval",       "style": "Gothic, dark medieval lettering"},
    8:  {"name": "Pixelify Sans",  "label": "8Bit",           "style": "Retro pixel/blocky characters"},
    9:  {"name": "Ribes",          "label": "Decorative",     "style": "Expressive, decorative display"},
    10: {"name": "Sinistre",       "label": "Vampyre",        "style": "Dark, jagged, gothic elegant"},
    11: {"name": "GG Sans",        "label": "Default",        "style": "Standard Discord font"},
    12: {"name": "Zilla Slab",     "label": "Tempo",          "style": "Modern slab-serif, balanced weight"},
}


# ── Effect Reference (6 effects, IDs 1-6) ──────────────────────────

EFFECTS: Dict[int, Dict[str, Any]] = {
    1: {"name": "Solid",    "description": "Flat single color fill",              "colors_needed": 1},
    2: {"name": "Gradient", "description": "Smooth blend between two colors (L→R)", "colors_needed": 2},
    3: {"name": "Neon",     "description": "Glowing outline around the letters",  "colors_needed": 1},
    4: {"name": "Toon",     "description": "Subtle gradient fill with stroke outline", "colors_needed": 1},
    5: {"name": "Pop",      "description": "Colored drop shadow behind letters",  "colors_needed": 1},
    6: {"name": "Glow",     "description": "Soft outer glow (accent color optional)", "colors_needed": 1},
}


# ── Preset Styles ───────────────────────────────────────────────────

PRESETS: Dict[str, Dict[str, Any]] = {
    "sinistre-neon-white":       {"font_id": 10, "effect_id": 3, "colors": [16777215]},
    "ribes-neon-pink":           {"font_id": 9,  "effect_id": 3, "colors": [16711935]},
    "neo-castel-gradient":       {"font_id": 7,  "effect_id": 2, "colors": [5865, 16777215]},
    "pixelify-pop-purple":       {"font_id": 8,  "effect_id": 5, "colors": [8388736]},
    "bangers-glow-pink-purple":  {"font_id": 1,  "effect_id": 6, "colors": [16711935, 8388736]},
    "cherry-toon-white":         {"font_id": 3,  "effect_id": 4, "colors": [16777215]},
    "zilla-solid-blue":          {"font_id": 12, "effect_id": 1, "colors": [5865]},
    "sinistre-neon-gold":        {"font_id": 10, "effect_id": 3, "colors": [16766720]},
    "bangers-glow-cyan":         {"font_id": 1,  "effect_id": 6, "colors": [65535, 8388736]},
    "pixelify-pop-white":        {"font_id": 8,  "effect_id": 5, "colors": [16777215]},
    "ribes-gradient-fire":       {"font_id": 9,  "effect_id": 2, "colors": [15548997, 16766720]},
    "neo-castel-neon-purple":    {"font_id": 7,  "effect_id": 3, "colors": [8388736]},
    "chicle-toon-pink":          {"font_id": 4,  "effect_id": 4, "colors": [16711935]},
    "compagnon-solid-white":     {"font_id": 5,  "effect_id": 1, "colors": [16777215]},
    "zilla-glow-blurple":        {"font_id": 12, "effect_id": 6, "colors": [5793266, 65535]},
}


# ── Color Utilities ─────────────────────────────────────────────────

def hex_to_int(hex_color: str) -> int:
    """Convert hex color string to 24-bit integer."""
    return int(hex_color.replace("#", "").strip(), 16)


def int_to_hex(color_int: int) -> str:
    """Convert 24-bit integer to hex color string."""
    return f"#{color_int:06X}"


def is_valid_hex(hex_color: str) -> bool:
    """Check if string is a valid 6-digit hex color."""
    return bool(re.match(r"^#?[0-9a-fA-F]{6}$", hex_color.strip()))


# Regex imported at top is needed here, add import
import re


def is_valid_color_int(value: int) -> bool:
    """Check if value is a valid 24-bit color integer."""
    return isinstance(value, int) and 0 <= value <= 0xFFFFFF


# ── Validation ──────────────────────────────────────────────────────

def validate_name_style(font_id: int, effect_id: int, colors: List[int]) -> Optional[str]:
    """
    Validate name style parameters.
    Returns error message string if invalid, None if valid.
    """
    if font_id not in FONTS:
        return f"Invalid font ID: {font_id}. Must be 1-12."

    if effect_id not in EFFECTS:
        return f"Invalid effect ID: {effect_id}. Must be 1-6."

    if not isinstance(colors, list) or len(colors) < 1 or len(colors) > 2:
        return "Colors must be an array of 1 or 2 integers."

    for c in colors:
        if not is_valid_color_int(c):
            return f"Invalid color value: {c}. Must be 0-16777215."

    if effect_id == 2 and len(colors) < 2:
        return "Gradient effect requires exactly 2 colors."

    return None


# ── Discord REST API Calls ──────────────────────────────────────────

async def apply_name_style(
    bot_token: str,
    guild_id: int,
    font_id: int,
    effect_id: int,
    colors: List[int]
) -> Tuple[int, str]:
    """
    Apply a name style to the bot in a specific guild.
    Returns (status_code, response_text).
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/@me"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }
    body = {
        "display_name_font_id": font_id,
        "display_name_effect_id": effect_id,
        "display_name_colors": colors,
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=body) as resp:
            text = await resp.text()
            return resp.status, text


async def reset_name_style(bot_token: str, guild_id: int) -> Tuple[int, str]:
    """
    Reset the bot's name style to default in a specific guild.
    Returns (status_code, response_text).
    """
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/@me"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }
    body = {
        "display_name_font_id": None,
        "display_name_effect_id": None,
        "display_name_colors": None,
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=body) as resp:
            text = await resp.text()
            return resp.status, text
