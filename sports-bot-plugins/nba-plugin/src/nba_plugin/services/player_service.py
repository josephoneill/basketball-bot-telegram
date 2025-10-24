from typing import List, Dict, Optional, Callable
from nba_api.stats.static import players
from ..api.nba import get_player_career_stats, get_player_gamelog, get_scoreboard, get_boxscore, get_player_profile
from ..util.nba_utils import get_player_team, find_players, get_headers, get_formatted_player_career_stats, get_player_stats_from_gamelog, get_game_header_set_data, get_player_stats_from_boxscore

class PlayerService:
    def __init__(self, handle_multiple_players: Callable):
        self.handle_multiple_players = handle_multiple_players

    def find_players(self, player_query: str):
        """Find players using fuzzy partial match."""
        if player_query.isdigit():
            player = players.find_player_by_id(player_query)
            return [player] if player else []

        all_players = players.get_players()
        query_lower = player_query.lower()

        # Simple partial match
        matched_players = [
            p for p in all_players
            if query_lower in p["full_name"].lower()
        ]

        return matched_players

    
    def is_player_supported(self, player_name: str) -> bool:
        """Check if a player is supported by this plugin using partial match."""
        players = find_players(player_name)
        return len(players) > 0

    async def get_player_career_stats(self, player_name: str, update, context) -> str:
        players_found = find_players(player_name)

        if len(players_found) != 1:
            await self.handle_multiple_players(players_found, update, context, "career_stats", "nba")
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

    async def get_player_season_stats(self, player_name: str, update, context, start_year: Optional[str] = None, end_year: Optional[str] = None) -> Dict:
        player = await self.get_player(player_name, update, context, "season_stats")
        if not player:
            return player

        player_profile = get_player_profile(player_id=player["id"])
        # TODO: Implement the stats parsing
        return {}

    def format_player_season_stats(self, season_stats: Dict, player_name: str) -> str:
        """Format player stats into a readable message."""
        # TODO: Implement formatting logic
        return f"Stats for {player_name}"

    async def get_player_live_stats(self, player_name: str, update, context) -> str:
        """Get current/live stats for a specific NBA player."""
        player = await self.get_player(player_name, update, context, "current_stats")
        if not player:
            return player

        player_id = player["id"]
        player_name = player["full_name"].strip()

        # Then, check if player is currently playing
        _, game_id = PlayerService._find_boxscore_id(player_id)
        boxscore = get_boxscore(game_id) if game_id else None
        stats = {}

        if boxscore:
            stats = await PlayerService._get_stats_from_boxscore(player_id, boxscore)
        else:
            # If not, check their game log and report last game
            stats = await PlayerService._get_stats_from_gamelog_game(player_id)

        formatted_msg = (
            f"{player_name} {stats.get('has_tense', '')} "
            f"{stats.get('points')}/{stats.get('rebounds')}/{stats.get('assists')}/"
            f"{stats.get('blocks')}/{stats.get('steals')} "
            f"on {stats.get('field_goal_pct')}/{stats.get('three_point_pct')}/"
            f"{stats.get('free_throw_pct')} shooting "
            f"in {stats.get('time_played')} minutes"
        )

        if stats.get("game_date"):
            formatted_msg += f" on {stats['game_date']}"

        return formatted_msg
    
    async def get_player_fts(self, player_name, update, context):
        player = await self.get_player(player_name, update, context, "fts")
        if not player:
            return player
        
        player_id = player["id"]
        player_name = player["full_name"].strip()

        _, game_id = PlayerService._find_boxscore_id(player_id)
        boxscore = get_boxscore(game_id) if game_id else None
        stats = {}

        if boxscore:
            stats = await PlayerService._get_stats_from_boxscore(player_id, boxscore)
        else:
            # If not, check their game log and report last game
            stats = await PlayerService._get_stats_from_gamelog_game(player_id)

        formatted_msg = f"{player_name} {stats.get('has_tense')} shot {stats.get('ftm')}/{stats.get('fta')} FTA"
        if stats.get("game_date"):
            formatted_msg += f" on {stats['game_date']}"

        return formatted_msg

    
    async def get_player(self, player_name, update, context, requesting_command_name):
        # First, find the correct player
        players_found = find_players(player_name)

        if len(players_found) != 1:
            await self.handle_multiple_players(players_found, update, context, requesting_command_name, "nba")
            return ""
        
        player = players_found[0]

        return player
        
    @staticmethod
    async def _get_stats_from_gamelog_game(player_id):
        log = get_player_gamelog(player_id=player_id)

        if "resultSets" not in log or len(log["resultSets"]) == 0:
            return

        resultSet = log["resultSets"][0]
        game = resultSet["rowSet"][0]
        headers = get_headers(resultSet)

        stats = get_player_stats_from_gamelog(game, headers)   
        return stats 

    @staticmethod
    def _find_boxscore_id(player_id):
        team_id = get_player_team(player_id)
        score_board = get_scoreboard()
        resultSets = score_board["resultSets"]

        if not resultSets or len(resultSets) == 0:
            return None, None
                
        gameheader = resultSets[0]

        gameheader_headers = get_headers(gameheader)
        game_header_set = get_game_header_set_data(gameheader)

        for game in game_header_set:
            home_team_id = game[gameheader_headers["HOME_TEAM_ID"]]
            away_team_id = game[gameheader_headers["VISITOR_TEAM_ID"]]

            if home_team_id == team_id or away_team_id == team_id:
                # Return the game dataset and the game id
                return game, game[gameheader_headers["GAME_ID"]]
        
        return None, None
    
    async def _get_stats_from_boxscore(player_id, boxscore):
        team_id = get_player_team(player_id)

        game = boxscore["game"]
        team_data = game["homeTeam"] if game["homeTeam"]["teamId"] == team_id else game["awayTeam"]

        player_data = next((player for player in team_data["players"] if player["personId"] == player_id), None)

        if not player_data:
            return
        
        stats = get_player_stats_from_boxscore(player_data["statistics"])
        return stats