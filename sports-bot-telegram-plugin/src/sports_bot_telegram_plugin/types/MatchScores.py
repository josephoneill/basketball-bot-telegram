from dataclasses import dataclass
from typing import Optional

@dataclass
class MatchScores:
    home_team: str
    home_score: Optional[int | str]
    home_team_record: str
    away_team: str
    away_score: Optional[int | str]
    away_team_record: str

    game_status: str
    game_start_time: str
    game_curr_time: str
    home_team_logo_url: Optional[str] = None
    away_team_logo_url: Optional[str] = None
