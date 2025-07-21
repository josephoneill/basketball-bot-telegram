from typing import Optional, Dict, List
from telegram.ext import Application
import importlib.metadata
import logging
from sports_bot_telegram_plugin import SportsBotPlugin

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Manages plugin discovery and lifecycle.
    
    This class handles:
    - Loading plugins via entry points
    - Managing plugin instances
    - Routing requests to appropriate plugins
    - Registering plugin-specific handlers
    """
    
    _plugin_instances: Dict[str, SportsBotPlugin] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Load and initialize all available plugins"""
        if cls._initialized:
            return

        # Discover plugins via entry points
        for entry_point in importlib.metadata.entry_points().get('sports_bot_telegram_plugins', []):
            try:
                register_func = entry_point.load()
                plugin_class = register_func()
                cls._plugin_instances[entry_point.name] = plugin_class()
                logger.info(f"Loaded plugin: {entry_point.name} version {cls._plugin_instances[entry_point.name].version}")
            except Exception as e:
                logger.error(f"Failed to load plugin {entry_point.name}: {str(e)}")

        if not cls._plugin_instances:
            logger.warning("No plugins were found. Install plugins to enable sports functionality.")
        
        cls._initialized = True

    @classmethod
    def find_plugin_for_team(cls, team: str) -> Optional[SportsBotPlugin]:
        """
        Find a plugin that supports the given team.
        
        Args:
            team: Team name or identifier to find a plugin for
            
        Returns:
            Plugin instance that supports the team, or None if no plugin found
        """
        cls._initialize()
        for plugin in cls._plugin_instances.values():
            if plugin.is_team_supported(team):
                return plugin
        return None
    
    @classmethod
    def find_plugin_for_player(cls, player_name: str) -> Optional[SportsBotPlugin]:
        """
        Find a plugin that supports the given player.
        
        Args:
            player_name: Player name to find a plugin for
            
        Returns:
            Plugin instance that supports the player, or None if no plugin found
        """
        cls._initialize()
        for plugin in cls._plugin_instances.values():
            if plugin.is_player_supported(player_name):
                return plugin
        return None

    @classmethod
    def get_all_plugins(cls) -> List[SportsBotPlugin]:
        """Get all available plugin instances"""
        cls._initialize()
        return list(cls._plugin_instances.values())

    @classmethod
    def setup_plugin_handlers(cls, application: Application) -> None:
        """
        Set up all plugin-specific command handlers.
        
        Args:
            application: Telegram bot application instance
        """
        cls._initialize()
        for plugin in cls._plugin_instances.values():
            handlers = plugin.get_handlers()
            for handler in handlers:
                application.add_handler(handler)
            if handlers:
                logger.info(f"Registered {len(handlers)} handlers from plugin {plugin.get_plugin_name()}") 