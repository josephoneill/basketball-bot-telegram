from datetime import datetime
from typing import Dict, Sequence, Optional, Type
import re
import logging
import telegram
from telegram.ext import CommandHandler, BaseHandler
from sports_bot_telegram_plugin import SportsBotPlugin
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from .services.live_score_service import LiveScoreService
from .services.player_service import PlayerService
from .services.team_service import TeamService

logger = logging.getLogger(__name__)


class NBAPlugin(SportsBotPlugin):
    def __init__(self):
        super().__init__()
        self.name = "NBA"
        self.description = "NBA plugin for sports-bot-telegram"
        self.version = "0.1.1"
        self.player_service = PlayerService(self.handle_none_or_mult_players_found)
        self.live_score_service = LiveScoreService()
        self.team_service = TeamService()

    async def get_live_scores(self, team: str, game_date: Optional[datetime] = None) -> MatchScores:
        """
        Get live scores for a specific NBA team on a given date.
        
        Args:
            team: Team name or identifier
            game_date: Optional date to get scores for. If None, gets current/most recent game.
            
        Returns:
            MatchScores object containing game scores and details
        """
        return await self.live_score_service.get_scores(team, game_date)

    async def get_player_career_stats(self, player_name: str, update=None, context=None) -> str:
        """
        Get career stats for a specific NBA player.
        
        Args:
            player_name: Name of the player to get stats for
            update: Optional telegram update object
            context: Optional telegram callback context
            
        Returns:
            String containing formatted career statistics
        """
        return await self.player_service.get_player_career_stats(player_name, update, context)

    async def get_player_live_stats(self, player_name: str, update, context) -> str:
        """
        Get current/live stats for a specific NBA player.
        
        Args:
            player_name: Name of the player to get stats for
            
        Returns:
            Dictionary containing player's current statistics
        """
        return await self.player_service.get_player_live_stats(player_name, update, context)

    async def get_player_season_stats(self, player_name: str, update, context, start_year: Optional[str] = None, end_year: Optional[str] = None) -> str:
        """
        Get season stats for a specific NBA player.
        
        Args:
            player_name: Name of the player to get stats for
            start_year: Optional start year for stats range
            end_year: Optional end year for stats range
            
        Returns:
            String containing formatted season statistics
        """
        return await self.player_service.get_player_season_stats(player_name, update, context, start_year, end_year)

    def is_team_supported(self, team: str) -> bool:
        """
        Check if an NBA team is supported by this plugin.
        
        Args:
            team: Team name or identifier to check
            
        Returns:
            True if the team is supported, False otherwise
        """
        return self.team_service.is_team_supported(team)
    
    def is_player_supported(self, player_name: str) -> bool:
        """
        Check if an NBA player is supported by this plugin.
        
        Args:
            player_name: Name of the player to check

        Returns:
            True if the player is supported, False otherwise
        """
        return self.player_service.is_player_supported(player_name)
    
    async def ft_command_handler(self, update, context, player_id=""):
        player_name = player_id if player_id else ' '.join(update.message.text.split(' ')[1:])
        player_fts_msg = await self.player_service.get_player_fts(player_name, update, context)

        if player_fts_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_fts_msg)
            return

        # Mutliple players found
        if player_fts_msg == "":
            return

        await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")

    def get_handlers(self) -> Sequence[BaseHandler]:
        """
        Get custom telegram command handlers for this plugin.
        
        Returns:
            List of telegram command handlers
        """
        return [
            CommandHandler('fts', self.ft_command_handler)
        ]
    
    async def handle_callback_query(self, update, context, data_dict: Dict[str, str]):
        handler = data_dict.get("handler", "")
        player_id = data_dict.get("id")
        if handler == "fts":
            await self.ft_command_handler(update.callback_query, context, player_id)


def register_plugin() -> Type[SportsBotPlugin]:
    """Register the NBA plugin."""
    return NBAPlugin 