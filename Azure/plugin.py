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
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.conf as conf
import supybot.log as log
from supybot.commands import *
from string import Template
import json
import requests


class Azure(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(Azure, self)
        self.__parent.__init__(irc)
        r = requests.get(
            "https://api.cognitive.microsofttranslator.com/languages?api-version=3.0&scope=translation",
            timeout=10,
        )
        self.languages = json.loads(r.content.decode())
        self.languages = self.languages["translation"]

    def translate(self, irc, msg, args, optlist, text):
        """[--from <source>] [--to <target>] <text>
        Translate text using Microsoft Azure. Uses automatic language detection if source not
        set. No target uses the plugin default.
        https://docs.microsoft.com/en-us/azure/cognitive-services/translator/language-support
        """
        optlist = dict(optlist)
        if "from" in optlist:
            source = optlist.get("from")
        else:
            source = self.registryValue("translate.source", msg.channel)
        if "to" in optlist:
            target = optlist.get("to")
        else:
            target = self.registryValue("translate.target", msg.channel)

        url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&"
        if source != "auto":
            if not self.languages.get(source):
                for lang in self.languages:
                    if (
                        source.lower() in self.languages[lang]["name"].lower()
                        or source.lower() in self.languages[lang]["nativeName"].lower()
                    ):
                        source = lang
                        break
            if not self.languages.get(target):
                for lang in self.languages:
                    if (
                        target.lower() in self.languages[lang]["name"].lower()
                        or target.lower() in self.languages[lang]["nativeName"].lower()
                    ):
                        target = lang
                        break
            if self.languages.get(source) and self.languages.get(target):
                url += "to={0}&from={1}".format(target, source)
            else:
                irc.reply("Invalid language selection.")
                return
        else:
            if not self.languages.get(target):
                for lang in self.languages:
                    if (
                        target.lower() in self.languages[lang]["name"].lower()
                        or target.lower() in self.languages[lang]["nativeName"].lower()
                    ):
                        target = lang
                        break
            if self.languages.get(target):
                url += "to={0}".format(target)
            else:
                irc.reply("Invalid language selection.")
                return
        key = self.registryValue("translate.key")
        headers = {"Ocp-Apim-Subscription-Key": key, "Content-type": "application/json"}
        body = [{"text": text}]
        response = requests.post(url, headers=headers, json=body)
        if not response.status_code == 200:
            log.debug(
                "Azure: Error accessing {0}: {1}".format(url, response.content.decode())
            )
            return
        result = json.loads(response.content.decode())
        if result[0].get("translations"):
            template = Template(self.registryValue("translate.template", msg.channel))
            results = {
                "text": result[0]["translations"][0]["text"],
                "targetName": self.languages[target]["name"],
                "targetNativeName": self.languages[target]["nativeName"],
                "targetISO": target,
            }
            if result[0].get("detectedLanguage"):
                results["sourceName"] = self.languages[
                    result[0]["detectedLanguage"]["language"]
                ]["name"]
                results["sourceNativeName"] = self.languages[
                    result[0]["detectedLanguage"]["language"]
                ]["nativeName"]
            else:
                results["sourceName"] = self.languages[source]["name"]
                results["sourceNativeName"] = self.languages[source]["nativeName"]
            irc.reply(template.safe_substitute(results))

    translate = wrap(translate, [getopts({"from": "text", "to": "text"}), "text"])


Class = Azure
