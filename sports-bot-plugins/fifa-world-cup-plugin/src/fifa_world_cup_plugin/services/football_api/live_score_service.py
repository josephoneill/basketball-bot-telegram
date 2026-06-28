from ...util.football_api.fifa_utils import FifaUtils
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from ...util.common import timestamp_to_eastern

class LiveScoreService():
  def __init__(self):
      self.fifa_utils = FifaUtils()

  async def get_scores(self, team, extra_params=None) -> MatchScores | None:
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
      match = self.fifa_utils.get_fixture_by_team(live_scores.get('response', []), team_id)

      # game_fixture not found, use previous game
      if not match:
         match = await self.fifa_utils.get_previous_fixture_by_team(team_id)
         if not match:
            return

      return MatchScores(
        home_team=match.get('teams', {}).get('home', {}).get('name'),
        away_team=match.get('teams', {}).get('away', {}).get('name'),
        home_score=match.get('goals', {}).get('home'),
        away_score=match.get('goals', {}).get('away'),
        game_curr_time=self.fifa_utils.get_match_time(match),
        game_status=self.fifa_utils.get_match_status(match),
        game_start_time=timestamp_to_eastern(match.get('fixture', {}).get('timestamp')),
        home_team_record=await self.fifa_utils.get_team_standings(match.get('teams', {}).get('home', {}).get('id')),
        away_team_record=await self.fifa_utils.get_team_standings(match.get('teams', {}).get('away', {}).get('id')),
        home_team_logo_url=match.get('teams', {}).get('home', {}).get('logo'),
        away_team_logo_url=match.get('teams', {}).get('away', {}).get('logo')
      )

  