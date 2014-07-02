###
# Copyright (c) 2014, Wekeden
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

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cobe')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Cobe', True)


Cobe = conf.registerPlugin('Cobe')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Cobe, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))

conf.registerGlobalValue(Cobe, 'ignoreRegex', registry.String('^[.@!$%]', _("""Regex to ignore when learning text. Perfect for ignoring commands!.""")))
conf.registerGlobalValue(Cobe, 'stripUrls', registry.Boolean(True, _("""Keep the bot from learning URLs?""")))
conf.registerGlobalValue(Cobe, 'stripNicks', registry.Boolean(False, _("""Strip all nicks, including the bots, when learning? This replaces a nick with the keyword MAGIC_NICK to use for random highlighting.""")))
conf.registerChannelValue(Cobe, 'probability', registry.NonNegativeInteger(0, _("""Determines the percent of messages the bot will answer.""")))
conf.registerChannelValue(Cobe, 'probabilityWhenAddressed', registry.NonNegativeInteger(10000, _("""Determines the percent of messages adressed to the bot the bot will answer, to the 0.01%. The maximum is 10000/10000""")))
conf.registerChannelValue(Cobe, 'waitTimeBetweenSpeaking', registry.NonNegativeInteger(10, _("""Seconds to wait in a channel before speaking again.""")))
conf.registerChannelValue(Cobe, 'ignoreWaitTimeIfAddressed', registry.Boolean(True, _("""If directly addressed, should we ignore the wait time?""")))
conf.registerChannelValue(Cobe, 'responseDelay', registry.Boolean(False, _("""Delay responding for 2 to 4 seconds in order to seem more human?""")))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
