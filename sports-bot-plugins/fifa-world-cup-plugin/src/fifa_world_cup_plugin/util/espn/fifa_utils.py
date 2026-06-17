from datetime import datetime
from zoneinfo import ZoneInfo

from .fifa_api import FifaApi
from ..common import find_team_id_with_match_fallback
from ..common import timestamp_to_eastern as format_timestamp_to_eastern

class FifaUtils():
    def __init__(self):
        self.fifa_api = FifaApi()

    async def find_team_id(self, team_name):
        teams = await self.fifa_api.get_teams()
        response = teams.get('sports', [])
        if len(response) == 0:
            return None

        team_data = response[0].get('leagues', [])[0].get("teams", [])
        return find_team_id_with_match_fallback(
            team_name,
            team_data,
            extract_team=lambda entry: entry.get('team', {}),
            name_key='displayName',
            code_key='abbreviation',
        )
    
    def get_match_by_team(self, scoreboard, team_id):
        if len(scoreboard) == 0:
            return None

        for event in scoreboard.get('events', []):
            for competition in event.get("competitions", []):
                for competitor in competition.get('competitors', []):
                    team = competitor.get('id')
                    if team == team_id:
                        return competition
        return None

    async def get_live_scores(self):
        return await self.fifa_api.get_scoreboard()

    def get_match_status(self, match):
        return match['status']['type']['description']
    
    def get_match_time(self, match):
        time = match['status']['displayClock']

        return time
    
    async def get_team_standings(self, team_id):
        standings = await self.fifa_api.get_standings()
        response = standings.get('children', [])
        
        for group_entry in response:
            group_standings = group_entry.get('standings', []).get('entries', [])
            
            for team_data in group_standings:
                team = group_standings.get('team', {})
                if team.get('id') == team_id:
                    standing_data = team_data.get('stats')
                    if standing_data:
                        return f"{standing_data.get('wins', '')}-{standing_data.get('ties', '')}-{standing_data.get('losses', '')}"
        
        return ''
    
    async def get_previous_match_by_team(self, team_id):
        schedule = await self.fifa_api.get_schedule(team_id)
        events = schedule.get('events', [])
        if not events:
            return None

        last_event = events[-1]
        event_date = last_event.get('date')
        if not event_date:
            return None

        eastern_scoreboard_date = self._get_eastern_scoreboard_date(event_date)
        if not eastern_scoreboard_date:
            return None

        scoreboard = await self.fifa_api.get_scoreboard(eastern_scoreboard_date)
        return self.get_match_by_team(scoreboard, team_id)

    def _get_eastern_scoreboard_date(self, event_date):
        try:
            iso_value = event_date.replace('Z', '+00:00')
            parsed = datetime.fromisoformat(iso_value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo('UTC'))

            eastern = parsed.astimezone(ZoneInfo('America/New_York'))
            return eastern.strftime('%Y%m%d')
        except (TypeError, ValueError):
            return None