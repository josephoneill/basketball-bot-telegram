from datetime import datetime, date
from nba_api.stats.static import players

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