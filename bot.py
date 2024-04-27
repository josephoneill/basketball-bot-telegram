import json
import logging
import re
from urllib.request import Request, urlopen
import uuid
from datetime import date
from datetime import datetime

import telegram
from pytz import timezone

from nba_api.stats.static import players
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CommandHandler, ApplicationBuilder
from telegram.ext import InlineQueryHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ChosenInlineResultHandler

from settings import TELEGRAM_TOKEN
from image_generator import generate_score_img

linescore_headers = {}
current_season = "2023-24"

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


async def start(update, context):
    # This is the unicode for a cowboy :)
    await context.bot.send_message(chat_id=update.message.chat_id, text=u'\U0001F920')

    global current_season
    current_season = get_current_season()


async def season_stats_command_handler(update, context, player_id=-1):
    if update.message is None:
        return

    formatted_message = get_formatted_input_message(update.message.text)
    split_input_msg = re.split(r'\s|-', formatted_message)
    player_name_input = ""
    index = 0
    for word in split_input_msg:
        if word.isdigit():
            if index != 0:
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

    players_found = find_players(player_name_input if player_id == -1 else player_id)

    if len(players_found) != 1:
        await handle_none_or_mult_players_found(players_found, update, context, 'season_stats')
        return

    player = players_found[0]
    player_id = player["id"]
    player_name = player["full_name"]

    player_career_stats = get_player_career_stats(player_id)

    player_season_stats = get_player_reg_season_stats(player_career_stats, start_year, end_year)

    msg = get_formatted_player_season_stats(player_season_stats, player_name)

    await context.bot.send_message(chat_id=update.message.chat_id, text=msg)


async def career_stats_command_handler(update, context, player_id=-1):
    formatted_message = get_formatted_input_message(update.message.text)
    players_found = find_players(formatted_message if player_id == -1 else player_id)

    if len(players_found) != 1:
        await handle_none_or_mult_players_found(players_found, update, context, "career_stats")
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
    await context.bot.send_message(chat_id=update.message.chat_id, text=msg)


async def current_stats_command_handler(update, context, player_id=-1):
    formatted_message = get_formatted_input_message(update.message.text)
    players_found = find_players(formatted_message if player_id == -1 else player_id)

    if len(players_found) != 1:
        await handle_none_or_mult_players_found(players_found, update, context, "current_stats")
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
    await context.bot.send_message(chat_id=update.message.chat_id, text=msg)


async def scores_command_handler(update, context):
    formatted_message = get_formatted_input_message(update.message.text)
    score_board = get_scoreboard()
    linescore = get_linescore(score_board)
    gameheader = get_gameheader(score_board)
    team_scores = get_team_scores(gameheader, linescore, formatted_message)[0]

    await context.bot.send_photo(chat_id=update.message.chat_id, photo=generate_score_img(team_scores))

async def callback_query_keyboard_handler(update, context):
    callback_data = [s.strip() for s in update.callback_query.data.split(',')]
    player_id = callback_data[0].split('=')[1]
    handler = callback_data[1].split('=')[1]

    await context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat.id, message_id=update.callback_query.message.message_id, reply_markup=None)

    if handler == "current_stats":
        await current_stats_command_handler(update.callback_query, context, player_id)
    elif handler == "career_stats":
        await career_stats_command_handler(update.callback_query, context, player_id)
    elif handler == "season_stats":
        await season_stats_command_handler(update.callback_query, context, player_id)


def get_formatted_input_message(msg):
    input_msg = msg.lower()
    return input_msg.replace(input_msg[0:input_msg.find(' ') + 1], '')


def get_scoreboard():
    curr_date = str(get_current_eastern_time()).split()[0]
    request_url = f"https://stats.nba.com/stats/scoreboardv2?DayOffset=0&GameDate={curr_date}&LeagueID=00&refresh={uuid.uuid4()}"
    req = create_request(request_url)
    score_board = urlopen(req).read()
    return json.loads(score_board)


def get_boxscore(game_id, game_date):
    game_date_dt_obj = datetime.strptime(game_date, "%b %d, %Y")
    api_formatted_date = game_date_dt_obj.strftime('%Y%m%d')
    day = datetime.strftime(game_date_dt_obj, "%Y%m%d")
    req = create_request(
        f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json",
        'cdn.nba.com', referer='https://cdn.nba.com/')
    box_score = urlopen(req).read()
    return json.loads(box_score)


def get_linescore(score_board):
    for item in score_board["resultSets"]:
        if item["name"] == "LineScore":
            if len(linescore_headers) < 1:
                set_linescore_headers(get_headers(item))
            return item
    return [{'empty'}]


def get_gameheader(score_board):
    for item in score_board["resultSets"]:
        if item["name"] == "GameHeader":
            return item
    return [{'empty'}]


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


def find_players(player_name):
    found_players = {}
    if player_name.isdigit():
        found_players = [players.find_player_by_id(player_name)]
    else:
        found_players = players.find_players_by_full_name(player_name)

    return found_players


def get_team_id_by_player(player_id):
    req = create_request(f"https://stats.nba.com/stats/commonplayerinfo?LeagueID=&PlayerID={player_id}")
    common_player_response = urlopen(req).read()
    common_player_info = json.loads(common_player_response)
    result_set = common_player_info["resultSets"][0]
    cpi_headers = get_headers(result_set)

    team = result_set["rowSet"][0][cpi_headers["TEAM_ID"]]
    return team


def get_player_career_stats(player_id):
    req = create_request(f"https://stats.nba.com/stats/playercareerstats?LeagueID=&PerMode=Totals&PlayerID={player_id}")
    player_career_stats = urlopen(req).read()

    return json.loads(player_career_stats)


def get_player_common_info(player_id):
    req = create_request(f"https://stats.nba.com/stats/commonplayerinfo?LeagueID=&PlayerID={player_id}")
    player_common_info = urlopen(req).read()
    return json.loads(player_common_info)


def get_player_game_log(player_id):
    season = current_season
    req = create_request(
        f"https://stats.nba.com/stats/playergamelog?DateFrom=&DateTo=&LeagueID=&PlayerID={player_id}&Season={season}&SeasonType=Regular+Season")
    player_game_log = urlopen(req).read()
    return json.loads(player_game_log)


def create_request(url, host='stats.nba.com', referer='https://stats.nba.com/'):
    req = Request(url)
    req.add_header('User-Agent', 'PostmanRuntime/7.24.0')
    req.add_header('Host', host)
    req.add_header('Referer', referer)
    req.add_header('Accept', '*/*')
    req.add_header('x-nba-stats-origin', 'stats')
    req.add_header('x-nba-stats-token', 'true')
    return req


def get_player_reg_season_stats(career_stats, start_year, end_year):
    if not start_year.isdigit(): dict(headers={}, data={})

    curr_year = get_current_eastern_time().year
    season_id = ""
    if end_year != "":
        season_id = f"{start_year}-{end_year[-2:]}"
    elif start_year != "":
        ref_year = int(start_year) - 1
        season_id = f"{ref_year}-{start_year[-2:]}"
    else:
        season_id = current_season

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


def get_player_most_recent_game(player_id, teams_data, player_team_id):
    game_id = 0
    game_date = datetime.strftime(get_current_eastern_time(), "%b %d, %Y")

    for team_data in teams_data:
        if team_data[linescore_headers["TEAM_ID"]] == player_team_id:
            game_id = team_data[linescore_headers["GAME_ID"]]

    if game_id == 0:
        player_game_log_result = get_player_game_log(player_id)
        player_game_log_result_set = player_game_log_result["resultSets"][0]
        headers = get_headers(player_game_log_result_set)
        if len(player_game_log_result_set["rowSet"]) > 0:
            # Return the game id of the first item in the rowSet, which will be the latest game
            game_id = player_game_log_result_set["rowSet"][0][headers["Game_ID"]]
            game_date = player_game_log_result_set["rowSet"][0][headers["GAME_DATE"]]


    return dict(game_id=game_id, game_date=game_date)


def get_player_current_game_stats(teams_data, player_id, player_team_id):
    team_players_stats_set = {}
    player_stats = {}
    common_player_info = get_player_common_info(player_id=player_id)["resultSets"][0]
    common_player_headers = get_headers(common_player_info)
    team_name = common_player_info["rowSet"][0][common_player_headers["TEAM_NAME"]]
    first_name = common_player_info["rowSet"][0][common_player_headers["FIRST_NAME"]]
    last_name = common_player_info["rowSet"][0][common_player_headers["LAST_NAME"]]

    most_recent_game = get_player_most_recent_game(player_id, teams_data, player_team_id)
    game_id = most_recent_game["game_id"]
    game_date = most_recent_game["game_date"]

    # If a current game could not be found
    if game_id == 0:
        return dict(headers={}, data=player_stats)

    box_score = get_boxscore(game_id, game_date)["game"]

    home_player = box_score["homeTeam"]["teamName"] == team_name

    if len(box_score) == 0:
        return dict(data={}, headers={}, game_ongoing={})

    game_ongoing = box_score["gameStatusText"] != "Final"

    if len(box_score["homeTeam" if home_player else "awayTeam"]["players"]) == 0:
        return dict(data={}, headers={}, game_ongoing={})

    players_stats_set = box_score["homeTeam" if home_player else "awayTeam"]["players"]

    for player_data in players_stats_set:
        if player_data["personId"] == player_id or (player_data["firstName"] == f"{first_name}" and player_data["familyName"] == f"{last_name}"):
            player_stats = player_data['statistics']
            break

    return dict(data=player_stats, game_ongoing=game_ongoing)


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

    averaged_tense = "is averaging" if season == current_season else "averaged"

    formatted_msg = f"{player_name} {averaged_tense} {ppg}/{rpg}/{apg} in the {season} season"
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

    data = player_current_stats["data"]
    game_ongoing = player_current_stats["game_ongoing"]

    points = data["points"]

    # If points is null, game hasn't started
    if points is None:
        return "Game has not started yet"

    o_rebounds = safe_int(data["reboundsOffensive"])
    d_rebounds = safe_int(data["reboundsDefensive"])

    rebounds = o_rebounds + d_rebounds

    assists = safe_int(data["assists"])

    field_goal_a = safe_int(data["fieldGoalsAttempted"])
    field_goal_m = safe_int(data["fieldGoalsMade"])
    field_goal_p = safe_stat_percentage(field_goal_m, field_goal_a)

    three_point_a = safe_int(data["threePointersAttempted"])
    three_point_m = safe_int(data["threePointersMade"])
    three_point_p = safe_stat_percentage(three_point_m, three_point_a)

    free_throw_a = safe_int(data["freeThrowsAttempted"])
    free_throw_m = safe_int(data["freeThrowsMade"])
    free_throw_p = safe_stat_percentage(free_throw_m, free_throw_a)

    minutes = data["minutes"]
    minutes_played = minutes[2:minutes.index('M')]
    seconds_played = minutes[minutes.index('M') + 1:minutes.index('.')]
    time_played = f"{minutes_played}:{seconds_played}"
    has_tense = "has" if game_ongoing else "had"

    formatted_msg = f"{player_name} {has_tense} {points}/{rebounds}/{assists} on " \
                    f"{field_goal_p}/{three_point_p}/{free_throw_p} shooting in {time_played} minutes"
    return formatted_msg


async def handle_none_or_mult_players_found(players_found, update, context, requesting_command_name):
    if len(players_found) == 0:
        await send_player_not_found_message(update, context)
    else:
        msg = "Please select a player.\n"
        keyboard = []

        for player_found in players_found:
            keyboard.append([telegram.InlineKeyboardButton(
                text=player_found['full_name'],
                callback_data=f"id={player_found['id']}, code={requesting_command_name}")]
            )

        reply_markup = telegram.InlineKeyboardMarkup(
            inline_keyboard=keyboard,
        )

        await context.bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=reply_markup)\


def safe_stat_percentage(a, b):
    if b == 0: return 0
    return round(a / b * 100)


def safe_int(a):
    if a is None or not (isinstance(a, (int, float, complex, str)) and not isinstance(a, bool)):
        return 0
    else:
        return int(a)


def get_team_scores(gameheader, linescore, query):
    gameheader_headers = get_headers(gameheader)
    teams_data = get_current_teams_data(linescore)
    game_header_set = get_game_header_set_data(gameheader)
    results = list()

    for i in range(0, int(len(teams_data) - 1), 2):
        team_a = teams_data[i]
        team_b = teams_data[i + 1]

        start_time = game_header_set[int(i / 2)][gameheader_headers["GAME_STATUS_TEXT"]]

        team_a_name = team_a[linescore_headers["TEAM_NAME"]]
        team_b_name = team_b[linescore_headers["TEAM_NAME"]]


        if query.lower() in team_a_name.lower() or query.lower() in team_b_name.lower():
            team_compare_data = get_team_compare_data(gameheader, start_time, team_a, team_b)
            results.append(team_compare_data)

    return results

def create_inline_query_lists(gameheader, linescore, query):
    results = list()
    team_data_list = get_team_scores(gameheader, linescore, query)

    for team_data in team_data_list:
        message = create_inline_request_message(team_data)
        team_a_name = team_data["team_a_name"]
        team_b_name = team_data["team_b_name"]
        results.append(
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title=f"{team_a_name} vs. {team_b_name}",
                input_message_content=InputTextMessageContent(message)
            )
        )

    return results


def get_team_compare_data(gameheader, start_time, team_a, team_b):
    gameheader_headers = get_headers(gameheader)
    game_header_set = get_game_header_set_data(gameheader)

    team_a_name = team_a[linescore_headers["TEAM_NAME"]]
    team_b_name = team_b[linescore_headers["TEAM_NAME"]]

    team_a_record = team_a[linescore_headers["TEAM_WINS_LOSSES"]]
    team_b_record = team_b[linescore_headers["TEAM_WINS_LOSSES"]]

    team_a_score = team_a[linescore_headers["PTS"]]
    team_b_score = team_b[linescore_headers["PTS"]]

    gameheader_game_index = [(i, el) for i, el in enumerate(game_header_set) if
                             el[gameheader_headers["GAME_ID"]] == team_a[linescore_headers["GAME_ID"]]][0][0]

    game_status = game_header_set[gameheader_game_index][gameheader_headers["GAME_STATUS_TEXT"]]
    live_pc_time = game_header_set[gameheader_game_index][gameheader_headers["LIVE_PC_TIME"]]

    team_compare_data = {}
    team_compare_data["team_a_name"] = team_a_name
    team_compare_data["team_b_name"] = team_b_name
    team_compare_data["team_a_record"] = team_a_record
    team_compare_data["team_b_record"] = team_b_record
    team_compare_data["team_a_score"] = team_a_score
    team_compare_data["team_b_score"] = team_b_score
    team_compare_data["game_status"] = game_status
    team_compare_data["start_time"] = start_time
    team_compare_data["live_pc_time"] = live_pc_time

    return team_compare_data

def create_inline_request_message(team_compare_data):
    team_a_name = team_compare_data["team_a_name"]
    team_b_name = team_compare_data["team_b_name"]
    team_a_record = team_compare_data["team_a_record"]
    team_b_record = team_compare_data["team_b_record"]
    team_a_score = team_compare_data["team_a_score"]
    team_b_score = team_compare_data["team_b_score"]
    game_status = team_compare_data["game_status"]
    start_time = team_compare_data["start_time"]

    game_status_text = "defeated" if game_status == "Final" else "are currently leading"
    if team_a_score is None or team_b_score is None:
        message = f"The {team_a_name}-{team_b_name} game does not start until {start_time}"
        return message

    if team_a_score > team_b_score:
        message = f"The {team_a_name} ({team_a_record}) {game_status_text} the {team_b_name} ({team_b_record})," \
                  f" {team_a_score}-{team_b_score} "
    elif team_a_score < team_b_score:
        message = f"The {team_b_name} ({team_b_record}) {game_status_text} the {team_a_name} ({team_a_record})," \
                  f" {team_b_score}-{team_a_score}"
    else:
        message = f"The {team_a_name} ({team_a_record}) are currently tied with the {team_b_name} ({team_b_record})," \
                  f" {team_a_score}-{team_b_score}"

    return message


def get_current_season():
    current_year = datetime.now().year
    next_year_str = str(current_year + 1)

    season = f"{current_year}-{next_year_str[-2:]}"

    season_end = date(current_year, 7, 1)

    if datetime.now().date() < season_end:
        previous_year = current_year - 1
        season = f"{previous_year}-{str(current_year)[-2:]}"

    return season


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


async def inline_teams_scores(update, context):
    query = update.inline_query.query
    if not query:
        return

    score_board = get_scoreboard()
    linescore = get_linescore(score_board)
    gameheader = get_gameheader(score_board)

    results = create_inline_query_lists(gameheader, linescore, query)
    if len(results) == 0:
        results.append(
            InlineQueryResultArticle(
                id=uuid.uuid4(),
                title=f"No current games",
                input_message_content=InputTextMessageContent("No current games")
            )
        )

    await context.bot.answer_inline_query(update.inline_query.id, results)


def get_current_eastern_time():
    eastern = timezone('US/Eastern')
    time = datetime.now(eastern)
    return time


def days_between(d1, d2):
    return abs((d2 - d1).days)


async def unknown(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command")


async def send_invalid_message(update, context):
   await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid input")


async def send_player_not_found_message(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # create and add handlers

    season_stats_handler = CommandHandler('seasonstats', season_stats_command_handler)
    application.add_handler(season_stats_handler)

    career_stats_handler = CommandHandler('careerstats', career_stats_command_handler)
    application.add_handler(career_stats_handler)

    current_stats_handler = CommandHandler('currentstats', current_stats_command_handler)
    application.add_handler(current_stats_handler)

    scores_handler = CommandHandler('scores', scores_command_handler)
    application.add_handler(scores_handler)

    callback_query_handler = CallbackQueryHandler(callback_query_keyboard_handler)
    application.add_handler(callback_query_handler)

    inline_scores_handler = InlineQueryHandler(inline_teams_scores)
    application.add_handler(inline_scores_handler)

    #start the bot
    application.run_polling()
