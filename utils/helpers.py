"""
Helper utilities for the Music Bot.
- Time formatting, text truncation, URL validation, progress bars.
All adapted from the original music.py with improvements.
"""

import re
from typing import Optional


# ── URL / Link Detection ────────────────────────────────────────────

URL_PATTERN = re.compile(
    r"^(https?:\/\/)?"                     # optional protocol
    r"((([A-Za-z0-9-]+\.)+[A-Za-z]{2,})|" # domain
    r"((\d{1,3}\.){3}\d{1,3}))"           # or IP
    r"(:\d+)?(\/\S*)?$",                   # optional port + path
    re.IGNORECASE,
)


def is_url(text: str) -> bool:
    """Check if the given text is a URL/link."""
    return bool(URL_PATTERN.match(text))


# ── Time Formatting ─────────────────────────────────────────────────

def format_duration(ms: int) -> str:
    """
    Convert milliseconds to a human-readable duration string.
    Examples: 65000 → "1m 5s", 3600000 → "1h", 0 → "0s"
    """
    if ms <= 0:
        return "0s"

    try:
        seconds = ms // 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts) if parts else "0s"
    except Exception:
        return "0s"


# ── Text Truncation ─────────────────────────────────────────────────

def truncate(text: str, limit: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length, adding suffix if truncated."""
    if not text:
        return "Unknown"
    if len(text) <= limit:
        return text
    return text[:limit - len(suffix)] + suffix


# ── Progress Bar ────────────────────────────────────────────────────

def progress_bar(current: int, total: int, length: int = 20) -> str:
    """
    Build a visual progress bar.
    Example: ████████░░░░░░░░░░░░
    """
    if total <= 0:
        return "░" * length

    filled = int((current / total) * length)
    filled = max(0, min(filled, length))
    return "█" * filled + "░" * (length - filled)


# ── Volume Bar ──────────────────────────────────────────────────────

def volume_bar(volume: int, length: int = 10) -> str:
    """Build a visual volume bar."""
    filled = max(0, min(volume // (100 // length), length))
    return "█" * filled + "░" * (length - filled)


# ── Safe Int Parse ──────────────────────────────────────────────────

def safe_int(value: str, default: Optional[int] = None) -> Optional[int]:
    """Safely parse a string to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ── Emoji Constants ─────────────────────────────────────────────────

class Emojis:
    """Centralized emoji reference — replace with custom emojis if desired."""
    PLAYING   = "▶️"
    PAUSED    = "⏸️"
    STOP       = "⏹️"
    SKIP      = "⏭️"
    QUEUE     = "📋"
    SUCCESS   = "✅"
    ERROR     = "❌"
    WARNING   = "⚠️"
    LOADING   = "🔄"
    MUSIC     = "🎵"
    VOLUME    = "🔊"
    LOOP      = "🔁"
    SHUFFLE   = "🔀"
    AUTOPLAY  = "🤖"
    CLOCK     = "🕐"
    LINK      = "🔗"
    INFO      = "ℹ️"
    TRASH     = "🗑️"
    SAVE      = "💾"
    LYRICS    = "📝"
    SEARCH    = "🔍"
    JOIN      = "📥"
    LEAVE     = "📤"
    FILTER    = "🎛️"
    SPEED     = "⚡"
    HISTORY   = "📜"
    STAR      = "⭐"
    CROWN     = "👑"
    BOT       = "🤖"
    PING      = "🏓"
    STATS     = "�j"
    INVITE    = "📨"
    HELP      = "❔"
    UPTIME    = "⏱️"
    JOKE      = "😈"
    MEME      = "🖼️"
    EIGHTBALL = "🎱"
    COIN      = "🪩"
    DICE      = "🎲"
    RPS       = "✊"
    AVATAR    = "🖼️"
    SERVER    = "🏠"
    USER      = "👤"
    BANNER    = "🏴"
    EMOJI     = "😀"
    FONT      = "🔤"
    PALETTE   = "🎨"
    SPARKLES  = "✨"
