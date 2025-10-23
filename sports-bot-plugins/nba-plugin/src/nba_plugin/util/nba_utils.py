from datetime import datetime, date
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import CommonPlayerInfo
from functools import lru_cache
from rapidfuzz import process

def get_headers(result_set):
    headers = {}
    index = 0
    for header in result_set["headers"]:
        headers[header] = index
        index += 1
    return headers

def create_linescore_headers(headers):
    linescore_headers = {}
    for key, value in headers.items():
        linescore_headers[key] = value

    return linescore_headers

def get_linescore(score_board):
    linescore_headers = {}
    for item in score_board["resultSets"]:
        if item["name"] == "LineScore":
            linescore_headers = create_linescore_headers(get_headers(item))
            return { "linescore": item, "linescore_headers": linescore_headers }
    return {"empty": True}


def get_gameheader(score_board):
    for item in score_board["resultSets"]:
        if item["name"] == "GameHeader":
            return item
    return {"empty": True}


def get_current_teams_data(linescore):
    teams_data = list()
    for game_set in linescore["rowSet"]:
        teams_data.append(game_set)
    return teams_data


def get_game_header_set_data(gameheader):
    game_header_set = list()
    for game_set in gameheader["rowSet"]:
        game_header_set.append(game_set)
    return game_header_set

def get_current_season():
    current_year = datetime.now().year
    next_year_str = str(current_year + 1)

    season = f"{current_year}-{next_year_str[-2:]}"

    season_end = date(current_year, 7, 1)

    if datetime.now().date() < season_end:
        previous_year = current_year - 1
        season = f"{previous_year}-{str(current_year)[-2:]}"

    return season

def _get_player_stats_averages(stats):
    """Helper function to calculate player stats averages"""
    if stats["data"] == {}: return "Invalid input"

    headers = stats["headers"]
    data = stats["data"]

    games_played = data[headers["GP"]]
    points = data[headers["PTS"]]
    rebounds = data[headers["REB"]]
    assists = data[headers["AST"]]

    ppg = round(points / games_played, 1)
    rpg = round(rebounds / games_played, 1)
    apg = round(assists / games_played, 1)

    return ppg, rpg, apg

def get_formatted_player_career_stats(player_career_stats, player_name):
    ppg, rpg, apg = _get_player_stats_averages(player_career_stats)
    if ppg == "Invalid input": return ppg
    
    formatted_msg = f"{player_name} averages {ppg}/{rpg}/{apg} in his career"
    return formatted_msg

def get_formatted_player_season_stats(player_season_stats, player_name):
    current_season = get_current_season()
    ppg, rpg, apg = _get_player_stats_averages(player_season_stats)
    if ppg == "Invalid input": return ppg

    season = player_season_stats["data"][player_season_stats["headers"]["SEASON_ID"]]
    averaged_tense = "is averaging" if season == current_season else "averaged"

    formatted_msg = f"{player_name} {averaged_tense} {ppg}/{rpg}/{apg} in the {season} season"
    return formatted_msg

def find_players(player_name):
    found_players = {}
    if player_name.isdigit():
        found_players = [players.find_player_by_id(player_name)]
    else:
        found_players = players.find_players_by_full_name(player_name)

    return found_players

@lru_cache(maxsize=1)
def get_team_name_map():
    """Build and cache a lookup map of all possible team name variations"""
    nba_teams = teams.get_teams()
    team_name_map = {}

    for team in nba_teams:
        variations = {
            team["full_name"],
            team["nickname"],
            team["abbreviation"],
            team["city"],
            f"{team['city']} {team['nickname']}",
        }
        for name in variations:
            team_name_map[name.lower()] = team

    return team_name_map

def get_player_team(player_id):
    """
    Fetches the team name for a given player ID.
    """
    if player_id is None:
        return None
        
    player_info = CommonPlayerInfo(player_id=player_id)
    player_info_dict = player_info.get_normalized_dict()
    
    team_name = player_info_dict['CommonPlayerInfo'][0]['TEAM_ID']
    return team_name


def find_team_id(user_query):
    team_name_map = get_team_name_map()
    choices = list(team_name_map.keys())

    match, score, _ = process.extractOne(user_query.lower(), choices)
    matched_team = team_name_map[match]

    return matched_team["id"]

def get_team_by_id(team_id):
    team_name = ""
    try:
        team_data = teams.find_team_name_by_id(team_id=team_id)
        team_name = team_data["nickname"]
    except:
        return ""

    return team_name

def game_clock_to_mm_ss(gameclock):
    clock = gameclock.replace("PT", "").replace("M", ":")[:5]
    # Return empty string if game is over
    if clock == "00:00":
        return ""

    return clock

def game_et_to_hh_mm(gameEt):
    dt = datetime.fromisoformat(gameEt)
    time = dt.strftime('%H:%M')

    return f"{time} ET"

def get_player_stats_from_gamelog(game, headers):
    game_date = game[headers["GAME_DATE"]]
    has_tense = "had"
    points = game[headers["PTS"]]
    rebounds = game[headers["REB"]]
    assists = game[headers["AST"]]
    steals = game[headers["STL"]]
    blocks = game[headers["BLK"]]
    field_goal_pct = int(game[headers["FG_PCT"]] * 100)
    three_point_pct = int(game[headers["FG3_PCT"]] * 100)
    free_throw_pct = int(game[headers["FT_PCT"]] * 100)
    time_played = game[headers["MIN"]]

    return {
        "has_tense": has_tense,
        "points": points,
        "rebounds": rebounds,
        "assists": assists,
        "steals": steals,
        "blocks": blocks,
        "field_goal_pct": field_goal_pct,
        "three_point_pct": three_point_pct,
        "free_throw_pct": free_throw_pct,
        "time_played": time_played,
        "game_date": game_date
    }

def get_player_stats_from_boxscore(player_data):
    has_tense = "has"
    points = player_data["points"]
    rebounds = player_data["reboundsTotal"]
    assists = player_data["assists"]
    steals = player_data["steals"]
    blocks = player_data["blocks"] 
    field_goal_pct = int(player_data["fieldGoalsPercentage"] * 100)
    three_point_pct = int(player_data["threePointersPercentage"] * 100)
    free_throw_pct = int(player_data["freeThrowsPercentage"] * 100)
    time_played = game_clock_to_mm_ss(player_data["minutes"])

    return {
        "has_tense": has_tense,
        "points": points,
        "rebounds": rebounds,
        "assists": assists,
        "steals": steals,
        "blocks": blocks,
        "field_goal_pct": field_goal_pct,
        "three_point_pct": three_point_pct,
        "free_throw_pct": free_throw_pct,
        "time_played": time_played
    }