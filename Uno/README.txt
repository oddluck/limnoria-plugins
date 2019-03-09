Forked from https://github.com/SpiderDave/spidey-supybot-plugins/tree/master/Plugins/Uno

This is a Limnoria plugin implementation of UNO.

made Python3 compatible, fixed minor bugs
add colors and reply with notices.

uno setoption use_colors False (disable colors)
uno setoption use_notice False (disable notices)

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
