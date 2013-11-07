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
        log.info('*** Loaded TriviaTime!!! ***')
        self.__parent = super(TriviaTime, self)
        self.__parent.__init__(irc)

        """ games info """
        self.games = {} # separate game for each channel
        self.skips = {}
        self.pings = {}

        """ connections """
        dbLocation = self.registryValue('sqlitedb')
        # tuple head, tail ('example/example/', 'filename.txt')
        dbFolder = os.path.split(dbLocation)
        # take folder from split
        dbFolder = dbFolder[0]
        # create the folder
        if not os.path.exists(dbFolder):
            log.info("""The database location did not exist, creating folder structure""")
            os.makedirs(dbFolder)
        self.storage = self.Storage(dbLocation)
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
        #self.storage.dropQuestionTable()
        self.storage.makeQuestionTable()
        #self.storage.dropTemporaryQuestionTable()
        self.storage.makeTemporaryQuestionTable()
        #self.storage.dropEditTable()
        self.storage.makeEditTable()
        #self.storage.insertUserLog('root', 1, 1, 10, 10, 30, 2013)
        #self.storage.insertUser('root', 1, 1)

        #filename = self.registryValue('quizfile')
        #self.addQuestionsFromFile(filename)

    def doPrivmsg(self, irc, msg):
        """
            Catches all PRIVMSG, including channels communication
        """
        username = str.lower(msg.nick)
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
            username = str.lower(user.name)
        except KeyError:
            pass
        channel = ircutils.toLower(msg.args[0])
        # Make sure that it is starting inside of a channel, not in pm
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if channel in self.games:
            # Look for command to list remaining KAOS
            if msg.args[1] == self.registryValue('showHintCommandKAOS',channel):
                self.games[channel].getRemainingKAOS()
            elif msg.args[1] == self.registryValue('showOtherHintCommand', channel):
                self.games[channel].getOtherHint(username)
            elif str.lower(msg.args[1]) == self.registryValue('repeatCommand', channel):
                self.games[channel].repeatQuestion()
            else:
                # check the answer
                self.games[channel].checkAnswer(msg)

    def doJoin(self,irc,msg):
        username = str.lower(msg.nick)
        # is it a user?
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
            username = str.lower(user.name)
        except KeyError:
            pass
        channel = str.lower(msg.args[0])
        user = self.storage.getUser(username)
        numTopToVoice = self.registryValue('numTopToVoice')
        if len(user) >= 1:
            if user[13] <= numTopToVoice and user[4] > self.registryValue('minPointsVoiceYear'):
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving MVP to %s for being top #%d this YEAR' % (username, user[13])))
                irc.queueMsg(ircmsgs.voice(channel, username))
            elif user[14] <= numTopToVoice and user[6] > self.registryValue('minPointsVoiceMonth'):
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving MVP to %s for being top #%d this MONTH' % (username, user[14])))
                irc.queueMsg(ircmsgs.voice(channel, username))
            elif user[15] <= numTopToVoice and user[8] > self.registryValue('minPointsVoiceWeek'):
                irc.sendMsg(ircmsgs.privmsg(channel, 'Giving MVP to %s for being top #%d this WEEK' % (username, user[15])))
                irc.queueMsg(ircmsgs.voice(channel, username))

    def doNotice(self,irc,msg):
        username = str.lower(msg.nick)
        if msg.args[1][1:5] == "PING":
            if username in self.pings:
                pingTime = float(time.time() - self.pings[username][0])
                irc.sendMsg(ircmsgs.privmsg(self.pings[username][1], """ %s Pong: response %0.2f seconds""" % (username, pingTime)))
                del self.pings[username]

    def acceptedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Accept a question edit, and remove edit. Channel is only necessary when editing from outside of the channel
        """
        edit = self.storage.getEditById(num)
        if len(edit) < 1:
            irc.error('Could not find that edit')
        else:
            edit = edit[0]
            question = self.storage.getQuestion(edit[1])
            self.storage.updateQuestion(edit[1], edit[2])
            self.storage.updateUser(edit[4], 0, 1)
            self.storage.removeEdit(edit[0])
            irc.reply('Question #%d updated!' % edit[1])
            irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (edit[2])))
            if len(question) > 0:
                question = question[0]
                irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (question[2])))
            else:
                irc.error('Question could not be found for this edit')
    acceptedit = wrap(acceptedit, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def accepttempquestion(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Accept a new question, and add it to the database. Channel is only necessary when editing from outside of the channel
        """
        q = self.storage.getTemporaryQuestionById(num)
        if len(q) < 1:
            irc.error('Could not find that temp question')
        else:
            q = q[0]
            self.storage.insertQuestionsBulk([(q[3], q[3])])
            self.storage.removeTemporaryQuestion(q[0])
            irc.reply('Question accepted!')
    accepttempquestion = wrap(accepttempquestion, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def addquestion(self, irc, msg, arg, question):
        """<question text>
            Adds a question to the database
        """
        username = ircutils.toLower(msg.nick)
        channel = ircutils.toLower(msg.args[0])
        charMask = self.registryValue('charMask', channel)   
        if charMask not in question:
            irc.error(' The question must include the separating character %s ' % (charMask))
            return
        self.storage.insertTemporaryQuestion(username, channel, question)
        irc.reply(' Thank you for adding your question to the question database, it is awaiting approval. ')
    addquestion = wrap(addquestion, ['text'])

    def addquestionfile(self, irc, msg, arg, filename):
        """[<filename>]
        Add a file of questions to the servers question database, filename defaults to configured quesiton file
        """
        if filename is None:
            filename = self.registryValue('quizfile')
        try:
            filesLines = open(filename).readlines()
        except:
            irc.error('Could not open file to add to database. Make sure it exists on the server.')
            return
        irc.reply('Adding questions from %s to database.. This may take a few minutes' % filename)
        insertList = []
        for line in filesLines:
            insertList.append((str(line).strip(),str(line).strip()))
        info = self.storage.insertQuestionsBulk(insertList)
        irc.reply('Successfully added %d questions, skipped %d' % (info[0], info[1]))
    addquestionfile = wrap(addquestionfile, ['admin', optional('text')])

    def clearpoints(self, irc, msg, arg, username):
        """<username>

        Deletes all of a users points, and removes all their records
        """
        self.storage.removeUserLogs(str.lower(username))
        irc.reply('Removed all points from %s' % (username))
    clearpoints = wrap(clearpoints, ['admin','nick'])

    def day(self, irc, msg, arg):
        """
            Gives the top10 scores of the day
        """
        channel = ircutils.toLower(msg.args[0])
        tops = self.storage.viewDayTop10()
        topsText = '\x0301,08 TODAYS Top 10 - '
        for i in range(len(tops)):
            topsText += '\x02\x0301,08 #%d:\x02 \x0300,04 %s %d ' % ((i+1) , tops[i][1], tops[i][2])
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    day = wrap(day)

    def deletequestion(self, irc, msg, arg, id):
        """<question id>
            Deletes a question from the database.
        """
        if not self.storage.questionIdExists(id):
            self.error('That question does not exist.')
            return
        self.storage.deleteQuestion(id)
        irc.reply('Deleted question %d.' % id)
    deletequestion = wrap(deletequestion, ['admin', 'int'])

    def edit(self, irc, msg, arg, user, channel, num, question):
        """[<channel>] <question number> <corrected text>
        Correct a question by providing the question number and the corrected text. Channel is only necessary when editing from outside of the channel
        """
        username = str.lower(msg.nick)
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
            username = str.lower(user.name)
        except KeyError:
            pass
        q = self.storage.getQuestion(num)
        if len(question) > 0:
            q = q[0]
            self.storage.insertEdit(num, question, username, msg.args[0])
            self.storage.updateUser(username, 1, 0)
            irc.reply("Success! Submitted edit for further review.")
            irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (question)))
            irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (q[2])))
        else:
            irc.error("Question does not exist")
    edit = wrap(edit, ['user', ('checkChannelCapability', 'triviamod'), 'int', 'text'])

    def givepoints(self, irc, msg, arg, username, points, days):
        """<username> <points> [<daysAgo>]

        Give a user points, last argument is optional amount of days in past to add records
        """
        if points < 1:
            irc.error("You cannot give less than 1 point.")
            return
        day=None
        month=None
        year=None
        if days is not None:
            d = datetime.date.today()
            d -= datetime.timedelta(days)
            day = d.day
            month = d.month
            year = d.year
        self.storage.updateUserLog(str.lower(username), points, 0, 0, day, month, year)
        irc.reply('Added %d points to %s' % (points, username))
    givepoints = wrap(givepoints, ['admin','nick', 'int', optional('int')])

    def info(self, irc, msg, arg):
        """
        Get TriviaTime information, how many questions/users in database, time, etc
        """
        numActiveThisWeek = self.storage.getNumActiveThisWeek()
        infoText = ''' TriviaTime by #trivialand on Freenode'''
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        infoText = ''' Time is %s ''' % (time.asctime(time.localtime(),))
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        infoText = '''\x02 %d Users\x02 on scoreboard \x02%d Active This Week\x02''' % (self.storage.getNumUser(), numActiveThisWeek)
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        numKaos = self.storage.getNumKAOS()
        numQuestionTotal = self.storage.getNumQuestions()
        infoText = '''\x02 %d Questions\x02 and \x02%d KAOS\x02 (\x02%d Total\x02) in the database ''' % ((numQuestionTotal-numKaos), numKaos, numQuestionTotal)
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
    info = wrap(info)

    def latency(self, irc, msg, arg):
        channel = ircutils.toLower(msg.args[0])
        username = str.lower(msg.nick)
        expiredPings = []

        for ping in self.pings:
            if time.time() - self.pings[ping][0] > 60:
                expiredPings.append(ping)
        for ping in expiredPings:
            del expiredPings[ping]
        if username in self.pings:
            return
        self.pings[username] = (time.time(), channel)
        irc.sendMsg(ircmsgs.privmsg(username, """\x01PING ping\x01"""))
    latency = wrap(latency)

    def me(self, irc, msg, arg):
        """
            Get your rank, score & questions asked for day, month, year
        """
        username = str.lower(msg.nick)
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
            username = str.lower(user.name)
        except KeyError:
            pass
        channel = ircutils.toLower(msg.args[0])
        info = self.storage.getUser(str.lower(username))
        if len(info) < 3:
            irc.error("I couldn't find you in my database.")
        else:
            infoText = ' %s\'s Stats: \x02Today:\x02 #%d %d (%d) \x02This Week:\x02 #%d %d (%d) \x02This Month:\x02 #%d %d (%d) \x02This Year:\x02 #%d %d (%d)' % (username, info[16], info[10], info[11], info[15], info[8], info[9], info[14], info[6], info[7], info[13], info[4], info[5])
            irc.sendMsg(ircmsgs.privmsg(channel, infoText))
        irc.noReply()
    me = wrap(me)

    def month(self, irc, msg, arg):
        """
            Gives the top10 scores of the month
        """
        channel = ircutils.toLower(msg.args[0])
        tops = self.storage.viewMonthTop10()
        topsText = '\x0301,08 This MONTHS Top 10 Players - '
        for i in range(len(tops)):
            topsText += '\x02\x0301,08 #%d:\x02 \x0300,04 %s %d ' % ((i+1) , tops[i][1], tops[i][2])
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    month = wrap(month)

    def removeedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] <int>
        Remove a edit without accepting it. Channel is only necessary when editing from outside of the channel
        """
        edit = self.storage.getEditById(num)
        if len(edit) < 1:
            irc.error('Could not find that edit')
        else:
            edit = edit[0]
            self.storage.removeEdit(edit[0])
            irc.reply('Edit %d removed!' % edit[0])
    removeedit = wrap(removeedit, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def removereport(self, irc, msg, arg, user, channel, num):
        """[<channel>] <report num>
        Remove a old report by report number. Channel is only necessary when editing from outside of the channel
        """
        report = self.storage.getReportById(num)
        if len(report) < 1:
            irc.error('Could not find that report')
        else:
            report = report[0]
            self.storage.removeReport(report[0])
            irc.reply('Report %d removed!' % report[0])
    removereport = wrap(removereport, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def removetempquestion(self, irc, msg, arg, user, channel, num):
        """[<channel>] <int>
        Remove a temp question without accepting it. Channel is only necessary when editing from outside of the channel
        """
        q = self.storage.getTemporaryQuestionById(num)
        if len(q) < 1:
            irc.error('Could not find that temp question')
        else:
            q = q[0]
            self.storage.removeTemporaryQuestion(q[0])
            irc.reply('Temp question #%d removed!' % q[0])
    removetempquestion = wrap(removetempquestion, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def report(self, irc, msg, arg, roundNum, text):
        """<report id> <report text>
        Provide a report for a bad question. Be sure to include the round number and any problems.
        """
        username = str.lower(msg.nick)
        try:
            user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
            username = str.lower(user.name)
        except KeyError:
            pass
        channel = str.lower(msg.args[0])
        if channel in self.games:
            if self.games[channel].numAsked == roundNum and self.games[channel].questionOver == False:
                irc.reply("Sorry you must wait until the current question is over to report it.")
                return
        question = self.storage.getQuestionByRound(roundNum, channel)
        if len(question) > 0:
            question = question[0]
            inp = text.strip()
            self.storage.updateUser(username, 1, 0)
            if inp[:2] == 's/':
                regex = inp[2:].split('/')
                if len(regex) > 1:
                    newOne = regex[1]
                    oldOne = regex[0]
                    newQuestionText = question[2].replace(oldOne, newOne)
                    self.storage.insertEdit(question[0], newQuestionText, username, channel)
                    irc.reply('** Regex detected ** Your report has been submitted!')
                    irc.sendMsg(ircmsgs.notice(username, 'NEW: %s' % (newQuestionText)))
                    irc.sendMsg(ircmsgs.notice(username, 'OLD: %s' % (question[2])))
                    return
            self.storage.insertReport(channel, username, text, question[0])
            irc.reply('Your report has been submitted!')
        else:
            irc.error('Sorry, round %d could not be found in the database')
    report = wrap(report, ['int', 'text'])

    def skip(self, irc, msg, arg):
        """
            Skip a question
        """
        username = ircutils.toLower(msg.nick)
        channel = ircutils.toLower(msg.args[0])

        timeSeconds = self.registryValue('skipActiveTime', channel)
        totalActive = self.storage.getNumUserActiveIn(timeSeconds)

        if channel not in self.games:
            irc.error('No questions are currently being asked.')
            return

        if self.games[channel].questionOver == True:
            irc.error('No question is currently being asked.')
            return

        if not self.storage.wasUserActiveIn(username, timeSeconds):
            irc.error('Only users who have answered a question in the last 10 minutes can skip.')
            return

        if username in self.games[channel].skipVoteCount:
            irc.error('You can only vote to skip once.')
            return

        skipSeconds = self.registryValue('skipLimitTime', channel)
        oldSkips = []
        for usr in self.skips:
            if int(time.mktime(time.localtime())) - self.skips[usr] > skipSeconds:
                oldSkips.append(usr)
        for usr in oldSkips:
            del self.skips[usr]
        if username in self.skips:
            if int(time.mktime(time.localtime())) - self.skips[username] < skipSeconds:
                irc.error('You must wait to be able to skip again.')
                return

        self.games[channel].skipVoteCount[username] = 1
        self.skips[username] = int(time.mktime(time.localtime()))

        irc.sendMsg(ircmsgs.privmsg(channel, '%s voted to skip this question.' % username))
        if totalActive < 1:
            return

        percentAnswered = ((1.0*len(self.games[channel].skipVoteCount))/(totalActive*1.0))

        # not all have skipped yet, we need to get out of here
        if percentAnswered < self.registryValue('skipThreshold', channel):
            irc.noReply()
            return

        if channel not in self.games:
            irc.error('Trivia is not running.')
            return
        if self.games[channel].active == False:
            irc.error('Trivia is not running.')
            return
        try:
            schedule.removeEvent('%s.trivia' % channel)
        except KeyError:
            pass
        irc.sendMsg(ircmsgs.privmsg(channel, 'Skipped question! (%d of %d voted)' % (len(self.games[channel].skipVoteCount), totalActive)))

        self.games[channel].nextQuestion()
        irc.noReply()
    skip = wrap(skip)

    def showstats(self, irc, msg, arg, username):
        """
            Get someones rank, score & questions asked for day, month, year
        """
        channel = ircutils.toLower(msg.args[0])
        info = self.storage.getUser(str.lower(username))
        if len(info) < 3:
            irc.error("I couldn't find you in my database.")
        else:
            infoText = '\x0305,08 %s\'s Stats:\x0301,08 Points (answers) \x0305,08Today: #%d %d (%d) This Week: #%d %d (%d) This Month: #%d %d (%d) This Year: #%d %d (%d)' % (info[1], info[16], info[10], info[11], info[15], info[8], info[9], info[14], info[6], info[7], info[13], info[4], info[5])
            irc.sendMsg(ircmsgs.privmsg(channel, infoText))
        irc.noReply()
    showstats = wrap(showstats,['nick'])

    def showquestion(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Search question database for question at line num. Channel is only necessary when editing from outside of the channel
        """
        question = self.storage.getQuestion(num)
        if len(question) < 1:
            irc.error("Question not found")
        else:
            question = question[0]
            irc.reply('''Question#%d: %s''' % (num, question[2]))
    showquestion = wrap(showquestion, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def showround(self, irc, msg, arg, user, channel, num):
        """[<channel>] <round num>
        Show what question was asked during the round. Channel is only necessary when editing from outside of the channel
        """
        question = self.storage.getQuestionByRound(num, msg.args[0])
        if len(question) < 1:
            irc.error("Round not found")
        else:
            question = question[0]
            irc.reply('''Round %d: Question#%d, Text:%s''' % (num, question[0], question[2]))
    showround = wrap(showround, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def showreport(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<report num>]
        Shows report information, if num is provided one record is shown, otherwise the last 3 are. Channel is only necessary when editing from outside of the channel
        """
        if num is not None:
            report = self.storage.getReportById(num)
            if len(report) < 1:
                irc.reply('No reports found')
            else:
                report = report[0]
                irc.reply('Report #%d `%s` by %s on %s Q#%d '%(report[0], report[3], report[2], report[1], report[7]))
                
                question = self.storage.getQuestion(report[7])
                if len(question) < 1:
                    irc.reply("Error: Tried to find question but couldn't")
                else:
                    question = question[0]
                    irc.reply('''Question#%d: %s''' % (question[0], question[2]))
        else:
            reports  = self.storage.getReportTop3()
            if len(reports) < 1:
                irc.reply('No reports found')
            for report in reports:
                irc.reply('Report #%d `%s` by %s on %s Q#%d '%(report[0], report[3], report[2], report[1], report[7]))
    showreport = wrap(showreport, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def showedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<edit num>]
        Show top 3 edits, or provide edit num to view one. Channel is only necessary when editing from outside of the channel
        """
        if num is not None:
            edit = self.storage.getEditById(num)
            if len(edit) > 0:
                edit = edit[0]
                question = self.storage.getQuestion(edit[1])
                irc.reply('Edit #%d, Question#%d'%(edit[0], edit[1]))
                irc.reply('NEW:%s' %(edit[2]))
                if len(question) > 0:
                    question = question[0]
                    irc.reply('OLD:%s' % (question[2]))
                else:
                    irc.error('Question could not be found for this edit')
            else:
                irc.error('Edit #%d not found' % num)
        else:
            edits = self.storage.getEditTop3()
            if len(edits) < 1:
                irc.reply('No edits found')
            for edit in edits:
                question = self.storage.getQuestion(edit[1])
                question = question[0]
                irc.reply('Edit #%d, Question#%d, NEW:%s'%(edit[0], edit[1], edit[2]))
            irc.reply('type .showedit <edit number> to see more information')
    showedit = wrap(showedit, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def showtempquestion(self, irc, msg, arg, num):
        """[<temp question #>]
        Show questions awaiting approval
        """
        if num is not None:
            q = self.storage.getTemporaryQuestionById(num)
            if len(q) > 0:
                q = q[0]
                irc.reply('Temp Q #%d: %s'%(q[0], q[3]))
            else:
                irc.error('Temp Q #%d not found' % num)
        else:
            q = self.storage.getTemporaryQuestionTop3()
            if len(q) < 1:
                irc.reply('No temp questions found')
            for ques in q:
                irc.reply('Temp Q #%d: %s'%(ques[0], ques[3]))
            irc.reply('type .showtempquestion <temp question #> to see more information')
    showtempquestion = wrap(showtempquestion, [optional('int')])

    def start(self, irc, msg, args):
        """
            Begins a round of Trivia inside of your current channel.
        """
        channel = ircutils.toLower(msg.args[0])
        if not irc.isChannel(channel):
            irc.reply('Sorry, I can start inside of a channel, try joining #trivialand. Or fork TriviaLand on github')
            return
        if channel in self.games:
            if self.games[channel].stopPending == True:
                self.games[channel].stopPending = False
                irc.sendMsg(ircmsgs.privmsg(channel, 'Pending stop aborted'))
            elif not self.games[channel].active:
                del self.games[channel]
                try:
                    schedule.removeEvent('%s.trivia' % channel)
                except KeyError:
                    pass
                #irc.error(self.registryValue('alreadyStarted'))
                irc.sendMsg(ircmsgs.privmsg(channel, self.registryValue('starting')))
                self.games[channel] = self.Game(irc, channel, self)
            else:
                irc.sendMsg(ircmsgs.privmsg(channel, self.registryValue('alreadyStarted')))
        else:
            # create a new game
            irc.sendMsg(ircmsgs.privmsg(channel, self.registryValue('starting')))
            self.games[channel] = self.Game(irc, channel, self)
        irc.noReply()
    start = wrap(start)

    def stop(self, irc, msg, channel, args):
        """[<channel>] 
            Ends Trivia. Only use this if you know what you are doing.. Channel is only necessary when editing from outside of the channel
        """
        channel = ircutils.toLower(msg.args[0])
        if channel in self.games:
            if self.games[channel].questionOver == True:
                self.games[channel].stop()
                return
            if self.games[channel].active:
                self.games[channel].stopPending = True
                irc.sendMsg(ircmsgs.privmsg(channel, 'Trivia will now stop after this question.'))
            else:
                del self.games[channel]
                irc.sendMsg(ircmsgs.privmsg(channel, self.registryValue('stopped')))
        else:
            irc.sendMsg(ircmsgs.privmsg(channel, 'Game is already stopped'))
        irc.noReply()
    stop = wrap(stop, [('checkChannelCapability', 'triviamod')])

    def time(self, irc, msg, arg):
        """
            Figure out what time/day it is for the server
        """
        channel = ircutils.toLower(msg.args[0])
        timeObject = time.asctime(time.localtime())
        timeString = '\x0301,08The current server time appears to be %s' % timeObject
        irc.sendMsg(ircmsgs.privmsg(channel, timeString))
        irc.noReply()
    time = wrap(time)

    def transferpoints(self, irc, msg, arg, userfrom, userto):
        """<userfrom> <userto>

        Transfers all points and records from one user to another
        """
        userfrom = str.lower(userfrom)
        userto = str.lower(userto)
        self.storage.transferUserLogs(userfrom, userto)
        irc.reply('Done! Transfered records from %s to %s' % (userfrom, userto))
    transferpoints = wrap(transferpoints, ['admin', 'nick', 'nick'])

    def week(self, irc, msg, arg):
        """
            Gives the top10 scores of the week
        """
        channel = ircutils.toLower(msg.args[0])
        tops = self.storage.viewWeekTop10()
        topsText = '\x0301,08 This WEEKS Top 10 - '
        for i in range(len(tops)):
            topsText += '\x02\x0301,08 #%d:\x02 \x0300,04 %s %d ' % ((i+1) , tops[i][1], tops[i][2])
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    week = wrap(week)

    def year(self, irc, msg, arg):
        """
            Gives the top10 scores of the year
        """
        channel = ircutils.toLower(msg.args[0])
        tops = self.storage.viewYearTop10()
        topsText = '\x0301,08 Top 10 Players - '
        for i in range(len(tops)):
            topsText += '\x02\x0301,08 #%d:\x02 \x0300,04 %s %d ' % ((i+1) , tops[i][1], tops[i][2])
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    year = wrap(year)

    #Game instance
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
            self.stopPending = False
            self.shownHint = False
            self.questionRepeated = False
            self.skipVoteCount = {}
            self.streak       = 0
            self.lastWinner   = ''
            self.hintsCounter = 0
            self.numAsked     = 0
            self.lastAnswer   = time.time()
            self.roundStartedAt = time.mktime(time.localtime())

            self.loadGameState()

            # activate
            self.questionOver = True
            self.active = True

            # stop any old game and start a new one
            self.removeEvent()
            self.nextQuestion()

        def checkAnswer(self, msg):
            """
                Check users input to see if answer was given.
            """
            username = str.lower(msg.nick)
            # is it a user?
            try:
                user = ircdb.users.getUser(msg.prefix) # rootcoma!~rootcomaa@unaffiliated/rootcoma
                username = str.lower(user.name)
            except KeyError:
                pass
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
                    if str.lower(username) not in self.correctPlayers:
                        self.correctPlayers[str.lower(username)] = 1
                    self.correctPlayers[str.lower(username)] += 1
                    # KAOS? divide points
                    pointsAdded /= (len(self.answers) + 1)

                    # Convert score to int
                    pointsAdded = int(pointsAdded)

                    self.totalAmountWon += pointsAdded
                    # report the correct guess for kaos item
                    self.storage.updateUserLog(username,pointsAdded,0, 0)
                    self.lastAnswer = time.time()
                    self.sendMessage(self.registryValue('answeredKAOS', self.channel) 
                            % (username, pointsAdded, correctAnswer))
                else:
                    # Normal question solved
                    streakBonus = 0
                    # update streak info
                    if self.lastWinner != str.lower(username):
                        self.lastWinner = str.lower(username)
                        self.streak = 1
                    else:
                        self.streak += 1
                        streakBonus = pointsAdded * .01 * (self.streak-1)
                        maxBonus = 2 * pointsAdded
                        if streakBonus > maxBonus:
                            streakBonus = maxBonus
                        pointsAdded += streakBonus
                    self.storage.updateGameStreak(self.channel, self.lastWinner, self.streak)
                    # Convert score to int
                    pointsAdded = int(pointsAdded)

                    # report correct guess, and show players streak
                    self.storage.updateUserLog(username,pointsAdded,1, timeElapsed)
                    self.lastAnswer = time.time()
                    self.sendMessage(self.registryValue('answeredNormal', self.channel) 
                            % (username, correctAnswer, timeElapsed, pointsAdded, streakBonus))

                    if self.registryValue('showPlayerStats', self.channel):
                        playersStats = self.storage.getUser(username)
                        todaysScore = 0
                        userInfo = self.storage.getUser(username)
                        if len(userInfo) >= 3:
                            todaysScore = userInfo[10]
                            weekScore = userInfo[8]
                            monthScore = userInfo[6]
                            self.sendMessage(self.registryValue('playerStatsMsg', self.channel) 
                                    % (username, self.streak, todaysScore, weekScore, monthScore))

                # add guessed word to list so we can cross it out
                if self.guessedAnswers.count(attempt) == 0:
                    self.guessedAnswers.append(attempt)
                # can show more hints now
                self.shownHint = False

                # Have all of the answers been found?
                if len(self.guessedAnswers) == len(self.answers):
                    # question is over
                    self.questionOver = True
                    if len(self.guessedAnswers) > 1:
                        bonusPoints = 0
                        if len(self.correctPlayers) >= 2:
                            if len(self.answers) >= 9:
                                bonusPoints = self.registryValue('payoutKAOS', self.channel)
                        
                        bonusPointsText = ''
                        if bonusPoints > 0:
                            for nick in self.correctPlayers:
                                self.storage.updateUserLog(str(nick).lower(),bonusPoints, 0, 0)
                            bonusPointsText += self.registryValue('bonusKAOS', self.channel) % int(bonusPoints)

                        # give a special message if it was KAOS
                        self.sendMessage(self.registryValue('solvedAllKAOS', self.channel) % bonusPointsText)
                        self.sendMessage(self.registryValue('recapCompleteKaos', self.channel) % (int(self.totalAmountWon), len(self.correctPlayers)))

                    self.removeEvent()

                    if self.stopPending == True:
                        self.stop()
                        return

                    sleepTime = self.registryValue('sleepTime',self.channel)
                    if sleepTime < 2:
                        sleepTime = 2
                        log.error('sleepTime was set too low(<2 seconds). setting to 2 seconds')
                    sleepTime = time.time() + sleepTime
                    self.queueEvent(sleepTime, self.nextQuestion)

        def getHintString(self, hintNum=None):
            if hintNum == None:
                hintNum = self.hintsCounter
            hintRatio = self.registryValue('hintShowRatio') # % to show each hint
            hints = ''
            ratio = float(hintRatio * .01)
            charMask = self.registryValue('charMask', self.channel)

            # create a string with hints for all of the answers
            for ans in self.answers:
                if str.lower(ans) in self.guessedAnswers:
                    continue
                if hints != '':
                    hints += ' '
                if len(self.answers) > 1:
                    hints += '['
                if hintNum == 0:
                    masked = ans
                    hints += re.sub('\w', charMask, masked)
                elif hintNum == 1:
                    divider = int(len(ans) * ratio)
                    if divider > 3:
                        divider = 3
                    if divider >= len(ans):
                        divider = len(ans)-1
                    hints += ans[:divider]
                    masked = ans[divider:]
                    hints += re.sub('\w', charMask, masked)
                elif hintNum == 2:
                    divider = int(len(ans) * ratio)
                    if divider > 3:
                        divider = 3
                    if divider >= len(ans):
                        divider = len(ans)-1
                    lettersInARow=divider-1
                    maskedInARow=0
                    hints += ans[:divider]
                    ansend = ans[divider:]
                    hintsend = ''
                    unmasked = 0
                    for i in range(len(ans)-divider):
                        masked = ansend[i]
                        if masked == ' ':
                            hintsend = ' '
                            unmasked += 1
                        elif maskedInARow > 2 and unmasked < (len(ans)-divider):
                            lettersInARow += 1
                            hintsend += ansend[i]
                            unmasked += 1
                            maskedInARow = 0
                        elif lettersInARow < 3 and unmasked < (len(ans)-divider) and random.randint(0,100) < hintRatio:
                            lettersInARow += 1
                            hintsend += ansend[i]
                            unmasked += 1
                            maskedInARow = 0
                        else:
                            maskedInARow += 1
                            lettersInARow=0
                            hintsend += re.sub('\w', charMask, masked)
                    hints += hintsend
                if len(self.answers) > 1:
                    hints += ']'
            return hints

        def getOtherHintString(self):
            hintRatio = self.registryValue('hintShowRatio') # % to show each hint
            ratio = float(hintRatio * .01)
            timeElapsed = float(time.time() - self.askedAt)
            showPercentage = float((timeElapsed + (self.registryValue('timeout', self.channel)/2)) / (self.registryValue('timeout', self.channel) * 3))
            charMask = self.registryValue('charMask', self.channel)
            if len(self.answers) > 1 or len(self.answers) < 1:
                return
            ans = self.answers[0]
            divider = int(len(ans) * ratio * showPercentage + 1)
            if divider >= len(ans):
                divider = len(ans)-1
            hints = 'Hint: \x02\x0312'
            hints += ans[:divider]
            return hints

        def getOtherHint(self, username):
            if self.questionOver:
                return
            if self.shownHint == False:
                self.shownHint = True
                if len(self.answers) == 1:
                    self.sendMessage(self.getOtherHintString())

        def getRemainingKAOS(self):
            if len(self.answers) > 1:
                if self.shownHint == False:
                    self.shownHint = True
                    self.sendMessage(self.getHintString(self.hintsCounter-1))

        def loadGameState(self):
            gameInfo = self.storage.getGame(self.channel)
            if gameInfo is not None:
                self.numAsked = gameInfo[2]
                self.roundStartedAt = gameInfo[3]
                self.lastWinner = gameInfo[4]
                self.streak = int(gameInfo[5])

        def loopEvent(self):
            """
                Main game/question/hint loop called by event. Decides whether question or hint is needed.
            """
            # out of hints to give?
            if self.hintsCounter >= 3:
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

                #reset stuff
                self.answers = []
                self.alternativeAnswers = []
                self.question = ''
                self.questionOver = True

                if self.stopPending == True:
                    self.stop()
                    return

                # provide next question
                sleepTime = self.registryValue('sleepTime',self.channel)
                if sleepTime < 2:
                    sleepTime = 2
                    log.error('sleepTime was set too low(<2 seconds). setting to 2 seconds')
                sleepTime = time.time() + sleepTime
                self.queueEvent(sleepTime, self.nextQuestion)
            else:
                # give out more hints
                self.nextHint()

        def nextHint(self):
            """
                Max hints have not been reached, and no answer is found, need more hints
            """
            hints = self.getHintString(self.hintsCounter)
            #increment hints counter
            self.hintsCounter += 1
            self.sendMessage('Hint %s: %s' % (self.hintsCounter, hints), 1, 9)
            #reset hint shown
            self.shownHint = False

            timeout = 2
            if len(self.answers) > 1:
                timeout = self.registryValue('timeoutKAOS', self.channel)
            else:
                timeout = self.registryValue('timeout', self.channel)
            if timeout < 2:
                timout = 2
                log.error('timeout was set too low(<2 seconds). setting to 2 seconds')
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


            if self.stopPending == True:
                self.stop()
                return


            # reset and increment
            self.questionOver = False
            self.questionRepeated = False
            self.shownHint = False
            self.skipVoteCount = {}
            self.question = ''
            self.answers = []
            self.alternativeAnswers = []
            self.guessedAnswers = []
            self.totalAmountWon = 0
            self.lineNumber = -1
            self.correctPlayers = {}
            self.hintsCounter = 0
            self.numAsked += 1

            # grab the next q
            numQuestion = self.storage.getNumQuestions()
            if numQuestion == 0:
                self.stop()
                self.sendMessage('There are no questions. Stopping. If you are an admin use the addquestionfile to add questions to the database')
                return

            numQuestionsLeftInRound = self.storage.getNumQuestionsNotAsked(self.channel, self.roundStartedAt)
            if numQuestionsLeftInRound == 0:
                self.numAsked = 1
                self.roundStartedAt = time.mktime(time.localtime())
                self.storage.updateGameRoundStarted(self.channel, self.roundStartedAt)
                self.sendMessage('All of the questions have been asked, shuffling and starting over')

            self.storage.updateGame(self.channel, self.numAsked) #increment q's asked
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

            tempQuestion = self.question.rstrip()
            if tempQuestion[-1:] != '?':
                tempQuestion += ' ?'

            # bold the q
            questionText = '%s' % (tempQuestion)

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

        def repeatQuestion(self):
            if self.questionRepeated == True:
                return
            if self.questionOver == True:
                return
            self.questionRepeated = True
            try:
                tempQuestion = self.question.rstrip()
                if tempQuestion[-1:] != '?':
                    tempQuestion += ' ?'

                # bold the q
                questionText = '%s' % (tempQuestion)

                # KAOS? report # of answers
                if len(self.answers) > 1:
                    questionText += ' %d possible answers' % (len(self.answers))

                self.sendMessage('.%s. %s' % (self.numAsked, questionText), 1, 9)
            except AttributeError:
                pass

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
            lineNumber, question = self.retrieveQuestionFromSql()
            answer = question.split('*', 1)
            if len(answer) > 1:
                question = answer[0].strip()
                answers = answer[1].split('*')
                answer = []
                alternativeAnswers = []
                if str.lower(question[:4]) == 'kaos':
                    for ans in answers:
                        answer.append(ans.strip())
                elif str.lower(question[:5]) == 'uword':
                    for ans in answers:
                        answer.append(ans)
                        question = 'Unscramble the letters: '
                        shuffledLetters = list(ans)
                        random.shuffle(shuffledLetters)
                        for letter in shuffledLetters:
                            question += str.lower(letter)
                            question += ' '
                        break
                else:                
                    for ans in answers:
                        if answer == []:
                            answer.append(str(ans).strip())
                        else:
                            alternativeAnswers.append(str(ans).strip())

                points = self.registryValue('defaultPoints', self.channel)
                if len(answer) > 1:
                    points = self.registryValue('defaultPointsKAOS', self.channel) * len(answers)
                return {'p':points,
                        'q':question,
                        'a':answer, 
                        'aa':alternativeAnswers, 
                        '#':lineNumber
                        }
            else:
                log.info('Bad question found on line#%d' % lineNumber)
                # TODO report bad question

            # default question, everything went wrong with grabbing question
            return {'#':lineNumber,
                    'p':10050,
                    'q':'KAOS: The 10 Worst U.S. Presidents (Last Name Only)? (This is a panic question, if you see this report this question. it is malformed.)',
                    'a':['Bush', 'Nixon', 'Hoover', 'Grant', 'Johnson', 
                            'Ford', 'Reagan', 'Coolidge', 'Pierce'], 
                    'aa':['Obama']
                    }

        def retrieveQuestionFromSql(self):
            question = self.storage.getRandomQuestionNotAsked(self.channel, self.roundStartedAt)
            question = question[0]
            return (question[0], question[2])

        def sendMessage(self, msg, color=None, bgcolor=None):
            """ <msg>, [<color>], [<bgcolor>]

                helper for game instance to send messages to channel
            """
            # with colors? bgcolor?
            if color is None:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, ' %s ' % msg))
            elif bgcolor is None:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x03%02d %s ' % (color, msg)))
            else:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x03%02d,%02d %s ' % (color, bgcolor, msg)))

        def stop(self):
            """
                Stop a game in progress
            """
            # responsible for stopping a timer/thread after being told to stop
            self.active = False
            self.removeEvent()
            self.sendMessage(self.registryValue('stopped'), 2)
            if self.channel in self.games:
                del self.games[self.channel]

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

        def chunk(self, qs, rows=10000):
            """ Divides the data into 10000 rows each """
            for i in xrange(0, len(qs), rows):
                yield qs[i:i+rows]

        def deleteQuestion(self, questionId):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                deleted=1
                                where id=?''', (questionId,))
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

        def dropQuestionTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviaquestion''')
            except:
                pass
            c.close()

        def dropTemporaryQuestionTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviatemporaryquestion''')
            except:
                pass
            c.close()

        def dropEditTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''drop table triviaedit''')
            except:
                pass
            c.close()

        def getRandomQuestionNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            c.execute('''select * from triviaquestion 
                            where id not in (select line_num from triviagameslog where deleted=1 or (channel=? and asked_at>=?))
                            order by random() limit 1''', (str.lower(channel),roundStart))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getQuestionByRound(self, roundNumber, channel):
            channel=str.lower(channel)
            c = self.conn.cursor()
            c.execute('''select * from triviaquestion where id=(select tgl.line_num
                                                                from triviagameslog tgl
                                                                where tgl.round_num=?
                                                                and tgl.channel=?
                                                                order by id desc
                                                                limit 1)''', (roundNumber,channel))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getNumQuestionsNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            result = c.execute('''select count(id) from triviaquestion 
                            where id not in (select line_num from triviagameslog where deleted=1 or (channel=? and asked_at>=?))''', 
                                    (channel,roundStart))
            rows = result.fetchone()[0]
            c.close()
            return rows

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

        def getNumUser(self):
            c = self.conn.cursor()
            result = c.execute('select count(*) from triviausers')
            result = result.fetchone()[0]
            c.close()
            return result

        def getNumQuestions(self):
            c = self.conn.cursor()
            result = c.execute('select count(*) from triviaquestion where deleted=0')
            result = result.fetchone()[0]
            c.close()
            return result

        def getNumKAOS(self):
            c = self.conn.cursor()
            result = c.execute('select count(*) from triviaquestion where lower(substr(question,1,4))=?',('kaos',))
            result = result.fetchone()[0]
            c.close()
            return result

        def getQuestion(self, id):
            c = self.conn.cursor()
            c.execute('select * from triviaquestion where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getNumActiveThisWeek(self):
            d = datetime.date.today()
            weekday=d.weekday()
            d -= datetime.timedelta(weekday)
            weekSqlString = ''
            for i in range(7):
                if i > 0:
                    weekSqlString += ' or ' 
                weekSqlString += '''
                            (tl.year=%d
                            and tl.month=%d
                            and tl.day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)
            c = self.conn.cursor()
            weekSql = '''select count(distinct(tl.username))
                        from triviauserlog tl
                        where '''
            weekSql += weekSqlString
            result = c.execute(weekSql)
            rows = result.fetchone()[0]
            return rows

        def getReportById(self, id):
            c = self.conn.cursor()
            c.execute('select * from triviareport where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getReportTop3(self):
            c = self.conn.cursor()
            c.execute('select * from triviareport order by id desc limit 3')
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getTemporaryQuestionTop3(self):
            c = self.conn.cursor()
            c.execute('select * from triviatemporaryquestion order by id desc limit 3')
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getTemporaryQuestionById(self, id):
            c = self.conn.cursor()
            c.execute('select * from triviatemporaryquestion where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getEditById(self, id):
            c = self.conn.cursor()
            c.execute('select * from triviaedit where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getNumUserActiveIn(self,timeSeconds):
            epoch = int(time.mktime(time.localtime()))
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviauserlog 
                        where day=? and month=? and year=?
                        and last_updated>?''', (day, month, year,(epoch-timeSeconds)))
            rows = result.fetchone()[0]
            c.close()
            return rows

        def gameExists(self, channel):
            channel = str.lower(channel)
            c = self.conn.cursor()
            result = c.execute('select count(id) from triviagames where channel=?', (channel,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def getEditTop3(self):
            c = self.conn.cursor()
            c.execute('select * from triviaedit order by id desc limit 3')
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def insertUserLog(self, username, score, numAnswered, timeTaken, day=None, month=None, year=None, epoch=None):
            if day == None and month == None and year == None:
                dateObject = datetime.date.today()
                day   = dateObject.day
                month = dateObject.month
                year  = dateObject.year
            score = int(score)
            if epoch is None:
                epoch = int(time.mktime(time.localtime()))
            if self.userLogExists(username, day, month, year):
                return self.updateUserLog(username, score, numAnswered, timeTaken, day, month, year, epoch)
            c = self.conn.cursor()
            username = str.lower(username)
            scoreAvg = 'NULL'
            if numAnswered >= 1:
                scoreAvg = score / numAnswered
            c.execute('insert into triviauserlog values (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                                    (username, score, numAnswered, day, month, year, epoch, timeTaken, scoreAvg))
            self.conn.commit()
            c.close()

        def insertUser(self, username, numReported=0, numAccepted=0):
            username = str.lower(username)
            if self.userExists(username):
                return self.updateUser(username)
            c = self.conn.cursor()
            c.execute('insert into triviausers values (NULL, ?, ?, ?)', (username,numReported,numAccepted))
            self.conn.commit()
            c.close()

        def insertGame(self, channel, numAsked=0, epoch=None):
            channel = str.lower(channel)
            lastWinner  = str.lower(lastWinner)
            if self.gameExists(channel):
                return self.updateGame(channel, numAsked)
            if epoch is None:
                epoch = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviagames values (NULL, ?, ?, ?)', (channel,numAsked,epoch))
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

        def insertReport(self, channel, username, reportText, questionNum, reportedAt=None):
            channel = str.lower(channel)
            username = str.lower(username)
            if reportedAt is None:
                reportedAt = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviareport values (NULL, ?, ?, ?, ?, NULL, NULL, ?)', 
                                        (channel,username,reportText,reportedAt,questionNum))
            self.conn.commit()
            c.close()

        def insertQuestionsBulk(self, questions):
            c = self.conn.cursor()
            #skipped=0
            divData = self.chunk(questions) # divide into 10000 rows each
            for chunk in divData:
                c.executemany('''insert into triviaquestion values (NULL, ?, ?, 0)''', 
                                            chunk)
            self.conn.commit()
            skipped = self.removeDuplicateQuestions()
            c.close()
            return ((len(questions) - skipped), skipped)

        def insertEdit(self, questionId, questionText, username, channel, createdAt=None):
            c = self.conn.cursor()
            username = str.lower(username)
            channel = str.lower(channel)
            if createdAt is None:
                createdAt = int(time.mktime(time.localtime()))
            c.execute('insert into triviaedit values (NULL, ?, ?, NULL, ?, ?, ?)', 
                                        (questionId,questionText,username,channel,createdAt))
            self.conn.commit()
            c.close()

        def insertTemporaryQuestion(self, username, channel, question):
            c = self.conn.cursor()
            username = str.lower(username)
            channel = str.lower(channel)
            c.execute('insert into triviatemporaryquestion values (NULL, ?, ?, ?)', 
                                        (username,channel,question))
            self.conn.commit()
            c.close()

        def makeUserTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviausers (
                        id integer primary key autoincrement, 
                        username text not null unique,
                        num_reported integer,
                        num_accepted integer
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
                        last_updated integer,
                        average_time integer,
                        average_score integer,
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
                        num_asked integer,
                        round_started integer,
                        last_winner text,
                        streak integer
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
                        fixed_by text,
                        question_num integer
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeTemporaryQuestionTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviatemporaryquestion (
                        id integer primary key autoincrement,
                        username text,
                        channel text,
                        question text
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeQuestionTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviaquestion (
                        id integer primary key autoincrement,
                        question_canonical text,
                        question text,
                        deleted integer not null default 0
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeEditTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviaedit (
                        id integer primary key autoincrement,
                        question_id integer,
                        question text,
                        status text,
                        username text,
                        channel text,
                        created_at text
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def questionExists(self, question):
            c = self.conn.cursor()
            result = c.execute('select count(id) from triviaquestion where question=? or question_canonical=?', (question,question))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def questionIdExists(self, id):
            c = self.conn.cursor()
            result = c.execute('select count(id) from triviaquestion where id=?', (id,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def removeDuplicateQuestions(self):
            c = self.conn.cursor()
            c.execute('''delete from triviaquestion where id not in (select min(id) from triviaquestion GROUP BY question_canonical)''')
            num = c.rowcount
            self.conn.commit()
            c.close()
            return num

        def removeEdit(self, editId):
            c = self.conn.cursor()
            c.execute('''delete from triviaedit
                        where id=?''', (editId,))
            self.conn.commit()
            c.close()

        def removeReport(self, repId):
            c = self.conn.cursor()
            c.execute('''delete from triviareport
                        where id=?''', (repId,))
            self.conn.commit()
            c.close()

        def removeTemporaryQuestion(self, id):
            c = self.conn.cursor()
            c.execute('''delete from triviatemporaryquestion
                        where id=?''', (id,))
            self.conn.commit()
            c.close()

        def removeUserLogs(self, username):
            username = str.lower(username)
            c = self.conn.cursor()
            c.execute('''delete from triviauserlog
                        where username=?''', (username,))
            self.conn.commit()
            c.close()

        def transferUserLogs(self, userFrom, userTo): 
            userFrom = str.lower(userFrom) 
            userTo = str.lower(userTo)
            c = self.conn.cursor()
            c.execute('''
                    update triviauserlog
                    set num_answered=num_answered
                            +ifnull(
                                    (
                                            select t3.num_answered 
                                            from triviauserlog t3 
                                            where t3.day=triviauserlog.day 
                                            and t3.month=triviauserlog.month 
                                            and t3.year=triviauserlog.year 
                                            and t3.username=?
                                    )
                            ,0),
                    points_made=points_made
                            +ifnull(
                                    (
                                            select t2.points_made 
                                            from triviauserlog t2 
                                            where t2.day=triviauserlog.day 
                                            and t2.month=triviauserlog.month 
                                            and t2.year=triviauserlog.year 
                                            and t2.username=?
                                    )
                            ,0)
                    where id in (
                            select id 
                            from triviauserlog tl 
                            where username=? 
                            and exists (
                                    select id 
                                    from triviauserlog tl2 
                                    where tl2.day=tl.day
                                    and tl2.month=tl.month 
                                    and tl2.year=tl.year 
                                    and username=?
                            )
                    )
            ''', (userFrom,userFrom,userTo,userFrom))

            c.execute('''
                    update triviauserlog
                    set username=?
                    where username=? 
                    and not exists (
                            select 1 
                            from triviauserlog tl 
                            where tl.day=triviauserlog.day 
                            and tl.month=triviauserlog.month 
                            and tl.year=triviauserlog.year 
                            and tl.username=?
                    )
            ''',(userTo, userFrom, userTo))
            self.conn.commit()

            self.removeUserLogs(userFrom)

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
            result = c.execute('select count(id) from triviausers where lower(username)=?', usr)
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def updateUserLog(self, username, score, numAnswered, timeTaken, day=None, month=None, year=None, epoch=None):
            username = str.lower(username)
            if not self.userExists(username):
                self.insertUser(username)
            if day == None and month == None and year == None:
                dateObject = datetime.date.today()
                day   = dateObject.day
                month = dateObject.month
                year  = dateObject.year
            if epoch is None:
                epoch = int(time.mktime(time.localtime()))
            if not self.userLogExists(username, day, month, year):
                return self.insertUserLog(username, score, numAnswered, timeTaken, day, month, year, epoch)
            c = self.conn.cursor()
            usr = str.lower(username)
            scr = score
            numAns = numAnswered
            test = c.execute('''update triviauserlog set 
                                points_made = points_made+?,
                                average_time=( average_time * (1.0*num_answered/(num_answered+?)) + ? * (1.0*?/(num_answered+?)) ),
                                average_score=( average_score * (1.0*num_answered/(num_answered+?)) + ? * (1.0*?/(num_answered+?)) ),
                                num_answered = num_answered+?,
                                last_updated = ?
                                where username=?
                                and day=? 
                                and month=? 
                                and year=?''', (scr,numAns,timeTaken,numAns,numAns,numAns,score,numAns,numAns,numAns,epoch,usr,day,month,year))
            self.conn.commit()
            c.close()

        def updateUser(self, username, numReported=0, numAccepted=0):
            username = str.lower(username)
            if not self.userExists(username):
                return self.insertUser(username, numReported, numAccepted)
            c = self.conn.cursor()
            c.execute('''update triviausers set
                                num_reported=num_reported+?,
                                num_accepted=num_accepted+?
                                where username=?''', (numReported, numAccepted, username))
            self.conn.commit()
            c.close()
            
        def updateGame(self, channel, numAsked):
            channel = str.lower(channel)
            if not self.gameExists(channel):
                return self.insertGame(channel, numAsked)
            c = self.conn.cursor()
            test = c.execute('''update triviagames set
                                num_asked=?
                                where channel=?''', (numAsked, channel))
            self.conn.commit()
            c.close()

        def updateGameStreak(self, channel, lastWinner, streak):
            channel = str.lower(channel)
            lastWinner  = str.lower(lastWinner)
            if not self.gameExists(channel):
                return self.insertGame(channel, 0, None)
            c = self.conn.cursor()
            test = c.execute('''update triviagames set
                                last_winner=?,
                                streak=?
                                where channel=?''', (lastWinner, streak, channel))
            self.conn.commit()
            c.close()

        def updateGameRoundStarted(self, channel, lastRoundStarted):
            channel = str.lower(channel)
            if not self.gameExists(channel):
                return self.insertGame(channel, numAsked)
            c = self.conn.cursor()
            test = c.execute('''update triviagames set
                                round_started=?
                                where channel=?''', (lastRoundStarted, channel))
            self.conn.commit()
            c.close()

        def updateQuestion(self, id, newQuestion):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                question=?
                                where id=?''', (newQuestion, id))
            self.conn.commit()
            c.close()

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

        def viewAllTimeTop10(self):
            c = self.conn.cursor()
            c.execute('''select id,
                        username,
                        sum(points_made),
                        sum(num_answered)
                        from triviauserlog
                        group by username 
                        order by points_made desc 
                        limit 10''')

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewMonthTop10(self, year=None, month=None):
            d = datetime.date.today()
            if year is None or month is None:
                year = d.year
                month = d.month
            c = self.conn.cursor()

            c.execute('''select id,
                        username,
                        sum(points_made),
                        sum(num_answered)
                        from triviauserlog 
                        where year=? and month=?
                        group by username 
                        order by points_made desc 
                        limit 10''', (year,month))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewYearTop10(self, year=None):
            d = datetime.date.today()
            if year is None:
                year = d.year
            c = self.conn.cursor()

            c.execute('''select id,
                        username,
                        sum(points_made),
                        sum(num_answered)
                        from triviauserlog 
                        where year=?
                        group by username 
                        order by points_made desc 
                        limit 10''', (year,))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewWeekTop10(self):
            d = datetime.date.today()
            weekday=d.weekday()
            d -= datetime.timedelta(weekday)
            weekSqlString = ''
            for i in range(7):
                if i > 0:
                    weekSqlString += ' or ' 
                weekSqlString += '''
                            (year=%d
                            and month=%d
                            and day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)
            c = self.conn.cursor()
            weekSql = '''select id,
                        username,
                        sum(points_made),
                        sum(num_answered)
                        from triviauserlog 
                        where '''
            weekSql += weekSqlString
            weekSql += ''' group by username order by points_made desc limit 10'''
            c.execute(weekSql)

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def wasUserActiveIn(self,username,timeSeconds):
            username = str.lower(username)
            epoch = int(time.mktime(time.localtime()))
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviauserlog 
                        where day=? and month=? and year=?
                        and username=? and last_updated>?''', (day, month, year,username,(epoch-timeSeconds)))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

Class = TriviaTime
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
