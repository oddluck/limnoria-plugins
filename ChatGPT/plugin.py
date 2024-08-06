###
# Copyright (c) 2023, oddluck
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
import openai


_ = PluginInternationalization("ChatGPT")


class ChatGPT(callbacks.Plugin):
    """Use the OpenAI ChatGPT API"""

    threaded = True

    def __init__(self, irc):
        self.__parent = super(ChatGPT, self)
        self.__parent.__init__(irc)
        self.history = {}

    def chat(self, irc, msg, args, text):
        """Manual Call to the ChatGPT API"""
        channel = msg.channel
        if not irc.isChannel(channel):
            channel = msg.nick
        if self.registryValue("nick_include", msg.channel):
            text = "%s: %s" % (msg.nick, text)
        self.history.setdefault(channel, None)
        max_history = self.registryValue("max_history", msg.channel)
        prompt = self.registryValue("prompt", msg.channel).replace("$botnick", irc.nick)
        if not self.history[channel] or max_history < 1:
            self.history[channel] = []
        openai.api_key = self.registryValue("api_key")
        completion = openai.chat.completions.create(
            model=self.registryValue("model", msg.channel),
            messages=self.history[channel][-max_history:]
            + [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            temperature=self.registryValue("temperature", msg.channel),
            top_p=self.registryValue("top_p", msg.channel),
            max_tokens=self.registryValue("max_tokens", msg.channel),
            presence_penalty=self.registryValue("presence_penalty", msg.channel),
            frequency_penalty=self.registryValue("frequency_penalty", msg.channel),
            user=msg.nick,
        )
        if self.registryValue("nick_strip", msg.channel):
            content = re.sub(
                r"^%s: " % (irc.nick), "", completion.choices[0].message.content
            )
        else:
            content = completion.choices[0].message.content
        prefix = self.registryValue("nick_prefix", msg.channel)
        if self.registryValue("reply_intact", msg.channel):
            for line in content.splitlines():
                if line:
                    irc.reply(line, prefixNick=prefix)
        else:
            response = " ".join(content.splitlines())
            irc.reply(response, prefixNick=prefix)
        self.history[channel].append({"role": "user", "content": text})
        self.history[channel].append({"role": "assistant", "content": content})

    chat = wrap(chat, ["text"])


Class = ChatGPT

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
