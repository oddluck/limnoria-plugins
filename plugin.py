# -*- coding: utf-8 -*-
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
import supybot.log as log
import supybot.conf as conf
import os
import re
import sqlite3
import random
import time
import datetime
import unicodedata
import hashlib

#A list with items that are removed when timeout is reached, values must be unique
class TimeoutList:
    """
    A dict wrapper used to store timeout values for unique usernames.
    """
    def __init__(self, timeout):
        self.timeout = timeout
        self.dict = {}

    def setTimeout(self, timeout):
        self.timeout = timeout

    def clearTimeout(self):
        for k, t in self.dict.items():
            if t < (time.time() - self.timeout):
                del self.dict[k]

    def append(self, key):
        self.clearTimeout()
        self.dict[key] = time.time()

    def has(self, key):
        self.clearTimeout()
        if key in self.dict:
            return True
        return False
		
    def getTimeLeft(self, key):
        return self.timeout - (time.time() - self.dict[key])


#Game instance
class Game:
    """
    Main game logic, single game instance for each channel.
    """
    def __init__(self, irc, channel, base):
        # constants
        self.unmaskedChars = " -'\"_=+&%$#@!~`()[]{}?.,<>|\\/:;"
        
        # get utilities from base plugin
        self.base = base
        self.games = base.games
        self.storage = base.storage
        self.registryValue = base.registryValue
        self.channel = channel
        self.irc = irc
        self.network = irc.network

        # Initialize timeout lists
        self.skipTimeoutList = TimeoutList(self.registryValue('skip.skipTime', channel))
        self.hintTimeoutList = TimeoutList(self.registryValue('hints.extraHintTime', channel))
        
        # Initialize state variables
        self.state = 'no-question'
        self.stopPending = False
        self.shownHint = False
        self.questionRepeated = False
        
        # Initialize game properties
        self.questionID = -1
        self.questionType = ''
        self.question = ''
        self.answers = []
        self.questionPoints = -1
        self.correctPlayers = {}
        self.guessedAnswers = []
        self.skipList = []
        self.streak = 0
        self.lastWinner = ''
        self.hintsCounter = 0
        self.numAsked = 0
        self.lastAnswer = time.time()
        self.roundStartedAt = time.mktime(time.localtime())

        # activate
        self.loadGameState()
        self.active = True

        # Remove any old event and start the next question
        self.removeEvent()
        self.nextQuestion()

    def checkAnswer(self, msg):
        """
        Check users input to see if answer was given.
        """
        channel = msg.args[0]
        # is it a user?
        username = self.base.getUsername(msg.nick, msg.prefix)
        usernameCanonical = ircutils.toLower(username)
        correctAnswerFound = False
        correctAnswer = ''

        attempt = self.normalizeString(msg.args[1])

        # Check for a correct answer that hasn't already been guessed
        for ans in self.answers:
            normalizedAns = self.normalizeString(ans)
            if normalizedAns == attempt and normalizedAns not in self.guessedAnswers:
                correctAnswerFound = True
                correctAnswer = ans

        # Immediately return if not a correct answer
        if not correctAnswerFound:
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        
        timeElapsed = float(time.time() - self.askedAt)
        points = self.questionPoints

        # Add answer to list so we can cross it out
        if self.guessedAnswers.count(attempt) == 0:
            self.guessedAnswers.append(attempt)
        
        # Past first hint? deduct points
        if self.hintsCounter > 1:
            points /= 2 * (self.hintsCounter - 1)

        # Handle a correct answer for a KAOS question
        if self.questionType == 'kaos':
            if usernameCanonical not in self.correctPlayers:
                self.correctPlayers[usernameCanonical] = 0
            self.correctPlayers[usernameCanonical] += 1
            # KAOS? divide points and convert score to int
            points = int(points / (len(self.answers) + 1))
            self.totalAmountWon += points
            
            # Update database with the correct guess for KAOS item
            threadStorage.updateUserLog(username, self.channel, points, 0, 0)
            self.lastAnswer = time.time()
            self.sendMessage('\x02%s\x02 gets \x02%d\x02 points for: \x02%s\x02' % (username, points, correctAnswer))
        
            # can show more hints now
            self.shownHint = False
        
            # Check if all answers have been answered
            if len(self.guessedAnswers) == len(self.answers):
                self.state = 'post-question'
                self.removeEvent()
                
                # Check if question qualifies for bonus points
                bonusPointsText = ''
                if len(self.correctPlayers) >= 2 and len(self.answers) >= 9:
                    bonusPoints = self.registryValue('kaos.payoutKAOS', self.channel)
                    if bonusPoints > 0:
                        for nick in self.correctPlayers:
                            threadStorage.updateUserLog(nick, self.channel, bonusPoints, 0, 0)
                            self.totalAmountWon += bonusPoints
                        bonusPointsText = 'Everyone gets a %d Point Bonus!!' % int(bonusPoints)

                # Give a special KAOS message 
                self.sendMessage('All KAOS answered! %s' % bonusPointsText)
                self.sendMessage('Total Awarded: \x02%d\x02 Points to \x02%d\x02 Players' % (int(self.totalAmountWon), len(self.correctPlayers)))

                threadStorage.updateQuestionStats(self.questionID, 1, 0)
                
        # Handle a correct answer for a regular question
        else:
            self.state = 'post-question'
            self.removeEvent()
            streakBonus = 0
            minStreak = self.registryValue('general.minBreakStreak', channel)
            # update streak info
            if ircutils.toLower(self.lastWinner) != usernameCanonical:
                #streakbreak
                if self.streak > minStreak:
                    streakBonus = points * .05
                    self.sendMessage('\x02%s\x02 broke \x02%s\x02\'s streak of \x02%d\x02!' % (username, self.lastWinner, self.streak)) 
                self.lastWinner = username
                self.streak = 1
            else:
                self.streak += 1
                streakBonus = points * .01 * (self.streak-1)
                streakBonus = min(streakBonus, points * .5)

            # Update database
            threadStorage.updateGameStreak(self.channel, self.lastWinner, self.streak)
            threadStorage.updateUserHighestStreak(self.lastWinner, self.streak)
            threadStorage.updateGameLongestStreak(self.channel, username, self.streak)
            threadStorage.updateUserLog(username, self.channel, int(points + streakBonus), 1, timeElapsed)
            threadStorage.updateQuestionStats(self.questionID, 1, 0)
            
            # Show congratulatory message
            self.lastAnswer = time.time()
            self.sendMessage('DING DING DING, \x02%s\x02 got the correct answer, \x02%s\x02, in \x02%0.4f\x02 seconds for \x02%d(+%d)\x02 points!' % (username, correctAnswer, timeElapsed, points, streakBonus))

            if self.registryValue('general.showStats', self.channel):
                if self.registryValue('general.globalStats'):
                    stat = threadStorage.getUserStat(username, None)
                else:
                    stat = threadStorage.getUserStat(username, self.channel)
                
                if stat:
                    todaysScore = stat['points_day']
                    weekScore = stat['points_week']
                    monthScore = stat['points_month']
                    recapMessageList = ['\x02%s\x02 has won \x02%d\x02 in a row!' % (username, self.streak)]
                    recapMessageList.append(' Total Points')
                    recapMessageList.append(' TODAY: \x02%d\x02' % (todaysScore))
                    if weekScore > points:
                        recapMessageList.append(' this WEEK \x02%d\x02' % (weekScore))
                    if weekScore > points or todaysScore > points:
                        if monthScore > points:
                            recapMessageList.append(' &')
                    if monthScore > points:
                        recapMessageList.append(' this MONTH: \x02%d\x02' % (monthScore))
                    recapMessage = ''.join(recapMessageList)
                    self.sendMessage(recapMessage)
        
        if self.state == 'post-question':
            # Check for any pending stops, otherwise queue next question
            if self.stopPending == True:
                self.stop()
            else:
                waitTime = self.registryValue('general.waitTime',self.channel)
                if waitTime < 2:
                    waitTime = 2
                    log.error('waitTime was set too low (<2 seconds). Setting to 2 seconds')
                waitTime += time.time()
                self.queueEvent(waitTime, self.nextQuestion)
                self.state = 'no-question'

    def getHintString(self, hintNum=None):
        if hintNum == None:
            hintNum = self.hintsCounter
        hintRatio = self.registryValue('hints.hintRatio') # % to show each hint
        hint = ''
        ratio = float(hintRatio * .01)
        charMask = self.registryValue('hints.charMask', self.channel)

        # create a string with hints for all of the answers
        if self.questionType == 'kaos':
            for ans in self.answers:
                if ircutils.toLower(ans) not in self.guessedAnswers:
                    ans = unicode(ans.decode('utf-8'))
                    hintStr = ''
                    if hintNum == 0:
                        for char in ans:
                            if char in self.unmaskedChars:
                                hintStr += char
                            else:
                                hintStr += charMask
                    elif hintNum == 1:
                        divider = int(len(ans) * ratio)
                        divider = min(divider, 3)
                        divider = min(divider, len(ans)-1)
                        hintStr += ans[:divider]
                        masked = ans[divider:]
                        for char in masked:
                            if char in self.unmaskedChars:
                                hintStr += char
                            else:
                                hintStr += charMask
                    elif hintNum == 2:
                        divider = int(len(ans) * ratio)
                        divider = min(divider, 3)
                        divider = min(divider, len(ans)-1)
                        lettersInARow = divider-1
                        maskedInARow = 0
                        hintStr += ans[:divider]
                        ansend = ans[divider:]
                        hintsend = ''
                        unmasked = 0
                        if self.registryValue('hints.vowelsHint', self.channel):
                            hintStr += self.getMaskedVowels(ansend, divider-1)
                        else:
                            hintStr += self.getMaskedRandom(ansend, divider-1)
                    hint += ' [{0}]'.format(hintStr)
        else:
            ans = unicode(self.answers[0].decode('utf-8'))
            if hintNum == 0:
                for char in ans:
                    if char in self.unmaskedChars:
                        hint += char
                    else:
                        hint += charMask
            elif hintNum == 1:
                divider = int(len(ans) * ratio)
                divider = min(divider, 3)
                divider = min(divider, len(ans)-1)
                hint += ans[:divider]
                masked = ans[divider:]
                for char in masked:
                    if char in self.unmaskedChars:
                        hint += char
                    else:
                        hint += charMask
            elif hintNum == 2:
                divider = int(len(ans) * ratio)
                divider = min(divider, 3)
                divider = min(divider, len(ans)-1)
                lettersInARow = divider-1
                maskedInARow = 0
                hint += ans[:divider]
                ansend = ans[divider:]
                hintsend = ''
                unmasked = 0
                if self.registryValue('hints.vowelsHint', self.channel):
                    hint += self.getMaskedVowels(ansend, divider-1)
                else:
                    hint += self.getMaskedRandom(ansend, divider-1)
        
        return hint.strip().encode('utf-8')

    def getMaskedVowels(self, letters, sizeOfUnmasked):
        charMask = self.registryValue('hints.charMask', self.channel)
        hintsList = ['']
        unmasked = 0
        lettersInARow = sizeOfUnmasked
        for char in letters:
            if char in self.unmaskedChars:
                hintsList.append(char)
            elif str.lower(self.removeAccents(char.encode('utf-8'))) in 'aeiou' and unmasked < (len(letters)-1) and lettersInARow < 3:
                hintsList.append(char)
                lettersInARow += 1
                unmasked += 1
            else:
                hintsList.append(charMask)
                lettersInARow = 0
        hints = ''.join(hintsList)
        return hints

    def getMaskedRandom(self, letters, sizeOfUnmasked):
        charMask = self.registryValue('hints.charMask', self.channel)
        hintRatio = self.registryValue('hints.hintRatio') # % to show each hint
        hints = ''
        unmasked = 0
        maskedInARow = 0
        lettersInARow = sizeOfUnmasked
        for char in letters:
            if char in self.unmaskedChars:
                hints += char
                unmasked += 1
            elif maskedInARow > 2 and unmasked < (len(letters)-1):
                lettersInARow += 1
                unmasked += 1
                maskedInARow = 0
                hints += char
            elif lettersInARow < 3 and unmasked < (len(letters)-1) and random.randint(0,100) < hintRatio:
                lettersInARow += 1
                unmasked += 1
                maskedInARow = 0
                hints += char
            else:
                maskedInARow += 1
                lettersInARow=0
                hints += charMask
        return hints

    def getExtraHintString(self):
        charMask = self.registryValue('hints.charMask', self.channel)
        ans = self.answers[0]
        hints = ' Extra Hint: \x02\x0312'
        divider = 0

        if len(ans) < 2:
            divider = 0
        elif self.hintsCounter == 1:
            divider = 1
        elif self.hintsCounter == 2:
            divider = min(int((len(ans) * .25) + 1), 4)
        elif self.hintsCounter == 3:
            divider = min(int((len(ans) * .5) + 1), 6)
            
        if divider == len(ans):
            divider -= 1

        if divider > 0:
            hints += ans[:divider]

        return hints

    def getExtraHint(self):
        if self.shownHint == False:
            self.shownHint = True
            self.sendMessage(self.getExtraHintString())

    def getRemainingKAOS(self):
        if self.shownHint == False:
            self.shownHint = True
            self.sendMessage('\x02\x0312%s' % (self.getHintString(self.hintsCounter-1)))

    def loadGameState(self):
        gameInfo = self.storage.getGame(self.channel)
        if gameInfo is not None:
            self.numAsked = gameInfo['num_asked']
            self.roundStartedAt = gameInfo['round_started']
            self.lastWinner = gameInfo['last_winner']
            self.streak = int(gameInfo['streak'])

    def loopEvent(self):
        """
            Main game/question/hint loop called by event. Decides whether question or hint is needed.
        """
        # out of hints to give?
        if self.hintsCounter >= 3:
            self.state = 'post-question'
            
            if self.questionType == 'kaos':
                # Create a string to show answers missed
                missedAnswers = ''
                for ans in self.answers:
                    if ircutils.toLower(ans) not in self.guessedAnswers:
                        missedAnswers += ' [{0}]'.format(ans)
                self.sendMessage( """Time's up! No one got \x02%s\x02""" % missedAnswers.strip())
                self.sendMessage("""Correctly Answered: \x02%d\x02 of \x02%d\x02 Total Awarded: \x02%d\x02 Points to \x02%d\x02 Players"""
                                % (len(self.guessedAnswers), len(self.answers), int(self.totalAmountWon), len(self.correctPlayers))
                                )
            else:
                self.sendMessage( """Time's up! The answer was \x02%s\x02.""" % self.answers[0])

            self.storage.updateQuestionStats(self.questionID, 0, 1)

            # Check for any pending stops, otherwise queue next question
            if self.stopPending == True:
                self.stop()
            else:
                waitTime = self.registryValue('general.waitTime', self.channel)
                if waitTime < 2:
                    waitTime = 2
                    log.error('waitTime was set too low (<2 seconds). Setting to 2 seconds')
                waitTime += time.time()
                self.queueEvent(waitTime, self.nextQuestion)
                self.state = 'no-question'
        else:
            # Give out next hint and queue this event again
            self.showHint()
            if self.questionType == 'kaos':
                hintTime = self.registryValue('kaos.hintKAOS', self.channel)
            else:
                hintTime = self.registryValue('questions.hintTime', self.channel)

            if hintTime < 2:
                hintTime = 2
                log.error('hintTime was set too low (<2 seconds). Setting to 2 seconds.')

            hintTime += time.time()
            self.queueEvent(hintTime, self.loopEvent)
            
    def showHint(self):
        """
            Max hints have not been reached, and no answer is found, need more hints
        """
        hints = self.getHintString(self.hintsCounter)
        self.hintsCounter += 1 #increment hints counter
        self.shownHint = False #reset hint shown
        self.sendMessage(' Hint %s: \x02\x0312%s' % (self.hintsCounter, hints), 1, 9)        

    def nextQuestion(self):
        """
            Time for a new question
        """
        inactivityTime = self.registryValue('general.timeout')
        if self.lastAnswer < time.time() - inactivityTime:
            self.sendMessage('Stopping due to inactivity')
            self.stop()
            return
        elif self.stopPending == True:
            self.stop()
            return

        # Reset and increment question properties
        self.state = 'pre-question'
        del self.skipList[:]
        del self.guessedAnswers[:]
        self.totalAmountWon = 0
        self.correctPlayers.clear()
        self.hintsCounter = 0
        self.numAsked += 1

        # grab the next question
        numQuestion = self.storage.getNumQuestions()
        if numQuestion == 0:
            self.sendMessage('There are no questions. Stopping. If you are an admin, use the addfile command to add questions to the database.')
            self.stop()
            return

        # Check if we've asked all questions
        numQuestionsLeftInRound = self.storage.getNumQuestionsNotAsked(self.channel, self.roundStartedAt)
        if numQuestionsLeftInRound == 0:
            self.numAsked = 1
            self.roundStartedAt = time.mktime(time.localtime())
            self.storage.updateGameRoundStarted(self.channel, self.roundStartedAt)
            self.sendMessage('All of the questions have been asked, shuffling and starting over')

        # Update DB with new round number
        self.storage.updateGame(self.channel, self.numAsked) 
        
        # Retrieve new question from DB
        retrievedQuestion = self.retrieveQuestion()
        self.questionID = retrievedQuestion['id']
        self.questionType = retrievedQuestion['type']
        self.question = retrievedQuestion['question']
        self.answers = retrievedQuestion['answers']
        self.questionPoints = retrievedQuestion['points']

        # Store the question and round number so it can be reported
        self.storage.insertGameLog(self.channel, self.numAsked, self.questionID, self.question)
        
        # Send question to channel
        self.sendQuestion()
        
        # Set state variables after question has been sent
        self.state = 'in-question'
        self.questionRepeated = False
        self.shownHint = False
        self.askedAt = time.time()
        
        # Start hint loop
        self.loopEvent()

    def normalizeString(self, s):
        return str.lower(self.removeExtraSpaces(self.removeAccents(s)))
        
    def queueEvent(self, time, event):
        """
            Schedules a new event.
        """
        # Schedule a new event to happen at the specified time
        if self.active:
            try:
                schedule.addEvent(event, time, '%s.trivia' % self.channel)
            except AssertionError as e:
                log.error('Unable to queue {0} because another event is already scheduled.'.format(event.func_name))

    def removeAccents(self, text):
        text = unicode(text.decode('utf-8'))
        normalized = unicodedata.normalize('NFKD', text)
        normalized = u''.join([c for c in normalized if not unicodedata.combining(c)])
        return normalized.encode('utf-8')

    def removeExtraSpaces(self, text):
        return utils.str.normalizeWhitespace(text)

    def repeatQuestion(self):
        if self.questionRepeated == False:
            self.questionRepeated = True
            self.sendQuestion()

    def removeEvent(self):
        """
            Remove/cancel trivia timer event
        """
        # try and remove the current timer and thread, if we fail just carry on
        try:
            schedule.removeEvent('%s.trivia' % self.channel)
        except KeyError:
            pass

    def retrieveQuestion(self):
        # Retrieve and parse question data from database
        rawData = self.storage.getRandomQuestionNotAsked(self.channel, self.roundStartedAt)
        rawQuestion = rawData['question']
        netTimesAnswered = rawData['num_answered'] - rawData['num_missed']
        questionParts = rawQuestion.split('*')
        
        if len(questionParts) > 1:
            question = questionParts[0].strip()
            answers = []
            # Parse question and answers
            if ircutils.toLower(question[:4]) == 'kaos':
                questionType = 'kaos'
                for ans in questionParts[1:]:
                    if answers.count(ans) == 0: # Filter out duplicate answers
                        answers.append(str(ans).strip())
            elif ircutils.toLower(question[:5]) == 'uword':
                questionType = 'uword'
                ans = questionParts[1]
                answers.append(str(ans).strip())
                shuffledLetters = list(unicode(ans.decode('utf-8')))
                random.shuffle(shuffledLetters)
                question = 'Unscramble the letters: {0}'.format(' '.join(shuffledLetters)).encode('utf-8')
            else:
                questionType = 'regular'
                for ans in questionParts[1:]:
                    answers.append(str(ans).strip())

            if questionType == 'kaos':
                points = self.registryValue('kaos.defaultKAOS', self.channel) * len(answers)
            else:
                points = self.registryValue('questions.defaultPoints', self.channel)

            # Calculate additional points
            addPoints = -5 * netTimesAnswered
            addPoints = min(addPoints, 200)
            addPoints = max(addPoints, -200)

            return {'id': rawData['id'],
                    'type': questionType,
                    'points': points + addPoints,
                    'question': question,
                    'answers': answers
                    }
        else:
            log.info('Question #%d is invalid.' % rawData['id'])
            # TODO report bad question

        # default question, everything went wrong with grabbing question
        return {'id': rawData['id'],
                'type': 'kaos',
                'points': 10050,
                'question': 'KAOS: The 10 Worst U.S. Presidents (Last Name Only)? (This is a panic question, if you see this report this question. it is malformed.)',
                'answers': ['Bush', 'Nixon', 'Hoover', 'Grant', 'Johnson', 'Ford', 'Reagan', 'Coolidge', 'Pierce']
                }

    def sendMessage(self, msg, color=None, bgcolor=None):
        """ <msg>, [<color>], [<bgcolor>]
        helper for game instance to send messages to channel
        """
        # no color
        self.irc.sendMsg(ircmsgs.privmsg(self.channel, '%s' % msg))

    def sendQuestion(self):
        question = self.question
        if question[-1:] != '?':
            question += '?'

        # bold the q, add color
        questionText = '\x02\x0303%s' % (question)

        # KAOS? report # of answers
        if self.questionType == 'kaos':
            questionText += ' %d possible answers' % (len(self.answers))

        questionMessageString = ' %s: %s' % (self.numAsked, questionText)
        maxLength = 400
        questionMesagePieces = [questionMessageString[i:i+maxLength] for i in range(0, len(questionMessageString), maxLength)]
        multipleMessages=False

        for msgPiece in questionMesagePieces:
            if multipleMessages:
                msgPiece = '\x02\x0303%s' % (msgPiece)
            multipleMessages = True
            self.sendMessage(msgPiece, 1, 9)
        
    def stop(self):
        """
            Stop a game in progress
        """
        # responsible for stopping a timer/thread after being told to stop
        self.active = False
        self.stopPending = False
        self.removeEvent()
        self.sendMessage('Trivia stopped. :\'(')
        channelCanonical = ircutils.toLower(self.channel)
        if self.network in self.games:
            if channelCanonical in self.games[self.network]:
                del self.games[self.network][channelCanonical]
        

#Storage for users and points using sqlite3
class Storage:
    """
    Storage class
    """
    def __init__(self,loc):
        self.loc = loc
        self.conn = sqlite3.connect(loc, check_same_thread=False) # dont check threads
                                                                  # otherwise errors
        self.conn.text_factory = str
        self.conn.row_factory = sqlite3.Row

    def chunk(self, qs, rows=10000):
        """ Divides the data into 10000 rows each """
        for i in xrange(0, len(qs), rows):
            yield qs[i:i+rows]

    def countTemporaryQuestions(self, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviatemporaryquestion''')
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviatemporaryquestion
                         WHERE channel_canonical=?''', 
                         (ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]

    def countDeletes(self, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviadelete''')
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviadelete
                         WHERE channel_canonical=?''', 
                         (ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]

    def countEdits(self, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit''')
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit
                         WHERE channel_canonical=?''', 
                         (ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]

    def countNotMyEdits(self, username, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit
                         WHERE username<>?''',
                         (username,))
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit
                         WHERE username<>?
                         AND channel_canonical=?''', 
                         (username,
                         ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]

    def countMyEdits(self, username, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit
                         WHERE username=?''',
                         (username,))
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviaedit
                         WHERE username=?
                         AND channel_canonical=?''', 
                         (username,
                         ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]

    def countReports(self, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT COUNT(*) 
                         FROM triviareport''')
        else:
            c.execute('''SELECT COUNT(*) 
                         FROM triviareport
                         WHERE channel_canonical=?''', 
                         (ircutils.toLower(channel),))
        row = c.fetchone()
        c.close()
        return row[0]
    
    def deleteQuestion(self, questionId):
        c = self.conn.cursor()
        test = c.execute('''UPDATE triviaquestion 
                            SET deleted=1
                            WHERE id=?''', 
                            (questionId,))
        self.conn.commit()
        c.close()

    def dropActivityTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviaactivity''')
        except:
            pass
        c.close()

    def dropDeleteTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviadelete''')
        except:
            pass
        c.close()

    def dropUserTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviausers''')
        except:
            pass
        c.close()

    def dropLoginTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE trivialogin''')
        except:
            pass
        c.close()

    def dropUserLogTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviauserlog''')
        except:
            pass
        c.close()

    def dropGameTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP table triviagames''')
        except:
            pass
        c.close()

    def dropGameLogTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviagameslog''')
            c.execute('''DROP INDEX gamelograndomindex''')
        except:
            pass
        c.close()

    def dropReportTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviareport''')
        except:
            pass
        c.close()

    def dropQuestionTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviaquestion''')
            c.execute('''DROP INDEX questionrandomindex''')
        except:
            pass
        c.close()

    def dropTemporaryQuestionTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviatemporaryquestion''')
        except:
            pass
        c.close()

    def dropEditTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE triviaedit''')
        except:
            pass
        c.close()
        
    def dropLevelTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''DROP TABLE trivialevel''')
        except:
            pass
        c.close()

    def getRandomQuestionNotAsked(self, channel, roundStart):
        c = self.conn.cursor()
        c.execute('''SELECT * 
                     FROM triviaquestion
                     WHERE deleted=0 AND 
                           id NOT IN 
                               (SELECT tl.line_num 
                                FROM triviagameslog tl 
                                WHERE tl.channel_canonical=? AND 
                                      tl.asked_at>=?)
                     ORDER BY random() LIMIT 1''', 
                     (ircutils.toLower(channel),roundStart))
        row = c.fetchone()
        c.close()
        return row

    def getQuestionById(self, id):
        c = self.conn.cursor()
        c.execute('''SELECT * 
                     FROM triviaquestion 
                     WHERE id=? LIMIT 1''', 
                     (id,))
        row = c.fetchone()
        c.close()
        return row

    def getQuestionByRound(self, roundNumber, channel):
        channel=ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''SELECT * 
                     FROM triviaquestion 
                     WHERE id=(SELECT tgl.line_num 
                               FROM triviagameslog tgl
                               WHERE tgl.round_num=? AND 
                                     tgl.channel_canonical=?
                               ORDER BY id DESC LIMIT 1)''', 
                     (roundNumber,channel))
        row = c.fetchone()
        c.close()
        return row

    def getNumQuestionsNotAsked(self, channel, roundStart):
        c = self.conn.cursor()
        c.execute('''SELECT count(id) 
                     FROM triviaquestion
                     WHERE deleted=0 AND 
                           id NOT IN 
                                (SELECT tl.line_num 
                                 FROM triviagameslog tl 
                                 WHERE tl.channel=? AND 
                                       tl.asked_at>=?)''', 
                    (channel,roundStart))
        row = c.fetchone()
        c.close()
        return row[0]

    def getUserRank(self, username, channel):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = None
        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
        dateObject = datetime.date.today()
        day   = dateObject.day
        month = dateObject.month
        year  = dateObject.year
        data = {}
        
        # Retrieve total rank
        query = '''SELECT tr.rank
                   FROM (SELECT COUNT(tu2.id)+1 AS rank
                         FROM (SELECT id, 
                                      username, 
                                      sum(points_made) AS totalscore
                               FROM triviauserlog'''
        arguments = []

        if channel is not None:
            query = '''%s WHERE channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical) AS tu2
                        WHERE tu2.totalscore > (
                            SELECT SUM(points_made)
                            FROM triviauserlog
                            WHERE username_canonical=?''' % (query)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s )) AS tr
                    WHERE EXISTS(
                            SELECT *
                            FROM triviauserlog
                            WHERE username_canonical=?''' % (query)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s ) LIMIT 1''' % (query)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        row = c.fetchone()
        data['total'] = row[0] if row else 0

        # Retrieve year rank
        query = '''SELECT tr.rank
                   FROM (SELECT COUNT(tu2.id)+1 AS rank
                         FROM (SELECT id, 
                                      username, 
                                      SUM(points_made) AS totalscore
                               FROM triviauserlog
                               WHERE year=?'''
        arguments = [year]

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical) AS tu2
                        WHERE tu2.totalscore > (
                            SELECT sum(points_made)
                            FROM triviauserlog
                            WHERE year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s )) AS tr
                    WHERE EXISTS(
                            SELECT *
                            FROM triviauserlog
                            WHERE year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s ) LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        data['year'] = row[0] if row else 0

        # Retrieve month rank
        query = '''SELECT tr.rank
                   FROM (SELECT COUNT(tu2.id)+1 AS rank
                         FROM (SELECT id, 
                                      username, 
                                      SUM(points_made) AS totalscore
                               FROM triviauserlog
                               WHERE month=? AND 
                                     year=?'''
        arguments = [month, year]

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical) AS tu2
                        WHERE tu2.totalscore > (
                            SELECT SUM(points_made)
                            FROM triviauserlog
                            WHERE month=? AND 
                                  year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(month)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s )) AS tr
                    WHERE EXISTS(
                            SELECT *
                            FROM triviauserlog
                            WHERE month=? AND 
                                  year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(month)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s ) LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        data['month'] = row[0] if row else 0
        
        # Retrieve week rank
        weekSqlClause = ''
        d = datetime.date.today()
        weekday=d.weekday()
        d -= datetime.timedelta(weekday)
        for i in range(7):
            if i > 0:
                weekSqlClause += ' or '
            weekSqlClause += '''(year=%d AND 
                                 month=%d AND 
                                 day=%d)''' % (d.year, d.month, d.day)
            d += datetime.timedelta(1)

        weekSql = '''SELECT tr.rank
                     FROM (SELECT count(tu2.id)+1 AS rank
                           FROM (SELECT id, 
                                        username, 
                                        SUM(points_made) AS totalscore
                                 FROM triviauserlog
                                 WHERE ('''
        weekSql += weekSqlClause
        weekSql +=''')'''
        arguments = []

        if channel is not None:
            weekSql = '''%s AND channel_canonical=?''' % (weekSql)
            arguments.append(channelCanonical)

        weekSql += '''GROUP BY username_canonical) AS tu2
                        WHERE tu2.totalscore > (
                            SELECT SUM(points_made)
                            FROM triviauserlog
                            WHERE username_canonical=?'''
        arguments.append(usernameCanonical)

        if channel is not None:
            weekSql = '''%s AND channel_canonical=?''' % (weekSql)
            arguments.append(channelCanonical)

        weekSql += ''' AND ('''
        weekSql += weekSqlClause
        weekSql += '''))) AS tr
                    WHERE EXISTS(
                            SELECT *
                            FROM triviauserlog
                            WHERE username_canonical=?'''
        arguments.append(usernameCanonical)

        if channel is not None:
            weekSql = '''%s AND channel_canonical=?''' % (weekSql)
            arguments.append(channelCanonical)

        weekSql += ''' AND ('''
        weekSql += weekSqlClause
        weekSql += ''')) LIMIT 1'''
        
        c.execute(weekSql, tuple(arguments))
        row = c.fetchone()
        data['week'] = row[0] if row else 0

        # Retrieve day rank
        query = '''SELECT tr.rank
                   FROM (SELECT COUNT(tu2.id)+1 AS rank
                         FROM (SELECT id, 
                                      username, 
                                      SUM(points_made) AS totalscore
                               FROM triviauserlog
                               WHERE day=? AND 
                                     month=? AND 
                                     year=?'''
        arguments = [day, month, year]

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical) AS tu2
                        WHERE tu2.totalscore > (
                            SELECT SUM(points_made)
                            FROM triviauserlog
                            WHERE day=? AND 
                                  month=? AND 
                                  year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(day)
        arguments.append(month)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s and channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s )) AS tr
                    WHERE EXISTS(
                            SELECT *
                            FROM triviauserlog
                            WHERE day=? AND 
                                  month=? AND 
                                  year=? AND 
                                  username_canonical=?''' % (query)
        arguments.append(day)
        arguments.append(month)
        arguments.append(year)
        arguments.append(usernameCanonical)

        if channel is not None:
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s ) LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        data['day'] = row[0] if row else 0

        c.close()
        return data

    def getUserStat(self, username, channel):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = None
        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
        dateObject = datetime.date.today()
        day   = dateObject.day
        month = dateObject.month
        year  = dateObject.year

        c = self.conn.cursor()

        data = {}
        data['username'] = username
        data['username_canonical'] = usernameCanonical

        # Retrieve total points and answered
        query = '''SELECT SUM(tl.points_made) AS points,
                          SUM(tl.num_answered) AS answered
                   FROM triviauserlog tl
                   WHERE tl.username_canonical=?'''
        arguments = [usernameCanonical]

        if channel is not None:
            query = '''%s AND tl.channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        if row:
            data['points_total'] = row[0]
            data['answer_total'] = row[1]
        
        # Retrieve year points and answered
        query = '''SELECT SUM(tl.points_made) AS yearPoints,
                          SUM(tl.num_answered) AS yearAnswered
                   FROM triviauserlog tl
                   WHERE tl.username_canonical=? AND 
                         tl.year=?'''
        arguments = [usernameCanonical, year]

        if channel is not None:
            query = '''%s AND tl.channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        if row:
            data['points_year'] = row[0]
            data['answer_year'] = row[1]

        # Retrieve month points and answered
        query = '''SELECT SUM(tl.points_made) AS yearPoints,
                          SUM(tl.num_answered) AS yearAnswered
                   FROM triviauserlog tl
                   WHERE tl.username_canonical=? AND 
                         tl.year=? AND 
                         tl.month=?'''
        arguments = [usernameCanonical, year, month]

        if channel is not None:
            query = '''%s AND tl.channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s LIMIT 1''' % (query)
        
        c.execute(query, tuple(arguments))
        row = c.fetchone()
        if row:
            data['points_month'] = row[0]
            data['answer_month'] = row[1]

        # Retrieve week points and answered
        query = '''SELECT SUM(tl.points_made) AS yearPoints,
                          SUM(tl.num_answered) AS yearAnswered
                   FROM triviauserlog tl
                   WHERE tl.username_canonical=? AND ('''

        d = datetime.date.today()
        weekday=d.weekday()
        d -= datetime.timedelta(weekday)
        for i in range(7):
            if i > 0:
                query += ' or '
            query += '''
                        (tl.year=%d
                        AND tl.month=%d
                        AND tl.day=%d)''' % (d.year, d.month, d.day)
            d += datetime.timedelta(1)

        query += ')'
        arguments = [usernameCanonical]

        if channel is not None:
            query = '''%s AND tl.channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s LIMIT 1''' % (query)
        
        c.execute(query, tuple(arguments))
        row = c.fetchone()
        if row:
            data['points_week'] = row[0]
            data['answer_week'] = row[1]

        # Retrieve day points and answered
        query = '''SELECT SUM(tl.points_made) AS yearPoints,
                          SUM(tl.num_answered) AS yearAnswered
                   FROM triviauserlog tl
                   WHERE tl.username_canonical=? AND 
                         tl.year=? AND 
                         tl.month=? AND 
                         tl.day=?'''
        arguments = [usernameCanonical, year, month, day]

        if channel is not None:
            query = '''%s AND tl.channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s LIMIT 1''' % (query)

        c.execute(query, tuple(arguments))
        row = c.fetchone()
        if row:
            data['points_day'] = row[0]
            data['answer_day'] = row[1]

        c.close()
        return data
    
    def getUserLevel(self, username, channel):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        
        c = self.conn.cursor()
        c.execute('''SELECT level 
                     FROM trivialevel
                     WHERE username_canonical=? AND 
                           channel_canonical=?''', 
                     (username_canonical, channel_canonical))
        row = c.fetchone()
        c.close()
        return row[0]
        
    def getGame(self, channel):
        channel = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''SELECT * 
                     FROM triviagames
                     WHERE channel_canonical=? 
                     LIMIT 1''', 
                     (channel,))
        row = c.fetchone()
        c.close()
        return row

    def getNumUser(self, channel):
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(DISTINCT(username_canonical)) 
                     FROM triviauserlog 
                     WHERE channel_canonical=?''', 
                     (channelCanonical,))
        row = c.fetchone()
        c.close()
        return row[0]

    def getNumQuestions(self):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) 
                     FROM triviaquestion 
                     WHERE deleted=0''')
        row = c.fetchone()
        c.close()
        return row[0]

    def getNumKAOS(self):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) 
                     FROM triviaquestion 
                     WHERE lower(substr(question,1,4))=?''', 
                     ('kaos',))
        row = c.fetchone()
        c.close()
        return row[0]

    def getNumActiveThisWeek(self, channel):
        channelCanonical = ircutils.toLower(channel)
        d = datetime.date.today()
        weekday=d.weekday()
        d -= datetime.timedelta(weekday)
        weekSqlString = ''
        for i in range(7):
            if i > 0:
                weekSqlString += ' or '
            weekSqlString += '''
                        (tl.year=%d
                        AND tl.month=%d
                        AND tl.day=%d)''' % (d.year, d.month, d.day)
            d += datetime.timedelta(1)
        c = self.conn.cursor()
        weekSql = '''SELECT COUNT(DISTINCT(tl.username_canonical))
                     FROM triviauserlog tl
                     WHERE channel_canonical=? AND ('''
        weekSql += weekSqlString
        weekSql += ''')'''
        c.execute(weekSql, (channelCanonical,))
        row = c.fetchone()
        c.close()
        return row[0]

    def getDeleteById(self, id, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviadelete 
                         WHERE id=? LIMIT 1''', 
                         (id,))
        else:
            c.execute('''SELECT * 
                         FROM triviadelete 
                         WHERE id=? AND 
                               channel_canonical=? 
                         LIMIT 1''', 
                         (id, ircutils.toLower(channel)))
        row = c.fetchone()
        c.close()
        return row

    def getDeleteTop3(self, page=1, amount=3, channel=None):
        if page < 1:
            page=1
        if amount < 1:
            amount=3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviadelete 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviadelete 
                         WHERE channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows

    def getReportById(self, id, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviareport 
                         WHERE id=? LIMIT 1''', 
                         (id,))
        else:
            c.execute('''SELECT * 
                         FROM triviareport 
                         WHERE id=? AND 
                               channel_canonical=? 
                         LIMIT 1''', 
                         (id, ircutils.toLower(channel)))
        row = c.fetchone()
        c.close()
        return row

    def getReportTop3(self, page=1, amount=3, channel=None):
        if page < 1:
            page=1
        if amount < 1:
            amount=3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviareport 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviareport 
                         WHERE channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows

    def getTemporaryQuestionTop3(self, page=1, amount=3, channel=None):
        if page < 1:
            page=1
        if amount < 1:
            amount=3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviatemporaryquestion 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviatemporaryquestion 
                         WHERE channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows

    def getTemporaryQuestionById(self, id, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviatemporaryquestion 
                         WHERE id=? 
                         LIMIT 1''', 
                         (id,))
        else:
            c.execute('''SELECT * 
                         FROM triviatemporaryquestion 
                         WHERE id=? AND 
                               channel_canonical=? 
                         LIMIT 1''', 
                         (id, ircutils.toLower(channel)))
        row = c.fetchone()
        c.close()
        return row

    def getEditTop3(self, page=1, amount=3, channel=None):
        if page < 1:
            page = 1
        if amount < 1:
            amount = 3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         WHERE channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows
        
    def getNotMyEditTop3(self, username, page=1, amount=3, channel=None):
        if page < 1:
            page = 1
        if amount < 1:
            amount = 3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviaedit
                         WHERE username<>?
                         ORDER BY id ASC LIMIT ?, ?''',
                         (username, start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         WHERE username<>?
                         AND channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (username, ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows
        
    def getMyEditTop3(self, username, page=1, amount=3, channel=None):
        if page < 1:
            page = 1
        if amount < 1:
            amount = 3
        page -= 1
        start = page * amount
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviaedit
                         WHERE username=?
                         ORDER BY id ASC LIMIT ?, ?''',
                         (username, start, amount))
        else:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         WHERE username=?
                         AND channel_canonical=? 
                         ORDER BY id ASC LIMIT ?, ?''', 
                         (username, ircutils.toLower(channel), start, amount))
        rows = c.fetchall()
        c.close()
        return rows
        
    def getEditById(self, id, channel=None):
        c = self.conn.cursor()
        if channel is None:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         WHERE id=? 
                         LIMIT 1''', 
                         (id,))
        else:
            c.execute('''SELECT * 
                         FROM triviaedit 
                         WHERE id=? AND 
                               channel_canonical=? 
                         LIMIT 1''', 
                         (id, ircutils.toLower(channel)))
        row = c.fetchone()
        c.close()
        return row

    def getNumUserActiveIn(self, channel, timeSeconds):
        channelCanonical = ircutils.toLower(channel)
        epoch = int(time.mktime(time.localtime()))
        dateObject = datetime.date.today()
        day   = dateObject.day
        month = dateObject.month
        year  = dateObject.year
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) 
                     FROM triviauserlog
                     WHERE day=? AND 
                           month=? AND 
                           year=? AND 
                           channel_canonical=? AND 
                           last_updated>?''', 
                     (day, month, year, channelCanonical, (epoch-timeSeconds)))
        row = c.fetchone()
        c.close()
        return row[0]
    
    def getVersion(self):
        c = self.conn.cursor();
        try:
            c.execute('''SELECT version 
                         FROM triviainfo''')
            return c.fetchone()
        except:
            pass

    def gameExists(self, channel):
        channel = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(id) 
                     FROM triviagames 
                     WHERE channel_canonical=?''', 
                     (channel,))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def loginExists(self, username):
        usernameCanonical = ircutils.toLower(username)
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(id) 
                     FROM trivialogin 
                     WHERE username_canonical=?''', 
                     (usernameCanonical,))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def insertActivity(self, aType, activity, channel, network, timestamp=None):
        if timestamp is None:
            timestamp = int(time.mktime(time.localtime()))
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviaactivity 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?)''',
                     (aType, activity, channel, channelCanonical, network, 
                      timestamp))
        self.conn.commit()

    def insertDelete(self, username, channel, lineNumber, reason):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviadelete 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?)''',
                     (username, usernameCanonical, lineNumber, channel, 
                      channelCanonical, reason))
        self.conn.commit()

    def insertLogin(self, username, salt, isHashed, password, capability):
        usernameCanonical = ircutils.toLower(username)
        if self.loginExists(username):
            return self.updateLogin(username, salt, isHashed, password, capability)
        if not isHashed:
            isHashed = 0
        else:
            isHashed = 1
        c = self.conn.cursor()
        c.execute('''INSERT INTO trivialogin 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?)''',
                     (username, usernameCanonical, salt, isHashed, 
                      password, capability))
        self.conn.commit()

    def insertUserLog(self, username, channel, score, numAnswered, timeTaken, day=None, month=None, year=None, epoch=None):
        if day == None and month == None and year == None:
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
        score = int(score)
        if epoch is None:
            epoch = int(time.mktime(time.localtime()))
        if self.userLogExists(username, channel, day, month, year):
            return self.updateUserLog(username, channel, score, numAnswered, timeTaken, day, month, year, epoch)
        c = self.conn.cursor()
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        scoreAvg = 'NULL'
        if numAnswered >= 1:
            scoreAvg = score / numAnswered
        c.execute('''INSERT INTO triviauserlog 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (username, score, numAnswered, day, month, year, 
                      epoch, timeTaken, scoreAvg, usernameCanonical, 
                      channel, channelCanonical))
        self.conn.commit()
        c.close()

    def insertUser(self, username, numEditted=0, numEdittedAccepted=0, numReported=0, numQuestionsAdded=0, numQuestionsAccepted=0):
        usernameCanonical = ircutils.toLower(username)
        if self.userExists(username):
            return self.updateUser(username, numEditted, numEdittedAccepted, numReported, numQuestionsAdded, numQuestionsAccepted)
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviausers 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, 0)''', 
                     (username, numEditted, numEdittedAccepted, 
                      usernameCanonical, numReported, 
                      numQuestionsAdded, numQuestionsAccepted))
        self.conn.commit()
        c.close()
    
    def insertUserLevel(self, username, channel, level):
        if self.userLevelExists(username, channel):
            return self.updateUserLevel(username, channel, level)
            
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        
        c = self.conn.cursor()
        c.execute('''INSERT INTO trivialevel 
                     VALUES (?, ?, ?, ?, ?)''',
                     (username, usernameCanonical, channel, 
                      channelCanonical, level))
        self.conn.commit()
        c.close()

    def insertGame(self, channel, numAsked=0, epoch=None):
        channelCanonical = ircutils.toLower(channel)
        if self.gameExists(channel):
            return self.updateGame(channel, numAsked)
        if epoch is None:
            epoch = int(time.mktime(time.localtime()))
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviagames 
                     VALUES (NULL, ?, ?, ?, 0, 0, ?, 0, "", "")''', 
                     (channel, numAsked, epoch, channelCanonical))
        self.conn.commit()
        c.close()

    def insertGameLog(self, channel, roundNumber, lineNumber, questionText, askedAt=None):
        channelCanonical = ircutils.toLower(channel)
        if askedAt is None:
            askedAt = int(time.mktime(time.localtime()))
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviagameslog 
                     VALUES (NULL, ?, ?, ?, ?, ?, ?)''', 
                     (channel, roundNumber, lineNumber, questionText, 
                      askedAt, channelCanonical))
        self.conn.commit()
        c.close()

    def insertReport(self, channel, username, reportText, questionNum, reportedAt=None):
        channelCanonical = ircutils.toLower(channel)
        usernameCanonical = ircutils.toLower(username)
        if reportedAt is None:
            reportedAt = int(time.mktime(time.localtime()))
        c = self.conn.cursor()
        c.execute('''INSERT INTO triviareport 
                     VALUES (NULL, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)''',
                     (channel, username, reportText, reportedAt, 
                      questionNum, usernameCanonical, channelCanonical))
        self.conn.commit()
        c.close()

    def insertQuestionsBulk(self, questions):
        c = self.conn.cursor()
        #skipped=0
        divData = self.chunk(questions) # divide into 10000 rows each
        for chunk in divData:
            c.executemany('''INSERT INTO triviaquestion 
                             VALUES (NULL, ?, ?, 0, 0, 0)''', 
                             chunk)
        self.conn.commit()
        skipped = self.removeDuplicateQuestions()
        c.close()
        return ((len(questions) - skipped), skipped)

    def insertEdit(self, questionId, questionText, username, channel, createdAt=None):
        c = self.conn.cursor()
        channelCanonical = ircutils.toLower(channel)
        usernameCanonical = ircutils.toLower(username)
        if createdAt is None:
            createdAt = int(time.mktime(time.localtime()))
        c.execute('''INSERT INTO triviaedit 
                     VALUES (NULL, ?, ?, NULL, ?, ?, ?, ?, ?)''',
                     (questionId, questionText, username, channel, 
                      createdAt, usernameCanonical, channelCanonical))
        self.conn.commit()
        c.close()

    def insertTemporaryQuestion(self, username, channel, question):
        c = self.conn.cursor()
        channelCanonical = ircutils.toLower(channel)
        usernameCanonical = ircutils.toLower(username)
        c.execute('''INSERT INTO triviatemporaryquestion 
                     VALUES (NULL, ?, ?, ?, ?, ?)''',
                     (username, channel, question, usernameCanonical, 
                      channelCanonical))
        self.conn.commit()
        c.close()

    def isQuestionDeleted(self, id):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) 
                     FROM triviaquestion
                     WHERE deleted=1 AND 
                           id=?''', 
                     (id,))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def isQuestionPendingDeletion(self, id):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) 
                     FROM triviadelete
                     WHERE line_num=?''', 
                     (id,))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def makeActivityTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviaactivity (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            type TEXT,
                            activity TEXT,
                            channel TEXT,
                            channel_canonical TEXT,
                            network TEXT,
                            timestamp INTEGER)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeDeleteTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviadelete (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            username_canonical TEXT,
                            line_num INTEGER,
                            channel TEXT,
                            channel_canonical TEXT,
                            reason TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()
    
    def makeLevelTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE trivialevel (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            username_canonical TEXT,
                            channel TEXT,
                            channel_canonical TEXT,
                            level INTEGER)''')
        except:
            pass

    def makeLoginTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE trivialogin (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            username_canonical TEXT NOT NULL UNIQUE,
                            salt TEXT,
                            is_hashed INTEGER NOT NULL DEFAULT 1,
                            password TEXT,
                            capability TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeUserTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviausers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            num_editted INTEGER,
                            num_editted_accepted INTEGER,
                            username_canonical TEXT NOT NULL UNIQUE,
                            num_reported INTEGER,
                            num_questions_added INTEGER,
                            num_questions_accepted INTEGER,
                            highest_streak INTEGER)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeUserLogTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviauserlog (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            points_made INTEGER,
                            num_answered INTEGER,
                            day INTEGER,
                            month INTEGER,
                            year INTEGER,
                            last_updated INTEGER,
                            average_time INTEGER,
                            average_score INTEGER,
                            username_canonical TEXT,
                            channel TEXT,
                            channel_canonical TEXT,
                            UNIQUE(username_canonical, channel_canonical, 
                                   day, month, year) ON CONFLICT REPLACE)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeGameTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviagames (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            channel TEXT,
                            num_asked INTEGER,
                            round_started INTEGER,
                            last_winner TEXT,
                            streak INTEGER,
                            channel_canonical TEXT NOT NULL UNIQUE,
                            longest_streak INTEGER,
                            longest_streak_holder TEXT,
                            longest_streak_holder_canonical TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeGameLogTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviagameslog (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            channel TEXT,
                            round_num INTEGER,
                            line_num INTEGER,
                            question TEXT,
                            asked_at INTEGER,
                            channel_canonical TEXT)''')
            c.execute('''CREATE INDEX gamelograndomindex
                         ON triviagameslog (channel, line_num, asked_at))''')
        except:
            pass
        self.conn.commit()
        c.close()
        
    def makeInfoTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviainfo (version INTEGER)''')
        except:
            pass

    def makeReportTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviareport (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            channel TEXT,
                            username TEXT,
                            report_text TEXT,
                            reported_at INTEGER,
                            fixed_at INTEGER,
                            fixed_by TEXT,
                            question_num INTEGER,
                            username_canonical TEXT,
                            channel_canonical TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeTemporaryQuestionTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviatemporaryquestion (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            channel TEXT,
                            question TEXT,
                            username_canonical TEXT,
                            channel_canonical TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeQuestionTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviaquestion (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question_canonical TEXT,
                            question TEXT,
                            deleted INTEGER NOT NULL DEFAULT 0,
                            num_answered INTEGER,
                            num_missed INTEGER)''')
            c.execute('''CREATE INDEX questionrandomindex
                         ON triviagameslog (id, deleted))''')
        except:
            pass
        self.conn.commit()
        c.close()

    def makeEditTable(self):
        c = self.conn.cursor()
        try:
            c.execute('''CREATE TABLE triviaedit (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question_id INTEGER,
                            question TEXT,
                            status TEXT,
                            username TEXT,
                            channel TEXT,
                            created_at TEXT,
                            username_canonical TEXT,
                            channel_canonical TEXT)''')
        except:
            pass
        self.conn.commit()
        c.close()

    def questionExists(self, question):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(id) 
                     FROM triviaquestion 
                     WHERE question=? OR 
                           question_canonical=?''', 
                     (question, question))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def questionIdExists(self, id):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(id) 
                     FROM triviaquestion 
                     WHERE id=?''', 
                     (id,))
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def removeOldActivity(self,count=100):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviaactivity
                     WHERE id NOT IN (
                        SELECT id
                        FROM triviaactivity
                        ORDER BY id DESC LIMIT ?)''', 
                     (count,))
        self.conn.commit()
        c.close()

    def removeDelete(self, deleteId):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviadelete
                     WHERE id=?''', 
                     (deleteId,))
        self.conn.commit()
        c.close()

    def removeDuplicateQuestions(self):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviaquestion 
                     WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM triviaquestion 
                        GROUP BY question_canonical)''')
        num = c.rowcount
        self.conn.commit()
        c.close()
        return num

    def removeEdit(self, editId):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviaedit
                     WHERE id=?''', 
                     (editId,))
        self.conn.commit()
        c.close()

    def removeLogin(self, username):
        usernameCanonical = ircutils.toLower(username)
        c = self.conn.cursor()
        c.execute('''DELETE FROM trivialogin
                     WHERE username_canonical=?''', 
                     (usernameCanonical,))
        self.conn.commit()
        c.close()

    def removeReport(self, repId):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviareport
                     WHERE id=?''', (repId,))
        self.conn.commit()
        c.close()

    def removeReportByQuestionNumber(self, id):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviareport
                     WHERE question_num=?''', 
                     (id,))
        self.conn.commit()
        c.close()

    def removeEditByQuestionNumber(self, id):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviaedit
                     WHERE question_id=?''', 
                     (id,))
        self.conn.commit()
        c.close()

    def removeDeleteByQuestionNumber(self, id):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviadelete
                     WHERE line_num=?''', 
                     (id,))
        self.conn.commit()
        c.close()

    def removeTemporaryQuestion(self, id):
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviatemporaryquestion
                     WHERE id=?''', 
                     (id,))
        self.conn.commit()
        c.close()

    def removeUserLogs(self, username, channel):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''DELETE FROM triviauserlog
                     WHERE username_canonical=? AND 
                           channel_canonical=?''', 
                     (usernameCanonical, channelCanonical))
        self.conn.commit()
        c.close()

    def restoreQuestion(self, id):
        c = self.conn.cursor()
        test = c.execute('''UPDATE triviaquestion 
                            SET deleted=0
                            WHERE id=?''', 
                            (id,))
        self.conn.commit()
        c.close()

    def transferUserLogs(self, userFrom, userTo, channel):
        userFromCanonical = ircutils.toLower(userFrom)
        userToCanonical = ircutils.toLower(userTo)
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        c.execute('''UPDATE triviauserlog
                     SET num_answered=num_answered+IFNULL(
                                        (SELECT t3.num_answered
                                         FROM triviauserlog t3
                                         WHERE t3.day=triviauserlog.day AND 
                                               t3.month=triviauserlog.month AND 
                                               t3.year=triviauserlog.year AND 
                                               t3.channel_canonical=? AND 
                                               t3.username_canonical=?),0),
                         points_made=points_made+IFNULL(
                                        (SELECT t2.points_made 
                                         FROM triviauserlog t2 
                                         WHERE t2.day=triviauserlog.day AND 
                                               t2.month=triviauserlog.month AND 
                                               t2.year=triviauserlog.year AND 
                                               t2.channel_canonical=? AND 
                                               t2.username_canonical=?),0)
                     WHERE id IN (
                            SELECT id
                            FROM triviauserlog tl
                            WHERE channel_canonical=? AND 
                                  username_canonical=? AND 
                                  EXISTS (
                                    SELECT id
                                    FROM triviauserlog tl2
                                    WHERE tl2.day=tl.day AND 
                                          tl2.month=tl.month AND 
                                          tl2.year=tl.year AND 
                                          tl2.channel_canonical=? AND 
                                          tl2.username_canonical=?)
                )
        ''', (channelCanonical, userFromCanonical,
              channelCanonical, userFromCanonical, 
              channelCanonical, userToCanonical,
              channelCanonical, userFromCanonical))

        c.execute('''UPDATE triviauserlog 
                     SET username=?,
                         username_canonical=?
                     WHERE username_canonical=? AND 
                           channel_canonical=? AND 
                           NOT EXISTS (
                                SELECT 1
                                FROM triviauserlog tl
                                WHERE tl.day=triviauserlog.day AND 
                                      tl.month=triviauserlog.month AND 
                                      tl.year=triviauserlog.year AND 
                                      tl.channel_canonical=? AND 
                                      tl.username_canonical=?)''', 
                  (userTo, userToCanonical, userFromCanonical, channelCanonical, 
                   channelCanonical, userToCanonical))
        self.conn.commit()

        self.removeUserLogs(userFrom, channel)

    def userLogExists(self, username, channel, day, month, year):
        c = self.conn.cursor()
        args = (ircutils.toLower(username),ircutils.toLower(channel),day,month,year)
        c.execute('''SELECT COUNT(id) 
                     FROM triviauserlog 
                     WHERE username_canonical=? AND 
                           channel_canonical=? AND 
                           day=? AND 
                           month=? and 
                           year=?''', args)
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def userExists(self, username):
        c = self.conn.cursor()
        usr = (ircutils.toLower(username),)
        c.execute('''SELECT COUNT(id) 
                     FROM triviausers 
                     WHERE username_canonical=?''', usr)
        row = c.fetchone()
        c.close()
        return row[0] > 0

    def userLevelExists(self, username, channel):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(id) 
                     FROM trivialevel
                     WHERE username_canonical=? AND 
                           channel_canonical=?''',
                    (usernameCanonical, channelCanonical))
        row = c.fetchone()
        c.close()
        return row[0] > 0
        
    def updateLogin(self, username, salt, isHashed, password, capability):
        if not self.loginExists(username):
            return self.insertLogin(username, salt, isHashed, password, capability)
        usernameCanonical = ircutils.toLower(username)
        if not isHashed:
            isHashed = 0
        else:
            isHashed = 1
        c = self.conn.cursor()
        c.execute('''UPDATE trivialogin 
                     SET username=?, 
                         salt=?, 
                         is_hashed=?, 
                         password=?, 
                         capability=?
                     WHERE username_canonical=?''', 
                    (username, salt, isHashed, password, capability, usernameCanonical))
        self.conn.commit()
        c.close()

    def updateUserLog(self, username, channel, score, numAnswered, timeTaken, day=None, month=None, year=None, epoch=None):
        if not self.userExists(username):
            self.insertUser(username)
        if day == None and month == None and year == None:
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
        if epoch is None:
            epoch = int(time.mktime(time.localtime()))
        if not self.userLogExists(username, channel, day, month, year):
            return self.insertUserLog(username, channel, score, numAnswered, timeTaken, day, month, year, epoch)
        c = self.conn.cursor()
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        test = c.execute('''UPDATE triviauserlog 
                            SET username=?,
                                points_made=points_made+?,
                                average_time=(average_time*(1.0*num_answered/(num_answered+?))+?*(1.0*?/(num_answered+?))),
                                average_score=(average_score*(1.0*num_answered/(num_answered+?))+?*(1.0*?/(num_answered+?))),
                                num_answered=num_answered+?,
                                last_updated=?
                            WHERE username_canonical=? AND 
                                  channel_canonical=? AND 
                                  day=? AND 
                                  month=? AND 
                                  year=?''', 
                            (username, score, numAnswered, timeTaken, numAnswered, 
                             numAnswered, numAnswered, score, numAnswered, numAnswered, 
                             numAnswered, epoch, usernameCanonical, channelCanonical, 
                             day, month, year))
        self.conn.commit()
        c.close()

    def updateUser(self, username, numEditted=0, numEdittedAccepted=0, numReported=0, numQuestionsAdded=0, numQuestionsAccepted=0):
        if not self.userExists(username):
            return self.insertUser(username, numEditted, numEdittedAccepted, numReported, numQuestionsAdded, numQuestionsAccepted)
        usernameCanonical = ircutils.toLower(username)
        c = self.conn.cursor()
        c.execute('''UPDATE triviausers 
                     SET username=?, 
                         num_editted=num_editted+?, 
                         num_editted_accepted=num_editted_accepted+?, 
                         num_reported=num_reported+?, 
                         num_questions_added=num_questions_added+?, 
                         num_questions_accepted=num_questions_accepted+?
                     WHERE username_canonical=?''', 
                    (username, numEditted, numEdittedAccepted, numReported,
                     numQuestionsAdded, numQuestionsAccepted, usernameCanonical))
        self.conn.commit()
        c.close()

    def updateUserHighestStreak(self, username, streak):
        if not self.userExists(username):
            return self.insertUser(username)
        usernameCanonical = ircutils.toLower(username)
        c = self.conn.cursor()
        c.execute('''UPDATE triviausers 
                     SET highest_streak=?
                     WHERE highest_streak<? AND 
                           username_canonical=?''', 
                    (streak, streak, usernameCanonical))
        self.conn.commit()
        c.close()
    
    def updateUserLevel(self, username, channel, level):
        if not self.userLevelExists(username, channel):
            return self.insertUserLevel(username, channel, level)
            
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        
        c = self.conn.cursor()
        c.execute('''UPDATE trivialevel 
                     SET level=?
                     WHERE username_canonical=? AND 
                           channel_canonical=?''',
                    (level, usernameCanonical, channelCanonical))
        self.conn.commit()
        c.close()
        
    def updateGame(self, channel, numAsked):
        if not self.gameExists(channel):
            return self.insertGame(channel, numAsked)
        c = self.conn.cursor()
        channelCanonical = ircutils.toLower(channel)
        test = c.execute('''UPDATE triviagames 
                            SET channel=?,
                                num_asked=?
                            WHERE channel_canonical=?''', 
                            (channel, numAsked, channelCanonical))
        self.conn.commit()
        c.close()

    def updateGameLongestStreak(self, channel, lastWinner, streak):
        c = self.conn.cursor()
        channelCanonical = ircutils.toLower(channel)
        lastWinnerCanonical = ircutils.toLower(lastWinner)
        test = c.execute('''UPDATE triviagames 
                            SET longest_streak=?,
                                longest_streak_holder=?,
                                longest_streak_holder_canonical=?
                            WHERE channel_canonical=? AND 
                                  longest_streak<?''', 
                            (streak, lastWinner, lastWinnerCanonical, 
                             channelCanonical, streak))
        self.conn.commit()
        c.close()

    def updateGameStreak(self, channel, lastWinner, streak):
        if not self.gameExists(channel):
            return self.insertGame(channel, 0, None)
        c = self.conn.cursor()
        channelCanonical = ircutils.toLower(channel)
        test = c.execute('''UPDATE triviagames 
                            SET last_winner=?,
                                streak=?
                            WHERE channel_canonical=?''', 
                            (lastWinner, streak, channelCanonical))
        self.conn.commit()
        c.close()

    def updateGameRoundStarted(self, channel, lastRoundStarted):
        if not self.gameExists(channel):
            return self.insertGame(channel, numAsked)
        channelCanonical = ircutils.toLower(channel)
        c = self.conn.cursor()
        test = c.execute('''UPDATE triviagames 
                            SET round_started=?
                            WHERE channel_canonical=?''', 
                            (lastRoundStarted, channelCanonical))
        self.conn.commit()
        c.close()

    def updateQuestion(self, id, newQuestion):
        c = self.conn.cursor()
        test = c.execute('''UPDATE triviaquestion 
                            SET question=?
                            WHERE id=?''', 
                            (newQuestion, id))
        self.conn.commit()
        c.close()

    def updateQuestionStats(self, id, timesAnswered, timesMissed):
        c = self.conn.cursor()
        test = c.execute('''UPDATE triviaquestion 
                            SET num_answered=num_answered+?,
                                num_missed=num_missed+?
                            WHERE id=?''', 
                            (timesAnswered, timesMissed, id))
        self.conn.commit()
        c.close()

    def viewDayTop10(self, channel, numUpTo=10):
        numUpTo -= 10
        dateObject = datetime.date.today()
        day   = dateObject.day
        month = dateObject.month
        year  = dateObject.year

        query = '''SELECT id, 
                          username,
                          SUM(points_made) AS points,
                          SUM(num_answered) AS num
                   FROM triviauserlog
                   WHERE day=? AND 
                         month=? AND 
                         year=?'''
        arguments = [day, month, year]

        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical
                    ORDER BY points DESC LIMIT ?, 10''' % (query)
        arguments.append(numUpTo)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        rows = c.fetchall()
        c.close()
        return rows

    def viewAllTimeTop10(self, channel, numUpTo=10):
        numUpTo -= 10

        query = '''SELECT id, 
                          username,
                          SUM(points_made) AS points,
                          SUM(num_answered) AS num
                   FROM triviauserlog'''
        arguments = []

        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
            query = '''%s WHERE channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical
                    ORDER BY points DESC LIMIT ?, 10''' % (query)
        arguments.append(numUpTo)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        rows = c.fetchall()
        c.close()
        return rows

    def viewMonthTop10(self, channel, numUpTo=10, year=None, month=None):
        numUpTo -= 10
        d = datetime.date.today()
        if year is None or month is None:
            year = d.year
            month = d.month

        query = '''SELECT id, 
                          username,
                          SUM(points_made) AS points,
                          SUM(num_answered) AS num
                   FROM triviauserlog
                   WHERE month=? AND 
                         year=?'''
        arguments = [month, year]

        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical
                    ORDER BY points DESC LIMIT ?, 10''' % (query)
        arguments.append(numUpTo)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        rows = c.fetchall()
        c.close()
        return rows

    def viewYearTop10(self, channel, numUpTo=10, year=None):
        numUpTo -= 10
        d = datetime.date.today()
        if year is None:
            year = d.year

        query = '''SELECT id, 
                          username,
                          SUM(points_made) AS points,
                          SUM(num_answered) AS num
                   FROM triviauserlog
                   WHERE year=?'''
        arguments = [year]

        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical
                    ORDER BY points DESC LIMIT ?, 10''' % (query)
        arguments.append(numUpTo)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        rows = c.fetchall()
        c.close()
        return rows

    def viewWeekTop10(self, channel, numUpTo=10):
        numUpTo -= 10
        d = datetime.date.today()
        weekday=d.weekday()
        d -= datetime.timedelta(weekday)
        weekSqlString = ''
        for i in range(7):
            if i > 0:
                weekSqlString += ' or '
            weekSqlString += '''
                        (year=%d
                        AND month=%d
                        AND day=%d)''' % (d.year, d.month, d.day)
            d += datetime.timedelta(1)

        query = '''SELECT id, 
                          username, 
                          SUM(points_made) AS points,
                          SUM(num_answered) AS num 
                   FROM triviauserlog
                   WHERE (%s)''' % weekSqlString
        arguments = []

        if channel is not None:
            channelCanonical = ircutils.toLower(channel)
            query = '''%s AND channel_canonical=?''' % (query)
            arguments.append(channelCanonical)

        query = '''%s GROUP BY username_canonical
                    ORDER BY points DESC LIMIT ?, 10''' % (query)
        arguments.append(numUpTo)

        c = self.conn.cursor()
        c.execute(query, tuple(arguments))
        rows = c.fetchall()
        c.close()
        return rows

    def wasUserActiveIn(self, username, channel, timeSeconds):
        usernameCanonical = ircutils.toLower(username)
        channelCanonical = ircutils.toLower(channel)
        epoch = int(time.mktime(time.localtime()))
        dateObject = datetime.date.today()
        day   = dateObject.day
        month = dateObject.month
        year  = dateObject.year
        c = self.conn.cursor()
        c.execute('''SELECT count(*) 
                     FROM triviauserlog
                     WHERE day=? AND 
                           month=? AND 
                           year=? AND 
                           username_canonical=? AND 
                           channel_canonical=? AND 
                           last_updated>?''', 
                     (day, month, year, usernameCanonical, 
                      channelCanonical, epoch-timeSeconds))
        row = c.fetchone()
        c.close()
        return row[0] > 0


#A log wrapper, ripoff of ChannelLogger
class Logger:
    def __init__(self, base):
        self.logs = {}
        self.registryValue = base.registryValue

    def logNameTimestamp(self, channel):
        return time.strftime('%Y-%m-%d')

    def getLogName(self, channel):
        return '%s.%s.log' % (channel, self.logNameTimestamp(channel))

    def getLogDir(self, irc, channel):
        logDir = conf.supybot.directories.log.dirize('TriviaTime')
        logDir = os.path.join(logDir, irc.network)
        logDir = os.path.join(logDir, channel)
        timeDir = time.strftime('%B')
        logDir = os.path.join(logDir, timeDir)
        if not os.path.exists(logDir):
            os.makedirs(logDir)
        return logDir

    def timestamp(self, log):
        format = conf.supybot.log.timestampFormat()
        if format:
            log.write(time.strftime(format))
            log.write(' ')

    def checkLogNames(self):
        for (irc, logs) in self.logs.items():
            for (channel, log) in logs.items():
                name = self.getLogName(channel)
                if name != log.name:
                    log.close()
                    del logs[channel]

    def getLog(self, irc, channel):
        self.checkLogNames()
        try:
            logs = self.logs[irc]
        except KeyError:
            logs = ircutils.IrcDict()
            self.logs[irc] = logs
        if channel in logs:
            return logs[channel]
        else:
            try:
                name = self.getLogName(channel)
                logDir = self.getLogDir(irc, channel)
                log = file(os.path.join(logDir, name), 'a')
                logs[channel] = log
                return log
            except IOError:
                self.log.exception('Error opening log:')
                return self.FakeLog()

    def doLog(self, irc, channel, s, *args):
        if not self.registryValue('general.logGames'):
            return
        s = format(s, *args)
        channel = self.normalizeChannel(irc, channel)
        log = self.getLog(irc, channel)
        self.timestamp(log)
        s = ircutils.stripFormatting(s)
        log.write(s)
        log.write('\n')
        log.flush()

    def normalizeChannel(self, irc, channel):
        return ircutils.toLower(channel)

    class FakeLog(object):
        def flush(self):
            return
        def close(self):
            return
        def write(self, s):
            return        


class TriviaTime(callbacks.Plugin):
    """
    TriviaTime - An enhanced multiplayer and multichannel trivia game for Supybot.
    Includes KAOS: work together to get all the answers before time runs out.
    """
    threaded = True # enables threading for supybot plugin
    currentDBVersion = 1.2

    def __init__(self, irc):
        log.info('** TriviaTime loaded! **')
        self.__parent = super(TriviaTime, self)
        self.__parent.__init__(irc)

        # games info
        self.games = {} # separate game for each channel
        self.voiceTimeouts = TimeoutList(self.registryValue('voice.timeoutVoice'))

        #Database amend statements for outdated versions
        self.dbamends = {} #Formatted like this: <DBVersion>: "<ALTERSTATEMENT>; <ALTERSTATEMENT>;" (This IS valid SQL as long as we include the semicolons)

        #logger
        self.logger = Logger(self)

        # connections
        dbLocation = self.registryValue('admin.db')
        # tuple head, tail ('example/example/', 'filename.txt')
        dbFolder = os.path.split(dbLocation)
        # take folder from split
        dbFolder = dbFolder[0]
        # create the folder
        if not os.path.exists(dbFolder):
            log.info('The database location did not exist, creating folder structure')
            os.makedirs(dbFolder)
        self.storage = Storage(dbLocation)
        #self.storage.dropActivityTable()
        self.storage.makeActivityTable()
        #self.storage.dropUserLogTable()
        self.storage.makeUserLogTable()
        #self.storage.dropGameTable()
        self.storage.makeGameTable()
        #self.storage.dropGameLogTable()
        self.storage.makeGameLogTable()
        #self.storage.dropUserTable()
        self.storage.makeUserTable()
        #self.storage.dropLoginTable()
        self.storage.makeLoginTable()
        #self.storage.dropReportTable()
        self.storage.makeReportTable()
        #self.storage.dropQuestionTable()
        self.storage.makeQuestionTable()
        #self.storage.dropTemporaryQuestionTable()
        self.storage.makeTemporaryQuestionTable()
        #self.storage.dropEditTable()
        self.storage.makeEditTable()
        #self.storage.dropDeleteTable()
        self.storage.makeDeleteTable()
        self.storage.makeInfoTable()
        #self.storage.makeLevelTable()
        #self.storage.dropLevelTable()
        #triviainfo table check
        #if self.storage.isTriviaVersionSet():
        if self.storage.getVersion() != None and self.storage.getVersion() != self.currentDBVersion:
            return

    def _games(self):
        for (network, games) in self.games.items():
            for (channel, game) in games.items():
                yield game

    def die(self):
        for game in self._games():
            game.stop()

    def reset(self):
        for game in self._games():
            game.stop()

    def doPrivmsg(self, irc, msg):
        """
            Catches all PRIVMSG, including channels communication
        """
        username = self.getUsername(msg.nick, msg.prefix)
        usernameCanonical = ircutils.toLower(username)
        channel = msg.args[0]
        # Make sure that it is starting inside of a channel, not in pm
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        channelCanonical = ircutils.toLower(channel)

        extraHintCommand  = self.registryValue('commands.extraHint', channel)
        extraHintTime = self.registryValue('hints.extraHintTime', channel)
        game = self.getGame(irc, channel)

        if game and game.state == 'in-question':
            if msg.args[1] == extraHintCommand: # Check for extra hint command
                if game.questionType == 'kaos':
                    game.getRemainingKAOS()
                else:
                    if self.registryValue('hints.enableExtraHints', channel):
                        game.hintTimeoutList.setTimeout(extraHintTime)
                        if game.hintTimeoutList.has(usernameCanonical):
                            self.reply(irc, msg, 'You must wait %d seconds to be able to use the extra hint command.' % (game.hintTimeoutList.getTimeLeft(usernameCanonical)), notice=True)
                        else:
                            game.hintTimeoutList.append(usernameCanonical)
                            game.getExtraHint()
            else: # Check the answer
                game.checkAnswer(msg)

    def doJoin(self, irc, msg):
        username = self.getUsername(msg.nick, msg.prefix)
        channel = msg.args[0]
        self.handleVoice(irc, msg.nick, username, channel)

    def doNotice(self, irc, msg):
        username = msg.nick
        if msg.args[1][1:5] == "PING":
            pingMsg = msg.args[1][6:]
            pingMsg = pingMsg[:-1]
            pingMsg = pingMsg.split('*', 1)
            if len(pingMsg) == 2:
                pingTime = time.time()-float(pingMsg[0])-1300000000
                channelHash = pingMsg[1]
                channel = ''
                for name in irc.state.channels:
                    if channelHash == self.shortHash(ircutils.toLower(name)):
                        if username in irc.state.channels[name].users:
                            channel = name
                            break
                if channel == '':
                    irc.sendMsg(ircmsgs.notice(username, 'Ping reply: %0.2f seconds' % (pingTime)))
                else:
                    irc.sendMsg(ircmsgs.privmsg(channel, '%s: Ping reply: %0.2f seconds' % (username, pingTime)))

    def voiceUser(self, irc, nick, username, channel):
        usernameCanonical = ircutils.toLower(username)
        irc.queueMsg(ircmsgs.voice(channel, nick))
        self.voiceTimeouts.append(usernameCanonical)
        
    #The following functions are not ready and still in testing. Actually, they haven't even been tested yet. Use at your own risk.
    """
    def checkLevel(self, irc, nick, username, channel):
        levels = {0:"noob", 1:"Guesser", 2:"Student", 3:"Player", 4:"Master", 5:"Genius", 6:"Distinguished", 7:"Addicted", 8:"Elite", 9:"KAOTIC", 10:"Trivia God"}
        levelMinQuestions = {0:1, 1:50, 2:137, 3:301, 4:500, 5:789, 6:1002, 7:1519, 8:1899, 9:2133, 10:2544}
        usernameCanonical = ircutils.toLower(username)
        if userLevelExists(usernameCanonical):
            currentLevel = getUserLevel(username)
            nextLevel = currentLevel + 1
            if questionsAnswered(usernameCanonical) >= nextLevel(questionCount):
                changeLevel(nextLevel)
        else:
            levelUp()
        
        def levelUp():
        if questionsAnswered(usernameCanonical) > levelMinQuestions[10]:
            changeLevel(10)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[9]:
            changeLevel(9)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[8]:
            changeLevel(8)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[7]:
            changelevel(7)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[6]:
            changelevel(6)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[5]:
            changelevel(5)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[4]
            changelevel(4)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[3]:
            changelevel(3)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[2]:
            changelevel(2)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[1]:
            changelevel(1)
        elif questionsAnswered(usernameCanonical) > levelMinQuestions[0]:
            changelLevel(0)

        Storage.getUserStat()

    def changeLevel(self, irc, nick, username, channel):
        usernameCanonical = ircutils.toLower(username)
        USERLEVEL = NEWUSERLEVEL
        irc.sendMsg(ircmsgs.privmsg(channel, 'Congratulations %s, you\'ve answered %d questions and leveled up to %s!' % (username, questionsAnswered(usernameCanonical), levels[newlevel])))
         #reward points levelMinQuestions[level] * 5
        if self.registryValue('general.globalStats'):
            stat = threadStorage.getUserStat(username, None)
        else:
            stat = threadStorage.getUserStat(username, channel)
        
        """
    def handleVoice(self, irc, nick, username, channel):
        if not self.registryValue('voice.enableVoice'):
            return

        timeoutVoice = self.registryValue('voice.timeoutVoice')
        self.voiceTimeouts.setTimeout(timeoutVoice)
        usernameCanonical = ircutils.toLower(username)
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            stat = threadStorage.getUserStat(username, None)
            rank = threadStorage.getUserRank(username, None)
        else:
            stat = threadStorage.getUserStat(username, channel)
            rank = threadStorage.getUserRank(username, channel)
        
        if stat and not self.voiceTimeouts.has(usernameCanonical):
            numTopToVoice = self.registryValue('voice.numTopToVoice')
            minPointsVoiceYear = self.registryValue('voice.minPointsVoiceYear')
            minPointsVoiceMonth = self.registryValue('voice.minPointsVoiceMonth')
            minPointsVoiceWeek = self.registryValue('voice.minPointsVoiceWeek')
        
            if rank['year'] <= numTopToVoice and stat['points_year'] >= minPointsVoiceYear:
                self.voiceUser(irc, nick, username, channel)
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving voice to %s for being MVP this YEAR (#%d)' % (nick, rank['year'])))
            elif rank['month'] <= numTopToVoice and stat['points_month'] >= minPointsVoiceMonth:
                self.voiceUser(irc, nick, username, channel)
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving voice to %s for being MVP this MONTH (#%d)' % (nick, rank['month'])))
            elif rank['week'] <= numTopToVoice and stat['points_week'] >= minPointsVoiceWeek:
                self.voiceUser(irc, nick, username, channel)
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving voice to %s for being MVP this WEEK (#%d)' % (nick, rank['week'])))

    def addZeroWidthSpace(self, text):
        if len(text) <= 1:
            return text
        s = u'%s\u200b%s' % (text[:1], text[1:])
        return s.encode('utf-8')

    def shortHash(self, text):
        hashText = hashlib.sha1(text).hexdigest()
        hashText = self.numToBase94(int(hashText, 16), 8)
        return hashText

    def numToBase94(self, n, maxChars):
        chars = '!"#$%&\'() +,-./0123456789:;<=>?@ABCDEFGHUJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
        L = []
        for i in range(maxChars):
            L.append(chars[n % len(chars)])
            n = int(n / len(chars))
        return ''.join(L)

    def addActivity(self, activityType, activityText, channel, irc, storage=None):
        if storage is None:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
        else:
            threadStorage = storage
        threadStorage.removeOldActivity()
        threadStorage.insertActivity(activityType, activityText, channel, irc.network)

    def deleteGame(self, irc, channel):
        channelCanonical = ircutils.toLower(channel)
        if irc.network in self.games:
            if channelCanonical in self.games[irc.network]:
                del self.games[irc.network][channelCanonical]
                if len(self.games[irc.network]) < 1:
                    del self.games[irc.network]

    def createGame(self, irc, channel):
        if irc.network not in self.games:
            self.games[irc.network] = {}
        channelCanonical = ircutils.toLower(channel)
        newGame = Game(irc, channel, self)
        if newGame.active == True:
            self.games[irc.network][channelCanonical] = newGame

    def getGame(self, irc, channel):
        channelCanonical = ircutils.toLower(channel)
        if irc.network in self.games:
            if channelCanonical in self.games[irc.network]:
                return self.games[irc.network][channelCanonical]
        return None

    def isTriviaMod(self, hostmask, channel):
        channel = ircutils.toLower(channel)
        cap = self.getTriviaCapability(hostmask, channel)
        return cap in ['{0},{1}'.format(channel,'triviamod'), 
                       '{0},{1}'.format(channel,'triviaadmin'), 'owner']
    
    def isTriviaAdmin(self, hostmask, channel):
        channel = ircutils.toLower(channel)
        cap = self.getTriviaCapability(hostmask, channel)
        return cap in ['{0},{1}'.format(channel,'triviaadmin'), 'owner']
                
    def getTriviaCapability(self, hostmask, channel):
        if ircdb.users.hasUser(hostmask):
            channel = ircutils.toLower(channel)
            caps = list(ircdb.users.getUser(hostmask).capabilities)
            triviamod = '{0},{1}'.format(channel,'triviamod')
            triviaadmin = '{0},{1}'.format(channel,'triviaadmin')
            
            # If multiple capabilities exist, pick the most important
            if 'owner' in caps:
                return 'owner'
            elif triviaadmin in caps:
                return triviaadmin
            elif triviamod in caps:
                return triviamod
            else:
                return 'user'
                
        return None
    
    def getUsername(self, nick, hostmask):
        username = nick
        try:
            #rootcoma!~rootcomaa@unaffiliated/rootcoma
            user = ircdb.users.getUser(hostmask) 
            username = user.name
        except KeyError:
            pass
        return username    
        
    def reply(self, irc, msg, outstr, notice=False, prefixNick=True):
        if ircutils.isChannel(msg.args[0]) and not notice:
            target = msg.args[0]
        else:
            target = msg.nick
        
        if notice:
            output = ircmsgs.notice
        else:
            output = ircmsgs.privmsg
        
        if prefixNick == False or ircutils.isNick(target):
            irc.sendMsg(output(target, outstr))
        else:
            irc.sendMsg(output(target, '%s: %s' % (msg.nick, outstr)))
        irc.noReply()
    
    def acceptdelete(self, irc, msg, arg, channel, num):
        """[<channel>] <num>
        Accept a question deletion.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        username = self.getUsername(msg.nick, hostmask)
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            delete = threadStorage.getDeleteById(num)
        else:
            delete = threadStorage.getDeleteById(num, channel)
            
        if delete:
            if username == delete['username']:
                irc.reply('You cannot accept your own deletion request.')
            else:
                questionNumber = delete['line_num']
                irc.reply('Question #%d deleted!' % questionNumber)
                threadStorage.removeReportByQuestionNumber(questionNumber)
                threadStorage.removeEditByQuestionNumber(questionNumber)
                threadStorage.deleteQuestion(questionNumber)
                threadStorage.removeDelete(num)
                threadStorage.removeDeleteByQuestionNumber(questionNumber)
                self.logger.doLog(irc, channel, "%s accepted delete# %i, question #%i deleted" % (msg.nick, num, questionNumber))
                activityText = '%s deleted a question, approved by %s' % (delete['username'], msg.nick)
                self.addActivity('delete', activityText, channel, irc, threadStorage)
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find delete #{0}.'.format(num))
            else:
                irc.error('Unable to find delete #{0} in {1}.'.format(num, channel))
    acceptdelete = wrap(acceptdelete, ['channel', 'int'])
        
    def acceptedit(self, irc, msg, arg, channel, num):
        """[<channel>] <num>
        Accept a question edit, and remove edit. 
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        username = self.getUsername(msg.nick, hostmask)
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            edit = threadStorage.getEditById(num)
        else:
            edit = threadStorage.getEditById(num, channel)
            
        if edit:
            if username == edit['username']:
                irc.reply('You cannot accept your own edit.')
            else:
                question = threadStorage.getQuestionById(edit['question_id'])
                questionOld = question['question'] if question else ''
                threadStorage.updateQuestion(edit['question_id'], edit['question'])
                threadStorage.updateUser(edit['username'], 0, 1)
                threadStorage.removeEdit(edit['id'])
                threadStorage.removeReportByQuestionNumber(edit['question_id'])
                
                irc.reply('Question #%d updated!' % edit['question_id'])
                self.logger.doLog(irc, channel, "%s accepted edit# %i, question #%i edited NEW: '%s' OLD '%s'" % (msg.nick, num, edit['question_id'], edit['question'], questionOld))
                activityText = '%s edited a question, approved by %s' % (edit['username'], msg.nick)
                self.addActivity('edit', activityText, channel, irc, threadStorage)
                irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (edit['question'])))
                if questionOld != '':
                    irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (questionOld)))
                else:
                    irc.error('Question could not be found for this edit')
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find edit #{0}.'.format(num))
            else:
                irc.error('Unable to find edit #{0} in {1}.'.format(num, channel))
    acceptedit = wrap(acceptedit, ['channel', 'int'])

    def acceptnew(self, irc, msg, arg, channel, num):
        """[<channel>] <num>
        Accept a new question, and add it to the database. 
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        username = self.getUsername(msg.nick, hostmask)
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            q = threadStorage.getTemporaryQuestionById(num)
        else:
            q = threadStorage.getTemporaryQuestionById(num, channel)
            
        if q:
            if username == q['username']:
                irc.reply('You cannot accept your own new question.')
            else:
                threadStorage.updateUser(q['username'], 0, 0, 0, 0, 1)
                threadStorage.insertQuestionsBulk([(q['question'], q['question'])])
                threadStorage.removeTemporaryQuestion(q['id'])
                irc.reply('Question accepted!')
                self.logger.doLog(irc, channel, "%s accepted new question #%i, '%s'" % (msg.nick, num, q['question']))
                activityText = '%s added a new question, approved by %s' % (q['username'], msg.nick)
                self.addActivity('new', activityText, channel, irc, threadStorage)
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find new question #{0}.'.format(num))
            else:
                irc.error('Unable to find new question #{0} in {1}.'.format(num, channel))
    acceptnew = wrap(acceptnew, ['channel', 'int'])

    def add(self, irc, msg, arg, user, channel, question):
        """[<channel>] <question text>
        Adds a question to the database.
        Channel is only required when using the command outside of a channel.
        """
        username = msg.nick
        charMask = self.registryValue('hints.charMask', channel)
        if charMask not in question:
            irc.error('The question must include the separating character %s ' % (charMask))
            return
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        threadStorage.updateUser(username, 0, 0, 0, 1)
        threadStorage.insertTemporaryQuestion(username, channel, question)
        irc.reply('Thank you for adding your question to the question database, it is awaiting approval. ')
        self.logger.doLog(irc, channel, "%s added new question: '%s'" % (username, question))
    add = wrap(add, ['user', 'channel', 'text'])

    def addfile(self, irc, msg, arg, filename):
        """[<filename>]
        Add a file of questions to the question database, 
        filename defaults to configured question file.
        """
        if filename is None:
            filename = self.registryValue('admin.file')
        try:
            filesLines = open(filename).readlines()
        except:
            irc.error('Could not open file to add to database. Make sure it exists on the server.')
            return
        irc.reply('Adding questions from %s to database.. This may take a few minutes' % filename)
        insertList = []
        channel = msg.args[0]
        for line in filesLines:
            insertList.append((str(line).strip(),str(line).strip()))
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        info = threadStorage.insertQuestionsBulk(insertList)
        irc.reply('Successfully added %d questions, skipped %d' % (info[0], info[1]))
        self.logger.doLog(irc, channel, "%s added question file: '%s', added: %i, skipped: %i" % (msg.nick, filename, info[0], info[1]))
    addfile = wrap(addfile, ['owner', optional('text')])

    def authweb(self, irc, msg, arg, channel):
        """[<channel>]
        This registers triviamods and triviaadmins on the website. 
        Use this command again if the account password has changed.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        capability = self.getTriviaCapability(hostmask, channel)
        if capability is None or capability == 'user':
            irc.reply('You must be a TriviaMod in {0} to use this command.'.format(channel))
            return

        user = ircdb.users.getUser(hostmask)
        salt = ''
        password = ''
        isHashed = user.hashed
        if isHashed:
            (salt, password) = user.password.split('|')
        else:
            password = user.password

        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        info = threadStorage.insertLogin(user.name, salt, isHashed, password, capability)
        irc.reply('Success, updated your web access login.')
        self.logger.doLog(irc, channel, "%s authed for web access" % (user.name))
    authweb = wrap(authweb, ['channel'])

    def clearpoints(self, irc, msg, arg, channel, username):
        """[<channel>] <username>
        Deletes all of a users points, and removes all their records.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaAdmin(hostmask, channel) == False:
            irc.reply('You must be a TriviaAdmin in {0} to use this command.'.format(channel))
            return
            
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        threadStorage.removeUserLogs(username, channel)
        irc.reply('Removed all points from {0} in {1}.'.format(username, channel))
        self.logger.doLog(irc, channel, '{0} cleared points for {1} in {2}.'.format(msg.nick, username, channel))
    clearpoints = wrap(clearpoints, ['channel', 'nick'])

    def day(self, irc, msg, arg, channel, num):
        """[<channel>] [<number>]
            Displays the top scores of the day. 
            Parameter is optional, display up to that number. (eg 20 - display 11-20)
            Channel is only required when using the command outside of a channel.
        """
        num = max(num, 10)
        offset = num-9
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewDayTop10(None, num)
        else:
            tops = threadStorage.viewDayTop10(channel, num)
        
        topsList = ['Today\'s Top {0}-{1} Players: '.format(offset, num)]
        if tops:
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
        else:
            topsList.append('No players')
        topsText = ''.join(topsList)
        self.reply(irc, msg, topsText, prefixNick=False)
    day = wrap(day, ['channel', optional('int')])

    def delete(self, irc, msg, arg, user, channel, t, id, reason):
        """[<channel>] [<type "R" or "Q">] <question id> [<reason>]
        Deletes a question from the database. Type decides whether to delete
        by round number (r), or question number (q) (default round).
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        username = self.getUsername(msg.nick, hostmask)
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        
        # Search for question ID if deletion is by 'round'
        if t is None or str.lower(t) == "round":
            q = threadStorage.getQuestionByRound(id, channel)
            if q:
                id = q['id']
            else:
                irc.error('Could not find that round #{0}.'.format(id))
                return
            
        if not threadStorage.questionIdExists(id):
            irc.error('That question does not exist.')
        elif threadStorage.isQuestionDeleted(id):
            irc.error('That question is already deleted.')
        elif threadStorage.isQuestionPendingDeletion(id):
            irc.error('That question is already pending deletion.')
        else:
            threadStorage.insertDelete(username, channel, id, reason)
            irc.reply('Question %d marked for deletion and pending review.' % id)
            self.logger.doLog(irc, channel, "%s marked question #%i for deletion" % (username, id))
    delete = wrap(delete, ['user', 'channel', optional(('literal',("question", "QUESTION", "ROUND", "round"))),'int', optional('text')])

    def edit(self, irc, msg, arg, user, channel, num, question):
        """[<channel>] <question number> <corrected text>
        Correct a question by providing the question number and the corrected text. 
        Channel is only required when using the command outside of a channel.
        """
        username = self.getUsername(msg.nick, msg.prefix)
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        q = threadStorage.getQuestionById(num)
        if q:
            questionParts = question.split('*')
            if len(questionParts) < 2:
                oldQuestionParts = q['question'].split('*')
                questionParts.extend(oldQuestionParts[1:])
                question = questionParts[0]
                for part in questionParts[1:]:
                    question += '*'
                    question += part
            if question == q['question']:
                irc.error('Your edit does not change the original question.')
            else:
                threadStorage.insertEdit(num, question, username, channel)
                threadStorage.updateUser(username, 1, 0)
                irc.reply('Success! Submitted edit for further review.')
                irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (question)))
                irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (q['question'])))
                self.logger.doLog(irc, channel, "%s edited question #%i: OLD: '%s' NEW: '%s'" % (username, num, q['question'], question))
        else:
            irc.error('Question does not exist')
    edit = wrap(edit, ['user', 'channel', 'int', 'text'])

    def givepoints(self, irc, msg, arg, channel, username, points, days):
        """[<channel>] <username> <points> [<daysAgo>]
        Give a user points, last argument is optional amount of days in past to add records.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaAdmin(hostmask, channel) == False:
            irc.reply('You must be a TriviaAdmin in {0} to use this command.'.format(channel))
            return
        elif points == 0:
            irc.error("You cannot give 0 points.")
            return
        
        username = self.getUsername(username, username)
        day=None
        month=None
        year=None
        if days is not None:
            d = datetime.date.today()
            d -= datetime.timedelta(days)
            day = d.day
            month = d.month
            year = d.year
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        threadStorage.updateUserLog(username, channel, points, 0, 0, day, month, year)
        irc.reply('Added {0} points to {1} in {2}.'.format(points, username, channel))
        self.logger.doLog(irc, channel, '{0} gave {1} points to {2} in {3}.'.format(msg.nick, points, username, channel))
    givepoints = wrap(givepoints, ['channel', 'nick', 'int', optional('int')])

    def listdeletes(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List questions pending deletion.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countDeletes()
        else:
            count = threadStorage.countDeletes(channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            deletes = threadStorage.getDeleteTop3(page)
        else:
            deletes = threadStorage.getDeleteTop3(page, channel=channel)
            
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No deletes found.')
            else:
                irc.reply('No deletes found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for delete in deletes:
                question = threadStorage.getQuestionById(delete['line_num'])
                questionText = question['question'] if question else 'Question not found'
                irc.reply('Delete #%d, by %s Question #%d: %s, Reason:%s'%(delete['id'], delete['username'], delete['line_num'], questionText, delete['reason']))
            irc.reply('Use the showdelete command to see more information')
    listdeletes = wrap(listdeletes, ['channel', optional('int')])

    def listalledits(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List all edits pending approval (even your own).
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countEdits()
        else:
            count = threadStorage.countEdits(channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            edits = threadStorage.getEditTop3(page)
        else:
            edits = threadStorage.getEditTop3(page, channel=channel)
            
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No edits found.')
            else:
                irc.reply('No edits found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for edit in edits:
                irc.reply('Edit #%d, Question #%d, NEW:%s'%(edit['id'], edit['question_id'], edit['question']))
            irc.reply('Use the showedit command to see more information')
    listalledits = wrap(listalledits, ['channel', optional('int')])

    def listmyedits(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List only your own edits pending approval.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        username = self.getUsername(msg.nick, msg.prefix)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countMyEdits(username)
        else:
            count = threadStorage.countMyEdits(username, channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            edits = threadStorage.getMyEditTop3(username, page)
        else:
            edits = threadStorage.getMyEditTop3(username, page, channel=channel)
            
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No edits found.')
            else:
                irc.reply('No edits found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for edit in edits:
                irc.reply('Edit #%d, Question #%d, NEW:%s'%(edit['id'], edit['question_id'], edit['question']))
            irc.reply('Use the showedit command to see more information')
    listmyedits = wrap(listmyedits, ['channel', optional('int')])

    def listedits(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List edits pending approval (by default does not include your own edits)
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        username = self.getUsername(msg.nick, msg.prefix)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countNotMyEdits(username)
        else:
            count = threadStorage.countNotMyEdits(username, channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            edits = threadStorage.getNotMyEditTop3(username, page)
        else:
            edits = threadStorage.getNotMyEditTop3(username, page, channel=channel)
            
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No edits found.')
            else:
                irc.reply('No edits found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for edit in edits:
                irc.reply('Edit #%d, Question #%d, NEW:%s'%(edit['id'], edit['question_id'], edit['question']))
            irc.reply('Use the showedit command to see more information')
    listedits = wrap(listedits, ['channel', optional('int')])

    def listreports(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List reports pending edit.
        Channel is only required when using the command outside of a channel.
        """
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countReports()
        else:
            count = threadStorage.countReports(channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            reports = threadStorage.getReportTop3(page)
        else:
            reports = threadStorage.getReportTop3(page, channel=channel)
        
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No reports found.')
            else:
                irc.reply('No reports found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for report in reports:
                irc.reply('Report #%d \'%s\' by %s on %s Q#%d '%(report['id'], report['report_text'], report['username'], report['channel'], report['question_num']))
            irc.reply('Use the showreport command to see more information')
    listreports = wrap(listreports, ['user', 'channel', optional('int')])

    def listnew(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List questions awaiting approval.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            count = threadStorage.countTemporaryQuestions()
        else:
            count = threadStorage.countTemporaryQuestions(channel)
        pages = int(count / 3) + int(count % 3 > 0)
        page = max(1, min(page, pages))
        if self.registryValue('general.globalstats'):
            q = threadStorage.getTemporaryQuestionTop3(page)
        else:
            q = threadStorage.getTemporaryQuestionTop3(page, channel=channel)
        
        # Output list
        if count < 1:
            if self.registryValue('general.globalstats'):
                irc.reply('No new questions found.')
            else:
                irc.reply('No new questions found in {0}.'.format(channel))
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for ques in q:
                irc.reply('Temp Q #%d: %s'%(ques['id'], ques['question']))
            irc.reply('Use the shownew to see more information')
    listnew = wrap(listnew, ['channel', optional('int')])

    def info(self, irc, msg, arg, channel):
        """[<channel>]
        Get TriviaTime information, how many questions/users in database, time, etc.
        Channel is only required when using the command outside of a channel.
        """
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        totalUsersEver = threadStorage.getNumUser(channel)
        numActiveThisWeek = threadStorage.getNumActiveThisWeek(channel)
        infoText = ' TriviaTime v1.3.2 by Trivialand on Freenode: https://github.com/tannn/TriviaTime '
        self.reply(irc, msg, infoText, prefixNick=False)
        infoText = '\x02 %d Users\x02 on scoreboard with \x02%d Active This Week\x02' % (totalUsersEver, numActiveThisWeek)
        self.reply(irc, msg, infoText, prefixNick=False)
        numKaos = threadStorage.getNumKAOS()
        numQuestionTotal = threadStorage.getNumQuestions()
        infoText = '\x02 %d Questions\x02 and \x02%d KAOS\x02 (\x02%d Total\x02) in the database ' % ((numQuestionTotal-numKaos), numKaos, numQuestionTotal)
        self.reply(irc, msg, infoText, prefixNick=False)
    info = wrap(info, ['channel'])

    def ping(self, irc, msg, arg):
        """
            Check your ping time to the bot. The client must respond correctly to pings.
        """
        channel = msg.args[0]
        channelHash = self.shortHash(ircutils.toLower(channel))
        username = msg.nick
        irc.sendMsg(ircmsgs.privmsg(username, '\x01PING %0.2f*%s\x01' % (time.time()-1300000000, channelHash)))
    ping = wrap(ping)

    def me(self, irc, msg, arg, channel):
        """[<channel>]
            Get your rank, score & questions asked for day, month, year.
            Channel is only required when using the command outside of a channel.
        """
        username = self.getUsername(msg.nick, msg.prefix)
        identified = ircdb.users.hasUser(msg.prefix)
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        
        if self.registryValue('general.globalStats'):
            stat = threadStorage.getUserStat(username, None)
            rank = threadStorage.getUserRank(username, None)
        else:
            stat = threadStorage.getUserStat(username, channel)
            rank = threadStorage.getUserRank(username, channel)
            
        if not stat:
            errorMessage = 'You do not have any points.'
            identifyMessage = ''
            if not identified:
                identifyMessage = ' You should identify to keep track of your score more accurately.'
            irc.reply('%s%s' % (errorMessage, identifyMessage))
        else:
            hasPoints = False
            infoList = ['%s\'s Stats: Points (answers)' % (self.addZeroWidthSpace(stat['username']))]
            if rank['day'] > 0 or stat['points_day'] > 0 or stat['answer_day'] > 0:
                hasPoints = True
                infoList.append(' \x02Today:\x02 #%d %d (%d)' % (rank['day'], stat['points_day'], stat['answer_day']))
            if rank['week'] > 0 or stat['points_week'] > 0 or stat['answer_week'] > 0:
                hasPoints = True
                infoList.append(' \x02This Week:\x02 #%d %d (%d)' % (rank['week'], stat['points_week'], stat['answer_week']))
            if rank['month'] > 0 or stat['points_month'] > 0 or stat['answer_week'] > 0:
                hasPoints = True
                infoList.append(' \x02This Month:\x02 #%d %d (%d)' % (rank['month'], stat['points_month'], stat['answer_month']))
            if rank['year'] > 0 or stat['points_year'] > 0 or stat['answer_year'] > 0:
                hasPoints = True
                infoList.append(' \x02This Year:\x02 #%d %d (%d)' % (rank['year'], stat['points_year'], stat['answer_year']))
            if not hasPoints:
                infoList = ['%s: You do not have any points.' % (username)]
                if not identified:
                    infoList.append(' You should identify to keep track of your score more accurately.')
            infoText = ''.join(infoList)
            self.reply(irc, msg, infoText, prefixNick=False)
    me = wrap(me, ['channel'])

    def month(self, irc, msg, arg, channel, num):
        """[<channel>] [<number>] 
            Displays the top ten scores of the month. 
            Parameter is optional, display up to that number. (eg 20 - display 11-20)
            Channel is only required when using the command outside of a channel.
        """
        num = max(num, 10)
        offset = num-9
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewMonthTop10(None, num)
        else:
            tops = threadStorage.viewMonthTop10(channel, num)
        
        topsList = ['This Month\'s Top {0}-{1} Players: '.format(offset, num)]
        if tops:
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
        else:
            topsList.append('No players')
        topsText = ''.join(topsList)
        self.reply(irc, msg, topsText, prefixNick=False)
    month = wrap(month, ['channel', optional('int')])

    def next(self, irc, msg, arg, channel):
        """
        Skip to the next question immediately.
        This can only be used by a user with a certain streak, set in the config.
        """
        username = self.getUsername(msg.nick, msg.prefix)
        minStreak = self.registryValue('general.nextMinStreak', channel)
        game = self.getGame(irc, channel)

        # Sanity checks
        # 1. Is trivia running?
        # 2. Is question is still being asked?
        # 3. Is caller the streak holder?
        # 4. Is streak high enough?
        if game is None or game.active == False:
            self.reply(irc, msg, 'Trivia is not currently running.')
        elif game.state != 'no-question':
            self.reply(irc, msg, 'You must wait until the current question is over.')
        elif ircutils.toLower(game.lastWinner) != ircutils.toLower(username):
            self.reply(irc, msg, 'You are not currently the streak holder.')
        elif game.streak < minStreak:
            self.reply(irc, msg, 'You do not have a large enough streak yet (%i of %i).' % (game.streak, minStreak))
        else:
            game.removeEvent()
            self.reply(irc, msg, 'Onto the next question!', prefixNick=False)
            game.nextQuestion()
    next = wrap(next, ['onlyInChannel'])

    def rmedit(self, irc, msg, arg, channel, num):
        """[<channel>] <int>
        Deny a question edit.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            edit = threadStorage.getEditById(num)
        else:
            edit = threadStorage.getEditById(num, channel)
            
        if edit:
            threadStorage.removeEdit(edit['id'])
            irc.reply('Edit %d removed!' % edit['id'])
            self.logger.doLog(irc, channel, "%s removed edit# %i, for question #%i, text: %s" % (msg.nick, edit['id'], edit['question_id'], edit['question']))
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find edit #{0}.'.format(num))
            else:
                irc.error('Unable to find edit #{0} in {1}.'.format(num, channel))
    rmedit = wrap(rmedit, ['channel', 'int'])

    def rmdelete(self, irc, msg, arg, channel, num):
        """[<channel>] <int>
        Deny a deletion request.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            delete = threadStorage.getDeleteById(num)
        else:
            delete = threadStorage.getDeleteById(num, channel)
            
        if delete:
            threadStorage.removeDelete(num)
            irc.reply('Delete %d removed!' % num)
            self.logger.doLog(irc, channel, "%s removed delete# %i, for question #%i, reason was '%s'" % (msg.nick, num, delete['line_num'], delete['reason']))
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find delete #{0}.'.format(num))
            else:
                irc.error('Unable to find delete #{0} in {1}.'.format(num, channel))
    rmdelete = wrap(rmdelete, ['channel', 'int'])

    def rmreport(self, irc, msg, arg, channel, num):
        """[<channel>] <report num>
        Delete a report.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            report = threadStorage.getReportById(num)
        else:
            report = threadStorage.getReportById(num, channel)
            
        if report:
            threadStorage.removeReport(report['id'])
            irc.reply('Report %d removed!' % report['id'])
            self.logger.doLog(irc, channel, "%s removed report# %i, for question #%i text was %s" % (msg.nick, report['id'], report['question_num'], report['report_text']))
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find report #{0}.'.format(num))
            else:
                irc.error('Unable to find report #{0} in {1}.'.format(num, channel))
    rmreport = wrap(rmreport, ['channel', 'int'])

    def rmnew(self, irc, msg, arg, channel, num):
        """[<channel>] <int>
        Deny a new question.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            q = threadStorage.getTemporaryQuestionById(num)
        else:
            q = threadStorage.getTemporaryQuestionById(num, channel)
        
        if q:
            threadStorage.removeTemporaryQuestion(q['id'])
            irc.reply('Temp question #%d removed!' % q['id'])
            self.logger.doLog(irc, channel, "%s removed new question #%i, '%s'" % (msg.nick, q['id'], q['question']))
        else:
            if self.registryValue('general.globalstats'):
                irc.error('Unable to find new question #{0}.'.format(num))
            else:
                irc.error('Unable to find new question #{0} in {1}.'.format(num, channel))
    rmnew = wrap(rmnew, ['channel', 'int'])

    def repeat(self, irc, msg, arg, channel):
        """
        Repeat the current question.
        """
        game = self.getGame(irc, channel)
        
        # Sanity checks
        # 1. Is trivia running?
        # 2. Is a question being asked?
        if game is None or game.active == False:
            self.reply(irc, msg, 'Trivia is not currently running.')
        elif game.state != 'in-question':
            self.reply(irc, msg, 'No question is currently being asked.')
        else:
            game.repeatQuestion()
            irc.noReply()
    repeat = wrap(repeat, ['onlyInChannel'])

    def report(self, irc, msg, arg, user, channel, round, text):
        """[channel] <round> <report text>
        Provide a report for a bad question. Be sure to include the round number and the problem(s). 
        To edit the question, input a regex substitution for the report text. To delete the 
        question, input 'delete' for the report text. Any other report text will be treated as a 
        regular report.
        Channel is a optional parameter which is only needed when reporting outside of the channel
        """
        username = self.getUsername(msg.nick, msg.prefix)
        channelCanonical = ircutils.toLower(channel)
        game = self.getGame(irc, channel)
        if game and text[:2] == 's/' and game.numAsked == round and game.state != 'no-question':
            irc.reply('Sorry, you must wait until the current question is over to make a regex report.')
            return
            
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        question = threadStorage.getQuestionByRound(round, channel)
        if question:
            if text[:2] == 's/': # Regex substitution
                regex = text[2:].split('/')
                if len(regex) > 1:
                    threadStorage.updateUser(username, 1, 0)
                    pattern = regex[0]
                    repl = regex[1]
                    try:
                        newQuestionText = re.sub(pattern, repl, question['question'])
                    except:
                        irc.error('Unable to process this regex substitution.')
                        return
                    
                    if newQuestionText == question['question']: # Ignore if no substitutions made
                        irc.error('This regex substitution expression does not change the original question.')
                    else:
                        threadStorage.insertEdit(question['id'], newQuestionText, username, channel)
                        irc.reply('Regex substitution detected: Question edited!')
                        irc.sendMsg(ircmsgs.notice(username, 'NEW: %s' % (newQuestionText)))
                        irc.sendMsg(ircmsgs.notice(username, 'OLD: %s' % (question['question'])))
                        self.logger.doLog(irc, channel, "%s edited question #%i, NEW: '%s', OLD: '%s'" % (msg.nick, question['id'], newQuestionText, question['question']))
                else: # Incomplete expression
                    irc.error('Incomplete regex substitution expression.')
            elif str.lower(utils.str.normalizeWhitespace(text))[:6] == 'delete': # Delete
                if not threadStorage.questionIdExists(question['id']):
                    irc.error('That question does not exist.')
                elif threadStorage.isQuestionDeleted(question['id']):
                    irc.error('That question is already deleted.')
                elif threadStorage.isQuestionPendingDeletion(question['id']):
                    irc.error('That question is already pending deletion.')
                else:
                    reason = utils.str.normalizeWhitespace(text)[6:]
                    reason = utils.str.normalizeWhitespace(reason)
                    irc.reply('Marked question for deletion.')
                    self.logger.doLog(irc, channel, "%s marked question #%i for deletion" % (msg.nick, question['id']))
                    threadStorage.insertDelete(username, channel, question['id'], reason)
            else: # Regular report
                threadStorage.updateUser(username, 0, 0, 1)
                threadStorage.insertReport(channel, username, text, question['id'])
                self.logger.doLog(irc, channel, "%s reported question #%i, Text: '%s'" % (msg.nick, question['id'], text))
                irc.reply('Your report has been submitted!')
        else:
            irc.error('Sorry, round %d could not be found in the database.' % (round))
    report = wrap(report, ['user', 'channel', 'int', 'text'])

    def restorequestion(self, irc, msg, arg, channel, questionNum):
        """[<channel>] <Question num>
        Restore a deleted question.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        username = msg.nick
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if not threadStorage.questionIdExists(questionNum):
            irc.error('That question does not exist.')
            return
        if not threadStorage.isQuestionDeleted(questionNum):
            irc.error('That question was not deleted.')
            return
        threadStorage.restoreQuestion(questionNum)
        irc.reply('Question %d restored!' % questionNum)
        self.logger.doLog(irc, channel, "%s restored question #%i" % (username, questionNum))
    restorequestion = wrap(restorequestion, ['channel', 'int'])

    def skip(self, irc, msg, arg, channel):
        """
            Skip the current question and start the next. Rate-limited. Requires a certain percentage of active players to skip.
        """
        username = self.getUsername(msg.nick, msg.prefix)
        usernameCanonical = ircutils.toLower(username)

        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        timeSeconds = self.registryValue('skip.skipActiveTime', channel)
        totalActive = threadStorage.getNumUserActiveIn(channel, timeSeconds)
        channelCanonical = ircutils.toLower(channel)
        game = self.getGame(irc, channel)
        
        # Sanity checks
        if game is None or game.active == False:
            self.reply(irc, msg, 'Trivia is not currently running.')
        elif game.state != 'in-question':
            self.reply(irc, msg, 'No question is currently being asked.')
        elif not threadStorage.wasUserActiveIn(username, channel, timeSeconds):
            self.reply(irc, msg, 'Only users who have answered a question in the last %s seconds can vote to skip.' % (timeSeconds))
        elif usernameCanonical in game.skipList:
            self.reply(irc, msg, 'You can only vote to skip once.')
        else:
            # Ensure the game's skip timeout is set? and then check the user
            skipSeconds = self.registryValue('skip.skipTime', channel)
            game.skipTimeoutList.setTimeout(skipSeconds)
            if game.skipTimeoutList.has(usernameCanonical):
                self.reply(irc, msg, 'You must wait %d seconds to be able to skip again.' % (game.skipTimeoutList.getTimeLeft(usernameCanonical)), notice=True)
                return

            # Update skip count
            game.skipList.append(usernameCanonical)
            game.skipTimeoutList.append(usernameCanonical)
            self.reply(irc, msg, '%s voted to skip this question.' % username, prefixNick=False)
            skipPercent = len(game.skipList)/(totalActive*1.0)

            # Check if skip threshold has been reached
            if skipPercent >= self.registryValue('skip.skipThreshold', channel):
                game.removeEvent()
                self.reply(irc, msg, 'Skipped question! (%d of %d voted)' % (len(game.skipList), totalActive), prefixNick=False)
                game.nextQuestion()
    skip = wrap(skip, ['onlyInChannel'])

    def stats(self, irc, msg, arg, channel, username):
        """ [<channel>] <username> 
            Show a player's rank, score & questions asked for day, month, and year.
            Channel is only required when using the command outside of a channel.
        """
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            stat = threadStorage.getUserStat(username, None)
            rank = threadStorage.getUserRank(username, None)
        else:
            stat = threadStorage.getUserStat(username, channel)
            rank = threadStorage.getUserRank(username, channel)
            
        if not stat:
            irc.reply("User not found in database.")
        else:
            hasPoints = False
            infoList = ['%s\'s Stats: Points (answers)' % (self.addZeroWidthSpace(stat['username']))]
            if rank['day'] > 0 or stat['points_day'] > 0 or stat['answer_day'] > 0:
                hasPoints = True
                infoList.append(' \x02Today:\x02 #%d %d (%d)' % (rank['day'], stat['points_day'], stat['answer_day']))
            if rank['week'] > 0 or stat['points_week'] > 0 or stat['answer_week'] > 0:
                hasPoints = True
                infoList.append(' \x02This Week:\x02 #%d %d (%d)' % (rank['week'], stat['points_week'], stat['answer_week']))
            if rank['month'] > 0 or stat['points_month'] > 0 or stat['answer_month'] > 0:
                hasPoints = True
                infoList.append(' \x02This Month:\x02 #%d %d (%d)' % (rank['month'], stat['points_month'], stat['answer_month']))
            if rank['year'] > 0 or stat['points_year'] > 0 or stat['answer_year'] > 0:
                hasPoints = True
                infoList.append(' \x02This Year:\x02 #%d %d (%d)' % (rank['year'], stat['points_year'], stat['answer_year']))
            if not hasPoints:
                infoList = ['%s: %s does not have any points.' % (msg.nick, username)]
            infoText = ''.join(infoList)
            self.reply(irc, msg, infoText, prefixNick=False)
    stats = wrap(stats, ['channel', 'nick'])

    def showdelete(self, irc, msg, arg, channel, num):
        """[<channel>] [<temp question #>]
        Show a deleteion request pending approval.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        if num is not None:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
            if self.registryValue('general.globalstats'):
                delete = threadStorage.getDeleteById(num)
            else:
                delete = threadStorage.getDeleteById(num, channel)
                
            if delete:
                question = threadStorage.getQuestionById(delete['line_num'])
                questionText = question['question'] if question else 'Question not found'
                irc.reply('Delete #%d, by %s Question #%d: %s, Reason: %s'%(delete['id'], delete['username'], delete['line_num'], questionText, delete['reason']))
            else:
                if self.registryValue('general.globalstats'):
                    irc.error('Unable to find delete #{0}.'.format(num))
                else:
                    irc.error('Unable to find delete #{0} in {1}.'.format(num, channel))
        else:
            self.listdeletes(irc, msg, [channel])
    showdelete = wrap(showdelete, ['channel', optional('int')])

    def showquestion(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Search question database for question at line number.
        Channel is only necessary when editing from outside of the channel.
        """
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        question = threadStorage.getQuestionById(num)
        if question:
            if question['deleted'] == 1:
                irc.reply('Info: This question is currently deleted.')
            irc.reply('Question #%d: %s' % (num, question['question']))
        else:
            irc.error('Question not found')
    showquestion = wrap(showquestion, ['user', 'channel', 'int'])

    def showround(self, irc, msg, arg, user, channel, round):
        """[<channel>] <round>
        Show what question was asked during gameplay.
        Channel is only necessary when editing from outside of the channel.
        """
        game = self.getGame(irc, channel)
        if game and round == game.numAsked and game.state != 'no-question':
            irc.error('The current question can\'t be displayed until it is over.')
        else:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
            question = threadStorage.getQuestionByRound(round, channel)
            if question:
                irc.reply('Round %d: Question #%d: %s' % (round, question['id'], question['question']))
            else:
                irc.error('Round not found')
    showround = wrap(showround, ['user', 'channel', 'int'])

    def showreport(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<report num>]
        Shows report information, if number is provided one record is shown, otherwise the last 3 are. 
        Channel is only necessary when editing from outside of the channel.
        """        
        if num is not None:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
            if self.registryValue('general.globalstats'):
                report = threadStorage.getReportById(num)
            else:
                report = threadStorage.getReportById(num, channel)
            
            if report:
                irc.reply('Report #%d \'%s\' by %s on %s Q#%d '%(report['id'], report['report_text'], report['username'], report['channel'], report['question_num']))
                question = threadStorage.getQuestionById(report['question_num'])
                if question:
                    irc.reply('Question #%d: %s' % (question['id'], question['question']))
                else:
                    irc.error('Question could not be found.')
            else:
                if self.registryValue('general.globalstats'):
                    irc.reply('Unable to find report #{0}.'.format(num))
                else:
                    irc.reply('Unable to find report #{0} in {1}.'.format(num, channel))
        else:
            self.listreports(irc, msg, [channel])
    showreport = wrap(showreport, ['user', 'channel', optional('int')])

    def showedit(self, irc, msg, arg, channel, num):
        """[<channel>] [<edit num>]
        Show top 3 edits, or provide edit num to view one. 
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
            
        if num is not None:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
            if self.registryValue('general.globalstats'):
                edit = threadStorage.getEditById(num)
            else:
                edit = threadStorage.getEditById(num, channel)
                
            if edit:
                question = threadStorage.getQuestionById(edit['question_id'])
                irc.reply('Edit #%d by %s, Question #%d'%(edit['id'], edit['username'], edit['question_id']))
                irc.reply('NEW:%s' %(edit['question']))
                if question:
                    irc.reply('OLD:%s' % (question['question']))
                else:
                    irc.error('Question could not be found for this edit')
            else:
                if self.registryValue('general.globalstats'):
                    irc.error('Unable to find edit #{0}.'.format(num))
                else:
                    irc.error('Unable to find edit #{0} in {1}.'.format(num, channel))
        else:
            self.listedits(irc, msg, [channel])
    showedit = wrap(showedit, ['channel', optional('int')])

    def shownew(self, irc, msg, arg, channel, num):
        """[<channel>] [<temp question #>]
        Show questions awaiting approval
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
                    
        if num is not None:
            dbLocation = self.registryValue('admin.db')
            threadStorage = Storage(dbLocation)
            if self.registryValue('general.globalstats'):
                q = threadStorage.getTemporaryQuestionById(num)
            else:
                q = threadStorage.getTemporaryQuestionById(num, channel)
                
            if q:
                irc.reply('Temp Q #%d by %s: %s'%(q['id'], q['username'], q['question']))
            else:
                if self.registryValue('general.globalstats'):
                    irc.error('Unable to find new question #{0}.'.format(num))
                else:
                    irc.error('Unable to find new question #{0} in {1}.'.format(num, channel))
        else:
            self.listnew(irc, msg, [channel])
    shownew = wrap(shownew, ['channel', optional('int')])

    def start(self, irc, msg, args, channel):
        """
        Begins a round of Trivia inside the current channel.
        """
        game = self.getGame(irc, channel)
        
        # Sanity checks
        # 1. Is trivia running?
        # 2. Is the previous trivia session still in the shutdown phase?
        # 3. Is there a stop pending?
        if game is None:
            # create a new game
            self.reply(irc, msg, 'Another epic round of trivia is about to begin.', prefixNick=False)
            self.createGame(irc, channel)
        elif game.active == False:
            self.reply(irc, msg, 'Please wait for the previous game instance to stop.')
        elif game.stopPending == True:
            game.stopPending = False
            self.reply(irc, msg, 'Pending stop aborted', prefixNick=False)
        else:
            self.reply(irc, msg, 'Trivia has already been started.')
    start = wrap(start, ['onlyInChannel'])

    def stop(self, irc, msg, args, user, channel):
        """
        Stops the current Trivia round.
        """
        game = self.getGame(irc, channel)
        
        # Sanity checks
        # 1. Is trivia running?
        # 2. Is a question being asked?
        # 2.1 Is a stop pending?
        if game is None or game.active == False:
            self.reply(irc, msg, 'Game is already stopped.')
        elif game.state != 'no-question':
            if game.stopPending == True:
                self.reply(irc, msg, 'Trivia is already pending stop.')
            else:
                game.stopPending = True
                self.reply(irc, msg, 'Trivia will now stop after this question.', prefixNick=False)
        else:
            game.stop()
            irc.noReply()
    stop = wrap(stop, ['user', 'onlyInChannel'])

    def time(self, irc, msg, arg):
        """
        Figure out what time/day it is on the server.
        """
        timeStr = time.asctime(time.localtime())
        self.reply(irc, msg, 'The current server time appears to be {0}'.format(timeStr), prefixNick=False)
    time = wrap(time)

    def transferpoints(self, irc, msg, arg, channel, userfrom, userto):
        """[<channel>] <userfrom> <userto>
        Transfers all points and records from one user to another.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaAdmin(hostmask, channel) == False:
            irc.reply('You must be a TriviaAdmin in {0} to use this command.'.format(channel))
            return
        
        userfrom = userfrom
        userto = userto
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        threadStorage.transferUserLogs(userfrom, userto, channel)
        irc.reply('Transferred all records from {0} to {1} in {2}.'.format(userfrom, userto, channel))
        self.logger.doLog(irc, channel, '{0} transferred records from {1} to {2} in {3}.'.format(msg.nick, userfrom, userto, channel))
    transferpoints = wrap(transferpoints, ['channel', 'nick', 'nick'])

    def week(self, irc, msg, arg, channel, num):
        """[<channel>] [<number>]
        Displays the top scores of the week. 
        Parameter is optional, display up to that number. (eg 20 - display 11-20)
        Channel is only required when using the command outside of a channel.
        """
        num = max(num, 10)
        offset = num-9
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewWeekTop10(None, num)
        else:
            tops = threadStorage.viewWeekTop10(channel, num)
        
        topsList = ['This Week\'s Top {0}-{1} Players: '.format(offset, num)]
        if tops:
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
        else:
            topsList.append('No players')
        topsText = ''.join(topsList)
        self.reply(irc, msg, topsText, prefixNick=False)
    week = wrap(week, ['channel', optional('int')])

    def year(self, irc, msg, arg, channel, num):
        """[<channel>] [<number>]
            Displays the top scores of the year. 
            Parameter is optional, display up to that number. (eg 20 - display 11-20)
            Channel is only required when using the command outside of a channel.
        """
        num = max(num, 10)
        offset = num-9
        dbLocation = self.registryValue('admin.db')
        threadStorage = Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewYearTop10(None, num)
        else:
            tops = threadStorage.viewYearTop10(channel, num)
            
        topsList = ['This Year\'s Top {0}-{1} Players: '.format(offset, num)]
        if tops:
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
        else:
            topsList.append('No players')
        topsText = ''.join(topsList)
        self.reply(irc, msg, topsText, prefixNick=False)
    year = wrap(year, ['channel', optional('int')])

    
Class = TriviaTime
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
