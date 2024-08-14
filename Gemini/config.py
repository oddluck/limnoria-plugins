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

from supybot import conf, registry

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("Gemini")
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

    conf.registerPlugin("Gemini", True)


Gemini = conf.registerPlugin("Gemini")
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Gemini, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))

conf.registerChannelValue(
    Gemini,
    "enabled",
    registry.Boolean(
        True,
        _("""Set False to disable the plugin, True to enable."""),
    ),
)

conf.registerChannelValue(
    Gemini,
    "api_key",
    registry.String(
        "",
        _("""Your GoogleAI API Key (required)"""),
        private=True,
    ),
)

conf.registerChannelValue(
    Gemini,
    "model",
    registry.String(
        "gemini-1.5-flash-latest",
        _(
            """
            GoogleAI endpoint model, default: "gemini-1.5-flash-latest"
            """
        ),
    ),
)

conf.registerChannelValue(
    Gemini,
    "prompt",
    registry.String(
        "You are $botnick the IRC bot. Be brief, helpful. Keep each line of reply 400 characters or less. Do not prefix replies with your name.",
        _(
            """
            The prompt defining your bot's personality.
            """
        ),
    ),
)

conf.registerChannelValue(
    Gemini,
    "max_tokens",
    registry.Integer(
        200,
        _(
            """
            The maximum number of tokens to generate in the response
            """
        ),
    ),
)

conf.registerChannelValue(
    Gemini,
    "max_history",
    registry.Integer(
        50,
        _(
            """
            The maximum number of messages to keep in conversation history. 0 to disable.
            """
        ),
    ),
)

conf.registerChannelValue(
    Gemini,
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
    Gemini,
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
    Gemini,
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
