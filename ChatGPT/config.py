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

from supybot import conf, registry

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("ChatGPT")
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn

    conf.registerPlugin("ChatGPT", True)


ChatGPT = conf.registerPlugin("ChatGPT")
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(ChatGPT, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
conf.registerGlobalValue(
    ChatGPT,
    "api_key",
    registry.String(
        "",
        _("""Your OpenAI API Key (required)"""),
        private=True,
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "prompt",
    registry.String(
        "You are $botnick the IRC bot. Be brief, helpful",
        _(
            """
            The prompt defining your bot's personality.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "model",
    registry.String(
        "gpt-3.5-turbo",
        _(
            """
            OpenAI endpoint model, default: "gpt-3.5-turbo"
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "reply_intact",
    registry.Boolean(
        False,
        _(
            """
            Get spammy and enable line per line reply...
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "nick_prefix",
    registry.Boolean(
        False,
        _(
            """
            Prefix nick on replies true/false...
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "temperature",
    registry.Float(
        1,
        _(
            """
            What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. We generally recommend altering this or top_p but not both.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "top_p",
    registry.Float(
        1,
        _(
            """
            An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "max_tokens",
    registry.Integer(
        200,
        _(
            """
            The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "presence_penalty",
    registry.Float(
        0,
        _(
            """
            Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "frequency_penalty",
    registry.Float(
        0,
        _(
            """
            Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "max_history",
    registry.Integer(
        10,
        _(
            """
            The maximum number of messages to keep in conversation history. 0 to disable.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "nick_include",
    registry.Boolean(
        True,
        _(
            """
            Include user nicks in history/queries. Disabled will treat conversation as if from a single user.
            """
        ),
    ),
)

conf.registerChannelValue(
    ChatGPT,
    "nick_strip",
    registry.Boolean(
        True,
        _(
            """
            Prevent the bot from starting replies with its own nick.
            """
        ),
    ),
)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
