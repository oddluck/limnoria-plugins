Description
~~~~~~~~~~~
Dicebot plugin contains the commands which simulate rolling of dice.
Though core supybot plugin Games contain 'dice' command, it is very simple and
is not sufficient for advanced uses, such as online playing of tabletop
role-playing games using IRC.
The most basic feature of any dicebot is, of course, rolling of one or several
identical dice and showing the results. That is what core 'dice' command can
do. It takes an expression such as 3d6 and returns a series of numbers -
results of rolling each (of 3) die (6-sided): '2, 4, and 4'. This may be
sufficient for some games, but usually you need more. Here is what this plugin
can do for you.

Features
~~~~~~~~
1. Sum of dice rolled. Expression form is just '2d6', plugin returns the sum
of dice values as one number.
2. Sum of several different dice and some fixed numbers. Expression:
'2d6+3d8-2+10'. After summing up dice results the specified number is added (or
subtracted) to the sum.
3. Separate results of several identical rolls which use previously described
form. This is written as '3#1d20+7' and yields 3 numbers, each meaning the
result of rolling 1d20+7 as described above.
4. Possibility to omit leading 1 as dice count and use just 'd6' or '3#d20'.
5. Two (three?) distinct modes of operation: roll command and autorolling (can
be enabled per-channel and for private messages, see configuration below).
roll command accepts just one expression and shows its result (if the
expression is valid). Autorolling means that bot automatically rolls and
displays all recognized expressions it sees (be it on the channel or in the
query). Autorolling is much more convenient during online play, but may be
confusing during normal talk, so it can be enabled only when it is needed.
6. To distinguish between different rolls, all results are prefixed with
requesting user's nick and requested expression.
7. If you use several expressions in one message, bot will roll all of them and
return all the results in one reply, separated with semicolon.
8. Shadowrun 4ed support, see included Shadowrun.txt; 7th Sea RnK support, see
7th Sea.txt; Dark Heresy/Rogue Trader/Deathwatch support, see DH.txt.
9. Concerning extensibility, you just need to add a regex for your expression
and a function which parses that expression and returns a string which will be
displayed.
10. Also includes basic card deck simulator, see below.

Configuration
~~~~~~~~~~~~~
autoRoll (per-channel): whether to roll all expressions seen on the channel
autoRollInPrivate (global): whether to roll expressions in the queries
Both settings are off by default, so that bot replies only to explicit !roll.

Deck
~~~~
Bot has a 54-card deck which it can shuffle (!shuffle command) and from which
you can draw (!draw or !deal command, with optional number argument if you want
to draw several cards). Drawn card is removed from the deck, but shuffle
restores full deck. If the last card is drawn, the deck is automatically
shuffled before drawing next card.

Thanks
~~~~~~
Ur-DnD roleplaying community (#dnd @ RusNet) for games, talking and fun, and
personally Zuzuzu for describing basic dicebot requirements, which led to
writing the first version of this plugin in August 2007.

