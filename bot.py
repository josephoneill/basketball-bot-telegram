import logging
import uuid
import re
from datetime import datetime
from datetime import date

from settings import TELEGRAM_TOKEN
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.endpoints import boxscoretraditionalv2
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo

linescore_headers = {}
nba_start_date = datetime(2019, 10, 22)

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="*Edgy starting message*")


def season_stats_command_handler(update, context):
    if update.message is None:
        return

    formatted_message = get_formatted_input_message(update.message.text)
    split_input_msg = re.split(r'\s|-', formatted_message)
    player_name_input = ""
    index = 0
    for word in split_input_msg:
        if word.isdigit():
            if index == 0:
                send_invalid_message(update, context)
                return
            else:
                break

        formatted_word = " " + word if index > 0 else word
        player_name_input += formatted_word
        index += 1

    start_year = ""
    end_year = ""
    if len(split_input_msg) - index >= 1:
        start_year = split_input_msg[index]

    if len(split_input_msg) - index >= 2:
        end_year = split_input_msg[index + 1]

    players_found = find_players(player_name_input)

    if len(players_found) != 1:
        handle_none_or_mult_players_found(players_found, update, context)
        return

    player = players_found[0]
    player_id = player["id"]
    player_name = player["full_name"]

    player_career_stats = get_player_career_stats(player_id)

    player_season_stats = get_player_reg_season_stats(player_career_stats, start_year, end_year)

    msg = get_formatted_player_season_stats(player_season_stats, player_name)

    context.bot.send_message(chat_id=update.message.chat_id, text=msg)


def career_stats_command_handler(update, context):
    formatted_message = get_formatted_input_message(update.message.text)
    players_found = find_players(formatted_message)

    if len(players_found) != 1:
        handle_none_or_mult_players_found(players_found, update, context)
        return

    player = players_found[0]
    player_id = player["id"]
    player_name = player["full_name"]
    career_totals = {}

    player_career_stats = get_player_career_stats(player_id)

    for result_set in player_career_stats["resultSets"]:
        if result_set["name"] == "CareerTotalsRegularSeason":
            career_totals = result_set
            break

    headers = get_headers(career_totals)

    msg = get_formatted_player_career_stats(dict(headers=headers, data=career_totals["rowSet"][0]), player_name)
    context.bot.send_message(chat_id=update.message.chat_id, text=msg)


def current_stats_command_handler(update, context):
    formatted_message = get_formatted_input_message(update.message.text)
    players_found = find_players(formatted_message)

    if len(players_found) != 1:
        handle_none_or_mult_players_found(players_found, update, context)
        return

    player = players_found[0]
    player_id = player["id"]
    player_name = player["full_name"]

    score_board = get_scoreboard()
    linescore = get_linescore(score_board)

    team_id = get_team_id_by_player(player_id)
    teams_data = get_current_teams_data(linescore)
    player_current_stats = get_player_current_game_stats(teams_data, player_id, team_id)
    msg = get_formatted_player_current_stats(player_current_stats, player_name)
    context.bot.send_message(chat_id=update.message.chat_id, text=msg)


def get_formatted_input_message(msg):
    input_msg = msg.lower()
    return input_msg.replace(input_msg[0:input_msg.find(' ') + 1], '')


def get_scoreboard():
    # score_board = scoreboardv2.ScoreboardV2(game_date=str(date.today()))
    score_board = scoreboardv2.ScoreboardV2(game_date=str(date.today()))
    return score_board.get_dict()


def get_boxscore(game_id):
    box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    return box_score.get_dict()


def get_linescore(score_board):
    for item in score_board["resultSets"]:
        if item["name"] == "LineScore":
            if len(linescore_headers) < 1:
                set_linescore_headers(get_headers(item))
            return item
    return [{'empty'}]


def get_current_teams_data(linescore):
    teams_data = list()
    for game_set in linescore["rowSet"]:
        teams_data.append(game_set)
    return teams_data


def find_players(player_name):
    found_players = {}
    if player_name.isdigit():
        found_players = [players.find_player_by_id(player_name)]
    else:
        found_players = players.find_players_by_full_name(player_name)

    return found_players


def get_team_id_by_player(player_id):
    common_player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
    result_set = common_player_info["resultSets"][0]
    cpi_headers = get_headers(result_set)

    team = result_set["rowSet"][0][cpi_headers["TEAM_ID"]]
    return team


def get_player_career_stats(player_id):
    return playercareerstats.PlayerCareerStats(player_id=player_id).get_dict()


def get_player_reg_season_stats(career_stats, start_year, end_year):
    if not start_year.isdigit(): dict(headers={}, data={})

    curr_year = datetime.now().year
    season_id = ""
    if end_year != "":
        season_id = f"{start_year}-{end_year[-2:]}"
    elif start_year == "":
        ref_year = int(curr_year - 1)
        season_id = f"{ref_year}-{start_year[-2:]}"
    else:
        ref_year = int(start_year) - 1
        season_id = f"{ref_year}-{start_year[-2:]}"

    reg_season_totals_set = {}
    for result_set in career_stats["resultSets"]:
        if result_set["name"] == "SeasonTotalsRegularSeason":
            reg_season_totals_set = result_set
            break

    headers = get_headers(reg_season_totals_set)
    row_set = reg_season_totals_set["rowSet"]

    if start_year == "":
        # If no year is provided, use latest season
        return dict(headers=headers, data=row_set[len(row_set) - 1])
    else:
        for item in row_set:
            if item[headers["SEASON_ID"]] == season_id:
                return dict(headers=headers, data=item)

    return dict(headers=headers, data={})


def get_player_most_recent_game_id(player_id, teams_data, player_team_id):
    game_id = 0
    for team_data in teams_data:
        if team_data[linescore_headers["TEAM_ID"]] == player_team_id:
            game_id = team_data[linescore_headers["GAME_ID"]]

    return game_id


def get_player_current_game_stats(teams_data, player_id, player_team_id):
    team_players_stats_set = {}
    player_stats = {}
    game_id = get_player_most_recent_game_id(player_id, teams_data, player_team_id)

    # If a current game could not be found
    if game_id == 0:
        return dict(headers={}, data=player_stats)

    box_score = get_boxscore(game_id)
    result_sets = box_score["resultSets"]

    for result_set in result_sets:
        if result_set["name"] == "PlayerStats":
            team_players_stats_set = result_set
            break

    headers = get_headers(team_players_stats_set)

    for player_data in team_players_stats_set["rowSet"]:
        if player_data[headers["PLAYER_ID"]] == player_id:
            player_stats = player_data
            break

    return dict(headers=headers, data=player_stats)


def get_formatted_player_season_stats(player_season_stats, player_name):
    if player_season_stats["data"] == {}: return "Invalid input"

    headers = player_season_stats["headers"]
    data = player_season_stats["data"]

    games_played = data[headers["GP"]]
    points = data[headers["PTS"]]
    rebounds = data[headers["REB"]]
    assists = data[headers["AST"]]
    season = data[headers["SEASON_ID"]]

    ppg = round(points / games_played, 1)
    rpg = round(rebounds / games_played, 1)
    apg = round(assists / games_played, 1)

    formatted_msg = f"{player_name} averaged {ppg}/{rpg}/{apg} in the {season} season"
    return formatted_msg


def get_formatted_player_career_stats(player_career_stats, player_name):
    if player_career_stats["data"] == {}: return "Invalid input"

    headers = player_career_stats["headers"]
    data = player_career_stats["data"]

    games_played = data[headers["GP"]]
    points = data[headers["PTS"]]
    rebounds = data[headers["REB"]]
    assists = data[headers["AST"]]

    ppg = round(points / games_played, 1)
    rpg = round(rebounds / games_played, 1)
    apg = round(assists / games_played, 1)

    formatted_msg = f"{player_name} averages {ppg}/{rpg}/{apg} in his career"
    return formatted_msg


# TODO: Combine this and the two functions above into one single function
def get_formatted_player_current_stats(player_current_stats, player_name):
    if player_current_stats["data"] == {}:
        return "Player is not currently playing"

    headers = player_current_stats["headers"]
    data = player_current_stats["data"]

    points = data[headers["PTS"]]
    rebounds = data[headers["REB"]]
    assists = data[headers["AST"]]

    field_goal_p = round(data[headers["FG_PCT"]] * 100)
    three_point_p = round(data[headers["FG3_PCT"]] * 100)
    free_throw_p = round(data[headers["FT_PCT"]] * 100)

    given_minutes_str = data[headers["MIN"]]
    minutes = int(given_minutes_str[0:given_minutes_str.find(':')])
    seconds = int(given_minutes_str[given_minutes_str.find(':')+1:len(given_minutes_str)])
    time_played = minutes if seconds <= 30 else minutes+1

    formatted_msg = f"{player_name} has {points}/{rebounds}/{assists} on " \
                    f"{field_goal_p}/{three_point_p}/{free_throw_p} shooting in {time_played} minutes"
    return formatted_msg


def handle_none_or_mult_players_found(players_found, update, context):
    if len(players_found) == 0:
        send_player_not_found_message(update, context)
    else:
        msg = "Multiple results found. Please try again with the desired player id.\n"
        for player_found in players_found:
            msg += f"{player_found['full_name']}; id={player_found['id']}\n"

        context.bot.send_message(chat_id=update.message.chat_id, text=msg)


def create_inline_query_lists(teams_data, query):
    results = list()
    for i in range(0, int(len(teams_data) - 1), 2):
        team_a = teams_data[i]
        team_b = teams_data[i + 1]

        team_a_name = team_a[linescore_headers["TEAM_NAME"]]
        team_b_name = team_b[linescore_headers["TEAM_NAME"]]

        message = create_inline_request_message(team_a, team_b)

        if query.lower() in team_a_name.lower() or query.lower() in team_b_name.lower():
            results.append(
                InlineQueryResultArticle(
                    id=uuid.uuid4(),
                    title=f"{team_a_name} vs. {team_b_name}",
                    input_message_content=InputTextMessageContent(message)
                )
            )

    return results


def create_inline_request_message(team_a, team_b):
    team_a_name = team_a[linescore_headers["TEAM_NAME"]]
    team_b_name = team_b[linescore_headers["TEAM_NAME"]]

    team_a_record = team_a[linescore_headers["TEAM_WINS_LOSSES"]]
    team_b_record = team_b[linescore_headers["TEAM_WINS_LOSSES"]]

    team_a_score = team_a[linescore_headers["PTS"]]
    team_b_score = team_b[linescore_headers["PTS"]]

    if team_a_score > team_b_score:
        message = f"The {team_a_name} ({team_a_record}) are currently leading the {team_b_name} ({team_b_record})," \
                  f" {team_a_score}-{team_b_score} "
    elif team_a_score < team_b_score:
        message = f"The {team_b_name} ({team_b_record}) are currently leading the {team_a_name} ({team_a_record})," \
                  f" {team_b_score}-{team_a_score}"
    else:
        message = f"The {team_a_name} ({team_a_record}) are currently tied with the {team_b_name} ({team_b_record})," \
                  f" {team_a_score}-{team_b_score}"

    return message


def set_linescore_headers(headers):
    for key, value in headers.items():
        linescore_headers[key] = value


def get_headers(result_set):
    headers = {}
    index = 0
    for header in result_set["headers"]:
        headers[header] = index
        index += 1
    return headers


def inline_teams_scores(update, context):
    query = update.inline_query.query
    if not query:
        return

    score_board = get_scoreboard()
    linescore = get_linescore(score_board)

    teams_data = get_current_teams_data(linescore)
    results = create_inline_query_lists(teams_data, query)
    context.bot.answer_inline_query(update.inline_query.id, results)


def countdown_command_handler(update, context):
    days_left = days_between(nba_start_date, datetime.today())
    context.bot.send_message(chat_id=update.message.chat_id, text=f"{days_left} days left until the 2019 season begins")


def days_between(d1, d2):
    return abs((d2 - d1).days)


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command")


def send_invalid_message(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Invalid input")


def send_player_not_found_message(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")


# create and add handlers
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

season_stats_handler = CommandHandler('seasonstats', season_stats_command_handler)
dispatcher.add_handler(season_stats_handler)

career_stats_handler = CommandHandler('careerstats', career_stats_command_handler)
dispatcher.add_handler(career_stats_handler)

current_stats_handler = CommandHandler('currentstats', current_stats_command_handler)
dispatcher.add_handler(current_stats_handler)

inline_scores_handler = InlineQueryHandler(inline_teams_scores)
dispatcher.add_handler(inline_scores_handler)

countdown_handler = CommandHandler('countdown', countdown_command_handler)
dispatcher.add_handler(countdown_handler)

# start the bot
updater.start_polling()
