import logging
from datetime import datetime
from typing import List, Dict

import telegram
from pytz import timezone
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CommandHandler, ApplicationBuilder
from telegram.ext import InlineQueryHandler
from telegram.ext import CallbackQueryHandler

from .settings import TELEGRAM_TOKEN
from .image_generator import generate_score_img, delete_img
from .plugin_management import PluginManager
import re

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

async def start(update, context):
    # This is the unicode for a cowboy :)
    await context.bot.send_message(chat_id=update.message.chat_id, text=u'\U0001F920')

def get_formatted_input_message(msg):
    input_msg = msg.lower()
    return input_msg.replace(input_msg[0:input_msg.find(' ') + 1], '')

def get_player_name_and_years(msg):
    if msg is None:
        return

    formatted_message = get_formatted_input_message(msg.text)
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

    return player_name_input, start_year, end_year

async def unknown(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command")

async def send_invalid_message(update, context):
   await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid input")

async def send_player_not_found_message(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")

async def scores_command_handler(update, context):
    formatted_message = get_formatted_input_message(update.message.text).split()
    team = formatted_message[0]
    game_date = None
    if len(formatted_message) > 1:
        game_date = formatted_message[1]

    plugin = PluginManager.find_plugin_for_team(team)
    if not plugin:
        await context.bot.send_message(
            chat_id=update.message.chat_id, 
            text="Sorry, I couldn't find a supported team with that name"
        )
        return

    try:
        if game_date:
            try:
                # Try common date formats
                for fmt in ["%m-%d-%Y", "%m-%d-%y", "%Y-%m-%d"]:
                    try:
                        date_obj = datetime.strptime(game_date, fmt)
                        game_date_obj = date_obj.strftime("%m-%d-%Y")
                        break
                    except ValueError:
                        continue
                else:
                    game_date_obj = None
            except Exception:
                game_date_obj = None
        else:
            game_date_obj = None
        team_scores = plugin.get_live_scores(team, game_date_obj)
        
        if not team_scores:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"No games found for {team}" + (f" on {game_date}" if game_date else "")
            )
            return

        scores_sticker = generate_score_img(team_scores)
        await context.bot.send_sticker(chat_id=update.message.chat_id, sticker=scores_sticker)
        delete_img(scores_sticker)
    except Exception as e:
        logger.error(f"Error getting scores: {str(e)}")
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Sorry, there was an error getting the scores"
        )

async def current_stats_command_handler(update, context, player_id=-1):
    formatted_message = get_formatted_input_message(update.message.text)
    
    # Try each registered plugin until we find player stats
    plugin = PluginManager.find_plugin_for_player(formatted_message)
    try:
        player_stats_msg = plugin.get_player_live_stats(formatted_message)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player stats: {str(e)}")
    
    await send_player_not_found_message(update, context)

async def season_stats_command_handler(update, context):
    player_name, start_year, end_year = get_player_name_and_years(update.message)
    # Try each registered plugin until we find player stats
    plugin = PluginManager.find_plugin_for_player(player_name)
    try:
        player_stats_msg = plugin.get_player_season_stats(player_name, start_year, end_year)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player season stats: {str(e)}")
        await send_player_not_found_message(update, context)

async def career_stats_command_handler(update, context):
    player_name, _, _ = get_player_name_and_years(update.message)
    plugin = PluginManager.find_plugin_for_player(player_name)
    try:
        player_stats_msg = plugin.get_player_career_stats(player_name)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player careerstats: {str(e)}")
        await send_player_not_found_message(update, context)


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register core handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    scores_handler = CommandHandler('scores', scores_command_handler)
    application.add_handler(scores_handler)

    current_stats_handler = CommandHandler('currentstats', current_stats_command_handler)
    application.add_handler(current_stats_handler)

    season_stats_handler = CommandHandler('seasonstats', season_stats_command_handler)
    application.add_handler(season_stats_handler)

    career_stats_handler = CommandHandler('careerstats', career_stats_command_handler)
    application.add_handler(career_stats_handler)

    # Register all plugin handlers
    PluginManager.setup_plugin_handlers(application)

    logger.info("Starting bot...")
    application.run_polling() 