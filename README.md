This plugin will be a feature packed trivia script for [Supybot][] in the future. Developers will need to refer to [TriviaTime][] for more information.
This plugin has been started but is not finished. For developers use only. Not ready for use.

# Plans
## Main Priority

* Average answer time (web only)
* Average answer score (web only)
* Show stats for reports, fixes, and verified edits for each user (web only)
* Allow for deletion of questions

## Second Priority
These items can wait until the game is almost ready for public testing.
* New Style design
* fix permissions for commands
* if stop is used during a question, wait until after the question is finished to stop the game.
* ping command

and much more, based off of BogusTrivia and Trivia (supybot plugin)

  [TriviaTime]: http://trivialand.org/triviatime/
  [Supybot]: http://sourceforge.net/projects/supybot/
  [Concept]: http://trivialand.org/triviatime/concept/

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

