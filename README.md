This plugin is in beta. Please report all bugs on GitHub.

# Configuration
## Setting up plugin
1. Download [Supybot][]
2. Download TriviaTime and place it into the plugins folder
3. Load TriviaTime
4. Configure your question file and database location in config.py or with commands
5. Use 'addquestionfile [filename]' command to load questions, the argument is optional

## Setting up PHP
1. Download PHP and PHP-MySQL (for PDO)
2. Configure config.php to point to your TriviaTime database in the plugin/TriviaTime/Storage/db folder

## How to update (beta only)
1. Unload TriviaTime
2. Install the new files
3. Drop all the tables (uncomment all the drops in plugin.py)
4. Load TriviaTime

  [Supybot]: http://sourceforge.net/projects/supybot/
