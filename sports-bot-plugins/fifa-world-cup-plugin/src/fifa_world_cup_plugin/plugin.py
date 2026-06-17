from datetime import datetime
import os
from typing import Dict, Sequence, Optional, Type
import re
import logging
from telegram import BotCommand
from telegram.ext import CommandHandler, BaseHandler
from sports_bot_telegram_plugin import SportsBotPlugin
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from .services.espn.live_score_service import LiveScoreService as ESPNLiveScoreService
from .services.espn.team_service import TeamService as ESPNTeamService
from .services.football_api.live_score_service import LiveScoreService as FootballAPILiveScoreService
from .services.football_api.team_service import TeamService as FootballAPITeamService

class FifaWorldCupPlugin(SportsBotPlugin):
  def __init__(self):
    super().__init__()
    self.name = "FIFA World Cup"
    self.description = "FIFA World Cup plugin for sports-bot-telegram"
    self.version = "1.0.0"
    self.commands = []

    fifa_api = os.getenv('FIFA_API', 'ESPN')

    if fifa_api == 'ESPN':
        self.live_score_service = ESPNLiveScoreService()
        self.team_service = ESPNTeamService()
    else:
       self.live_score_service = FootballAPILiveScoreService()
       self.team_service = FootballAPITeamService()

  async def get_live_scores(self, team: str, game_date: Optional[datetime] = None) -> MatchScores | None:
      """
      Get live scores for a specific FIFA World Cup team.
      
      Args:
          team: Team name or identifier
          game_date: Optional date to get scores for. If None, gets current/most recent game.
          
      Returns:
          MatchScores object containing game scores and details, or None if no match is found
      """
      return await self.live_score_service.get_scores(team)


  async def is_team_supported(self, team: str) -> bool:
      """
      Check if a team is supported by this plugin.
      
      Args:
          team: Team name or identifier to check
          
      Returns:
          True if the team is supported, False otherwise
      """
      return await self.team_service.is_team_supported(team)


def register_plugin() -> Type[SportsBotPlugin]:
    """Register the FIFA World Cup plugin."""
    return FifaWorldCupPlugin