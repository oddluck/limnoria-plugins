###
# Copyright (c) 2017, Ken Spencer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import supybot.log as log
import supybot.ircmsgs as ircmsgs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring


_ = PluginInternationalization('UndernetX')

@internationalizeDocstring
class UndernetX(callbacks.Plugin):
    """Logins to Undernet's X Service"""
    threaded = True

    def __init__(self, irc):
        global instance
        instance = self
        self.__parent = super(UndernetX, self)
        callbacks.Plugin.__init__(self, irc)
        instance.irc = irc

    def _login(self, irc):
        username = self.registryValue('auth.username')
        password = self.registryValue('auth.password')
        xserv = self.registryValue('auth.xservice')
        irc.sendMsg(ircmsgs.privmsg(xserv, "login {} {}".format(username, password)))

    def doNotice(self, irc, msg):
        if irc.state.supported.get('NETWORK', '') == 'UnderNet':
            if 'X!cservice@undernet.org' in msg.prefix:
                if 'AUTHENTICATION SUCCESSFUL as' in msg.args[1]:
                    log.info("Successfully authed to X.")
                    modex = self.registryValue('modeXonID')
                    if modex:
                        log.info("Setting +x")
                        irc.sendMsg(ircmsgs.IrcMsg("MODE {} +x".format(irc.nick)))

                else:
                    log.info("Received a NOTICE from X. msg: {}".format(msg.args[1]))
                    return
            else:
                if 'AUTHENTICATION SUCCESSFUL as' in msg.args[1]:
                    log.warning("Someone is impersonating X!")
        else:
            log.debug("Notice isn't from UnderNet.. Ignoring")

    def do376(self, irc, msg):
        """Watch for the MOTD and login if we can"""
        if irc.state.supported.get('NETWORK', '') == 'UnderNet':
            if self.registryValue('auth.username') and self.registryValue('auth.password'):
                log.info("Attempting login to XService")
            else:
                log.warning("username and password not set, this plugin will not work")
                return
            self._login(irc)

    # Similar to Services->Identify
    def login(self, irc, msg, args):
        """takes no arguments
        Logins to Undernet's X Service"""
        if irc.state.supported.get('NETWORK', '') == 'UnderNet':
            if self.registryValue('auth.username') and self.registryValue('auth.password'):
                log.info("Attempting login to XService")
            else:
                log.warning("username and password not set, this plugin will not work")
                return
            self._login(irc)
        else:
            log.error("We're not on UnderNet, we can't use this.")
            irc.error("We're not on UnderNet, this is useless.")
    login = wrap(login, ['admin'])

Class = UndernetX

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: