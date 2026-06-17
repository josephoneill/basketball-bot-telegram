from ...util.espn.fifa_utils import FifaUtils
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from ...util.common import timestamp_to_eastern

class LiveScoreService():
  def __init__(self):
      self.fifa_utils = FifaUtils()

  async def get_scores(self, team):
      """
      Get live scores for a specific FIFA World Cup team
      
      Args:
          team: Team name or identifier
          
      Returns:
          MatchScores object containing game scores and details
      """

      # Find team_id
      team_id = await self.fifa_utils.find_team_id(team)

      # Check if team is currently playing
      live_scores = await self.fifa_utils.get_live_scores()
      match = self.fifa_utils.get_match_by_team(live_scores, team_id)

      if not match:
        match = await self.fifa_utils.get_previous_match_by_team(team_id)

      # game_fixture not found, use previous game
      if not match:
         match = None # await self.fifa_utils.get_previous_fixture_by_team(team_id)
         if not match:
            return
         
      home_team = match.get('competitors')[0]
      away_team = match.get('competitors')[1]

      return MatchScores(
        home_team=home_team.get('team').get('displayName'),
        away_team=away_team.get('team').get('displayName'),
        home_score=next((stat.get('displayValue') for stat in home_team.get('statistics', []) if stat.get('name') == 'totalGoals'), 0),
        away_score=next((stat.get('displayValue') for stat in away_team.get('statistics', []) if stat.get('name') == 'totalGoals'), 0),
        game_curr_time=self.fifa_utils.get_match_time(match),
        game_status=self.fifa_utils.get_match_status(match),
        game_start_time=timestamp_to_eastern(match.get('startDate')),
        home_team_record=next((record.get('summary', '') for record in home_team.get('records', []) if record.get('name') == 'All Splits'), ''),
        away_team_record=next((record.get('summary', '') for record in away_team.get('records', []) if record.get('name') == 'All Splits'), ''),
        home_team_logo_url=home_team.get('team').get('logo'),
        away_team_logo_url=away_team.get('team').get('logo'),
      )

  