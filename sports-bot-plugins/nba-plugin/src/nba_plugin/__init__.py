"""
NBA Plugin for Sports Bot Telegram
================================

A plugin that provides NBA team scores and player statistics.
"""

from .plugin import NBAPlugin, register_plugin

__version__ = "0.1.0"
__all__ = ["NBAPlugin", "register_plugin"] 