Play interactive fiction Z-Machine games like the Infocom classic Zork.

Requires limnoria, python 3, pexpect

Uses the dfrotz (dumb frotz) interpreter https://github.com/DavidGriffith/frotz

Looks for games in ./games/ directory
and for the binary in ./frotz/dfrotz

usage:
frotz load <game name> ex. frotz load zork1.z5 - loads game
z <command> ex. z open mailbox, z look - send command
z <no input> - sends a blank line equivalent to [RETURN]/[ENTER] when needed
frotz stop - ends the game
frotz games - lists contents of ./games/ directory

one game allowed to run per channel/pm. will prompt you to stop running games before allowing a new one to be started.
this limits the number of potential child dfrotz processes and keeps this simpler in terms of routing the right game data
to the right place.

game text reformatted to eliminate line/by line output and for easier reading on various screen sizes.

Some games and a frotz binary included, may need to build your own depending on your system.
https://github.com/DavidGriffith/frotz/blob/master/DUMB

python3 -m pip install pexpect

Games included here are easily found and freely available all over the net, their owners are their respective owners 
and if you believe a game should not be here contact me and I will remove it immediately. 
