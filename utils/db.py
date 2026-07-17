"""
Simple JSON-based guild settings database.
Survives bot restarts, works on Render with ephemeral filesystem.
"""

import json
import os
import asyncio
from typing import Any, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_lock = asyncio.Lock()


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _guild_path(guild_id: int) -> str:
    return os.path.join(DATA_DIR, f'{guild_id}.json')


def get_guild_settings(guild_id: int) -> Dict[str, Any]:
    """Get guild settings, returns empty dict if no settings exist."""
    _ensure_data_dir()
    path = _guild_path(guild_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_guild_settings(guild_id: int, data: Dict[str, Any]):
    """Save guild settings atomically."""
    _ensure_data_dir()
    path = _guild_path(guild_id)
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp_path, path)


def update_guild_setting(guild_id: int, key: str, value: Any):
    """Update a single setting for a guild."""
    settings = get_guild_settings(guild_id)
    settings[key] = value
    save_guild_settings(guild_id, settings)


def delete_guild_setting(guild_id: int, key: str):
    """Delete a single setting for a guild."""
    settings = get_guild_settings(guild_id)
    if key in settings:
        del settings[key]
        save_guild_settings(guild_id, settings)


def get_setting(guild_id: int, key: str, default: Any = None) -> Any:
    """Get a single setting with a default value."""
    settings = get_guild_settings(guild_id)
    return settings.get(key, default)


# Music-specific helpers
def get_music_settings(guild_id: int) -> Dict[str, Any]:
    """Get music-specific settings."""
    settings = get_guild_settings(guild_id)
    return settings.get('music', {})


def save_music_settings(guild_id: int, music_data: Dict[str, Any]):
    """Save music-specific settings."""
    settings = get_guild_settings(guild_id)
    settings['music'] = music_data
    save_guild_settings(guild_id, settings)


def update_music_setting(guild_id: int, key: str, value: Any):
    """Update a single music setting."""
    music = get_music_settings(guild_id)
    music[key] = value
    save_music_settings(guild_id, music)


# Name Style helpers
def get_namestyle_settings(guild_id: int) -> Optional[Dict[str, Any]]:
    """Get name style settings for a guild."""
    settings = get_guild_settings(guild_id)
    return settings.get('namestyle')


def save_namestyle_settings(guild_id: int, style_data: Dict[str, Any]):
    """Save name style settings."""
    settings = get_guild_settings(guild_id)
    settings['namestyle'] = style_data
    save_guild_settings(guild_id, settings)


def clear_namestyle_settings(guild_id: int):
    """Clear name style settings."""
    settings = get_guild_settings(guild_id)
    if 'namestyle' in settings:
        del settings['namestyle']
        save_guild_settings(guild_id, settings)
