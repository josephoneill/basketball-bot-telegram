from nba_plugin.util.nba_utils import find_team_id

class TeamService:
    def is_team_supported(self, team: str) -> bool:
        """Check if an NBA team is supported by this plugin."""
        if not team or not team.strip():
            return False

        try:
            team_id = find_team_id(team.strip())
            return team_id is not None
        except Exception:
            return False