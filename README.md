This plugin will be a feature packed trivia script for [Supybot][] in the future. Developers will need to refer to [TriviaTime][] for more information.
This plugin has been started and it almost ready. For developers user only.

# Plans
## Main Priority

* if stop is used during a question, wait until after the question is finished to stop the game.
* New Style design - remove colors and use bold where necessary
* Update permissions - prevent the typical user from accessing admin commands
* when question is skipped start the next question immediately
* add amount of active players in last seven days to .info

## Second Priority
These items are bonus features that will not effect gameplay.
* ping command
* Merge points command

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

