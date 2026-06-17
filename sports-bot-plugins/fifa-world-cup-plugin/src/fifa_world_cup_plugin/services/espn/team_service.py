from ...util.espn.fifa_utils import FifaUtils

class TeamService():
    def __init__(self):
        self.fifa_utils = FifaUtils()

    async def is_team_supported(self, team: str) -> bool:
        """
        Check if a team is supported (exists in FIFA standings).
        
        Args:
            team: Team name or code
            
        Returns:
            True if team is found, False otherwise
        """
        team_id = await self.fifa_utils.find_team_id(team)
        return team_id is not None