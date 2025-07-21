from typing import List, Dict, Optional, Callable
from nba_api.stats.static import players
from ..api.nba import get_player_career_stats
from ..util.nba_utils import find_players, get_headers, get_formatted_player_career_stats

class PlayerService:
    def __init__(self, handle_multiple_players: Callable):
        self.handle_multiple_players = handle_multiple_players

    def find_players(self, player_name: str) -> List[Dict]:
        """Find players by name or ID."""
        if player_name.isdigit():
            return [players.find_player_by_id(player_name)]
        return players.find_players_by_full_name(player_name)
    
    def is_player_supported(self, player_name: str) -> bool:
        """Check if a player is supported by this plugin."""
        return any(player["full_name"] == player_name for player in self.find_players(player_name))

    async def get_player_career_stats(self, player_name: str, update, context) -> str:
        players_found = find_players(player_name)

        if len(players_found) != 1:
            await self.handle_multiple_players(players_found, update, context, "career_stats")
            return None

        player = players_found[0]
        player_id = player["id"]
        player_name = player["full_name"]
        career_totals = {}

        player_career_stats = get_player_career_stats(player_id)

        for result_set in player_career_stats["resultSets"]:
            if result_set["name"] == "CareerTotalsRegularSeason":
                career_totals = result_set
                break

        headers = get_headers(career_totals)

        msg = get_formatted_player_career_stats(dict(headers=headers, data=career_totals["rowSet"][0]), player_name)
        return msg

    def get_player_season_stats(self, career_stats: Dict, start_year: Optional[str] = None, end_year: Optional[str] = None) -> Dict:
        """Get regular season stats for a player within a date range."""
        # TODO: Implement filtering logic
        return career_stats

    def format_player_season_stats(self, season_stats: Dict, player_name: str) -> str:
        """Format player stats into a readable message."""
        # TODO: Implement formatting logic
        return f"Stats for {player_name}"

    def get_player_live_stats(self, player_name: str) -> Dict:
        """Get current/live stats for a specific NBA player."""
        # TODO: Implement live stats retrieval
        return {} 