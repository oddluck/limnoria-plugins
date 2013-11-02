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
    registry.NormalizedString("""/tmp/trivia.t""", 
        """Location of sqlite database file""")
    )

conf.registerChannelValue(TriviaTime, 'quizfile', 
    registry.NormalizedString("""/home/trivia/bogus.ques.sample""", 
        """Location of question file""")
    )

# timeout, number of hints, values
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

conf.registerChannelValue(TriviaTime, 'timeout', 
    registry.Integer(15, 
        """Time in between hints""")
    )

conf.registerChannelValue(TriviaTime, 'sleepTime', 
    registry.Integer(15, 
        """Time in between the end of one question and the start of another""")
    )

conf.registerChannelValue(TriviaTime, 'payoutKAOS', 
    registry.Integer(5000, 
        """Extra points for teamwork on KAOS""")
    )

conf.registerChannelValue(TriviaTime, 'inactivityDelay', 
    registry.Integer(600, 
        """Time before game shuts off in seconds""")
    )

conf.registerChannelValue(TriviaTime, 'defaultPoints', 
    registry.Integer(750, 
        """Default points for a correct answer""")
    )

conf.registerChannelValue(TriviaTime, 'hintShowRatio', 
    registry.Integer(40, 
        """Percent of word to show per hint""")
    )

conf.registerChannelValue(TriviaTime, 'charMask', 
    registry.NormalizedString('*', 
        """Masking character for hints""")
    )

# victory text, help messages, formatting
conf.registerChannelValue(TriviaTime, 'starting', 
    registry.NormalizedString("""Trivia starting in 5 seconds, get ready!!!""", 
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
    registry.NormalizedString("""\x0304%s\x0312 gets \x0304%d\x0312 points for: \x0304%s\x0312""",
        """Message for one correct guess during KAOS""")
    )

conf.registerChannelValue(TriviaTime, 'answeredNormal', 
    registry.NormalizedString("""\x0312DING DING DING, \x0304%s\x0312 got the answer -> \x0304%s\x0312 <- in \x0304%0.4f\x0312 seconds, and gets \x0304%d\x0312 points""", 
        """Message for a correct answer""")
    )

conf.registerChannelValue(TriviaTime, 'notAnswered', 
    registry.NormalizedString("""\x0304Time's up!\x0312 The answer was -> \x0304%s\x0312 <-""", 
        """Message when no one guesses the answer""")
    )

conf.registerChannelValue(TriviaTime, 'notAnsweredKAOS', 
    registry.NormalizedString("""\x0312Time's up!  \x0304No one got\x0312 %s""", 
        """Message when time is up and KAOS are left""")
    )

conf.registerChannelValue(TriviaTime, 'recapNotCompleteKAOS', 
    registry.NormalizedString("""\x0312Correctly Answered: \x0304%d of %d\x0312 Total Awarded: \x0304%d Points\x0312 to %d Players""", 
        """Message after KAOS game that not all questions were answered in""")
    )

conf.registerChannelValue(TriviaTime, 'recapCompleteKAOS', 
    registry.NormalizedString("""\x0312Total Awarded: \x0304%d Points\x0312 to %d Players""", 
        """Message after KAOS game that all questions were answered in""")
    )

conf.registerChannelValue(TriviaTime, 'solvedAllKaos', 
    registry.NormalizedString("""Congratulations, \x0304You've Guessed Them All !!%s""", 
        """Message stating all KAOS have been guessed""")
    )

conf.registerChannelValue(TriviaTime, 'bonusKAOS', 
    registry.NormalizedString(""" \x0300,04 Everyone gets a %d Point Bonus !!""", 
        """Message for bonus points from KAOS for group play""")
    )

conf.registerChannelValue(TriviaTime, 'playerStatsMsg', 
    registry.NormalizedString("""\x0304%s\x0312 has won \x0304%d\x0312 in a row! Total Points TODAY: \x0304%d\x0312 this WEEK \x0304%d\x0312 & this MONTH: \x0304%d\x0312""", 
        """Message showing a users stats after guessing a answer correctly""")
    )

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
