###
# Copyright (c) 2019 oddluck
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
from telnetlib import Telnet
import re

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('MUD')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class MUD(callbacks.Plugin):
    """
    Play Infocom (Interactive Fiction, Z_machine) Games.
    """
    threaded = True

    def __init__(self, irc):
        self.__parent = super(MUD, self)
        self.__parent.__init__(irc)
        self.tn = {}
        self.ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    def join(self, irc, msg, args):
        """
        Join the MUD
        """
        channel = msg.args[0]
        nick = msg.nick
        self.tn[nick] = Telnet(self.registryValue('server'), self.registryValue('port'))
        response = self.output(self.tn[nick])
        for line in response:
            if line.strip():
                irc.reply(line, prefixNick=False)
    join = wrap(join)

    def m(self, irc, msg, args, input):
        """[<input>]
        Send user input or blank line (ENTER/RETURN) to the game.
        """
        channel = msg.args[0]
        nick = msg.nick
        if input:
            command = input.strip()
        else:
            command = None
        if self.tn[nick]:
            if command:
                self.tn[nick].write(command.encode() + b"\r\n")
            else:
                self.tn[nick].write(b"\n")
            response = self.output(self.tn[nick])
            for line in response:
                 if line.strip():
                     irc.reply(line, prefixNick=False)
        else:
            irc.reply("Nick not connected?")
    m = wrap(m, [additional('text')])

    def stop(self, irc, msg, args):
        """
        Stop game.
        """
        channel = msg.args[0]
        nick = msg.nick
        try:
            if self.tn[nick]:
                irc.reply("Closing connection.")
                self.tn[nick].close()
                del self.tn[nick]
            else:
                irc.reply("No connection opened.")
        except:
            irc.reply("No connection opened.")
    stop = wrap(stop)

    def output(self, output):
        response = []
        response = output.read_until(b">", timeout=1)
        clean = []
        for line in response.splitlines():
            clean.append(self.ansi_escape.sub('', line.decode()))
        return clean

Class = MUD

