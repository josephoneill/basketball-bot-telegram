from typing import Dict, Optional, List
from datetime import datetime
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from nba_plugin.api.nba import get_scoreboard
from nba_plugin.util.nba_utils import get_linescore, get_gameheader, get_headers, get_current_teams_data, get_game_header_set_data


class LiveScoreService:
  def get_live_scores(self, team: str, game_date: Optional[datetime] = None) -> MatchScores:
    try:
      score_board = get_scoreboard(game_date)
    except Exception as e:
      print(f"Error in get_scoreboard: {e}")
      return None
    try:
      linescore = get_linescore(score_board)
    except Exception as e:
      print(f"Error in get_linescore: {e}")
      return None
    try:
      gameheader = get_gameheader(score_board)
    except Exception as e:
      print(f"Error in get_gameheader: {e}")
      return None

    if linescore.get("empty") or gameheader.get("empty"):
      return None
    
    try:
      linescore_data = linescore["linescore"]
      linescore_headers = linescore["linescore_headers"]
      match_scores = self._get_live_team_scores(gameheader, linescore_data, linescore_headers, team)
      if not match_scores:
          return None
      match_scores = match_scores[0]
      return match_scores
    except Exception as e:
      print(f"Error processing scores: {e}")
      return None

  @staticmethod
  def _get_live_team_scores(gameheader, linescore, linescore_headers, query) -> List[MatchScores]:
      gameheader_headers = get_headers(gameheader)
      teams_data = get_current_teams_data(linescore)
      game_header_set = get_game_header_set_data(gameheader)
      results = list()

      for i in range(0, int(len(teams_data) - 1), 2):
          home_team = teams_data[i]
          away_team = teams_data[i + 1]

          start_time = game_header_set[int(i / 2)][gameheader_headers["GAME_STATUS_TEXT"]]

          home_team_name = home_team[linescore_headers["TEAM_NAME"]]
          away_team_name = away_team[linescore_headers["TEAM_NAME"]]


          if query.lower() in home_team_name.lower() or query.lower() in away_team_name.lower():
              team_compare_data = LiveScoreService._get_match_score_data(gameheader, linescore_headers, start_time, home_team, away_team)
              results.append(team_compare_data)

      return results

  @staticmethod
  def _get_match_score_data(gameheader, linescore_headers, start_time, home_team, away_team) -> MatchScores:
    gameheader_headers = get_headers(gameheader)
    game_header_set = get_game_header_set_data(gameheader)

    home_team_name = home_team[linescore_headers["TEAM_NAME"]]
    away_team_name = away_team[linescore_headers["TEAM_NAME"]]

    home_team_record = home_team[linescore_headers["TEAM_WINS_LOSSES"]]
    away_team_record = away_team[linescore_headers["TEAM_WINS_LOSSES"]]

    home_team_score = home_team[linescore_headers["PTS"]]
    away_team_score = away_team[linescore_headers["PTS"]]

    gameheader_game_index = [(i, el) for i, el in enumerate(game_header_set) if
                             el[gameheader_headers["GAME_ID"]] == home_team[linescore_headers["GAME_ID"]]][0][0]

    game_status = game_header_set[gameheader_game_index][gameheader_headers["GAME_STATUS_TEXT"]]
    live_pc_time = game_header_set[gameheader_game_index][gameheader_headers["LIVE_PC_TIME"]]

    match_score_data = MatchScores(
      home_team=home_team_name,
      home_score=home_team_score,
      away_team=away_team_name,
      away_score=away_team_score,
      game_status=game_status,
      home_team_record=home_team_record,
      away_team_record=away_team_record,
      game_start_time=start_time,
      game_curr_time=live_pc_time
    )

    return match_score_data