This is a Supybot plugin implementation of psychological number games described in Metamagical Themas by Douglas Hofstadter.

==== Usage ====

To use this plugin, you need to change a game setting to allow it.  This requires channel,op capability (or owner).
The command is:
    ucsetoption allow_game true
There are other options you can change, view them with this command:
    ucshowoptions
To unset/clear an option, use:
    ucsetoption foobar unset


==== Rules for the games ====

-- Undercut --
Two players take turns choosing a number from 1 to 5, secretly.
The numbers are revealed and players get points equal to the number they chose, except as noted below:
If one of the player's numbers is exactly one less than the other player's number, it's an "Undercut", and the player with the lower number gets points equal to his number plus his opponents (the opponent gets no points).
The game is played until one or more players has 40 or more points.
If at the end of the game, both players have equal points, it's a tie.
If at the end of the game, both players have 40 or more points, the player with the most points wins.

-- Flaunt --
The rules are the same as Undercut, with added rules for repetition.
If a player plays the same number multiple times in a row, the point value is multiplied by the number of times played.  In the case of an undercut, the player with the lower number gets the points for his number as well as his opponents, including any bonuses for repetition.

-- Flaunt2 (SuperFlaunt) --
The rules are the same as Flaunt, except numbers are raised to a power equal to the number of times played.  For example, if a player plays the number 3 twice, it would be worth 9 the second time played.  If played a third time, it would be worth 27 points.
Given the potential for large point values, the game is played to 200 points.

-- Flaunt3 --
The rules are the same as Flaunt, except a point is added for each time a number is repeated.  For example, if a player plays the number 3 twice, it would be worth 4 the second time played.  If played a third time, it would be worth 5 points.
