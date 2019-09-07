import logging
import uuid
from datetime import date

from settings import TELEGRAM_TOKEN
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

from nba_api.stats.endpoints import scoreboardv2

linescore_headers = {}

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="*Edgy starting message*")


def player_stats_handler(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="hey")


def get_scoreboard():
    # score_board = scoreboardv2.ScoreboardV2(game_date=str(date.today()))
    score_board = scoreboardv2.ScoreboardV2(game_date="2019-04-15")
    return score_board


def get_linescore(score_board):
    for item in score_board.get_dict()["resultSets"]:
        if item["name"] == "LineScore":
            if len(linescore_headers) < 1:
                set_linescore_headers(item)
            return item
    return [{'empty'}]


def get_current_teams_data(linescore):
    teams_data = list()
    for game_set in linescore["rowSet"]:
        teams_data.append(game_set)
    return teams_data


def create_inline_query_lists(teams_data, query):
    results = list()
    for i in range(0, int(len(teams_data) - 1), 2):
        team_a = teams_data[i]
        team_b = teams_data[i + 1]

        team_a_name = team_a[linescore_headers["TEAM_NAME"]]
        team_b_name = team_b[linescore_headers["TEAM_NAME"]]

        message = create_inline_request_message(team_a, team_b)

        print(query.lower())
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


def set_linescore_headers(linescore):
    index = 0
    for header in linescore["headers"]:
        linescore_headers[header] = index
        index += 1
    return


def inline_teams_scores(update, context):
    query = update.inline_query.query
    if not query:
        return

    score_board = get_scoreboard()
    linescore = get_linescore(score_board)

    teams_data = get_current_teams_data(linescore)
    results = create_inline_query_lists(teams_data, query)
    print(results)
    context.bot.answer_inline_query(update.inline_query.id, results)


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


# create and add handlers
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

player_stats_handler = CommandHandler('playerstats', player_stats_handler)
dispatcher.add_handler(player_stats_handler)

inline_scores_handler = InlineQueryHandler(inline_teams_scores)
dispatcher.add_handler(inline_scores_handler)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

# start the bot
updater.start_polling()
