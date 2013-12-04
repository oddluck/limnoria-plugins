###
# Copyright (c) 2013, tann <tann@trivialand.org>
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('TriviaTime', True)

TriviaTime = conf.registerPlugin('TriviaTime')

conf.registerGroup(TriviaTime, 'kaos')
conf.registerGroup(TriviaTime, 'admin')
conf.registerGroup(TriviaTime, 'questions')
conf.registerGroup(TriviaTime, 'general')
conf.registerGroup(TriviaTime, 'commands')
conf.registerGroup(TriviaTime, 'voice')
conf.registerGroup(TriviaTime, 'skip')
conf.registerGroup(TriviaTime, 'hints')
# CONFIGURATION
# file locations for database and question
conf.registerChannelValue(TriviaTime.admin, 'sqlitedb', 
        registry.NormalizedString("""plugins/TriviaTime/storage/db/trivia.db""", 
                """Location of sqlite database file""")
        )

conf.registerChannelValue(TriviaTime.admin, 'quizfile', 
        registry.NormalizedString("""plugins/TriviaTime/storage/samplequestions""", 
                """Location of question file. Changes require reloading the plugin""")
        )

# timeout, number of hints, values
conf.registerChannelValue(TriviaTime.commands, 'extraHint', 
        registry.NormalizedString(""".""", 
                """The command to show alternative hints""")
        )

conf.registerChannelValue(TriviaTime.commands, 'showHintCommandKAOS', 
        registry.NormalizedString(""",""", 
                """The command for showing the remaining KAOS""")
        )

conf.registerChannelValue(TriviaTime.general, 'globalStats',
        registry.Boolean(False,
                """Stats are global across all channels""")
        )

conf.registerChannelValue(TriviaTime.hints, 'vowelsHint',
        registry.Boolean(True,
                """Show all vowels on the third hint. If false, random letters will be shown instead""")
        )

conf.registerChannelValue(TriviaTime.general, 'showStats', 
        registry.Boolean(True, 
                """Show player stats after correct answer?""")
        )

conf.registerChannelValue(TriviaTime.skip, 'skipThreshold', 
        registry.Float(.5, 
                """Percentage of active players who need to vote to skip""")
        )

conf.registerChannelValue(TriviaTime.skip, 'skipActiveTime', 
        registry.Integer((10*60), 
                """Amount of time a user is considered active after answering a question""")
        )

conf.registerChannelValue(TriviaTime.skip, 'skipTime', 
        registry.Integer(90, 
                """Time a user must wait to skip a question again after skipping in seconds""")
        )

conf.registerChannelValue(TriviaTime.questions, 'hintTime', 
        registry.Integer(10, 
                """Time in between hints""")
        )

conf.registerChannelValue(TriviaTime.kaos, 'hintKAOS', 
        registry.Integer(15, 
                """Time in between hints""")
        )

conf.registerChannelValue(TriviaTime.general, 'waitTime', 
        registry.Integer(15, 
                """Time in between the end of one question and the start of another""")
        )

conf.registerChannelValue(TriviaTime.voice, 'numTopToVoice',
        registry.Integer(10,
                """The number of top players who are elligible for voice""")
        )

conf.registerChannelValue(TriviaTime.voice, 'minPointsVoiceWeek',
        registry.Integer(30000,
                """Points required to be voiced for being top player in the week""")
        )

conf.registerChannelValue(TriviaTime.voice, 'minPointsVoiceMonth',
        registry.Integer(100000,
                """Points required to be voiced for being top player in the month""")
        )

conf.registerChannelValue(TriviaTime.voice, 'minPointsVoiceYear',
        registry.Integer(5000000,
                """Points required to be voiced for being top player in the year""")
        )

conf.registerChannelValue(TriviaTime.kaos, 'payoutKAOS', 
        registry.Integer(1000, 
                """Extra points for teamwork on KAOS""")
        )

conf.registerChannelValue(TriviaTime.general, 'timeout', 
        registry.Integer(600, 
                """Time before game shuts off in seconds""")
        )

conf.registerChannelValue(TriviaTime.questions, 'defaultPoints', 
        registry.Integer(500, 
                """Default points for a correct answer to a normal question""")
        )

conf.registerChannelValue(TriviaTime.kaos, 'defaultKAOS', 
        registry.Integer(300, 
                """Default points for a correct KAOS answer""")
        )

conf.registerChannelValue(TriviaTime.hints, 'hintRatio', 
        registry.Integer(35, 
                """Percent of word to show per hint""")
        )

conf.registerChannelValue(TriviaTime.hints, 'charMask', 
        registry.NormalizedString('*', 
                """Masking character for hints""")
        )

conf.registerChannelValue(TriviaTime.general, 'nextMinStreak', 
        registry.Integer(5, 
                """The amount of streak needed to use the next command""")
        )

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
