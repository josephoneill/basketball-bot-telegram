from .fifa_api import FifaApi
from ..common import find_team_id_with_match_fallback

class FifaUtils():
    def __init__(self):
        self.fifa_api = FifaApi()

    async def find_team_id(self, team_name):
        teams = await self.fifa_api.get_teams()
        response = teams.get('response', [])
        return find_team_id_with_match_fallback(
            team_name,
            response,
            extract_team=lambda entry: entry.get('team', {}),
        )
    
    async def get_live_scores(self):
        return await self.fifa_api.get_fixtures()


    def get_fixture_by_team(self, fixtures, team_id):
        if len(fixtures) == 0:
            return None

        for fixture in fixtures:
            teams = fixture.get('teams', {})
            if teams.get('home', {}).get('id') == team_id or teams.get('away', {}).get('id') == team_id:
                return fixture
        return None

    def get_match_status(self, match):
        return match['fixture']['status']['long']
    
    def get_match_time(self, match):
        elapsed = match['fixture']['status']['elapsed']
        extra = match['fixture']['status']['extra']

        if extra is not None:
            return f"{elapsed}+{extra}'"
        
        return elapsed
    
    async def get_team_standings(self, team_id):
        standings = await self.fifa_api.get_standings()
        response = standings.get('response', [])
        
        for league_entry in response:
            league = league_entry.get('league', {})
            standings_groups = league.get('standings', [])
            
            for group in standings_groups:
                for standing in group:
                    team = standing.get('team', {})
                    if team.get('id') == team_id:
                        standing_all = standing.get('all')
                        if standing_all:
                          return f"{standing_all.get('win', '')}-{standing_all.get('draw', '')}-{standing_all.get('lose', '')}"
        
        return ''
    
    async def get_previous_fixture_by_team(self, team_id):
        finished_fixtures = await self.fifa_api.get_finished_fixtures()
        response = list(reversed(finished_fixtures.get('response', [])))
        return self.get_fixture_by_team(response, team_id)