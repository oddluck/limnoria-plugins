###
# Copyright (c) 2015, butterscotchstallion
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
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

import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import random
import datetime
import os
import requests
import json

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("Cayenne")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Cayenne(callbacks.Plugin):
    """Displays cat facts or cat gifs based on probability"""
    threaded = True
    last_message_timestamp = False
    cat_facts = []

    def __init__(self, irc):
        self.__parent = super(Cayenne, self)
        self.__parent.__init__(irc)

    def get_fact(self):
        """
        Get a random cat fact
        """
        data = requests.get("https://catfact.ninja/fact")
        data = json.loads(data.content)
        return data['fact']

    def message_contains_trigger_word(self, message):
        """
        Check prefined list of trigger words and return
        which one was found, if any
        """
        words = self.registryValue("triggerWords")
        if words:
            words = [word.strip() for word in words]
            if words:
                for word in words:
                    if word and word in message:
                        return word
            else:
                self.log.error("Cayenne: no trigger words set apparently")
        return False

    def get_link(self):
        """
        Query cat URL to get a random link
        """
        try:
            link_url = self.registryValue("linkURL")
            response = utils.web.getUrl(link_url).decode("utf8")
            # Expecting a link
            if "http" in response:
                return response
            else:
                self.log.error("Received unexpected response from http://edgecats.net/random")
        except:
            self.log.exception("Error fetching URL")

    def doPrivmsg(self, irc, msg):
        """
        Checks each channel message to see if it contains a trigger word
        """
        channel = msg.args[0]
        is_channel = irc.isChannel(channel)
        is_ctcp = ircmsgs.isCtcp(msg)
        message = msg.args[1]
        bot_nick = irc.nick
        # Check origin nick to make sure the trigger
        # didn"t come from the bot.
        origin_nick = msg.nick
        is_message_from_self = origin_nick.lower() == bot_nick.lower()
        # Only react to messages/actions in a channel and to messages that aren't from
        # the bot itself.
        if is_channel and not is_ctcp and not is_message_from_self and self.registryValue('enable', channel):
            if type(message) is str and len(message):
                fact_chance = int(self.registryValue("factChance"))
                link_chance = int(self.registryValue("linkChance"))
                throttle_seconds = int(self.registryValue("throttleInSeconds"))
                triggered = self.message_contains_trigger_word(message)
                now = datetime.datetime.now()
                seconds = 0
                if self.last_message_timestamp:
                    seconds = (now - self.last_message_timestamp).total_seconds()
                    throttled = seconds < throttle_seconds
                else:
                    throttled = False
                if triggered is not False:
                    self.log.debug("Cayenne triggered because message contained %s" % (triggered))
                    fact_rand = random.randrange(0, 100) <= fact_chance
                    link_rand = random.randrange(0, 100) <= link_chance
                    if fact_rand or link_rand:
                        if throttled:
                            self.log.info("Cayenne throttled. Not meowing: it has been %s seconds" % (round(seconds, 1)))
                        else:
                            self.last_message_timestamp = now
                            if fact_rand:
                                output = self.get_fact()
                            if link_rand:
                                output = self.get_link()
                            if output:
                                irc.sendMsg(ircmsgs.privmsg(channel, output))
                            else:
                                self.log.error("Cayenne: error retrieving output")

Class = Cayenne
