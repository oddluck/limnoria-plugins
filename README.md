This plugin will be a feature packed trivia script for [Supybot][] in the future. Developers will need to refer to [TriviaTime][] for more information.
This plugin has been started but is not finished. For developers use only. Not ready for use.

# Plans
## Main Priority

* require minimum amount of points for autovoice
* allow shuffling of questions
* move databases to inside the TriviaTime plugin folder
* when reaching the end of questions, restart the question numbers per [Concept][] page
* extra points for streaks
* We plan on keeping track of players’ scores by their usernames. Should they want to change usernames and keep their scores, they will need to register to the bot. Supybots are already capable of keeping track of users across nicknames and hosts (per owner’s configuration)
* Store question in an SQL file. Create a system of assigning number to the question. That question number will only be used for reporting and when the question is displayed by the bot. If the question is reported, it will be assigned a new number for reporting. When edited, it will use the new report number.
* create live PHP website showing scores and to track reports
* Scores are tracked by nicknames. If a user is registered, it is then tracked by their supybot account

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

