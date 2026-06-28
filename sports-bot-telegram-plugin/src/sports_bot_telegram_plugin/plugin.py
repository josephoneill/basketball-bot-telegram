from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence
from datetime import datetime
import telegram
from telegram.ext import BaseHandler, CallbackContext
from telegram import Update, BotCommand
from .types.MatchScores import MatchScores

class SportsBotPlugin(ABC):
    """
    Base class for sports bot plugins.
    
    To create a new sport plugin:
    1. Subclass this class
    2. Implement all abstract methods
    3. Register your plugin using PluginRegistry.register()
    
    Example:
        class MyPlugin(SportsBotPlugin):
            def get_team_scores(self, team: str, game_date: Optional[datetime] = None) -> List[Dict]:
                # Implementation
                pass
                
            def get_player_stats(self, player_name: str) -> Dict:
                # Implementation
                pass
                
            def is_team_supported(self, team: str) -> bool:
                # Implementation
                pass
                
            def get_handlers(self) -> Sequence[BaseHandler]:
                # Optional: Return custom telegram command handlers
                return []
    """
    
    def __init__(self):
        """Initialize the plugin."""
        self.name = ''
        self.common_name = ''
        self.description = ''
        self.version = ''
        self.commands: list[BotCommand] = []

    async def handle_none_or_mult_players_found(self, players_found, update, context, requesting_command_name, plugin, year=None):
        """Handle cases where no players or multiple players are found."""
        if len(players_found) == 0:
            await self.send_player_not_found_message(update, context)
        else:
            msg = "Please select a player.\n"
            keyboard = []

            for player_found in players_found:
                # Build callback data with optional year parameter
                callback_data = f"id={player_found['id']}, handler={requesting_command_name}, plugin={plugin}"
                if year:
                    callback_data += f", year={year}"
                
                keyboard.append([telegram.InlineKeyboardButton(
                    text=player_found['full_name'],
                    callback_data=callback_data)]
                )

            reply_markup = telegram.InlineKeyboardMarkup(
                inline_keyboard=keyboard,
            )

            await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=reply_markup)

    async def send_player_not_found_message(self, update, context):
        """Send a message when a player is not found."""
        await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")

    @abstractmethod
    async def get_live_scores(self, team: str, game_date: Optional[datetime] = None, extra_params: Optional[Dict[str, str]] = None) -> MatchScores | None:
        """
        Get live scores for a specific team on a given date.
        
        Args:
            team: Team name or identifier
            game_date: Optional date to get scores for. If None, gets current/most recent game.
            extra_params: Optional dict of plugin-specific parameters parsed from the
                user's command. Reserved flags (``-d``, ``-plugin``) are stripped out
                by the core bot; all other ``-flag value`` pairs are passed here for
                the plugin to interpret as it sees fit.
            
        Returns:
            MatchScores object containing game scores and details
        """
        pass
        
    async def get_player_career_stats(self, player_name: str, update=None, context=None) -> str:
        """
        Get career stats for a specific player.
        """
        return "This plugin does not support player career stats."

    async def get_player_season_stats(self, player_name: str, update: Optional[Update], context: Optional[CallbackContext], start_year: Optional[str] = None, end_year: Optional[str] = None) -> str:
        """
        Get season stats for a specific player.
        """
        return "This plugin does not support player season stats."

    async def get_player_live_stats(self, player_name: str, update: Optional[Update], context: Optional[CallbackContext]) -> str:
        """
        Get current/live stats for a specific player.
        
        Args:
            player_name: Name of the player to get stats for
            
        Returns:
            string containing player's current statistics
        """
        return "This plugin does not support player live stats."

    @abstractmethod
    async def is_team_supported(self, team: str) -> bool:
        """
        Check if a team is supported by this plugin.
        
        Args:
            team: Team name or identifier to check
            
        Returns:
            True if the team is supported, False otherwise
        """
        pass

    async def is_player_supported(self, player_name: str) -> bool:
        """
        Check if a player is supported by this plugin.

        Args:
            player_name: Name of the player to check
            
        Returns:
            True if the player is supported, False otherwise
        """
        return False

    async def handle_callback_query(self, update, context, data_dict: Dict[str, str]):
        """
        Handle callback query from keyboard interactions.
        
        Args:
            update: Telegram update object
            context: Telegram callback context
            data_dict: Dictionary containing parsed callback data (e.g., {'id': '123', 'handler': 'career_stats'})
        """
        await context.bot.send_message(
            chat_id=update.callback_query.message.chat.id,
            text="This plugin does not support interactive player callbacks."
        )

    async def callback_query_keyboard_handler(self, update, context):
        """
        Generic callback query keyboard handler that can be used by any plugin.
        Expects callback_data in format: "id=<value>, handler=<handler_name>"
        """
        callback_data = [s.strip() for s in update.callback_query.data.split(',')]
        
        # Parse callback data
        data_dict = {}
        for item in callback_data:
            if '=' in item:
                key, value = item.split('=', 1)
                data_dict[key.strip()] = value.strip()
        
        # Delete previous followup message
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat.id,
                message_id=update.callback_query.message.message_id
            )
        except Exception as e:
            print(f"Failed to delete message: {e}")

        # Acknowledge the callback to remove the "loading" animation in the UI
        await update.callback_query.answer()
        
        # Call the plugin's specific callback handler
        await self.handle_callback_query(update, context, data_dict)

    def get_handlers(self) -> Sequence[BaseHandler]:
        """
        Get custom telegram command handlers for this plugin.
        Override this method to provide custom commands.
        
        Returns:
            List of telegram command handlers
        """
        return []

    def get_plugin_name(self) -> str:
        """Get the name of this plugin"""
        return self.__class__.__name__ 