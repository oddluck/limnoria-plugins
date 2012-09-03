\_o< ~ DuckHunt game for supybot ~ >o_/
=======================================

How to play
-----------
 * Use the "start" command to start a game.
 * The bot will randomly launch ducks. Whenever a duck is launched, the first person to use the "bang" command wins a point. 
 * Using the "bang" command when there is no duck launched costs a point.
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
 * frequency: Determines how often a duck will be launched. 0 means that no duck will ever be launched. 1 means that ducks will be launched one after another (somewhere between minthrottle and maxthrottle, of course).
 * minthrottle: The minimum amount of time before a new duck may be launched (in seconds)
 * maxthrottle: The maximum amount of time before a new duck may be launched (in seconds)
