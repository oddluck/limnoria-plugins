###
# Copyright (c) 2024, oddluck
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

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
from supybot.i18n import PluginInternationalization
import re
import google.generativeai as genai

_ = PluginInternationalization("Gemini")


class Gemini(callbacks.Plugin):
    """GoogleAI Gemini Chat Plugin"""

    threaded = True

    def __init__(self, irc):
        self.__parent = super(Gemini, self)
        self.__parent.__init__(irc)
        self.history = {}

    def chat(self, irc, msg, args, text):
        """Chat Call to the Gemini API"""
        channel = msg.channel
        if not irc.isChannel(channel):
            channel = msg.nick
        genai.configure(api_key=self.registryValue("api_key", msg.channel))
        prompt = self.registryValue("prompt", msg.channel).replace("$botnick", irc.nick)
        max_tokens = self.registryValue("max_tokens", msg.channel)
        model = genai.GenerativeModel(
            self.registryValue("model", msg.channel),
            generation_config={"max_output_tokens": max_tokens},
            system_instruction=prompt,
        )
        max_history = self.registryValue("max_history", msg.channel)
        self.history.setdefault(channel, None)
        if not self.history[channel] or max_history < 1:
            self.history[channel] = []
        chat = model.start_chat(history=self.history[channel][-max_history:])
        if self.registryValue("nick_include", msg.channel):
            response = chat.send_message("%s: %s" % (msg.nick, text))
        else:
            response = chat.send_message(text)
        if self.registryValue("nick_strip", msg.channel):
            content = re.sub(r"^%s: " % (irc.nick), "", response.text)
        else:
            content = response.text
        prefix = self.registryValue("nick_prefix", msg.channel)
        for line in content.splitlines():
            if line:
                irc.reply(line, prefixNick=prefix)
        self.history[channel] = chat.history

    chat = wrap(chat, ["text"])


Class = Gemini


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
