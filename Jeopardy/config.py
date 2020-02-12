###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2020, oddluck
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
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('Jeopardy')
def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Jeopardy', True)


Jeopardy = conf.registerPlugin('Jeopardy')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Jeopardy, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

conf.registerChannelValue(Jeopardy, 'blankChar',
        registry.String('*', _("""The character used for a blank when
        displaying hints""")))

conf.registerChannelValue(Jeopardy, 'numHints',
        registry.PositiveInteger(3, _("""The number of hints to be given for
        each question""")))

conf.registerChannelValue(Jeopardy, 'delay',
        registry.Integer(4, _("""The number of seconds to increase the delay
        between questions""")))

conf.registerChannelValue(Jeopardy, 'timeout',
        registry.PositiveInteger(90, _("""The number of seconds to allow for
        each question""")))

conf.registerChannelValue(Jeopardy, 'hintPercentage',
        registry.Probability(0.25, _("""The fraction of the answer that
        should be revealed with each hint""")))

conf.registerChannelValue(Jeopardy, 'hintReduction',
        registry.Probability(0.5, _("""The percentage by which to reduce points
        with each hint reveal""")))

conf.registerChannelValue(Jeopardy, 'flexibility',
        registry.Float(0.94, _("""The minimum similarity score of the answer checker.
        Uses jaro-winkler distance, 1.0 is identical/disabled. (Sane values > 0.90)""")))

conf.registerChannelValue(Jeopardy, 'inactiveShutoff',
        registry.Integer(5, _("""The number of questions that can go
        unanswered before the game stops automatically.""")))

conf.registerGlobalValue(Jeopardy, 'jserviceUrl',
        registry.String('http://jservice.io', _("""Set an alternate URL where
        jservice can be accessed at, for example a locally run jservice instance.""")))

conf.registerChannelValue(Jeopardy, 'defaultRoundLength',
        registry.PositiveInteger(10, _("""The default number of questions to
        be asked in a round.""")))

conf.registerChannelValue(Jeopardy, 'randomize',
        registry.Boolean(True, _("""This will determine whether or not the
        bot will randomize the questions.""")))

conf.registerChannelValue(Jeopardy, 'requireOps',
        registry.Boolean(False, _("""This will determine whether or not the
        user must be a channel operator to start/stop the game.""")))

conf.registerChannelValue(Jeopardy, 'enabled',
        registry.Boolean(True, _("""This will determine whether or not the
        game is enabled for a given channel""")))

conf.registerChannelValue(Jeopardy, 'defaultPointValue',
        registry.PositiveInteger(500, _("""The default point value for questions if
        no point value is given""")))

conf.registerChannelValue(Jeopardy, 'autoRestart',
        registry.Boolean(False, _("""Start a new round of random questions after
        the current round has ended.""")))

conf.registerChannelValue(Jeopardy, 'keepHistory',
        registry.Boolean(True, _("""Keep a history of previously asked questions per
        channel and don't repeat them.""")))

conf.registerChannelValue(Jeopardy, 'useBold',
     registry.Boolean(True, _("""Use bold in replies.""")))

conf.registerGroup(Jeopardy, 'template')

conf.registerChannelValue(Jeopardy.template, 'question',
        registry.String("#{{number}} of {{total}}: \x0313({{airdate}}) \x0309[${{points}}] \x0310\x1f{{category}}\x1f: {{clue}}",
        _("""The template used to render questions.""")))

conf.registerChannelValue(Jeopardy.template, 'hint',
        registry.String("HINT: {{hint}}", _("""The template used to render hints.""")))

conf.registerChannelValue(Jeopardy.template, 'correct',
        registry.String("\x0313{{nick}}\x03 got it! The full answer was: \x0310{{answer}}\x03. Points: \x0309{{points}}\x03 | Round Score: \x0309{{round}}\x03 | Total: \x0309{{total}}",
        _("""The template used to render correct answer replies.""")))

conf.registerChannelValue(Jeopardy.template, 'skip',
        registry.String("Skipping question. \x0310(Answer: {{answer}})",
        _("""The template used to render skip replies.""")))

conf.registerChannelValue(Jeopardy.template, 'stop',
        registry.String("Jeopardy! stopped.{% if answer %} \x0310(Answer: {{answer}}){% endif %}",
        _("""The template used to render stop replies.""")))
