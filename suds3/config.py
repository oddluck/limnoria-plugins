# -*- coding: utf-8 -*-
###
# This file is part of Soap.
#
# Soap is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# Soap is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should have received
# a copy of the GNU General Public License along with Soap. If not, see
# <http://www.gnu.org/licenses/>.
###

import supybot.conf as conf
import supybot.registry as registry
import re

class SemicolonSeparatedListOfStrings(registry.SeparatedListOf):
    Value = registry.String
    def splitter(self, s):
        return re.split(r'\s*;\s*', s)
    joiner = '; '.join


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('suds', True)


Suds = conf.registerPlugin('suds')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Suds, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))


# General configuration settings
conf.registerGlobalValue(Suds, 'channels',
    registry.SpaceSeparatedListOfStrings('', """ The channels you wish to use
        for OpenTTD communication """))
conf.registerGlobalValue(Suds, 'logdir',
    registry.String('None', """ Logging directory. This is where logfiles are
    saved to. It will rotate logs when a new game starts, and back up the old
    log. A maximum of 2 logs are backed up. To disable logging, set this to an
    invalid path or 'None' """))
conf.registerGlobalValue(Suds, 'logHistory',
    registry.Integer(2, """ Amount of logfiles to keep. This does not include
    the current logfile. A value of 2 will keep the current logfile, and the 2
    preceding ones as .log.1 and .log.2."""))

# OpenTTD server configuration
conf.registerChannelValue(Suds, 'serverID',
    registry.String('default', """ Optional hort name for the server, used for
    issuing commands via query. no spaces allowed. Should be unique to each
    server when managing multiple game-servers """))
conf.registerChannelValue(Suds, 'host',
    registry.String('127.0.0.1', """ The hostname or IP-adress of the OpenTTD
    server you wish the bot to connect to """))
conf.registerChannelValue(Suds, 'port',
    registry.Integer(3977, """ The port of the server's adminport """))
conf.registerChannelValue(Suds, 'password',
    registry.String('password', """ The password as set in openttd.cfg """))
conf.registerChannelValue(Suds, 'publicAddress',
    registry.String('openttd.example.org', """ Address players use to connect
    to the server """))

# File-related settings
conf.registerChannelValue(Suds, 'ofslocation',
    registry.String('/home/openttdserver/', """ Location of OpenTTD File Scripts
    (OFS). This can either be a local directory (/path/to/ofs/{OFS}) or in the form of
    'ssh -p23 user@host:/path/to/ofs/{OFS}'. In the latter case, make sure to set up
    the bot-user to have password-less login to the machine with ofs/openttd. Put
    {OFS} wher the actual ofs-command should go. """))

# Miscellanious server-specific settings
conf.registerChannelValue(Suds, 'autoConnect',
    registry.Boolean(False, """ Setting this to True will cause the bot to
    attempt to connect to OpenTTD automatically """))
conf.registerChannelValue(Suds, 'allowOps',
    registry.Boolean(True, """ Setting this to True will allow any op as well
    as trusted user in the channel to execute soap commands . Setting this to
    False only allows trusted users to do so """ ))
conf.registerChannelValue(Suds, 'minPlayers',
    registry.Integer(0, """ The defalt minimum number of players for the server
    to unpause itself. 0 means game never pauses unless manually paused """))
conf.registerChannelValue(Suds, 'checkClientVPN',
    registry.Boolean(False, """ True means players will have their IP checked for
     known VPN or other such ban evasion techniques, and kicked if they are using them."""))
conf.registerGlobalValue(Suds, 'checkClientVPNWhitelist',
    SemicolonSeparatedListOfStrings('', """If checkClientVPN is enabled, you can disable checking certain IPs here. Semicolon delimited."""))
conf.registerGlobalValue(Suds, 'nameBlacklist',
    SemicolonSeparatedListOfStrings('', """List of player names to autokick. Semicolon delimited."""))
conf.registerChannelValue(Suds, 'playAsPlayer',
    registry.Boolean(True, """ True means players can play with Player as their
    name. False will get them moved to spectators any time they try to join a
    company, and eventually kicked """))
conf.registerChannelValue(Suds, 'playerKickCount',
    registry.Integer(3, """ The number of times a player can attempt to join
    a company before they are automatically kicked. Setting to 0 will kick
    on the first infraction. """))
conf.registerChannelValue(Suds, 'passwordInterval',
    registry.Integer(0, """ Interval in seconds between soap changing the
    password clients use to join the server. Picks a random line from the
    included passwords.txt. If you don't want your server to have random
    passwords, leave this set at 0. People can use the password command to find
    the current password """))
conf.registerChannelValue(Suds, 'welcomeMessage',
    SemicolonSeparatedListOfStrings('', """ Welcome message to be sent to
    players when they connect. Separate lines with semicolons. to insert (for
    instance) the client name, put {clientname} in the string, including the {}.
    Valid replacements are: {clientname} {servername} and {serverversion}. Set
    this to 'None' to disable on-join welcome messages """))
conf.registerChannelValue(Suds, 'defaultSettings',
    registry.String('', """ This should be an absolute path pointing to a textfile
    containing one command per line. This file is read by the setdef command, and
    all commands are executed """))

# various URL's
conf.registerChannelValue(Suds, 'downloadUrl',
    registry.String('None', """ Custom download url. Use only if using a custom version
    that cannot be obtained from openttd.org. Soap will automatically generate url's
    for openttd stable and nightly versions."""))
conf.registerChannelValue(Suds, 'rulesUrl',
    registry.String('None', """ Url where the rules for the server can be found.
    Set to 'None' to disable the ingame and irc !rules commands. """))
conf.registerChannelValue(Suds, 'saveUrl',
    registry.String('None', """ Url where savegames will be available after
    using the transfer command. enter the full url, including the filename. Use
    {ID}  where the game number goes"""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
