###
# Copyright (c) 2012, Mike Mueller
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Do whatever you want
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

import re

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Wordgames', True)

Wordgames = conf.registerPlugin('Wordgames')

conf.registerGlobalValue(Wordgames, 'wordFile',
    registry.String('/usr/share/dict/american-english',
                    'Path to the dictionary file.'))

conf.registerGlobalValue(Wordgames, 'wordRegexp',
    registry.String('^[a-z]+$',
                    'Regular expression defining what a valid word looks ' +
                    'like (i.e. ignore proper names, contractions, etc. ' +
                    'Modify this if you need to allow non-English chars.'))

conf.registerGlobalValue(Wordgames, 'worddleDelay',
    registry.NonNegativeInteger(15,
                                'Delay (in seconds) before a Worddle game ' +
                                'begins.'))

conf.registerGlobalValue(Wordgames, 'worddleDuration',
    registry.NonNegativeInteger(90,
                                'Duration (in seconds) of a Worddle game ' +
                                '(not including the initial delay).'))

conf.registerGlobalValue(Wordgames, 'worddleDifficulty',
    registry.String('easy', 'Default difficulty for Worddle games.'))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
