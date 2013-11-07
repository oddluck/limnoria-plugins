This plugin has been started and it almost ready. For developers user only.

# TODO
## Main Priority

* New Style design - remove colors and use bold where necessary
* Allow setting of location for website - such as /home/public_html 
* continue streaks when trivia stops

# Configuration
## Setting up plugin
1. download supybot
2. download TriviaTime plugin and put it into your supybot plugin folder
3. enable the plugin through the supybot configuration
4. configure your question file and database location in config.py or by commands
5. use the 'addquestionfile [filename]' command to load questions, the argument is optional

## Setting up php
1. get php, php-mysql (for PDO)
2. configure config.php to point to your TriviaTime database in the plugin/TriviaTime/Storage/db folder

