from typing import Dict, Optional
from datetime import datetime
from sports_bot_telegram_plugin.types.MatchScores import MatchScores

class TeamService:
    def is_team_supported(self, team: str) -> bool:
        """Check if an NBA team is supported by this plugin."""
        # TODO: Implement team validation
        return True 