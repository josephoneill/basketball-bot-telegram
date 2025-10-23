from typing import Dict, Optional, List
from datetime import datetime
from sports_bot_telegram_plugin.types.MatchScores import MatchScores
from nba_plugin.api.nba import get_scoreboard, get_boxscore, get_team_record, get_most_recent_game
from nba_plugin.util.nba_utils import game_et_to_hh_mm, game_clock_to_mm_ss, get_headers, get_current_teams_data, get_game_header_set_data, find_team_id, get_team_by_id


class LiveScoreService:
  def get_scores(self, team: str, game_date: Optional[datetime] = None) -> MatchScores:
    score_board = get_scoreboard(date=game_date)
    resultSets = score_board["resultSets"]

    if not resultSets or len(resultSets) == 0:
       return None
    
    gameheader = resultSets[0]
    boxscore_id_result = LiveScoreService._get_game_id(team, gameheader)

    if not boxscore_id_result:
       return None
    
    game, boxscore_id = boxscore_id_result

    box_score = get_boxscore(boxscore_id)
    import json
    with open('box_score.json', 'w') as f:
      json.dump(box_score, f, indent=2)

    # There's a chance the box score for today's game isn't live yet
    # In this case, just generate a dummy score
    if not box_score:
       return LiveScoreService._get_not_started_team_scores(game, gameheader)
    
    match_score = LiveScoreService._get_team_scores_from_boxscore(boxscore=box_score)
    return match_score

  @staticmethod
  def _get_game_id(team, gameheader):
     # Get the id of the team query
    team_id = find_team_id(team)

    gameheader_headers = get_headers(gameheader)
    game_header_set = get_game_header_set_data(gameheader)

    for game in game_header_set:
      home_team_id = game[gameheader_headers["HOME_TEAM_ID"]]
      away_team_id = game[gameheader_headers["VISITOR_TEAM_ID"]]

      if home_team_id == team_id or away_team_id == team_id:
         # Return the game dataset and the game id
         return game, game[gameheader_headers["GAME_ID"]]
      
    # Couldn't find a game today for matched team, try to find most recent game
    last_game_id = get_most_recent_game(team_id) 

    if last_game_id:
       return None, last_game_id
      
    return None
  
  @staticmethod
  def _get_not_started_team_scores(game, gameheader) -> List[MatchScores]:
    gameheader_headers = get_headers(gameheader)

    home_team_id = game[gameheader_headers["HOME_TEAM_ID"]]
    away_team_id = game[gameheader_headers["VISITOR_TEAM_ID"]]

    home_team = get_team_by_id(home_team_id)
    away_team = get_team_by_id(away_team_id)

    home_team_record = get_team_record(home_team_id)
    away_team_record = get_team_record(away_team_id)

    game_start_time = game[gameheader_headers["GAME_STATUS_TEXT"]]
    game_curr_time = game[gameheader_headers["LIVE_PC_TIME"]]
  
    return MatchScores(
          home_team=home_team,
          home_score=None,
          home_team_record=home_team_record,
          away_team=away_team,
          away_score=None,
          away_team_record=away_team_record,
          game_status=game_start_time,
          game_start_time=game_start_time,
          game_curr_time=game_curr_time
       )
  
  @staticmethod
  def _get_team_scores_from_boxscore(boxscore) -> MatchScores:
    game = boxscore["game"]
    home_team = game["homeTeam"]
    away_team = game["awayTeam"]

    home_team_id = home_team["teamId"]
    away_team_id = away_team["teamId"]

    home_team_name = home_team["teamName"]
    home_team_score = home_team["score"]
    home_team_record = get_team_record(home_team_id)


    away_team_name = away_team["teamName"]
    away_team_score = away_team["score"]
    away_team_record = get_team_record(away_team_id)

    game_status = game["gameStatusText"]
    game_start_time = game_et_to_hh_mm(game["gameEt"])
    game_curr_time = game_clock_to_mm_ss(game["gameClock"])

    return MatchScores(
       home_team=home_team_name,
       home_score=home_team_score,
       home_team_record=home_team_record,
       away_team=away_team_name,
       away_score=away_team_score,
       away_team_record=away_team_record,
       game_status=game_status,
       game_start_time=game_start_time,
       game_curr_time=game_curr_time
    )
  
  @staticmethod
  def _get_live_team_scores_from_scoreboard(games, query) -> List[MatchScores]:
      results = list()

      for game in games:
          home_team = game["homeTeam"]
          away_team = game["awayTeam"]

          home_team_name = home_team["teamName"]
          away_team_name = away_team["teamName"]

          if query.lower() in home_team_name.lower() or query.lower() in away_team_name.lower():
              # Time format is like "PT10M11.00S"
              current_game_time = game["gameClock"]
              # Extract to MM:SS, two numbers after PT and 2 numbers after M
              current_game_time = current_game_time.replace("PT", "").replace("M", ":")[:5]

              team_compare_data = MatchScores(
                home_team=home_team_name,
                home_score=home_team["score"],
                home_team_record=f"{home_team['wins']}-{home_team['losses']}",
                away_team=away_team_name,
                away_score=away_team["score"],
                away_team_record=f"{away_team['wins']}-{away_team['losses']}",
                game_status=game["gameStatusText"].strip(),
                game_start_time=game["gameEt"],
                game_curr_time=current_game_time
              )
              results.append(team_compare_data)

      return results

  @staticmethod
  def _get_past_team_scores(gameheader, linescore, linescore_headers, query) -> List[MatchScores]:
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