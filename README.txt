This is a Supybot plugin implementation of UNO.

==== Usage ====

To use this plugin, you need to change a game setting to allow it.
This requires channel,op capability (or owner).

The command is:
    uno setoption allow_game true
There are other options you can change, view them with this command:
    uno showoptions
To unset/clear an option, use:
    uno setoption foobar unset


==== Rules ====
http://www.wonkavator.com/uno/unorules.html

Note: saying "Uno!" when you are down to one card doesn't work well
in IRC, and isn't required.