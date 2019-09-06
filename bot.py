import logging
import json
from datetime import date

from settings import TELEGRAM_TOKEN
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

from nba_api.stats.endpoints import scoreboardv2

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="*Edgy starting message*")


def get_scoreboard():
    score_board = scoreboardv2.ScoreboardV2(game_date=str(date.today()))
    test = get_linescore(score_board)


def get_linescore(score_board):
    for item in score_board.get_dict()["resultSets"]:
        if item["name"] == "LineScore":
            return item
    return [{'empty'}]


def inline_team_score(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


# create and add handlers
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

# start the bot
updater.start_polling()
get_scoreboard()
