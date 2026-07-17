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