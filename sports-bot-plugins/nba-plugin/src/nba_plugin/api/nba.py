from urllib.request import Request, urlopen
import json
import uuid
from datetime import datetime
from nba_plugin.util.utils import get_current_eastern_time
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

def get_scoreboard(date=None):
    curr_date = date if date is not None else str(get_current_eastern_time()).split()[0]
    request_url = f"https://stats.nba.com/stats/scoreboardv2?DayOffset=0&GameDate={curr_date}&LeagueID=00&refresh={uuid.uuid4()}"
    req = create_request(request_url)
    try:
        score_board = urlopen(req, timeout=10).read()
        return json.loads(score_board)
    except socket.timeout:
        print("Timeout when connecting to NBA stats API")
        return None
    except Exception as e:
        print(f"Error fetching scoreboard: {e}")
        return None


def get_boxscore(game_id, game_date):
    game_date_dt_obj = datetime.strptime(game_date, "%b %d, %Y")
    api_formatted_date = game_date_dt_obj.strftime('%Y%m%d')
    day = datetime.strftime(game_date_dt_obj, "%Y%m%d")
    req = create_request(
        f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json",
        'cdn.nba.com', referer='https://cdn.nba.com/')
    box_score = urlopen(req).read()
    return json.loads(box_score)