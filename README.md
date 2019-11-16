# basketball-bot-telegram

Work-in-progress bot for telegram for various NBA stats.

## Building
1) Fork or Clone Repo
2) Define .env file and add your bot's telegram token as `TELEGRAM_TOKEN`
3) Run `bot.py`

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
