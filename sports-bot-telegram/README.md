# basketball-bot-telegram

Work-in-progress bot for telegram for various NBA stats.

## Building
1) Fork or Clone Repo
2) Define .env file and add your bot's telegram token as `TELEGRAM_TOKEN`
3) Run `python -m bot.main`

## Commands:

### `/seasonstats {Player Name} {Season}`
+ Returns the stats of a given player in a given season in PTS/REB/AST format

Examples of valid syntax
+ `/seasonstats LeBron James 2011-2012`
+ `/seasonstats LeBron James 2012`

### `/careerstats {Player Name}`  
+ Returns the stats of a given player in PTS/REB/AST format  

Examples of valid syntax
+ `/careerstats LeBron James`

### `/currentstats {Player Name}`  
+ Returns the current stats of a plyaer if they are currently playing; otherwise, returns the stats of the player's most recent game  

Examples of valid syntax
+ `/currentstats LeBron James`

## Plugin Development

The bot supports a plugin system that allows developers to add support for different sports and teams. Here's how to create your own plugin:

### Plugin Structure

1. Create a new Python package with the following structure:
```
your_plugin_name/
├── setup.py
├── your_plugin_name/
│   ├── __init__.py
│   └── plugin.py
```

2. In your `setup.py`, define the entry point:
```python
from setuptools import setup

setup(
    name="your_plugin_name",
    version="0.1.0",
    packages=["your_plugin_name"],
    install_requires=[
        "sports-bot-telegram-plugin",  # The base plugin interface
    ],
    entry_points={
        "sports_bot_telegram_plugins": [
            "your_plugin_name = your_plugin_name.plugin:register_plugin"
        ]
    }
)
```

3. Create your plugin class in `plugin.py`:
```python
from sports_bot_telegram_plugin import SportsBotPlugin
from telegram.ext import CommandHandler

class YourPlugin(SportsBotPlugin):
    def __init__(self):
        super().__init__()
        self.supported_teams = ["Team1", "Team2"]  # List of teams your plugin supports

    def get_plugin_name(self) -> str:
        return "Your Plugin Name"

    def is_team_supported(self, team: str) -> bool:
        return team in self.supported_teams

    def get_handlers(self):
        return [
            CommandHandler("yourcommand", self.your_command_handler)
        ]

    async def your_command_handler(self, update, context):
        # Implement your command logic here
        pass

def register_plugin():
    return YourPlugin
```

### Plugin Interface

Your plugin must implement the following methods from `SportsBotPlugin`:

- `get_plugin_name()`: Returns the name of your plugin
- `is_team_supported(team)`: Returns whether your plugin supports a given team
- `get_handlers()`: Returns a list of Telegram command handlers

### Installing Your Plugin

1. Install your plugin in development mode:
```bash
pip install -e /path/to/your_plugin
```

2. The bot will automatically discover and load your plugin on startup.

### Best Practices

1. Handle errors gracefully and provide meaningful error messages
2. Use async/await for all Telegram interactions
3. Implement proper logging using the Python logging module
4. Add comprehensive documentation for your plugin's commands
5. Include unit tests for your plugin's functionality

### Example Plugin

Check out the example plugins in the `plugins` directory for reference implementations.

For more details about the plugin interface, see the `sports_bot_telegram_plugin` package documentation.
