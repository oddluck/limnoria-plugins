###
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
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.log as log
import supybot.conf as conf
import requests
import json
import html


class GoogleCloud(callbacks.Plugin):
    def translate(self, irc, msg, args, optlist, text):
        """[--from <source>] [--to <target>] <text>
        Translate text using Google Translate API. Uses automatic language detection
        if source not set. No target uses the plugin default.
        """
        optlist = dict(optlist)
        key = self.registryValue("translate.key")
        if not key:
            irc.reply("Error: No API key has been set.")
            return
        if "from" in optlist:
            source = optlist.get("from")
        else:
            source = self.registryValue("translate.source", msg.channel)
        if "to" in optlist:
            target = optlist.get("to")
        else:
            target = self.registryValue("translate.target", msg.channel)
        url = "https://translation.googleapis.com/language/translate/v2"
        if source != "auto":
            url += "?q={0}&target={1}&source={2}&key={3}".format(
                text, target, source, key
            )
        else:
            url += "?q={0}&target={1}&key={2}".format(text, target, key)
        response = requests.get(url, timeout=10)
        if not response.status_code == 200:
            log.debug(
                "GoogleCloud: Error accessing {0}: {1}".format(
                    url, response.content.decode()
                )
            )
            return
        result = json.loads(response.content)
        if not result.get("data"):
            log.debug("GoogleCloud: Error opening JSON response")
            return
        if result["data"]["translations"][0].get("detectedSourceLanguage"):
            reply = "{0} [{1}~>{2}]".format(
                html.unescape(result["data"]["translations"][0]["translatedText"]),
                result["data"]["translations"][0]["detectedSourceLanguage"],
                target,
            )
        else:
            reply = "{0} [{1}~>{2}]".format(
                html.unescape(result["data"]["translations"][0]["translatedText"]),
                source,
                target,
            )
        irc.reply(reply)

    translate = wrap(translate, [getopts({"from": "text", "to": "text"}), "text"])


Class = GoogleCloud
