# Sports Bot Telegram Plugin Interface

This package provides the interface for creating plugins for the sports-bot-telegram bot.

## Installation

```bash
pip install sports-bot-telegram-plugin
```

## Creating a Plugin

1. Create a new Python package for your plugin
2. Install this package as a dependency:
```toml
[tool.poetry.dependencies]
sports-bot-telegram-plugin = "^0.1.0"
```

3. Create your plugin class:
```python
from datetime import datetime
from typing import Dict, List, Optional, Type
from sports_bot_telegram_plugin import SportsBotPlugin

class MyPlugin(SportsBotPlugin):
    # Required class variables - must be defined
    name = "MyPlugin"  # Plugin name (e.g., "NBA", "NFL")
    description = "Description of what your plugin does"
    version = "1.0.0"  # Plugin version

    def get_team_scores(self, team: str, game_date: Optional[datetime] = None) -> List[Dict]:
        # Implementation
        pass
        
    def get_player_stats(self, player_name: str) -> Dict:
        # Implementation
        pass
        
    def is_team_supported(self, team: str) -> bool:
        # Implementation
        pass

def register_plugin() -> Type[SportsBotPlugin]:
    return MyPlugin
```

4. Register your plugin in your package's `pyproject.toml`:
```toml
[tool.poetry.plugins."sports_bot_telegram_plugins"]
my_plugin = "my_package.plugin:register_plugin"
```

The plugin will be automatically discovered and registered when the bot starts.

## Adding Custom Commands

Your plugin can add custom Telegram commands:

```python
from telegram.ext import CommandHandler
from sports_bot_telegram_plugin import SportsBotPlugin

class MyPlugin(SportsBotPlugin):
    def get_handlers(self):
        return [
            CommandHandler('my_command', self.my_command_handler)
        ]
        
    async def my_command_handler(self, update, context):
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Hello from my plugin!"
        )
```

## Plugin Interface

### SportsBotPlugin

Base class for all plugins. Requires implementing:

Required class variables:
- `name: str` - Plugin name (e.g., "NBA", "NFL")
- `description: str` - Description of what the plugin does
- `version: str` - Plugin version

Required methods:
- `get_live_scores(team: str, game_date: Optional[datetime] = None) -> MatchScores`
- `get_player_live_stats(player_name: str) -> Dict`
- `get_player_career_stats(player_name: str) -> str`
- `get_player_season_stats(player_name: str, start_year: Optional[str] = None, end_year: Optional[str] = None) -> str`
- `is_team_supported(team: str) -> bool`
- `is_player_supported(player_name: str) -> bool`

Optional methods:
- `get_handlers() -> Sequence[BaseHandler]`
- `get_plugin_name() -> str`

### PluginRegistry

Manages plugin registration and discovery:

- Auto-discovers plugins via entry points
- `get_sport_plugin(team: str) -> Optional[SportsBotPlugin]`
- `get_all_plugins() -> List[SportsBotPlugin]`
- `register_handlers(application: Application)`

## Plugin Discovery

Plugins are discovered automatically using Python's entry points system. To make your plugin discoverable:

1. Create a registration function that returns your plugin class:
```python
def register_plugin() -> Type[SportsBotPlugin]:
    return MyPlugin
```

2. Add an entry point in your pyproject.toml:
```toml
[tool.poetry.plugins."sports_bot_telegram_plugins"]
my_plugin = "my_package.plugin:register_plugin"
```

The bot will automatically discover and load your plugin when it starts. 