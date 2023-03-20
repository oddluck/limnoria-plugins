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
import openai


_ = PluginInternationalization("ChatGPT")


class ChatGPT(callbacks.Plugin):
    """Use the OpenAI ChatGPT API"""

    threaded = True

    def chat(self, irc, msg, args, text):
        """Manual Call to the ChatGPT API"""
        openai.api_key = self.registryValue("api_key")
        prompt = self.registryValue("prompt", msg.channel)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
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
        response = " ".join(completion.choices[0].message.content.splitlines())
        irc.reply(response)

    chat = wrap(chat, ["text"])


Class = ChatGPT


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
