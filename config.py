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
# CONFIGURATION
# file locations for database and question
conf.registerChannelValue(TriviaTime, 'sqlitedb', 
        registry.NormalizedString("""plugins/TriviaTime/storage/db/trivia.db""", 
                """Location of sqlite database file""")
        )

conf.registerChannelValue(TriviaTime, 'quizfile', 
        registry.NormalizedString("""plugins/TriviaTime/storage/samplequestions""", 
                """Location of question file""")
        )

# timeout, number of hints, values
conf.registerChannelValue(TriviaTime, 'showOtherHintCommand', 
        registry.NormalizedString(""".""", 
                """The command to show alternative hints""")
        )

conf.registerChannelValue(TriviaTime, 'showHintCommandKAOS', 
        registry.NormalizedString(""",""", 
                """The command for showing the remaining KAOS""")
        )

conf.registerChannelValue(TriviaTime, 'showVowelsThirdHint',
        registry.Boolean(True,
                """Show all vowels on the third hint. If false, random letters will be shown instead""")
        )

conf.registerChannelValue(TriviaTime, 'repeatCommand', 
        registry.NormalizedString("""repeat""", 
                """The command to repeat the question""")
        )

conf.registerChannelValue(TriviaTime, 'showPlayerStats', 
        registry.Boolean(True, 
                """Show player stats after correct answer?""")
        )

conf.registerChannelValue(TriviaTime, 'skipThreshold', 
        registry.Float(.5, 
                """Percentage of active players who need to vote to skip""")
        )

conf.registerChannelValue(TriviaTime, 'skipActiveTime', 
        registry.Integer((10*60), 
                """Amount of time a user is considered active after answering a question""")
        )

conf.registerChannelValue(TriviaTime, 'skipLimitTime', 
        registry.Integer(60, 
                """Time a user must wait to skip a question again after skipping in seconds""")
        )

conf.registerChannelValue(TriviaTime, 'timeout', 
        registry.Integer(10, 
                """Time in between hints""")
        )

conf.registerChannelValue(TriviaTime, 'timeoutKAOS', 
        registry.Integer(15, 
                """Time in between hints""")
        )

conf.registerChannelValue(TriviaTime, 'sleepTime', 
        registry.Integer(15, 
                """Time in between the end of one question and the start of another""")
        )

conf.registerChannelValue(TriviaTime, 'numTopToVoice',
        registry.Integer(10,
                """The number of top players who are elligible for voice""")
        )

conf.registerChannelValue(TriviaTime, 'minPointsVoiceWeek',
        registry.Integer(30000,
                """Points required to be voiced for being top player in the week""")
        )

conf.registerChannelValue(TriviaTime, 'minPointsVoiceMonth',
        registry.Integer(100000,
                """Points required to be voiced for being top player in the month""")
        )

conf.registerChannelValue(TriviaTime, 'minPointsVoiceYear',
        registry.Integer(5000000,
                """Points required to be voiced for being top player in the year""")
        )

conf.registerChannelValue(TriviaTime, 'payoutKAOS', 
        registry.Integer(1000, 
                """Extra points for teamwork on KAOS""")
        )

conf.registerChannelValue(TriviaTime, 'inactivityDelay', 
        registry.Integer(600, 
                """Time before game shuts off in seconds""")
        )

conf.registerChannelValue(TriviaTime, 'defaultPoints', 
        registry.Integer(500, 
                """Default points for a correct answer to a normal question""")
        )

conf.registerChannelValue(TriviaTime, 'defaultPointsKAOS', 
        registry.Integer(300, 
                """Default points for a correct KAOS answer""")
        )

conf.registerChannelValue(TriviaTime, 'hintShowRatio', 
        registry.Integer(35, 
                """Percent of word to show per hint""")
        )

conf.registerChannelValue(TriviaTime, 'charMask', 
        registry.NormalizedString('*', 
                """Masking character for hints""")
        )

# victory text, help messages, formatting
conf.registerChannelValue(TriviaTime, 'starting', 
        registry.NormalizedString("""Another epic round of trivia is about to begin.""", 
                """Message shown when trivia starts""")
        )

conf.registerChannelValue(TriviaTime, 'stopped', 
        registry.NormalizedString("""Trivia stopped. :'(""", 
                """Message shown when trivia stops""")
        )

conf.registerChannelValue(TriviaTime, 'alreadyStopped', 
        registry.NormalizedString("""Trivia has already been stopped.""", 
                """Message stating chat has already been stopped""")
        )

conf.registerChannelValue(TriviaTime, 'alreadyStarted', 
        registry.NormalizedString("""Trivia has already been started.""", 
                """Message stating chat has already been started""")
        )

conf.registerChannelValue(TriviaTime, 'answeredKAOS', 
        registry.NormalizedString("""\x02%s\x02 gets \x02%d\x02 points for: \x02%s\x02""",
                """Message for one correct guess during KAOS""")
        )

conf.registerChannelValue(TriviaTime, 'answeredNormal', 
        registry.NormalizedString("""DING DING DING, \x02%s\x02 got the answer -> \x02%s\x02 <- in \x02%0.4f\x02 seconds for \x02%d(+%d)\x02 points""", 
                """Message for a correct answer""")
        )

conf.registerChannelValue(TriviaTime, 'notAnswered', 
        registry.NormalizedString("""Time's up! The answer was \x02%s\x02""", 
                """Message when no one guesses the answer""")
        )

conf.registerChannelValue(TriviaTime, 'notAnsweredKAOS', 
        registry.NormalizedString("""Time's up! No one got \x02%s\x02""", 
                """Message when time is up and KAOS are left""")
        )

conf.registerChannelValue(TriviaTime, 'recapNotCompleteKAOS', 
        registry.NormalizedString("""Correctly Answered: \x02%d of %d\x02 Total Awarded: \x02%d Points to %d Players\x02""", 
                """Message after KAOS game that not all questions were answered in""")
        )

conf.registerChannelValue(TriviaTime, 'recapCompleteKAOS', 
        registry.NormalizedString("""Total Awarded: \x02%d Points to %d Players\x02""", 
                """Message after KAOS game that all questions were answered in""")
        )

conf.registerChannelValue(TriviaTime, 'solvedAllKaos', 
        registry.NormalizedString("""All KAOS answered! %s""", 
                """Message stating all KAOS have been guessed""")
        )

conf.registerChannelValue(TriviaTime, 'bonusKAOS', 
        registry.NormalizedString("""Everyone gets a %d Point Bonus!!""", 
                """Message for bonus points from KAOS for group play""")
        )

conf.registerChannelValue(TriviaTime, 'playerStatsMsg', 
        registry.NormalizedString("""\x02%s\x02 has won \x02%d\x02 in a row! Total Points TODAY: \x02%d\x02 this WEEK \x02%d\x02 & this MONTH: \x02%d\x02""", 
                """Message showing a users stats after guessing a answer correctly""")
        )

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79: