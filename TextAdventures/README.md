Play interactive fiction Z-Machine games like the Infocom classic Zork.

Requires limnoria, python 3, pexpect

Uses the dfrotz (dumb frotz) interpreter https://github.com/DavidGriffith/frotz

git clone https://github.com/DavidGriffith/frotz<br>
cd frotz<br>
make dumb<br>
sudo make install_dumb<br>

config plugins.frotz.dfrotzPath (path_to_dfrotz_binary) (default /usr/local/bin/dfrotz)
Looks for games in ./games/ directory

usage:

open <game name> ex. open zork1.z5 - loads game
  
Game will process channel messages as commands while a game is running.
  
z <command> ex. z open mailbox, z look - send command manually

z <no input> - sends a blank line equivalent to [RETURN]/[ENTER] when needed
  
end - ends the game

games - lists contents of ./games/ directory

one game allowed to run per channel/pm. will prompt you to stop running games before allowing a new one to be started.
this limits the number of potential child dfrotz processes and keeps this simpler in terms of routing the right game data
to the right place.

python3 -m pip install pexpect

Games included here are easily found and freely available all over the net, their owners are their respective owners 
and if you believe a game should not be here contact me and I will remove it immediately. 
