The classic game of IRC Duck Hunt.

Forked from https://github.com/veggiematts/supybot-duckhunt

Requires Python3, Limnoria.

Python 3 and score fixes. Plugin working.

\_o< ~ DuckHunt game for supybot ~ >o_/
=======================================

How to play
-----------
 * Use the "starthunt" command to start a game.
 * The bot will randomly launch ducks. Whenever a duck is launched, the first person to use the "bang" command wins a point. 
 * Using the "bang" command when there is no duck launched costs a point.
 * Using the "bang" command two or more times while reloading costs a point.
 * If a player shoots all the ducks during a hunt, it's a perfect! This player gets extra bonus points.
 * The best scores for a channel are recorded and can be displayed with the "listscores" command.
 * The quickest and longest shoots are also recorded and can be displayed with the "listtimes" command.
 * The "launched" command tells if there is currently a duck to shoot.

How to install
--------------
Just place the DuckHunt plugin in the plugins directory of your supybot installation and load the module.

How to configure
----------------
Several per-channel configuration variables are available (look at the "channel" command to learn more on how to configure per-channel configuration variables):
 * autoRestart: Does a new hunt automatically start when the previous one is over?
 * ducks: Number of ducks during a hunt?
 * minthrottle: The minimum amount of time before a new duck may be launched (in seconds)
 * maxthrottle: The maximum amount of time before a new duck may be launched (in seconds)
 * reloadTime: The time it takes to reload your rifle once you have shot (in seconds)
 * kickMode: If someone shoots when there is no duck, should he be kicked from the channel? (this requires the bot to be op on the channel)
 * autoFriday: Do we need to automatically launch more ducks on friday?
 * missProbability: The probability to miss the duck

Update
------
Get latest version at : https://github.com/veggiematts/supybot-duckhunt
