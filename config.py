###
# Copyright (c) 2012, Matthias Meusburger
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

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('DuckHunt', True)


DuckHunt = conf.registerPlugin('DuckHunt')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Quote, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
conf.registerChannelValue(DuckHunt, 'autoRestart',
     registry.Boolean(False, """Does a new hunt automatically start when the previous one is over?"""))

conf.registerChannelValue(DuckHunt, 'ducks',
     registry.Integer(5, """Number of ducks during a hunt?"""))

conf.registerChannelValue(DuckHunt, 'minthrottle', 
     registry.Integer(30, """The minimum amount of time before a new duck may be launched (in seconds)"""))

conf.registerChannelValue(DuckHunt, 'maxthrottle', 
     registry.Integer(300, """The maximum amount of time before a new duck may be launched (in seconds)"""))

conf.registerChannelValue(DuckHunt, 'reloadTime', 
     registry.Integer(5, """The time it takes to reload your rifle once you have shot (in seconds)"""))

conf.registerChannelValue(DuckHunt, 'missProbability', 
     registry.Probability(0.2, """The probability to miss the duck"""))

conf.registerChannelValue(DuckHunt, 'kickMode',
     registry.Boolean(True, """If someone shoots when there is no duck, should he be kicked from the channel? (this requires the bot to be op on the channel)"""))

conf.registerChannelValue(DuckHunt, 'autoFriday',
     registry.Boolean(True, """ Do we need to automatically launch more ducks on friday? """))



# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
