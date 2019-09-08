# Suds from /r/openttd
### A Supybot Plugin for communicating with OpenTTD servers via the AdminPort interface
____

This plugin is released under the GPL, a copy of which has been included in COPYING.txt
____

#### Prerequisites
 * working OpenTTD server (optionally OFS installed and configured)
 * Supybot set up in a channel
 * libottdadmin2 by Xaroth installed

 Supybot comes with its own installation instructions. Those and its user manual
 can be found here: http://sourceforge.net/projects/supybot/

 OFS (Openttd File Scripts) can be obtained here: http://dev.openttdcoop.org/projects/ofs
 It simply needs to be copied to a directory on the same user@host as that
 OpenTTD server, and configured. See the included readme.txt for details. If the
 server is located on a different user@host from the bot, you will need to give
 the user running the bot password-less ssh access to the user@host. This allows
 the bot to eg download a savegame to the server.
 
 ###### Installing libottdadmin2:
 First go to https://github.com/Xaroth/libottdadmin2 and either download the zip
 or git clone. Now there are 2 ways you can install this lib:

 The first one is the easiest one, run `python2 setup.py install` from the
 libottdadmin2 dir. This will install the lib systemwide and make it available
 to any other python programs that may need it. You may need sudo access
 depending on the system setup though.

 The other way is to copy the libottdadmin2 dir into the Soap plugin directory.
 Copied right client.py should be found at this path:
 `<PathToPlugins>/Soap/libottdadmin2/client.py`
 This will give the same functionality, but only for the Soap plugin. On the
 upside, no sudo access required.
 
____

#### Installation

 To install Soap, simply copy the Soap directory into the bots plugin directory,
 and load the plugin once the bot is running.
#### Configuration

 Configuration is handled via supybot's config command. First thing you want to
 configure is the default settings. Soap can handle multiple game-servers, but
 is bound to 1 server per irc-channel.

 Correct format for config would be `config plugins.Soap.<setting> <value>` - for example, `config plugins.Soap.host 127.0.0.1`

 This will set the default for any new server to 127.0.0.1

 To change a setting for one server only, you want to specify the channel: `config channel [#yourchan] plugins.Soap.<setting> <value>`

 #yourchannel is optional when used in the channel (it will use the current
 channel), but required when used in queries. You'll want to use the latter method
 for setting the password. Example: `config channel #mychannel supybot.plugins.Soap.host 127.0.0.1` can be used anywhere the  bot is, whilst `config channel plugins.Soap.host 127.0.0.1` will change the host for channel the command was issued in.

 Finally, you want to activate the channels by configuring the list of
 channels. This is a global value, so theres only one variation: `config plugins.Soap.channels #mychannel #myotherchannel ...`, which will enable below commands for servers tied to those channels. Changing this
 setting will require reloading the plugin so that it can set up all the connections correctly.

 If you didn't specify any settings for a channel, it will pick the default setting instead.
 This also means, that if you want one setting to apply to all the servers (eg you run
 all on a non-standard adminport), simply change the option as if it were a global
 setting.

 For a description of the individual variables, see config.py.
 
 ## Command List

Op/Trusted-only commands:
* `apconnect`     - connects to the openttd server
* `apdisconnect`   - disconnects from same
* `pause`          - manually pauses the game
* `unpause`        - manually unpauses the game (sets min_active_clients to 0)
* `auto`           - turns on autopause, and re-sets min_active_clients to theconfigured amount
* `rcon`           - sends an rcon command to the server
* `players`        - lists the clients connected to the server
* `content`        - updates the downloaded content from bananas
* `contentupdate`  - performs 'content update'. use this before using the 'content' command
* `rescan`         - rescans the content_download directory for new files. (May cause users to get disconnected)
* `save`           - saves the game to game.sav
* `transfer`       - transfers savegame to a web-accessible directory (usage: !transfer number savegame)

Commands requiring op/trusted and OFS installed
* `getsave`        - download savegame from url
* `start`          - starts OpenTTD dedicated server
* `update`         - updates the OpenTTD server and (re)starts it

Publicly available commands
* `playercount`    - shows how many people are playing
* `companies`      - lists companies
* `date`           - returns the ingame date
* `ding`           - should be ping, but that command was taken. Dings the server
* `help`           - links to http://wiki.openttdcoop.org/Soap
* `info`           - shows some basic info about the server
* `ip`             - replies with the address needed to join the server as a player
* `password`       - shows the current password needed to join the server
* `revision`       - shows current revision of the OpenTTD server
* `vehicles`       - totals each vehicle type in the game

 These commands can also be called with channel or serverID as parameter. This can
 be handy when you want to command a server from a different channel or from
 private message.

 There are also 3 ingame commands:
* `!admin`             - sends a message to irc requesting admins look at the server
* `!nick <newnick>`    - will change the ingame nick of the caller
* `!rules`             - replies with an url pointing to the rules for playing


### Credit where credit is due
* Taede Werkhoven: For writing SOAP, which this plugin is derived from
* Xaroth: For writing libottdadmin2
* Dihedral: generated passwords.txt from OpenTTD source