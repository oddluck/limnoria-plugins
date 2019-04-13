###
# Copyright (c) 2015, Michael Daniel Telatynski <postmaster@webdevguru.co.uk>
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

from supybot.commands import *
import supybot.conf as conf
import supybot.utils as utils
import supybot.plugins as plugins
import supybot.callbacks as callbacks

import requests

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('BotLibre')
except ImportError:
    _ = lambda x: x


class BotLibre(callbacks.Plugin):
    """BotLibre API Interface"""
    threaded = True
    public = True
    botNick = False

    def __init__(self, irc):
        self.__parent = super(BotLibre, self)
        self.__parent.__init__(irc)
        self.url = 'https://www.botlibre.com/rest/json/chat'
        self.conversation = {}

    def _queryBot(self, irc, channel, text):
        text = re.sub('fuck', 'screw', text, flags=re.IGNORECASE)
        text = re.sub('cunt', 'pussy', text, flags=re.IGNORECASE)
        text = re.sub('bitch', '', text, flags=re.IGNORECASE)
        text = re.sub('whore', 'slut', text, flags=re.IGNORECASE)
        self.conversation.setdefault(channel, None)
        if self.conversation[channel]:
            payload = {
                'application': self.registryValue('application'),
                'instance': self.registryValue('instance'),
                'message': text,
                'conversation': self.conversation[channel]
            }
        else:
            payload = {
                'application': self.registryValue('application'),
                'instance': self.registryValue('instance'),
                'message': text
            }
        try:
            r = requests.post(self.url, json=payload)
            j = r.json()
            response = j['message']
            self.conversation[channel] = j['conversation']
            if response:
                irc.reply(re.sub('<[^<]+?>', '', j['message']))
        except:
            return
        
    def botlibre(self, irc, msg, args, text):
        """Manual Call to the BotLibre API"""
        channel = msg.args[0]
        if not irc.isChannel(channel):
            channel = msg.nick
        self._queryBot(irc, channel, text)
    botlibre = wrap(botlibre, ['text'])

    def invalidCommand(self, irc, msg, tokens):
        chan = msg.args[0]
        if irc.isChannel(chan) and self.registryValue('invalidCommand', chan):
            self._queryBot(irc, chan, msg.args[1][1:].strip())

Class = BotLibre

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
