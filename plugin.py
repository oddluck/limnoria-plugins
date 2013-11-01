###
# Copyright (c) 2013, tann <tann@trivialand.org>
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
import os
import re
import sqlite3
import random
import time
import datetime

class TriviaTime(callbacks.Plugin):
    """
        TriviaTime - A trivia word game, guess the word and score points. Play KAOS rounds and work together to solve clues to find groups of words.
    """
    threaded = True # enables threading for supybot plugin

    def __init__(self, irc):
        print 'Loaded TriviaTime'
        self.__parent = super(TriviaTime, self)
        self.__parent.__init__(irc)

        """ games info """
        self.games = {} # separate game for each channel

        """ connections """
        self.storage = self.Storage(self.registryValue('sqlitedb'))
        #self.storage.dropUserLogTable()
        self.storage.makeUserLogTable()
        #self.storage.dropGameTable()
        self.storage.makeGameTable()
        #self.storage.dropGameLogTable()
        self.storage.makeGameLogTable()
        #self.storage.dropUserTable()
        self.storage.makeUserTable()
        #self.storage.dropReportTable()
        self.storage.makeReportTable()
        #self.storage.insertUserLog('root', 1, 1, 10, 30, 2013)
        #self.storage.insertUser('root', 1, 1)

    def doPrivmsg(self, irc, msg):
        """
            Catches all PRIVMSG, including channels communication
        """
        channel = ircutils.toLower(msg.args[0])
        # Make sure that it is starting inside of a channel, not in pm
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if channel in self.games:
            # check the answer
            self.games[channel].checkAnswer(msg)

    def clearpoints(self, irc, msg, arg, username):
        """<username>

        Deletes all of a users points, and removes all their records
        """
        self.storage.removeUserLogs(str.lower(username))
        irc.reply('Done! Removed all points from %s' % (username))
    clearpoints = wrap(clearpoints, ['admin','nick'])

    def day(self, irc, msg, arg):
        """
            Gives the top10 scores of the day
        """
        channel = ircutils.toLower(msg.args[0])
        tops = self.storage.viewDayTop10()
        topsText = '\x0301,08 TODAYS Top 10 - '
        for i in range(len(tops)):
            topsText += '\x02\x0301,08 #%d:\x02 \x0300,04%s %d ' % ((i+1) , tops[i][1], tops[i][2])
        irc.queueMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    day = wrap(day)

    def givepoints(self, irc, msg, arg, username, points, days):
        """<username> <points> [<daysAgo>]

        Give a user points, last argument is optional amount of days in past to add records
        """
        day=None
        month=None
        year=None
        if days is not None:
            d = datetime.date.today()
            d -= datetime.timedelta(days)
            day = d.day
            month = d.month
            year = d.year
        self.storage.updateUserLog(str.lower(username), points, 0, day, month, year)
        irc.reply('Done! Gave %d points to %s' % (points, username))
    givepoints = wrap(givepoints, ['admin','nick', 'int', optional('int')])

    def me(self, irc, msg, arg):
        """
            Get your rank, score & questions asked for day, month, year
        """
        channel = ircutils.toLower(msg.args[0])
        info = self.storage.getUser(str.lower(msg.nick))
        if len(info) < 3:
            irc.error("You do not exist! There is no spoon.")
        else:
            infoText = '\x0305,08 %s\'s Stats:\x0301,08 Points (answers) \x0305,08Today: #%d %d (%d) This Week: #%d %d (%d) This Month: #%d %d (%d) This Year: #%d %d (%d)' % (msg.nick, info[16], info[10], info[11], info[15], info[8], info[9], info[14], info[6], info[7], info[13], info[4], info[5])
            irc.queueMsg(ircmsgs.privmsg(channel, infoText))
        irc.noReply()
    me = wrap(me)

    def report(self, irc, msg, arg, text):
        channel = str.lower(msg.args[0])
        self.storage.insertReport(channel, msg.nick, text)
        irc.reply('Your report has been submitted!')
    report = wrap(report, ['text'])

    def skip(self, irc, msg, arg):
        """
            Skip a question
        """
        # is it a user?
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
        except KeyError:
            irc.error('You need to register with me to use this command. TODO: show command needed to register')
            return
        channel = ircutils.toLower(msg.args[0])
        if self.games[channel].active == False:
            return
        try:
            schedule.removeEvent('%s.trivia' % channel)
        except KeyError:
            pass
        irc.queueMsg(ircmsgs.privmsg(channel, 'Skipped question!'))
        self.games[channel].nextQuestion()
        irc.noReply()
    skip = wrap(skip)

    def start(self, irc, msg, args):
        """
            Begins a round of Trivia inside of your current channel.
        """
        channel = ircutils.toLower(msg.args[0])
        if not irc.isChannel(channel):
            irc.noReply()
            return
        if channel in self.games:
            if not self.games[channel].active:
                del self.games[channel]
                try:
                    schedule.removeEvent('%s.trivia' % channel)
                except KeyError:
                    pass
            irc.error(self.registryValue('alreadyStarted'))
        else:
            # create a new game
            irc.queueMsg(ircmsgs.privmsg(channel, self.registryValue('starting')))
            self.games[channel] = self.Game(irc, channel, self)
        irc.noReply()
    start = wrap(start)

    def stop(self, irc, msg, args):
        """
            Ends Trivia. Only use this if you know what you are doing.
        """
        # is it a user?
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
        except KeyError:
            irc.error('You need to register with me to use this command. TODO: show command needed to register')
            return

        channel = ircutils.toLower(msg.args[0])
        try:
            schedule.removeEvent('%s.trivia' % channel)
        except KeyError:
            irc.error(self.registryValue('alreadyStopped'))
        if channel in self.games:
            if self.games[channel].active:
                self.games[channel].stop()
            else:
                del self.games[channel]
                irc.queueMsg(ircmsgs.privmsg(channel, self.registryValue('stopped')))
        irc.noReply()
    stop = wrap(stop)

    def time(self, irc, msg, arg):
        """
            Figure out what time/day it is for the server
        """
        channel = ircutils.toLower(msg.args[0])
        timeObject = time.asctime(time.localtime())
        timeString = '\x0301,08The current server time appears to be %s' % timeObject
        irc.queueMsg(ircmsgs.privmsg(channel, timeString))
        irc.noReply()
    time = wrap(time)

    """
    def transferpoints(self, irc, msg, arg, userfrom, userto):
        '''<userfrom> <userto>

        Transfers all points and records from one user to another
        '''
        userfrom = str.lower(userfrom)
        userto = str.lower(userto)
        self.storage.transferUserLogs(userfrom, userto)
        irc.reply('Done! Transfered records from %s to %s' % (userfrom, userto))
    transferpoints = wrap(transferpoints, ['nick', 'nick'])
    """

    """
        Game instance
    """
    class Game:
        """
            Main game logic, single game instance for each channel.
        """
        def __init__(self, irc, channel, base):
            # get utilities from base plugin
            self.games         = base.games
            self.storage       = base.storage
            self.registryValue = base.registryValue
            self.channel       = channel
            self.irc = irc

            # reset stats
            self.streak       = 0
            self.lastWinner   = ''
            self.hintsCounter = 0
            self.numAsked     = 0
            self.lastAnswer   = time.time()

            self.loadGameState()

            # activate
            self.active = True

            # stop any old game and start a new one
            self.removeEvent()
            self.nextQuestion()

        def checkAnswer(self, msg):
            """
                Check users input to see if answer was given.
            """
            
            correctAnswerFound = False
            correctAnswer = ''

            attempt = str.lower(msg.args[1])

            # was a correct answer guessed?
            for ans in self.alternativeAnswers:
                if str.lower(ans) == attempt and str.lower(ans) not in self.guessedAnswers:
                    correctAnswerFound = True
                    correctAnswer = ans
            for ans in self.answers:
                if str.lower(ans) == attempt and str.lower(ans) not in self.guessedAnswers:
                    correctAnswerFound = True
                    correctAnswer = ans

            if correctAnswerFound:
                # time stats
                timeElapsed = float(time.time() - self.askedAt)
                pointsAdded = self.points

                # Past first hint? deduct points
                if self.hintsCounter > 1:
                    pointsAdded /= 2 * (self.hintsCounter - 1)

                if len(self.answers) > 1:
                    if str.lower(msg.nick) not in self.correctPlayers:
                        self.correctPlayers[str.lower(msg.nick)] = 1
                    self.correctPlayers[str.lower(msg.nick)] += 1
                    # KAOS? divide points
                    pointsAdded /= (len(self.answers) + 1)
                    self.totalAmountWon += pointsAdded
                    # report the correct guess for kaos item
                    self.storage.updateUserLog(msg.nick,pointsAdded,0)
                    self.lastAnswer = time.time()
                    self.sendMessage(self.registryValue('answeredKAOS', self.channel) 
                        % (msg.nick, pointsAdded, correctAnswer))
                else:
                    # Normal question solved
                    
                    # update streak info
                    if self.lastWinner != str.lower(msg.nick):
                        self.lastWinner = str.lower(msg.nick)
                        self.streak = 1
                    else:
                        self.streak += 1
                        streakBonus = pointsAdded * .01 * (self.streak-1)
                        maxBonus = 2 * pointsAdded
                        if streakBonus > maxBonus:
                            streakBonus = maxBonus
                        pointsAdded += streakBonus

                    # report correct guess, and show players streak
                    self.storage.updateUserLog(msg.nick,pointsAdded,1)
                    self.lastAnswer = time.time()
                    self.sendMessage(self.registryValue('answeredNormal', self.channel) 
                        % (msg.nick, correctAnswer, timeElapsed, pointsAdded))

                    if self.registryValue('showPlayerStats', self.channel):
                        playersStats = self.storage.getUser(msg.nick)
                        todaysScore = 0
                        userInfo = self.storage.getUser(msg.nick)
                        if len(userInfo) >= 3:
                            todaysScore = userInfo[8]
                            monthScore = userInfo[6]
                            yearScore = userInfo[4]
                        self.sendMessage(self.registryValue('playerStatsMsg', self.channel) 
                            % (msg.nick, self.streak, todaysScore, monthScore, yearScore))

                # add guessed word to list so we can cross it out
                if self.guessedAnswers.count(attempt) == 0:
                    self.guessedAnswers.append(attempt)

                # Have all of the answers been found?
                if len(self.guessedAnswers) == len(self.answers):
                    if len(self.guessedAnswers) > 1:
                        bonusPoints = 0
                        if len(self.correctPlayers) > 2:
                            bonusPoints = self.registryValue('payoutKAOS', self.channel)
                        
                        bonusPointsText = ''
                        if bonusPoints > 0:
                            for nick in self.correctPlayers:
                                self.storage.updateUserLog(str(msg.nick).lower(),bonusPoints)
                            bonusPointsText += self.registryValue('bonusKAOS', self.channel) % int(bonusPoints)

                        # give a special message if it was KAOS
                        self.sendMessage(self.registryValue('solvedAllKAOS', self.channel) % bonusPointsText)
                        self.sendMessage(self.registryValue('recapCompleteKaos', self.channel) % (int(self.totalAmountWon), len(self.correctPlayers)))

                    self.removeEvent()
                    sleepTime = self.registryValue('sleepTime',self.channel)
                    sleepTime = time.time() + sleepTime
                    self.queueEvent(sleepTime, self.nextQuestion)

        def loadGameState(self):
            gameInfo = self.storage.getGame(self.channel)
            if gameInfo is not None:
                self.numAsked = gameInfo[2]

        def loopEvent(self):
            """
                Main game/question/hint loop called by event. Decides whether question or hint is needed.
            """
            # out of hints to give?
            if self.hintsCounter >= self.registryValue('maxHints', self.channel):
                answer = ''
                # create a string to show answers missed
                for ans in self.answers:
                    # dont show guessed values at loss
                    if str.lower(ans) in self.guessedAnswers:
                        continue
                    if answer != '':
                        answer += ' '
                    if len(self.answers) > 1:
                        answer += '['
                    answer += ans
                    if len(self.answers) > 1:
                        answer += ']'

                # Give failure message
                if len(self.answers) > 1:
                    self.sendMessage(self.registryValue('notAnsweredKAOS', self.channel) % answer)

                    self.sendMessage(self.registryValue('recapNotCompleteKaos', self.channel) % (len(self.guessedAnswers), len(self.answers), int(self.totalAmountWon), len(self.correctPlayers)))
                else:
                    self.sendMessage(self.registryValue('notAnswered', self.channel) % answer)
                # provide next question
                
                sleepTime = self.registryValue('sleepTime',self.channel)
                sleepTime = time.time() + sleepTime
                self.queueEvent(sleepTime, self.nextQuestion)
            else:
                # give out more hints
                self.nextHint()

        def nextHint(self):
            """
                Max hints have not been reached, and no answer is found, need more hints
            """
            hintRatio = self.registryValue('hintShowRatio') # % to show each hint
            hints = ''
            
            # create a string with hints for all of the answers
            for ans in self.answers:
                if str.lower(ans) in self.guessedAnswers:
                    continue
                if hints != '':
                    hints += ' '
                if len(self.answers) > 1:
                    hints += '['
                divider = int(len(ans) * self.hintsCounter * hintRatio / 100)
                if divider == len(ans):
                    divider -= 1
                hints += ans[:divider]
                masked = ans[divider:]
                # unmasks a percentage of characters from the front of words
                # TODO a better algorithm for hints
                charMask = self.registryValue('charMask', self.channel)
                hints += re.sub('\w', charMask, masked)
                if len(self.answers) > 1:
                    hints += ']'
            #increment hints counter
            self.hintsCounter += 1
            self.sendMessage('Hint %s: %s' % (self.hintsCounter, hints), 1, 9)
            timeout = self.registryValue('timeout', self.channel)
            timeout += time.time()
            self.queueEvent(timeout, self.loopEvent)

        def nextQuestion(self):
            """
                Time for a new question
            """
            inactivityTime = self.registryValue('inactivityDelay')
            if self.lastAnswer < time.time() - inactivityTime:
                self.stop()
                self.sendMessage('Stopping due to inactivity')
                return

            # reset and increment
            self.question = ''
            self.answers = []
            self.alternativeAnswers = []
            self.guessedAnswers = []
            self.totalAmountWon = 0
            self.lineNumber = -1
            self.correctPlayers = {}
            self.hintsCounter = 0
            self.numAsked += 1
            self.storage.updateGame(self.channel, 1) #increment q's asked

            # grab the next q
            retrievedQuestion = self.retrieveQuestion()

            self.points = self.registryValue('defaultPoints', self.channel)
            for x in retrievedQuestion:
                if 'q' == x:
                   self.question = retrievedQuestion['q']
                if 'a' == x:
                    self.answers = retrievedQuestion['a']
                if 'aa' == x:
                    self.alternativeAnswers = retrievedQuestion['aa']
                if 'p' == x:
                    self.points = retrievedQuestion['p']
                if '#' == x:
                    self.lineNumber = retrievedQuestion['#']

            # store the question number so it can be reported
            self.storage.insertGameLog(self.channel, self.numAsked, 
                                self.lineNumber, self.question)

            # bold the q
            questionText = '%s' % self.question

            # KAOS? report # of answers
            if len(self.answers) > 1:
                questionText += ' %d possible answers' % (len(self.answers))

            self.sendMessage('.%s. %s' % (self.numAsked, questionText), 1, 9)
            self.queueEvent(0, self.loopEvent)
            self.askedAt = time.time()

        def queueEvent(self, timeout, func):
            """
                Create a new timer event for loopEvent call
            """
            # create a new thread for event next step to happen for [timeout] seconds
            def event():
                func()
            if self.active:
                schedule.addEvent(event, timeout, '%s.trivia' % self.channel)

        def removeEvent(self):
            """
                Remove/cancel timer event
            """
            # try and remove the current timer and thread, if we fail don't just carry on
            try:
                schedule.removeEvent('%s.trivia' % self.channel)
            except KeyError:
                pass

        def retrieveQuestion(self):
            # temporary function to get data
            lineNumber, question = self.retrieveRandomQuestionFromFile()
            answer = question.split('*', 1)
            if len(answer) > 1:
                question = answer[0].strip()
                answers = answer[1].split('*')
                answer = []
                alternativeAnswers = []
                points = self.registryValue('defaultPoints', self.channel)
                if str.lower(question[:4]) == 'kaos':
                    points *= len(answers)
                    for ans in answers:
                        answer.append(ans.strip())
                elif str.lower(question[:5]) == 'uword':
                    for ans in answers:
                        answer.append(ans)
                        question = 'Unscramble the letters: '
                        shuffledLetters = list(ans)
                        shuffle(shuffledLetters)
                        for letter in shuffledLetters:
                            question += str.lower(letter)
                        break
                else:                
                    for ans in answers:
                        if answer == []:
                            answer.append(str(ans).strip())
                        else:
                            alternativeAnswers.append(str(ans).strip())
                    answer = [answer[0]]
                print answer
                return {'p':points,
                        'q':question,
                        'a':answer, 
                        'aa':alternativeAnswers, 
                        '#':lineNumber
                        }

            # default question, everything went wrong with grabbing question
            return {'#':-1,
                    'p':10050,
                    'q':'KAOS: The 10 Worst U.S. Presidents (Last Name Only)?',
                    'a':['Bush', 'Nixon', 'Hoover', 'Grant', 'Johnson', 
                        'Ford', 'Reagan', 'Coolidge', 'Pierce'], 
                    'aa':['Obama']
                    }

        def retrieveRandomQuestionFromFile(self):
            """
                Helper function to grab a random line from a file
            """
            filename = self.registryValue('quizfile')
            filesLines = open(filename).readlines()
            randomNumber = random.randint(1,len(filesLines))
            randomLine = filesLines[randomNumber]
            return (randomNumber, randomLine)

        def sendMessage(self, msg, color=None, bgcolor=None):
            """ <msg>, [<color>], [<bgcolor>]

                helper for game instance to send messages to channel
            """
            # with colors? bgcolor?
            if color is None:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, ' %s ' % msg))
            elif bgcolor is None:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '\x03%02d %s ' % (color, msg)))
            else:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '\x03%02d,%02d %s ' % (color, bgcolor, msg)))

        def stop(self):
            """
                Stop a game in progress
            """
            # responsible for stopping a timer/thread after being told to stop
            self.active = False
            self.removeEvent()
            del self.games[self.channel]
            self.sendMessage(self.registryValue('stopped'), 1, 9)
        # end Game

    """
        Storage for users and points using sqlite3
    """
    class Storage:
        """
            Storage class
        """
        def __init__(self,loc):
            self.loc = loc
            self.conn = sqlite3.connect(loc, check_same_thread=False) # dont check threads
                                                                      # otherwise errors

        def insertUserLog(self, username, score, numAnswered, day=None, month=None, year=None):
            if day == None and month == None and year == None:
                dateObject = datetime.date.today()
                day   = dateObject.day
                month = dateObject.month
                year  = dateObject.year
            if self.userLogExists(username, day, month, year):
                return self.updateUserLog(username, score, day, month, year)
            c = self.conn.cursor()
            username = str.lower(username)
            c.execute('insert into triviauserlog values (NULL, ?, ?, ?, ?, ?, ?)', 
                (username, score, numAnswered, day, month, year))
            self.conn.commit()
            c.close()

        def insertUser(self, username):
            username = str.lower(username)
            if self.userExists(username):
                return self.updateUser(username)
            c = self.conn.cursor()
            c.execute('insert into triviausers values (NULL, ?)', (username,))
            self.conn.commit()
            c.close()

        def insertGame(self, channel, numAsked=0):
            channel = str.lower(channel)
            if self.gameExists(channel):
                return self.updateGame(channel, numAsked)
            c = self.conn.cursor()
            c.execute('insert into triviagames values (NULL, ?, ?)', (channel,numAsked))
            self.conn.commit()
            c.close()

        def insertGameLog(self, channel, roundNumber, lineNumber, questionText, askedAt=None):
            channel = str.lower(channel)
            if askedAt is None:
                askedAt = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviagameslog values (NULL, ?, ?, ?, ?, ?)', (channel,roundNumber,lineNumber,questionText,askedAt))
            self.conn.commit()
            c.close()

        def insertReport(self, channel, username, reportText, reportedAt=None):
            channel = str.lower(channel)
            username = str.lower(username)
            if reportedAt is None:
                reportedAt = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviareport values (NULL, ?, ?, ?, ?, NULL, NULL)', 
                                        (channel,username,reportText,reportedAt))
            self.conn.commit()
            c.close()

        def userLogExists(self, username, day, month, year):
            username = str.lower(username)
            c = self.conn.cursor()
            args = (str.lower(username),day,month,year)
            result = c.execute('select count(id) from triviauserlog where username=? and day=? and month=? and year=?', args)
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def userExists(self, username):
            c = self.conn.cursor()
            usr = (str.lower(username),)
            result = c.execute('select count(id) from triviausers where username=?', usr)
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def gameExists(self, channel):
            channel = str.lower(channel)
            c = self.conn.cursor()
            result = c.execute('select count(id) from triviagames where channel=?', (channel,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def updateUserLog(self, username, score, numAnswered, day=None, month=None, year=None):
            username = str.lower(username)
            if not self.userExists(username):
                self.insertUser(username)
            if day == None and month == None and year == None:
                dateObject = datetime.date.today()
                day   = dateObject.day
                month = dateObject.month
                year  = dateObject.year
            if not self.userLogExists(username, day, month, year):
                return self.insertUserLog(username, score, numAnswered, day, month, year)
            c = self.conn.cursor()
            usr = str.lower(username)
            scr = score
            numAns = numAnswered
            test = c.execute('''update triviauserlog set 
                                points_made = points_made+?,
                                num_answered = num_answered+?
                                where username=?
                                and day=? 
                                and month=? 
                                and year=?''', (scr,numAns,usr,day,month,year))
            self.conn.commit()
            c.close()

        def updateUser(self, username):
            username = str.lower(username)
            if not self.userExists(username):
                return self.insertUser(username)
            c = self.conn.cursor()
            test = c.execute('''update triviausers set
                                where username=?''', (username))
            self.conn.commit()
            c.close()
            
        def updateGame(self, channel, numAsked):
            channel = str.lower(channel)
            if not self.gameExists(channel):
                return self.insertGame(channel, numAsked)
            c = self.conn.cursor()
            test = c.execute('''update triviagames set
                                num_asked=num_asked+?
                                where channel=?''', (numAsked, channel))
            self.conn.commit()
            c.close()

        def dropUserTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviausers''')
            except:
                pass
            c.close()
            
        def dropUserLogTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviauserlog''')
            except:
                pass
            c.close()

        def dropGameTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviagames''')
            except:
                pass
            c.close()

        def dropGameLogTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviagameslog''')
            except:
                pass
            c.close()

        def dropReportTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviareport''')
            except:
                pass
            c.close()

        def makeUserTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviausers (
                        id integer primary key autoincrement, 
                        username text not null unique
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeUserLogTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviauserlog (
                        id integer primary key autoincrement, 
                        username text,
                        points_made integer,
                        num_answered integer,
                        day integer, 
                        month integer, 
                        year integer,
                        unique(username, day, month, year) on conflict replace
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeGameTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviagames (
                        id integer primary key autoincrement, 
                        channel text not null unique,
                        num_asked integer
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeGameLogTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviagameslog (
                        id integer primary key autoincrement, 
                        channel text,
                        round_num integer,
                        line_num integer,
                        question text,
                        asked_at integer
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeReportTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviareport (
                        id integer primary key autoincrement, 
                        channel text,
                        username text,
                        report_text text,
                        reported_at integer,
                        fixed_at integer,
                        fixed_by text
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def getUserRanks(self, username):
            username = str.lower(username)
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            c.execute('''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                group by username
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where username=?
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where username=?
                            )''', (username,username))
            data = []

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            c.execute('''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where year=?
                                group by username
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where year=? and username=?
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where year=? and username=?
                            )''', (year,year,username,year,username))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            c.execute('''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where month=? and year=?
                                group by username
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where month=? and year=? and username=?
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where month=? and year=? and username=?
                            )''', (month,year,month,year,username,month,year,username))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            weekSqlClause = ''
            d = datetime.date.today()
            weekday=d.weekday()
            d -= datetime.timedelta(weekday)
            for i in range(7):
                if i > 0:
                    weekSqlClause += ' or ' 
                weekSqlClause += '''(
                            year=%d
                            and month=%d
                            and day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)

            weekSql = '''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where'''
            weekSql += weekSqlClause
            weekSql +='''
                                group by username
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where username=? and ('''
            weekSql += weekSqlClause
            weekSql += ''' 
                                    )
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where username=? and ('''
            weekSql += weekSqlClause
            weekSql += ''' 
                                )
                            )'''
            c.execute(weekSql, (username,username))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            c.execute('''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where day=? and month=? and year=?
                                group by username
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where day=? and month=? and year=? and username=?
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where day=? and month=? and year=? and username=?
                            )''', (day,month,year,day,month,year,username,day,month,year,username))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            c.close()
            return data

        def getUser(self, username):
            username = str.lower(username)
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year

            c = self.conn.cursor()

            data = []
            data.append(username)
            data.append(username)

            c.execute('''select 
                            sum(tl.points_made) as points, 
                            sum(tl.num_answered) as answered
                        from triviauserlog tl
                        where tl.username=?''', (str.lower(username),))
            
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            c.execute('''select 
                            sum(tl.points_made) as yearPoints, 
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where 
                            tl.username=?
                        and tl.year=?''', (str.lower(username),year))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            c.execute('''select 
                            sum(tl.points_made) as yearPoints, 
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where 
                            tl.username=?
                        and tl.year=?
                        and tl.month=?''', (str.lower(username),year, month))
            
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            weekSqlString = '''select 
                            sum(tl.points_made) as yearPoints, 
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where 
                            tl.username=? 
                        and ('''
            
            d = datetime.date.today()
            weekday=d.weekday()
            d -= datetime.timedelta(weekday)
            for i in range(7):
                if i > 0:
                    weekSqlString += ' or ' 
                weekSqlString += '''
                            (tl.year=%d
                            and tl.month=%d
                            and tl.day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)
            
            weekSqlString += ')'
            c.execute(weekSqlString, (str.lower(username),))
            
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break
            
            c.execute('''select 
                            sum(tl.points_made) as yearPoints, 
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where 
                            tl.username=? 
                        and tl.year=?
                        and tl.month=?
                        and tl.day=?''', (str.lower(username),year, month,day))
            
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break
            for d in self.getUserRanks(username):
                data.append(d) 
            #print data

            c.close()
            return data

        def getGame(self, channel):
            channel = str.lower(channel)
            c = self.conn.cursor()
            c.execute('''select * from triviagames
                        where channel=?
                        limit 1''', (channel,))
            data = None
            for row in c:
                data = row
                break
            c.close()
            return data

        def viewDayTop10(self):
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            c.execute('''select * from triviauserlog 
                        where day=? and month=? and year=?
                        order by points_made desc limit 10''', (day, month, year))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data
        """
        def transferUserLogs(self, userFrom, userTo):  
            userFrom = str.lower(userFrom) 
            userTo = str.lower(userTo)
            c = self.conn.cursor()
            c.execute('''update triviauserlog
                            set
                                username=?,
                                points_made=(select
                                                    tl2.points_made
                                                    from triviauserlog tl2
                                                    where 
                                                        tl2.username=?
                                                    and tl2.day=day
                                                    and tl2.month=month
                                                    and tl2.year=year)
                                                ,
                                num_answered=(select
                                                    tl2.num_answered
                                                    from triviauserlog tl2
                                                    where
                                                        tl2.username=?
                                                    and tl2.day=day
                                                    and tl2.month=month
                                                    and tl2.year=year)
                            where
                                username=?''', (userTo,userTo,userTo,userFrom))
            self.conn.commit()
            c.close()
        """
        def removeUserLogs(self, username):
            username = str.lower(username)
            c = self.conn.cursor()
            c.execute('''delete from triviauserlog
                        where username=?''', (username,))
            c.close()


Class = TriviaTime
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
