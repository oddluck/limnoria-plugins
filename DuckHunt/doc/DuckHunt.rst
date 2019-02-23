Documentation for the DuckHunt plugin for Supybot
=================================================

Purpose
-------
This is a DuckHunt game for supybot

Usage
-----
A DuckHunt game for supybot. Use the "start" command to start a game.     The
bot will randomly launch ducks. Whenever a duck is launched, the first
person to use the "bang" command wins a point. Using the "bang" command
when there is no duck launched costs a point.

Commands
--------
bang
  Shoots the duck!

dayscores
  [<channel>] Shows the score list of the day for <channel>.

dbg
  This is a debug command. If debug mode is not enabled, it won't do anything

fridaymode
  [<status>] Enable/disable friday mode! (there are lots of ducks on friday :))

launched
  Is there a duck right now?

listscores
  [<size>] [<channel>] Shows the <size>-sized score list for <channel> (or for
  the current channel if no channel is given)

listtimes
  [<size>] [<channel>] Shows the <size>-sized time list for <channel> (or for
  the current channel if no channel is given)

mergescores
  [<channel>] <nickto> <nickfrom> nickto gets the points of nickfrom and
  nickfrom is removed from the scorelist

mergetimes
  [<channel>] <nickto> <nickfrom> nickto gets the best time of nickfrom if
  nickfrom time is better than nickto time, and nickfrom is removed from the
  timelist. Also works with worst times.

rmscore
  [<channel>] <nick> Remove <nick>'s score

rmtime
  [<channel>] <nick> Remove <nick>'s best time

score
  <nick> Shows the score for a given nick

start
  Starts the hunt

stop
  Stops the current hunt

total
  Shows the total amount of ducks shot in <channel> (or in the current channel
  if no channel is given)

weekscores
  [<week>] [<nick>] [<channel>] Shows the score list of the week for <channel>.
  If <nick> is provided, it will only show <nick>'s scores.

Configuration
-------------
supybot.plugins.DuckHunt.public
  This config variable defaults to True and is not channel specific.

  Determines whether this plugin is publicly visible.

supybot.plugins.DuckHunt.autoRestart
  This config variable defaults to False and is channel specific.

  Does a new hunt automatically start when the previous one is over?

supybot.plugins.DuckHunt.ducks
  This config variable defaults to 5 and is channel specific.

  Number of ducks during a hunt?

supybot.plugins.DuckHunt.minthrottle
  This config variable defaults to 30 and is channel specific.

  The minimum amount of time before a new duck may be launched (in seconds)

supybot.plugins.DuckHunt.maxthrottle
  This config variable defaults to 300 and is channel specific.

  The maximum amount of time before a new duck may be launched (in seconds)

supybot.plugins.DuckHunt.reloadTime
  This config variable defaults to 5 and is channel specific.

  The time it takes to reload your rifle once you have shot (in seconds)

supybot.plugins.DuckHunt.missProbability
  This config variable defaults to 0.20000000000000001 and is channel specific.

  The probability to miss the duck

supybot.plugins.DuckHunt.kickMode
  This config variable defaults to True and is channel specific.

  If someone shoots when there is no duck, should he be kicked from the
  channel? (this requires the bot to be op on the channel)

supybot.plugins.DuckHunt.autoFriday
  This config variable defaults to True and is channel specific.

  Do we need to automatically launch more ducks on friday?

