from urllib.request import Request, urlopen
import json
import uuid
from datetime import datetime
from nba_plugin.util.utils import get_current_eastern_time
from nba_api.live.nba.endpoints import ScoreBoard, BoxScore
from nba_api.stats.endpoints import ScoreboardV2, LeagueStandingsV3, TeamGameLog, PlayerGameLog, PlayerProfileV2
from ..util.nba_utils import get_headers
import socket

def create_request(url, host='stats.nba.com', referer='https://stats.nba.com/'):
    req = Request(url)
    req.add_header('User-Agent', 'PostmanRuntime/7.24.0')
    req.add_header('Host', host)
    req.add_header('Referer', referer)
    req.add_header('Accept', '*/*')
    req.add_header('x-nba-stats-origin', 'stats')
    req.add_header('x-nba-stats-token', 'true')
    return req

def get_player_career_stats(player_id):
    req = create_request(f"https://stats.nba.com/stats/playercareerstats?LeagueID=&PerMode=Totals&PlayerID={player_id}")
    player_career_stats = urlopen(req).read()

    return json.loads(player_career_stats)

def get_live_scoreboard(date=None):
    try:
        score_board = ScoreBoard()
        return score_board.get_dict()
    except Exception as e:
        print(f"Error fetching live scoreboard: {e}")
        return None

def get_scoreboard(date=None):
    curr_date = date if date is not None else str(get_current_eastern_time()).split()[0]
    try:
        score_board = ScoreboardV2(game_date=curr_date)
        return score_board.get_dict()
    except socket.timeout:
        print("Timeout when connecting to NBA stats API")
        return None
    except Exception as e:
        print(f"Error fetching scoreboard: {e}")
        return None
    
def get_boxscore(game_id):
    try:
        box_score = BoxScore(game_id=game_id)
    except Exception as e:
        print(f"Error fetching boxscore: {e}")
        return None

    return box_score.get_dict()


def get_team_record(team_id):
    try:
        data = LeagueStandingsV3().get_dict()
        teams = data['resultSets'][0]['rowSet']
        wins = 0
        losses = 0

        for team in teams:
            headers = data['resultSets'][0]['headers']
            team_data = dict(zip(headers, team))
            if team_data["TeamID"] == team_id:
                wins = team_data["WINS"]
                losses = team_data["LOSSES"]

        return f"{wins}-{losses}"
    except Exception as e:
        print(f"Error fetching league standings: {e}")
        return None
    

def get_most_recent_game(team_id):
    gamelog = TeamGameLog(team_id=team_id, league_id_nullable="00").get_dict()

    resultSet = gamelog["resultSets"][0]

    if not resultSet:
        return

    header = get_headers(resultSet)
    rowset = resultSet["rowSet"]

    if not rowset:
        return

    # Get most recent game
    last_row = rowset[0]

    game_id = last_row[header["Game_ID"]]

    return game_id

def get_player_gamelog(player_id):
    log = PlayerGameLog(player_id=player_id, league_id_nullable="00").get_dict()

    return log


# def get_boxscore(game_id, game_date):
#     game_date_dt_obj = datetime.strptime(game_date, "%b %d, %Y")
#     api_formatted_date = game_date_dt_obj.strftime('%Y%m%d')
#     day = datetime.strftime(game_date_dt_obj, "%Y%m%d")
#     req = create_request(
#         f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json",
#         'cdn.nba.com', referer='https://cdn.nba.com/')
#     box_score = urlopen(req).read()
#     return json.loads(box_score)

def get_player_profile(player_id):
    return PlayerProfileV2(player_id=player_id, per_mode36="PerGame", league_id_nullable="00").get_dict()