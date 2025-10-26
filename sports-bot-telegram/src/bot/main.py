import logging
from datetime import datetime
from typing import List, Dict

import telegram
from pytz import timezone
from telegram import InlineQueryResultArticle, InputTextMessageContent, BotCommand
from telegram.ext import CommandHandler, ApplicationBuilder, MessageHandler
from telegram.ext import InlineQueryHandler
from telegram.ext import CallbackQueryHandler

from .settings import TELEGRAM_TOKEN
from .image_generator import generate_score_img, delete_img
from .plugin_management import PluginManager
from importlib.metadata import version, PackageNotFoundError
import re
import asyncio

# setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

try:
    BOT_VERSION = version("sports-bot-telegram")
except PackageNotFoundError:
    BOT_VERSION = "1.1.3"

async def start(update, context):
    # This is the unicode for a cowboy :)
    await context.bot.send_message(chat_id=update.message.chat_id, text=u'\U0001F920')

def get_formatted_input_message(msg):
    input_msg = msg.lower()
    return input_msg.replace(input_msg[0:input_msg.find(' ') + 1], '')

def get_player_name_and_years(msg, id=-1, start_year=-1, end_year=-1):
    if id != -1:
        return id, start_year, end_year

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
    # Privacy mode is off, don't send a message for unknown commands
    return
    # await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command")


async def send_invalid_message(update, context):
   await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid input")

async def send_player_not_found_message(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I could not find a player with that name")

async def version_command_handler(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Bot version: {BOT_VERSION}"
    )

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
        team_scores = await plugin.get_live_scores(team, game_date_obj)
        
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
    formatted_message = get_formatted_input_message(update.message.text) if player_id == -1 else player_id
    
    # Try each registered plugin until we find player stats
    plugin = PluginManager.find_plugin_for_player(formatted_message)

    if not plugin:
        return

    try:
        player_stats_msg = await plugin.get_player_live_stats(formatted_message, update, context)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
        # Multiple players, don't send player not found message
        if player_stats_msg == "":
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player stats: {str(e)}")
    
    await send_player_not_found_message(update, context)

async def season_stats_command_handler(update, context, player_id = -1, start_year=-1, end_year=-1):
    player_name, start_year, end_year = get_player_name_and_years(update.message, player_id, start_year, end_year)
    # Try each registered plugin until we find player stats
    plugin = PluginManager.find_plugin_for_player(player_name)
    try:
        player_stats_msg = await plugin.get_player_season_stats(player_name, start_year, end_year)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player season stats: {str(e)}")
        await send_player_not_found_message(update, context)

async def callback_query_handler(update, context):
    """
    Generic callback query handler that routes to the appropriate plugin.
    Expects callback_data in format: "id=<value>, handler=<handler_name>, plugin=<plugin_name>, year=<year>"
    """
    try:
        callback_data = [s.strip() for s in update.callback_query.data.split(',')]
        
        # Parse callback data
        data_dict = {}
        for item in callback_data:
            if '=' in item:
                key, value = item.split('=', 1)
                data_dict[key.strip()] = value.strip()
        
        # Delete previous followup message
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat.id,
                message_id=update.callback_query.message.message_id
            )
        except Exception as e:
            print(f"Failed to delete message: {e}")
        
        # Get required data
        player_id = data_dict.get('id')
        handler = data_dict.get('handler')
        plugin_name = data_dict.get('plugin')
        year = data_dict.get('year')  # Optional for season stats
        
        if not player_id or not handler:
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat.id,
                text="Error: Missing required callback data"
            )
            return
        
        # Handle predefined functions automatically
        if handler in ["current_stats", "career_stats", "season_stats"]:
            await _handle_predefined_callback(update, context, player_id, handler, year)
            return
        
        # For custom handlers, route to plugin
        if plugin_name:
            plugin = PluginManager.find_plugin_by_name(plugin_name)
            if not plugin:
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat.id,
                    text=f"Error: Plugin '{plugin_name}' not found"
                )
                return
            
            # Call the plugin's custom callback handler
            await plugin.handle_callback_query(update, context, data_dict)
        else:
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat.id,
                text="Error: No plugin specified for custom handler"
            )
        
    except Exception as e:
        logger.error(f"Error handling callback query: {str(e)}")
        await context.bot.send_message(
            chat_id=update.callback_query.message.chat.id,
            text="Sorry, there was an error processing your request"
        )

async def _handle_predefined_callback(update, context, player_id, handler, year):
    if handler == "current_stats":
        await current_stats_command_handler(update.callback_query, context, player_id)
    elif handler == "career_stats":
        await career_stats_command_handler(update.callback_query, context, player_id)
    elif handler == "season_stats":
        await season_stats_command_handler(update.callback_query, context, player_id)


async def career_stats_command_handler(update, context, player_id=-1):
    player_name, _, _ = get_player_name_and_years(update.message, player_id)
    plugin = PluginManager.find_plugin_for_player(player_name)
    try:
        player_stats_msg = await plugin.get_player_career_stats(player_name, update, context)
        if player_stats_msg:
            await context.bot.send_message(chat_id=update.message.chat_id, text=player_stats_msg)
            return
    except Exception as e:
        logger.debug(f"Plugin failed to get player careerstats: {str(e)}")
        await send_player_not_found_message(update, context)


async def set_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("version", "View the current bot version"),
        BotCommand("scores", "Get live or historic scores"),
        BotCommand("stats", "Get current player stats"),
        BotCommand("seasonstats", "Get player season stats"),
        BotCommand("careerstats", "Get player career stats"),
    ]

    plugins = PluginManager.get_all_plugins()

    for plugin in plugins:
        commands.extend(plugin.commands)

    await application.bot.set_my_commands(commands)

async def post_init(application):
    await set_commands(application)


def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # Register core handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    version_handler = CommandHandler('version', version_command_handler)
    application.add_handler(version_handler)

    scores_handler = CommandHandler('scores', scores_command_handler)
    application.add_handler(scores_handler)

    current_stats_handler = CommandHandler('stats', current_stats_command_handler)
    application.add_handler(current_stats_handler)

    season_stats_handler = CommandHandler('seasonstats', season_stats_command_handler)
    application.add_handler(season_stats_handler)

    career_stats_handler = CommandHandler('careerstats', career_stats_command_handler)
    application.add_handler(career_stats_handler)

    # Add callback query handler
    callback_query_handler_instance = CallbackQueryHandler(callback_query_handler)
    application.add_handler(callback_query_handler_instance)
    
    # Register all plugin handlers
    PluginManager.setup_plugin_handlers(application)

    unknown_handler = MessageHandler(telegram.ext.filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    logger.info("Starting bot...")
    application.run_polling() 


if __name__ == '__main__':
    main()