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
import os
import re
import sqlite3
import random
import time
import datetime
import unicodedata
import hashlib

class TriviaTime(callbacks.Plugin):
    """
    TriviaTime - A trivia word game, guess the word and score points. 
    Play KAOS rounds and work together to solve clues to find groups of words.
    """
    threaded = True # enables threading for supybot plugin
    currentDBVersion = 1.2

    def __init__(self, irc):
        log.info('*** Loaded TriviaTime!!! ***')
        self.__parent = super(TriviaTime, self)
        self.__parent.__init__(irc)

        # games info
        self.games = {} # separate game for each channel

        #Database amend statements for outdated versions
        self.dbamends = {} #Formatted like this: <DBVersion>: "<ALTERSTATEMENT>; <ALTERSTATEMENT>;" (This IS valid SQL as long as we include the semicolons)

        # connections
        dbLocation = self.registryValue('admin.sqlitedb')
        # tuple head, tail ('example/example/', 'filename.txt')
        dbFolder = os.path.split(dbLocation)
        # take folder from split
        dbFolder = dbFolder[0]
        # create the folder
        if not os.path.exists(dbFolder):
            log.info('The database location did not exist, creating folder structure')
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
        #triviainfo table check
        #if self.storage.isTriviaVersionSet():
        if self.storage.getVersion() != None and self.storage.getVersion() != self.currentDBVersion:
            return

    def doPrivmsg(self, irc, msg):
        """
            Catches all PRIVMSG, including channels communication
        """
        username = msg.nick
        try:
            # rootcoma!~rootcomaa@unaffiliated/rootcoma
            user = ircdb.users.getUser(msg.prefix)
            username = user.name
        except KeyError:
            pass
        channel = msg.args[0]
        # Make sure that it is starting inside of a channel, not in pm
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        channelCanonical = ircutils.toLower(channel)

        otherHintCommand = self.registryValue('commands.showHintCommandKAOS', channel)
        kaosRemainingCommand = self.registryValue('commands.extraHint', channel)

        if channelCanonical in self.games:
            # Look for command to list remaining KAOS
            if msg.args[1] == otherHintCommand:
                self.games[channelCanonical].getRemainingKAOS()
            elif msg.args[1] == kaosRemainingCommand:
                self.games[channelCanonical].getOtherHint()
            else:
                # check the answer
                self.games[channelCanonical].checkAnswer(msg)

    def doJoin(self,irc,msg):
        username = msg.nick
        # is it a user?
        try:
            # rootcoma!~rootcomaa@unaffiliated/rootcoma
            user = ircdb.users.getUser(msg.prefix)
            username = user.name
        except KeyError:
            pass
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            user = threadStorage.getUser(username, None)
        else:
            user = threadStorage.getUser(username, channel)
        numTopToVoice = self.registryValue('voice.numTopToVoice')
        minPointsVoiceYear = self.registryValue('voice.minPointsVoiceYear')
        minPointsVoiceMonth = self.registryValue('voice.minPointsVoiceMonth')
        minPointsVoiceWeek = self.registryValue('voice.minPointsVoiceWeek')
        if len(user) >= 1:
            if user[13] <= numTopToVoice and user[4] >= minPointsVoiceYear:
                irc.sendMsg(
                        ircmsgs.privmsg(channel, 
                                'Giving MVP to %s for being top #%d this YEAR' % (username, user[13])
                                )
                        )
                irc.queueMsg(ircmsgs.voice(channel, username))
            elif user[14] <= numTopToVoice and user[6] >= minPointsVoiceMonth:
                irc.sendMsg(
                        ircmsgs.privmsg(channel, 
                                'Giving MVP to %s for being top #%d this MONTH' % (username, user[14])
                                )
                        )
                irc.queueMsg(ircmsgs.voice(channel, username))
            elif user[15] <= numTopToVoice and user[8] >= minPointsVoiceWeek:
                irc.sendMsg(
                        ircmsgs.privmsg(channel, 
                                'Giving MVP to %s for being top #%d this WEEK' % (username, user[15])
                                )
                        )
                irc.queueMsg(ircmsgs.voice(channel, username))

    def doNotice(self,irc,msg):
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
                    irc.sendMsg(ircmsgs.notice(username, '%s: Ping reply: %0.2f seconds' % (username, pingTime)))
                else:
                    irc.sendMsg(ircmsgs.privmsg(channel, '%s: Ping reply: %0.2f seconds' % (username, pingTime)))

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

    def acceptdelete(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Accept a question deletion
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        delete = self.storage.getDeleteById(num)
        if len(delete) < 1:
            irc.error('Could not find that delete')
        else:
            delete = delete[0]
            questionNumber = delete[3]
            irc.reply('Question #%d deleted!' % delete[3])
            threadStorage.removeReportByQuestionNumber(delete[3])
            threadStorage.removeEditByQuestionNumber(delete[3])
            threadStorage.deleteQuestion(questionNumber)
            threadStorage.removeDelete(num)
            threadStorage.removeDeleteByQuestionNumber(questionNumber)
    acceptdelete = wrap(acceptdelete, ['user', ('checkChannelCapability', 'triviamod'), 'int'])
        
    def acceptedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Accept a question edit, and remove edit. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        edit = self.storage.getEditById(num)
        if len(edit) < 1:
            irc.error('Could not find that edit')
        else:
            edit = edit[0]
            question = threadStorage.getQuestion(edit[1])
            threadStorage.updateQuestion(edit[1], edit[2])
            threadStorage.updateUser(edit[4], 0, 1)
            threadStorage.removeEdit(edit[0])
            threadStorage.removeReportByQuestionNumber(edit[1])
            irc.reply('Question #%d updated!' % edit[1])
            irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (edit[2])))
            if len(question) > 0:
                question = question[0]
                irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (question[2])))
            else:
                irc.error('Question could not be found for this edit')
    acceptedit = wrap(acceptedit, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def acceptnew(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Accept a new question, and add it to the database. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        q = threadStorage.getTemporaryQuestionById(num)
        if len(q) < 1:
            irc.error('Could not find that temp question')
        else:
            q = q[0]
            threadStorage.updateUser(q[1], 0, 0, 0, 0, 1)
            threadStorage.insertQuestionsBulk([(q[3], q[3])])
            threadStorage.removeTemporaryQuestion(q[0])
            irc.reply('Question accepted!')
    acceptnew = wrap(acceptnew, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def addquestion(self, irc, msg, arg, question):
        """<question text>
        Adds a question to the database
        """
        username = msg.nick
        channel = msg.args[0]
        charMask = self.registryValue('hints.charMask', channel)
        if charMask not in question:
            irc.error(' The question must include the separating character %s ' % (charMask))
            return
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        threadStorage.updateUser(username, 0, 0, 0, 1)
        threadStorage.insertTemporaryQuestion(username, channel, question)
        irc.reply(' Thank you for adding your question to the question database, it is awaiting approval. ')
    addquestion = wrap(addquestion, ['text'])

    def addfile(self, irc, msg, arg, filename):
        """[<filename>]
        Add a file of questions to the question database, 
        filename defaults to configured quesiton file.
        """
        if filename is None:
            filename = self.registryValue('admin.quizfile')
        try:
            filesLines = open(filename).readlines()
        except:
            irc.error('Could not open file to add to database. Make sure it exists on the server.')
            return
        irc.reply('Adding questions from %s to database.. This may take a few minutes' % filename)
        insertList = []
        for line in filesLines:
            insertList.append((str(line).strip(),str(line).strip()))
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        info = threadStorage.insertQuestionsBulk(insertList)
        irc.reply('Successfully added %d questions, skipped %d' % (info[0], info[1]))
    addfile = wrap(addfile, ['admin', optional('text')])

    def authweb(self, irc, msg, arg):
        """
        Triviamods only. Register for web access
        """
        try:
            user = ircdb.users.getUser(msg.prefix)
        except KeyError:
            irc.error('Sorry, you must be at least a triviamod to register for web login')
            return

        if not user.capabilities.check('triviamod'):
            irc.error('Sorry, you must be at least a triviamod to register for web login')

        capability = 'triviamod'

        if user.capabilities.check('owner'):
            capability = 'owner'

        username = user.name
        salt = ''
        password = ''
        isHashed = user.hashed
        if isHashed:
            (salt, password) = user.password.split('|')
        else:
            password = user.password

        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        info = threadStorage.insertLogin(username, salt, isHashed, password, capability)
        irc.reply('Success, updated your web access login.')
    authweb = wrap(authweb)

    def clearpoints(self, irc, msg, arg, username):
        """<username>
        Deletes all of a users points, and removes all their records
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        threadStorage.removeUserLogs(username)
        irc.reply('Removed all points from %s' % (username))
    clearpoints = wrap(clearpoints, ['admin','nick'])

    def day(self, irc, msg, arg, num):
        """[<number>]
            Displays the top ten scores of the day. 
            Parameter is optional, display up to that number. 
            eg 20 - display 11-20
        """
        if num is None or num < 10:
            num=10
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        tops = []
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewDayTop10(None, num)
        else:
            tops = threadStorage.viewDayTop10(channel, num)
        offset = num-9
        topsList = ['Today\'s Top 10 Players: ']
        for i in range(len(tops)):
            topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i][1]), tops[i][2]))
        topsText = ''.join(topsList)
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    day = wrap(day, [optional('int')])

    def deletequestion(self, irc, msg, arg, channel, t, id):
        """[<channel>] [<type "R" or "Q">] <question id>
        Deletes a question from the database. Type decides whether to delete
        by round number (r), or question number (q) (default round).
        Channel is only necessary when editing from outside of the channel
        """
        username = msg.nick
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if t is None or str.lower(t) == "round":
            q = threadStorage.getQuestionByRound(id, channel)
            if len(q) < 1:
                irc.error('Could not find that round.')
                return
            id = q[0][0]
        if not threadStorage.questionIdExists(id):
            irc.error('That question does not exist.')
            return
        if threadStorage.isQuestionDeleted(id):
            irc.error('That question is already deleted.')
            return
        if threadStorage.isQuestionPendingDeletion(id):
            irc.error('That question is already pending deletion.')
            return
        threadStorage.insertDelete(username, channel, id)
        irc.reply('Question %d marked for deletion and pending review.' % id)
    deletequestion = wrap(deletequestion, ["channel", optional(('literal',("question", "QUESTION", "ROUND", "round"))),'int'])

    def edit(self, irc, msg, arg, user, channel, num, question):
        """[<channel>] <question number> <corrected text>
        Correct a question by providing the question number and the corrected text. 
        Channel is only necessary when editing from outside of the channel
        """
        username = msg.nick
        try:
            #rootcoma!~rootcomaa@unaffiliated/rootcoma
            user = ircdb.users.getUser(msg.prefix) 
            username = user.name
        except KeyError:
            pass
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        q = threadStorage.getQuestion(num)
        if len(q) > 0:
            q = q[0]
            questionParts = question.split('*')
            if len(questionParts) < 2:
                oldQuestionParts = q[2].split('*')
                questionParts.extend(oldQuestionParts[1:])
                question = questionParts[0]
                for part in questionParts[1:]:
                    question += '*'
                    question += part
            threadStorage.insertEdit(num, question, username, msg.args[0])
            threadStorage.updateUser(username, 1, 0)
            irc.reply('Success! Submitted edit for further review.')
            irc.sendMsg(ircmsgs.notice(msg.nick, 'NEW: %s' % (question)))
            irc.sendMsg(ircmsgs.notice(msg.nick, 'OLD: %s' % (q[2])))
        else:
            irc.error('Question does not exist')
    edit = wrap(edit, ['user', ('checkChannelCapability', 'triviamod'), 'int', 'text'])

    def givepoints(self, irc, msg, arg, username, points, days):
        """<username> <points> [<daysAgo>]

        Give a user points, last argument is optional amount of days in past to add records
        """
        if points < 1:
            irc.error("You cannot give less than 1 point.")
            return
        try:
            user = ircdb.users.getUser(username)
            username = user.name
        except KeyError:
            pass
        day=None
        month=None
        year=None
        if days is not None:
            d = datetime.date.today()
            d -= datetime.timedelta(days)
            day = d.day
            month = d.month
            year = d.year
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        threadStorage.updateUserLog(username, channel, points, 0, 0, day, month, year)
        irc.reply('Added %d points to %s' % (points, username))
    givepoints = wrap(givepoints, ['admin','nick', 'int', optional('int')])

    def listdeletes(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List deletes.
        Channel is only required when using the command outside of a channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        count = threadStorage.countDeletes()
        if page is None or page < 1:
            page=1
        pages = int(count/3)
        deletes = threadStorage.getDeleteTop3(page)
        if count % 3 > 0:
            pages += 1
        if count < 1:
            irc.reply('No deletes found')
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for delete in deletes:
                question = threadStorage.getQuestion(delete[3])
                questionText = 'Question not found'
                if len(question) > 0:
                    question = question[0]
                    questionText = question[2]
                irc.reply('Delete #%d, by %s Question#%d: %s'%(delete[0], delete[1], delete[3], questionText))
            irc.reply('Use the showdelete command to see more information')
    listdeletes = wrap(listdeletes, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def listedits(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List edits.
        Channel is only required when using the command outside of a channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        count = threadStorage.countEdits()
        if page is None or page < 1:
            page=1
        pages = int(count/3)
        edits = threadStorage.getEditTop3(page)
        if count % 3 > 0:
            pages += 1
        if count < 1:
            irc.reply('No edits found')
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for edit in edits:
                irc.reply('Edit #%d, Question#%d, NEW:%s'%(edit[0], edit[1], edit[2]))
            irc.reply('Use the showedit command to see more information')
    listedits = wrap(listedits, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def listreports(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List reports.
        Channel is only required when using the command outside of a channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        count = threadStorage.countReports()
        if page is None or page < 1:
            page=1
        pages = int(count/3)
        reports = threadStorage.getReportTop3(page)
        if count % 3 > 0:
            pages += 1
        if count < 1:
            irc.reply('No reports found')
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for report in reports:
                irc.reply('Report #%d `%s` by %s on %s Q#%d '%(report[0], report[3], report[2], report[1], report[7]))
            irc.reply('Use the showreport command to see more information')
    listreports = wrap(listreports, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def listnew(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List questions awaiting approval.
        Channel is only required when using the command outside of a channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        count = threadStorage.countTemporaryQuestions()
        if page is None or page < 1:
            page=1
        pages = int(count/3)
        if count % 3 > 0:
            pages += 1
        q = threadStorage.getTemporaryQuestionTop3(page)
        if count < 1:
            irc.reply('No new questions found')
        else:
            irc.reply('Showing page %i of %i' % (page, pages))
            for ques in q:
                irc.reply('Temp Q #%d: %s'%(ques[0], ques[3]))
            irc.reply('Use the shownew to see more information')
    listnew = wrap(listnew, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def info(self, irc, msg, arg):
        """
        Get TriviaTime information, how many questions/users in database, time, etc
        """
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        totalUsersEver = threadStorage.getNumUser(channel)
        numActiveThisWeek = threadStorage.getNumActiveThisWeek(channel)
        infoText = ' TriviaTime v1.0-beta by Trivialand on Freenode https://github.com/tannn/TriviaTime '
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        infoText = ' Time is %s ' % (time.asctime(time.localtime(),))
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        infoText = '\x02 %d Users\x02 on scoreboard \x02%d Active This Week\x02' % (totalUsersEver, numActiveThisWeek)
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
        numKaos = threadStorage.getNumKAOS()
        numQuestionTotal = threadStorage.getNumQuestions()
        infoText = '\x02 %d Questions\x02 and \x02%d KAOS\x02 (\x02%d Total\x02) in the database ' % ((numQuestionTotal-numKaos), numKaos, numQuestionTotal)
        irc.sendMsg(ircmsgs.privmsg(msg.args[0], infoText))
    info = wrap(info)

    def ping(self, irc, msg, arg):
        """
        Check your ping to the bot. Make sure your client correclty responds to ctcp pings
        """
        channel = msg.args[0]
        channelHash = self.shortHash(ircutils.toLower(channel))
        username = msg.nick
        irc.sendMsg(ircmsgs.privmsg(username, '\x01PING %0.2f*%s\x01' % (time.time()-1300000000, channelHash)))
    ping = wrap(ping)

    def me(self, irc, msg, arg):
        """
            Get your rank, score & questions asked for day, month, year
        """
        username = msg.nick
        identified = False
        try:
            user = ircdb.users.getUser(msg.prefix)
            username = user.name
            identified = True
        except KeyError:
            pass
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            info = threadStorage.getUser(username, None)
        else:
            info = threadStorage.getUser(username, channel)
        if len(info) < 3:
            errorMessage = 'You do not have any points.'
            identifyMessage = ''
            if not identified:
                identifyMessage = ' You should identify to keep track of your score more accurately.'
            irc.reply('%s%s' % (errorMessage, identifyMessage))
        else:
            hasPoints = False
            infoList = ['%s\'s Stats: Points (answers)' % (self.addZeroWidthSpace(info[1]))]
            if info[10] > 0 or info[16] > 0 or info[11] > 0:
                hasPoints = True
                infoList.append(' \x02Today:\x02 #%d %d (%d)' % (info[16], info[10], info[11]))
            if info[15] > 0 or info[8] > 0 or info[9] > 0:
                hasPoints = True
                infoList.append(' \x02This Week:\x02 #%d %d (%d)' % (info[15], info[8], info[9]))
            if info[14] > 0 or info[6] > 0 or info[7] > 0:
                hasPoints = True
                infoList.append(' \x02This Month:\x02 #%d %d (%d)' % (info[14], info[6], info[7]))
            if info[13] > 0 or info[4] > 0 or info[5] > 0:
                hasPoints = True
                infoList.append(' \x02This Year:\x02 #%d %d (%d)' % (info[13], info[4], info[5]))
            if not hasPoints:
                infoList = ['%s: You do not have any points.' % (username)]
                if not identified:
                    infoList.append(' You should identify to keep track of your score more accurately.')
            infoText = ''.join(infoList)
            irc.sendMsg(ircmsgs.privmsg(channel, infoText))
        irc.noReply()
    me = wrap(me)

    def month(self, irc, msg, arg, num):
        """[<number>]
            Displays the top ten scores of the month. 
            Parameter is optional, display up to that number. 
            eg 20 - display 11-20
        """
        if num is None or num < 10:
            num=10
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewMonthTop10(None, num)
        else:
            tops = threadStorage.viewMonthTop10(channel, num)
        topsList = ['This Month\'s Top 10 Players: ']
        offset = num-9
        for i in range(len(tops)):
            topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i][1]), tops[i][2]))
        topsText = ''.join(topsList)
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    month = wrap(month, [optional('int')])

    def next(self, irc, msg, arg):
        """
        Skip to the next question immediately. This can only be used by someone with a certain streak.
        """
        username = msg.nick
        channel = msg.args[0]
        try:
            user = ircdb.users.getUser(msg.prefix)
            username = user.name
        except KeyError:
            pass

        if not irc.isChannel(channel):
            irc.error('This command can only be used in a channel.')
            return

        minStreak = self.registryValue('general.nextMinStreak', channel)
        channelCanonical = ircutils.toLower(channel)

        # Trivia isn't running
        if channelCanonical not in self.games or self.games[channelCanonical].active != True:
            irc.sendMsg(ircmsgs.privmsg(channel, '%s: Trivia is not currently running.' % (username)))
            irc.noReply()
            return
        # Question is still being asked, not over
        if self.games[channelCanonical].questionOver == False:
            irc.sendMsg(ircmsgs.privmsg(channel, '%s: You must wait until the current question is over.' % (username)))
            irc.noReply()
            return
        # Username isnt the streak holder
        if self.games[channelCanonical].lastWinner != ircutils.toLower(username):
            irc.sendMsg(ircmsgs.privmsg(channel, '%s: You are not currently the streak holder.' % (username)))
            irc.noReply()
            return
        # Streak isnt high enough
        if self.games[channelCanonical].streak < minStreak:
            irc.sendMsg(ircmsgs.privmsg(channel, '%s: You do not have a large enough streak yet (%i of %i).' % (username, self.games[channelCanonical].streak, minStreak)))
            irc.noReply()
            return

        irc.sendMsg(ircmsgs.privmsg(channel, 'No more waiting; starting next question.'))
        self.games[channelCanonical].removeEvent()
        self.games[channelCanonical].nextQuestion()
        irc.noReply()
    next = wrap(next)

    def removeedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] <int>
        Remove a edit without accepting it. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        edit = threadStorage.getEditById(num)
        if len(edit) < 1:
            irc.error('Could not find that edit')
        else:
            edit = edit[0]
            threadStorage.removeEdit(edit[0])
            irc.reply('Edit %d removed!' % edit[0])
    removeedit = wrap(removeedit, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def removedelete(self, irc, msg, arg, user, channel, num):
        """[<channel>] <int>
        Remove a delete without accepting it. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        delete = threadStorage.getDeleteById(num)
        if len(delete) < 1:
            irc.error('Could not find that delete')
        else:
            delete = delete[0]
            threadStorage.removeDelete(num)
            irc.reply('Delete %d removed!' % num)
    removedelete = wrap(removedelete, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def removereport(self, irc, msg, arg, user, channel, num):
        """[<channel>] <report num>
        Remove a old report by report number. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        report = threadStorage.getReportById(num)
        if len(report) < 1:
            irc.error('Could not find that report')
        else:
            report = report[0]
            threadStorage.removeReport(report[0])
            irc.reply('Report %d removed!' % report[0])
    removereport = wrap(removereport, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def delnew(self, irc, msg, arg, user, channel, num):
        """[<channel>] <int>
        Remove a temp question without accepting it. Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        q = threadStorage.getTemporaryQuestionById(num)
        if len(q) < 1:
            irc.error('Could not find that temp question')
        else:
            q = q[0]
            threadStorage.removeTemporaryQuestion(q[0])
            irc.reply('Temp question #%d removed!' % q[0])
    delnew = wrap(delnew, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def repeat(self, irc, msg, arg):
        """
        Repeat the current question.
        """
        channel = msg.args[0]
        channelCanonical = ircutils.toLower(channel)
        if channelCanonical in self.games:
            self.games[channelCanonical].repeatQuestion()
    repeat = wrap(repeat)

    def report(self, irc, msg, arg, channel, roundNum, text):
        """[channel] <round number> <report text>
        Provide a report for a bad question. Be sure to include the round number and any problems. 
        Channel is a optional parameter which is only needed when reporting outside of the channel
        """
        username = msg.nick
        inp = text.strip()
        try:
            user = ircdb.users.getUser(msg.prefix)
            username = user.name
        except KeyError:
            pass
        channelCanonical = ircutils.toLower(channel)
        if channelCanonical in self.games:
            numAsked = self.games[channelCanonical].numAsked
            questionOver = self.games[channelCanonical].questionOver
            if inp[:2] == 's/':
                if numAsked == roundNum and questionOver == False:
                    irc.reply('Sorry you must wait until the current question is over to report it.')
                    return
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        question = threadStorage.getQuestionByRound(roundNum, channel)
        if len(question) > 0:
            question = question[0]
            if inp[:2] == 's/':
                regex = inp[2:].split('/')
                if len(regex) > 1:
                    threadStorage.updateUser(username, 1, 0)
                    newOne = regex[1]
                    oldOne = regex[0]
                    newQuestionText = question[2].replace(oldOne, newOne)
                    threadStorage.insertEdit(question[0], newQuestionText, username, channel)
                    irc.reply('** Regex detected ** Your report has been submitted!')
                    irc.sendMsg(ircmsgs.notice(username, 'NEW: %s' % (newQuestionText)))
                    irc.sendMsg(ircmsgs.notice(username, 'OLD: %s' % (question[2])))
                    return
            elif str.lower(utils.str.normalizeWhitespace(inp)) == 'delete':
                if not threadStorage.questionIdExists(question[0]):
                    irc.error('That question does not exist.')
                    return
                if threadStorage.isQuestionDeleted(question[0]):
                    irc.error('That question is already deleted.')
                    return
                if threadStorage.isQuestionPendingDeletion(question[0]):
                    irc.error('That question is already pending deletion.')
                    return
                irc.reply('Marked question for deletion.')
                threadStorage.insertDelete(username, channel, question[0])
                return
            threadStorage.updateUser(username, 0, 0, 1)
            threadStorage.insertReport(channel, username, text, question[0])
            irc.reply('Your report has been submitted!')
        else:
            irc.error('Sorry, round %d could not be found in the database' % (roundNum))
    report = wrap(report, ['channel', 'int', 'text'])

    def restorequestion(self, irc, msg, arg, channel, questionNum):
        """[<channel>] <Question num>
        Restore a question from being deleted.
        """
        username = msg.nick
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if not threadStorage.questionIdExists(questionNum):
            irc.error('That question does not exist.')
            return
        if not threadStorage.isQuestionDeleted(questionNum):
            irc.error('That question is not deleted.')
            return
        threadStorage.restoreQuestion(questionNum)
        irc.reply('Question %d restored.' % questionNum)
    restorequestion = wrap(restorequestion, [('checkChannelCapability', 'triviamod'), 'int'])

    def skip(self, irc, msg, arg):
        """
            Skip the cureent question and start the next. Rate-limited.
        """
        username = msg.nick
        channel = msg.args[0]

        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        timeSeconds = self.registryValue('skip.skipActiveTime', channel)
        totalActive = threadStorage.getNumUserActiveIn(channel, timeSeconds)
        channelCanonical = ircutils.toLower(channel)
        if channelCanonical not in self.games:
            irc.error('No questions are currently being asked.')
            return

        if self.games[channelCanonical].questionOver == True:
            irc.error('No question is currently being asked.')
            return

        if not threadStorage.wasUserActiveIn(username, channel, timeSeconds):
            irc.error('Only users who have answered a question in the last 10 minutes can skip.')
            return

        if username in self.games[channelCanonical].skipVoteCount:
            irc.error('You can only vote to skip once.')
            return

        skipSeconds = self.registryValue('skip.skipTime', channel)
        oldSkips = []
        for usr in self.games[channelCanonical].skips:
            if int(time.mktime(time.localtime())) - self.games[channelCanonical].skips[usr] > skipSeconds:
                oldSkips.append(usr)
        for usr in oldSkips:
            del self.games[channelCanonical].skips[usr]
        if username in self.games[channelCanonical].skips:
            if int(time.mktime(time.localtime())) - self.games[channelCanonical].skips[username] < skipSeconds:
                irc.error('You must wait to be able to skip again.')
                return

        self.games[channelCanonical].skipVoteCount[username] = 1
        self.games[channelCanonical].skips[username] = int(time.mktime(time.localtime()))

        irc.sendMsg(ircmsgs.privmsg(channel, '%s voted to skip this question.' % username))
        if totalActive < 1:
            return

        percentAnswered = ((1.0*len(self.games[channelCanonical].skipVoteCount))/(totalActive*1.0))

        # not all have skipped yet, we need to get out of here
        if percentAnswered < self.registryValue('skip.skipThreshold', channel):
            irc.noReply()
            return

        if channelCanonical not in self.games:
            irc.error('Trivia is not running.')
            return
        if self.games[channelCanonical].active == False:
            irc.error('Trivia is not running.')
            return
        try:
            schedule.removeEvent('%s.trivia' % channel)
        except KeyError:
            pass
        irc.sendMsg(ircmsgs.privmsg(channel, 'Skipped question! (%d of %d voted)' % (len(self.games[channelCanonical].skipVoteCount), totalActive)))

        self.games[channelCanonical].nextQuestion()
        irc.noReply()
    skip = wrap(skip)

    def stats(self, irc, msg, arg, username):
        """ <username>
            Show a  player's rank, score & questions asked for day, month, and year
        """
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            info = threadStorage.getUser(username, None)
        else:
            info = threadStorage.getUser(username, channel)
        if len(info) < 3:
            irc.error("I couldn't find that user in the database.")
        else:
            hasPoints = False
            infoList = ['%s\'s Stats: Points (answers)' % (self.addZeroWidthSpace(info[1]))]
            if info[10] > 0 or info[16] > 0 or info[11] > 0:
                hasPoints = True
                infoList.append(' \x02Today:\x02 #%d %d (%d)' % (info[16], info[10], info[11]))
            if info[15] > 0 or info[8] > 0 or info[9] > 0:
                hasPoints = True
                infoList.append(' \x02This Week:\x02 #%d %d (%d)' % (info[15], info[8], info[9]))
            if info[14] > 0 or info[6] > 0 or info[7] > 0:
                hasPoints = True
                infoList.append(' \x02This Month:\x02 #%d %d (%d)' % (info[14], info[6], info[7]))
            if info[13] > 0 or info[4] > 0 or info[5] > 0:
                hasPoints = True
                infoList.append(' \x02This Year:\x02 #%d %d (%d)' % (info[13], info[4], info[5]))
            if not hasPoints:
                infoList = ['%s: %s does not have any points.' % (msg.nick, username)]
            infoText = ''.join(infoList)
            irc.sendMsg(ircmsgs.privmsg(channel, infoText))
        irc.noReply()
    stats = wrap(stats,['nick'])

    def showdelete(self, irc, msg, arg, user, channel, num):
        """[<temp question #>]
        Show deletes awaiting approval
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if num is not None:
            q = threadStorage.getDeleteById(num)
            if len(q) > 0:
                q = q[0]
                question = threadStorage.getQuestion(q[3])
                questionText = 'Question not found'
                if len(question) > 0:
                    question = question[0]
                    questionText = question[2]
                irc.reply('Delete #%d, by %s Question#%d: %s'%(q[0], q[1], q[3], questionText))
            else:
                irc.error('Delete #%d not found' % num)
        else:
            q = threadStorage.getDeleteTop3()
            if len(q) < 1:
                irc.reply('No deletes found')
            for ques in q:
                question = threadStorage.getQuestion(ques[3])
                questionText = 'Delete not found'
                if len(question) > 0:
                    question = question[0]
                    questionText = question[2]
                irc.reply('Delete #%d, by %s Question#%d: %s'%(ques[0], ques[1], ques[3], questionText))
            irc.reply('Use the showdelete to see more information')
    showdelete = wrap(showdelete, ['user', ('checkChannelCapability', 'triviamod'),optional('int')])

    def showquestion(self, irc, msg, arg, user, channel, num):
        """[<channel>] <num>
        Search question database for question at line num. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        question = threadStorage.getQuestion(num)
        if len(question) < 1:
            irc.error('Question not found')
        else:
            question = question[0]
            if question[3] == 1:
                irc.reply('Info: This question is currently deleted.')
            irc.reply('Question#%d: %s' % (num, question[2]))
    showquestion = wrap(showquestion, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def showround(self, irc, msg, arg, user, channel, num):
        """[<channel>] <round num>
        Show what question was asked during the round. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        question = threadStorage.getQuestionByRound(num, channel)
        if len(question) < 1:
            irc.error('Round not found')
        else:
            question = question[0]
            irc.reply('Round %d: Question#%d, Text:%s' % (num, question[0], question[2]))
    showround = wrap(showround, ['user', ('checkChannelCapability', 'triviamod'), 'int'])

    def showreport(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<report num>]
        Shows report information, if num is provided one record is shown, otherwise the last 3 are. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if num is not None:
            report = threadStorage.getReportById(num)
            if len(report) < 1:
                irc.reply('No reports found')
            else:
                report = report[0]
                irc.reply('Report #%d `%s` by %s on %s Q#%d '%(report[0], report[3], report[2], report[1], report[7]))

                question = threadStorage.getQuestion(report[7])
                if len(question) < 1:
                    irc.reply('Error: Tried to find question but couldn\'t')
                else:
                    question = question[0]
                    irc.reply('Question#%d: %s' % (question[0], question[2]))
        else:
            reports  = threadStorage.getReportTop3()
            if len(reports) < 1:
                irc.reply('No reports found')
            for report in reports:
                irc.reply('Report #%d `%s` by %s on %s Q#%d '%(report[0], report[3], report[2], report[1], report[7]))
    showreport = wrap(showreport, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def showedit(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<edit num>]
        Show top 3 edits, or provide edit num to view one. 
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if num is not None:
            edit = threadStorage.getEditById(num)
            if len(edit) > 0:
                edit = edit[0]
                question = threadStorage.getQuestion(edit[1])
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
            edits = threadStorage.getEditTop3()
            if len(edits) < 1:
                irc.reply('No edits found')
            for edit in edits:
                question = threadStorage.getQuestion(edit[1])
                question = question[0]
                irc.reply('Edit #%d, Question#%d, NEW:%s'%(edit[0], edit[1], edit[2]))
            irc.reply('Use the showedit command to see more information')
    showedit = wrap(showedit, ['user', ('checkChannelCapability', 'triviamod'), optional('int')])

    def shownew(self, irc, msg, arg, user, channel, num):
        """[<temp question #>]
        Show questions awaiting approval
        Channel is only necessary when editing from outside of the channel
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if num is not None:
            q = threadStorage.getTemporaryQuestionById(num)
            if len(q) > 0:
                q = q[0]
                irc.reply('Temp Q #%d: %s'%(q[0], q[3]))
            else:
                irc.error('Temp Q #%d not found' % num)
        else:
            q = threadStorage.getTemporaryQuestionTop3()
            if len(q) < 1:
                irc.reply('No temp questions found')
            for ques in q:
                irc.reply('Temp Q #%d: %s'%(ques[0], ques[3]))
            irc.reply('Use the shownew to see more information')
    shownew = wrap(shownew, ['user', ('checkChannelCapability', 'triviamod'),optional('int')])

    def start(self, irc, msg, args):
        """
        Begins a round of Trivia inside the current channel.
        """
        channel = msg.args[0]
        channelCanonical = ircutils.toLower(channel)
        if not irc.isChannel(channel):
            irc.error('This command can only be used in a channel.')
            return
        if channelCanonical in self.games:
            if self.games[channelCanonical].stopPending == True:
                self.games[channelCanonical].stopPending = False
                irc.sendMsg(ircmsgs.privmsg(channel, 'Pending stop aborted'))
            elif not self.games[channelCanonical].active:
                del self.games[channelCanonical]
                try:
                    schedule.removeEvent('%s.trivia' % channel)
                except KeyError:
                    pass
                irc.sendMsg(ircmsgs.privmsg(channel, 'Another epic round of trivia is about to begin.'))
                self.games[channelCanonical] = self.Game(irc, channel, self)
            else:
                irc.sendMsg(ircmsgs.privmsg(channel, 'Trivia has already been started.'))
        else:
            # create a new game
            irc.sendMsg(ircmsgs.privmsg(channel, 'Another epic round of trivia is about to begin.'))
            self.games[channelCanonical] = self.Game(irc, channel, self)
        irc.noReply()
    start = wrap(start)

    def stop(self, irc, msg, args, channel):
        """[<channel>]
        Stops the current Trivia round.
        Channel is only necessary when using from outside of the channel
        """
        channelCanonical = ircutils.toLower(channel)
        if channelCanonical in self.games:
            if self.games[channelCanonical].questionOver == True:
                self.games[channelCanonical].stop()
                return
            if self.games[channelCanonical].active:
                self.games[channelCanonical].stopPending = True
                irc.sendMsg(ircmsgs.privmsg(channel, 'Trivia will now stop after this question.'))
            else:
                del self.games[channelCanonical]
                irc.sendMsg(ircmsgs.privmsg(channel, 'Trivia stopped. :\'('))
        else:
            irc.sendMsg(ircmsgs.privmsg(channel, 'Game is already stopped'))
        irc.noReply()
    stop = wrap(stop, [('checkChannelCapability', 'triviamod')])

    def time(self, irc, msg, arg):
        """
        Figure out what time/day it is for the server
        """
        channel = msg.args[0]
        timeObject = time.asctime(time.localtime())
        timeString = 'The current server time appears to be %s' % timeObject
        irc.sendMsg(ircmsgs.privmsg(channel, timeString))
        irc.noReply()
    time = wrap(time)

    def transferpoints(self, irc, msg, arg, userfrom, userto):
        """<userfrom> <userto>
        Transfers all points and records from one user to another
        """
        userfrom = userfrom
        userto = userto
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        threadStorage.transferUserLogs(userfrom, userto)
        irc.reply('Done! Transfered records from %s to %s' % (userfrom, userto))
    transferpoints = wrap(transferpoints, ['admin', 'nick', 'nick'])

    def week(self, irc, msg, arg, num):
        """[<number>]
        Displays the top ten scores of the week. 
        Parameter is optional, display up to that number. 
        eg 20 - display 11-20
        """
        if num is None or num < 10:
            num=10
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewWeekTop10(None, num)
        else:
            tops = threadStorage.viewWeekTop10(channel, num)
        topsList = ['This Week\'s Top 10 Players: ']
        offset = num-9
        for i in range(len(tops)):
            topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i][1]), tops[i][2]))
        topsText = ''.join(topsList)
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    week = wrap(week, [optional('int')])

    def year(self, irc, msg, arg, num):
        """[<number>]
            Displays the top ten scores of the year. Parameter is optional, display up to that number. eg 20 - display 11-20
        """
        if num is None or num < 10:
            num=10
        channel = msg.args[0]
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewYearTop10(None, num)
        else:
            tops = threadStorage.viewYearTop10(channel, num)
        topsList = ['This Year\'s Top 10 Players: ']
        offset = num-9
        for i in range(len(tops)):
            topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i][1]), tops[i][2]))
        topsText = ''.join(topsList)
        irc.sendMsg(ircmsgs.privmsg(channel, topsText))
        irc.noReply()
    year = wrap(year, [optional('int')])

    #Game instance
    class Game:
        """
        Main game logic, single game instance for each channel.
        """
        def __init__(self, irc, channel, base):
            # constants
            self.unmaskedChars = " -'\"_=+&%$#@!~`[]{}?.,<>|\\/:;"
            
            # get utilities from base plugin
            self.games = base.games
            self.storage = base.storage
            self.Storage = base.Storage
            self.registryValue = base.registryValue
            self.channel = channel
            self.irc = irc

            # reset stats
            self.skips = {}
            self.stopPending = False
            self.shownHint = False
            self.questionRepeated = False
            self.skipVoteCount = {}
            self.streak = 0
            self.lastWinner = ''
            self.hintsCounter = 0
            self.numAsked = 0
            self.lastAnswer = time.time()
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
            # Already done? get out of here
            if self.questionOver:
                return
            
            username = msg.nick
            # is it a user?
            try:
                user = ircdb.users.getUser(msg.prefix)
                username = user.name
            except KeyError:
                pass
            correctAnswerFound = False
            correctAnswer = ''

            attempt = str.lower(msg.args[1])
            attempt = self.removeAccents(attempt)
            attempt = self.removeExtraSpaces(attempt)

            # was a correct answer guessed?
            for ans in self.alternativeAnswers:
                normalizedAns = self.removeAccents(ans)
                normalizedAns = self.removeExtraSpaces(normalizedAns)
                normalizedAns = str.lower(normalizedAns)
                if normalizedAns == attempt and normalizedAns not in self.guessedAnswers:
                    correctAnswerFound = True
                    correctAnswer = ans
            for ans in self.answers:
                normalizedAns = self.removeAccents(ans)
                normalizedAns = self.removeExtraSpaces(normalizedAns)
                normalizedAns = str.lower(normalizedAns)
                if normalizedAns == attempt and normalizedAns not in self.guessedAnswers:
                    correctAnswerFound = True
                    correctAnswer = ans

            if correctAnswerFound:
                dbLocation = self.registryValue('admin.sqlitedb')
                threadStorage = self.Storage(dbLocation)
                # time stats
                timeElapsed = float(time.time() - self.askedAt)
                pointsAdded = self.points

                # Past first hint? deduct points
                if self.hintsCounter > 1:
                    pointsAdded /= 2 * (self.hintsCounter - 1)

                if len(self.answers) > 1:
                    if ircutils.toLower(username) not in self.correctPlayers:
                        self.correctPlayers[ircutils.toLower(username)] = 1
                    self.correctPlayers[ircutils.toLower(username)] += 1
                    # KAOS? divide points
                    pointsAdded /= (len(self.answers) + 1)

                    # Convert score to int
                    pointsAdded = int(pointsAdded)

                    self.totalAmountWon += pointsAdded
                    # report the correct guess for kaos item
                    threadStorage.updateUserLog(username, self.channel, pointsAdded,0, 0)
                    self.lastAnswer = time.time()
                    self.sendMessage('\x02%s\x02 gets \x02%d\x02 points for: \x02%s\x02' % (username, pointsAdded, correctAnswer))
                else:
                    # Normal question solved
                    streakBonus = 0
                    # update streak info
                    if ircutils.toLower(self.lastWinner) != ircutils.toLower(username):
                        self.lastWinner = ircutils.toLower(username)
                        self.streak = 1
                    else:
                        self.streak += 1
                        streakBonus = pointsAdded * .01 * (self.streak-1)
                        if streakBonus > pointsAdded:
                            streakBonus = pointsAdded
                        pointsAdded += streakBonus
                    threadStorage.updateGameStreak(self.channel, self.lastWinner, self.streak)
                    threadStorage.updateUserHighestStreak(self.lastWinner, self.streak)
                    threadStorage.updateGameLongestStreak(self.channel, username, self.streak)
                    # Convert score to int
                    pointsAdded = int(pointsAdded)

                    # report correct guess, and show players streak
                    threadStorage.updateUserLog(username, self.channel, pointsAdded,1, timeElapsed)
                    self.lastAnswer = time.time()
                    self.sendMessage('DING DING DING, \x02%s\x02 got the correct answer, \x02%s\x02, in \x02%0.4f\x02 seconds for \x02%d(+%d)\x02 points!' % (username, correctAnswer, timeElapsed, pointsAdded, streakBonus))

                    if self.registryValue('general.showStats', self.channel):
                        if self.registryValue('general.globalStats'):
                            userInfo = threadStorage.getUser(username, None)
                        else:
                            userInfo = threadStorage.getUser(username, self.channel)
                        if len(userInfo) >= 3:
                            todaysScore = userInfo[10]
                            weekScore = userInfo[8]
                            monthScore = userInfo[6]
                            recapMessageList = ['\x02%s\x02 has won \x02%d\x02 in a row!' % (username, self.streak)]
                            if todaysScore > pointsAdded or weekScore > pointsAdded or monthScore > pointsAdded:
                                recapMessageList.append(' Total Points')
                            if todaysScore > pointsAdded:
                                recapMessageList.append(' TODAY: \x02%d\x02' % (todaysScore))
                            if weekScore > pointsAdded:
                                recapMessageList.append(' this WEEK \x02%d\x02' % (weekScore))
                            if weekScore > pointsAdded or todaysScore > pointsAdded:
                                if monthScore > pointsAdded:
                                    recapMessageList.append(' &')
                            if monthScore > pointsAdded:
                                recapMessageList.append(' this MONTH: \x02%d\x02' % (monthScore))
                            recapMessage = ''.join(recapMessageList)
                            self.sendMessage(recapMessage)

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
                                bonusPoints = self.registryValue('kaos.payoutKAOS', self.channel)

                        bonusPointsText = ''
                        if bonusPoints > 0:
                            for nick in self.correctPlayers:
                                threadStorage.updateUserLog(nick, self.channel, bonusPoints, 0, 0)
                            bonusPointsText = 'Everyone gets a %d Point Bonus!!' % int(bonusPoints)

                        # give a special message if it was KAOS
                        self.sendMessage('All KAOS answered! %s' % bonusPointsText)
                        self.sendMessage('Total Awarded: \x02%d Points to %d Players\x02' % (int(self.totalAmountWon), len(self.correctPlayers)))

                    self.removeEvent()

                    threadStorage.updateQuestionStats(self.lineNumber, (4-self.hintsCounter), 0)

                    if self.stopPending == True:
                        self.stop()
                        return

                    waitTime = self.registryValue('general.waitTime',self.channel)
                    if waitTime < 2:
                        waitTime = 2
                        log.error('waitTime was set too low (<2 seconds). Setting to 2 seconds')
                    waitTime = time.time() + waitTime
                    self.queueEvent(waitTime, self.nextQuestion)

        def getHintString(self, hintNum=None):
            if hintNum == None:
                hintNum = self.hintsCounter
            hintRatio = self.registryValue('hints.hintRatio') # % to show each hint
            hints = ''
            ratio = float(hintRatio * .01)
            charMask = self.registryValue('hints.charMask', self.channel)

            # create a string with hints for all of the answers
            for ans in self.answers:
                if ircutils.toLower(ans) in self.guessedAnswers:
                    continue
                ans = unicode(ans.decode('utf-8'))
                if hints != '':
                    hints += ' '
                if len(self.answers) > 1:
                    hints += '['
                if hintNum == 0:
                    masked = ans
                    for i in range(len(masked)):
                        if masked[i] in self.unmaskedChars:
                            hints+= masked[i]
                        else:
                            hints += charMask
                elif hintNum == 1:
                    divider = int(len(ans) * ratio)
                    if divider > 3:
                        divider = 3
                    if divider >= len(ans):
                        divider = len(ans)-1
                    hints += ans[:divider]
                    masked = ans[divider:]
                    for i in range(len(masked)):
                        if masked[i] in self.unmaskedChars:
                            hints+= masked[i]
                        else:
                            hints += charMask
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
                    if self.registryValue('hints.vowelsHint', self.channel):
                        hints+= self.getMaskedVowels(ansend, divider-1)
                    else:
                        hints+= self.getMaskedRandom(ansend, divider-1)
                if len(self.answers) > 1:
                    hints += ']'
            return hints.encode('utf-8')

        def getMaskedVowels(self, letters, sizeOfUnmasked):
            charMask = self.registryValue('hints.charMask', self.channel)
            hintsList = ['']
            unmasked = 0
            lettersInARow = sizeOfUnmasked
            for i in range(len(letters)):
                masked = letters[i]
                if masked in self.unmaskedChars:
                    hintsList.append(masked)
                elif str.lower(self.removeAccents(masked.encode('utf-8'))) in 'aeiou' and unmasked < (len(letters)-1) and lettersInARow < 3:
                    hintsList.append(masked)
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
            maskedInARow=0
            lettersInARow=sizeOfUnmasked
            for i in range(len(letters)):
                masked = letters[i]
                if masked in self.unmaskedChars:
                    hints += masked
                    unmasked += 1
                elif maskedInARow > 2 and unmasked < (len(letters)-1):
                    lettersInARow += 1
                    unmasked += 1
                    maskedInARow = 0
                    hints += letters[i]
                elif lettersInARow < 3 and unmasked < (len(letters)-1) and random.randint(0,100) < hintRatio:
                    lettersInARow += 1
                    unmasked += 1
                    maskedInARow = 0
                    hints += letters[i]
                else:
                    maskedInARow += 1
                    lettersInARow=0
                    hints += charMask
            return hints

        def getOtherHintString(self):
            charMask = self.registryValue('hints.charMask', self.channel)
            if len(self.answers) > 1 or len(self.answers) < 1:
                return
            ans = self.answers[0]

            hints = 'Hint: \x02\x0312'

            divider = 0

            if len(ans) < 2:
                divider = 0
            elif self.hintsCounter == 1:
                divider = 1
            elif self.hintsCounter == 2:
                divider = int((len(ans) * .25) + 1)
                if divider > 4:
                    divider = 4
            elif self.hintsCounter == 3:
                divider = int((len(ans) * .5) + 1)
                if divider > 6:
                    divider = 6
            if divider == len(ans):
                divider -= 1

            if divider > 0:
                hints += ans[:divider]

            return hints

        def getOtherHint(self):
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
                    self.sendMessage('\x02\x0312%s' % (self.getHintString(self.hintsCounter-1)))

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
                    if ircutils.toLower(ans) in self.guessedAnswers:
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
                    self.sendMessage("""Time's up! No one got \x02%s\x02""" % answer)

                    self.sendMessage("""Correctly Answered: \x02%d of %d\x02 Total Awarded: \x02%d Points to %d Players\x02"""
                                    % (len(self.guessedAnswers), len(self.answers), int(self.totalAmountWon), len(self.correctPlayers))
                                    )
                else:
                    self.sendMessage("""Time's up! The answer was \x02%s\x02.""" % answer)

                self.storage.updateQuestionStats(self.lineNumber, 0, 1)

                #reset stuff
                self.answers = []
                self.alternativeAnswers = []
                self.question = ''
                self.questionOver = True

                if self.stopPending == True:
                    self.stop()
                    return

                # provide next question
                waitTime = self.registryValue('general.waitTime',self.channel)
                if waitTime < 2:
                    waitTime = 2
                    log.error('waitTime was set too low (<2 seconds). Setting to 2 seconds')
                waitTime = time.time() + waitTime
                self.queueEvent(waitTime, self.nextQuestion)
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
            self.sendMessage('Hint %s: \x02\x0312%s' % (self.hintsCounter, hints), 1, 9)
            #reset hint shown
            self.shownHint = False

            hintTime = 2
            if len(self.answers) > 1:
                hintTime = self.registryValue('kaos.hintKAOS', self.channel)
            else:
                hintTime = self.registryValue('questions.hintTime', self.channel)

            if hintTime < 2:
                timout = 2
                log.error('hintTime was set too low(<2 seconds). setting to 2 seconds')

            hintTime += time.time()
            self.queueEvent(hintTime, self.loopEvent)

        def nextQuestion(self):
            """
                Time for a new question
            """
            inactivityTime = self.registryValue('general.timeout')
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
                self.sendMessage('There are no questions. Stopping. If you are an admin use the addfile to add questions to the database')
                return

            numQuestionsLeftInRound = self.storage.getNumQuestionsNotAsked(self.channel, self.roundStartedAt)
            if numQuestionsLeftInRound == 0:
                self.numAsked = 1
                self.roundStartedAt = time.mktime(time.localtime())
                self.storage.updateGameRoundStarted(self.channel, self.roundStartedAt)
                self.sendMessage('All of the questions have been asked, shuffling and starting over')

            self.storage.updateGame(self.channel, self.numAsked) #increment q's asked
            retrievedQuestion = self.retrieveQuestion()

            self.points = self.registryValue('questions.defaultPoints', self.channel)
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
                tempQuestion = '%s?' % (tempQuestion)

            # bold the q, add color
            questionText = '\x02\x0303%s' % (tempQuestion)

            # KAOS? report # of answers
            if len(self.answers) > 1:
                questionText += ' %d possible answers' % (len(self.answers))

            questionMessageString = '%s: %s' % (self.numAsked, questionText)

            maxLength = 400

            questionMesagePieces = [questionMessageString[i:i+maxLength] for i in range(0, len(questionMessageString), maxLength)]

            multipleMessages=False

            for msgPiece in questionMesagePieces:
                if multipleMessages:
                    msgPiece = '\x02\x0303%s' % (msgPiece)
                multipleMessages = True
                self.sendMessage(msgPiece, 1, 9)
            self.queueEvent(0, self.loopEvent)
            self.askedAt = time.time()

        def queueEvent(self, hintTime, func):
            """
                Create a new timer event for loopEvent call
            """
            # create a new thread for event next step to happen for [hintTime] seconds
            def event():
                func()
            if self.active:
                schedule.addEvent(event, hintTime, '%s.trivia' % self.channel)

        def removeAccents(self, text):
            text = unicode(text.decode('utf-8'))
            normalized = unicodedata.normalize('NFKD', text)
            normalized = u''.join([c for c in normalized if not unicodedata.combining(c)])
            return normalized.encode('utf-8')

        def removeExtraSpaces(self, text):
            return utils.str.normalizeWhitespace(text)

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

                # bold the q, add color
                questionText = '\x02\x0303%s' % (tempQuestion)

                # KAOS? report # of answers
                if len(self.answers) > 1:
                    questionText += ' %d possible answers' % (len(self.answers))

                questionMessageString = '%s: %s' % (self.numAsked, questionText)

                maxLength = 400

                questionMesagePieces = [questionMessageString[i:i+maxLength] for i in range(0, len(questionMessageString), maxLength)]

                multipleMessages=False

                for msgPiece in questionMesagePieces:
                    if multipleMessages:
                        msgPiece = '\x02\x0303%s' % (msgPiece)
                    multipleMessages = True
                    self.sendMessage(msgPiece, 1, 9)
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
            lineNumber, question, timesAnswered, timesMissed = self.retrieveQuestionFromSql()
            answer = question.split('*', 1)
            if len(answer) > 1:
                question = answer[0].strip()
                answers = answer[1].split('*')
                answer = []
                alternativeAnswers = []
                if ircutils.toLower(question[:4]) == 'kaos':
                    for ans in answers:
                        answer.append(str(ans).strip())
                elif ircutils.toLower(question[:5]) == 'uword':
                    for ans in answers:
                        answer.append(str(ans).strip())
                        question = 'Unscramble the letters: '
                        shuffledLetters = list(unicode(ans.decode('utf-8')))
                        random.shuffle(shuffledLetters)
                        for letter in shuffledLetters:
                            question += letter
                            question += ' '
                        question = question.encode('utf-8')
                        break
                else:
                    for ans in answers:
                        if answer == []:
                            answer.append(str(ans).strip())
                        else:
                            alternativeAnswers.append(str(ans).strip())

                points = self.registryValue('questions.defaultPoints', self.channel)
                if len(answer) > 1:
                    points = self.registryValue('kaos.defaultKAOS', self.channel) * len(answers)

                additionalPoints = 0
                additionalPoints += timesAnswered * -5
                additionalPoints += timesMissed * 5
                if additionalPoints > 200:
                    additionalPoints = 200
                if additionalPoints < -200:
                    additionalPoints = -200
                points += additionalPoints
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
            return (question[0], question[2], question[4], question[5])

        def sendMessage(self, msg, color=None, bgcolor=None):
            """ <msg>, [<color>], [<bgcolor>]
            helper for game instance to send messages to channel
            """
            # no color
            self.irc.sendMsg(ircmsgs.privmsg(self.channel, ' %s ' % msg))

        def stop(self):
            """
                Stop a game in progress
            """
            # responsible for stopping a timer/thread after being told to stop
            self.active = False
            self.removeEvent()
            self.sendMessage('Trivia stopped. :\'(')
            channelCanonical = ircutils.toLower(self.channel)
            if channelCanonical in self.games:
                del self.games[channelCanonical]

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

        def countTemporaryQuestions(self):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviatemporaryquestion''')
            rows = result.fetchone()[0]
            c.close()
            return rows

        def countDeletes(self):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviadelete''')
            rows = result.fetchone()[0]
            c.close()
            return rows

        def countEdits(self):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviaedit''')
            rows = result.fetchone()[0]
            c.close()
            return rows

        def countReports(self):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviareport''')
            rows = result.fetchone()[0]
            c.close()
            return rows

        def deleteQuestion(self, questionId):
            c = self.conn.cursor()
            test = c.execute('''UPDATE triviaquestion set
                                deleted=1
                                WHERE id=?''', (questionId,))
            self.conn.commit()
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

        def getRandomQuestionNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviaquestion
                            WHERE deleted=0 AND id NOT IN (SELECT tl.line_num FROM triviagameslog tl WHERE tl.channel_canonical=? AND tl.asked_at>=?)
                            ORDER BY random() LIMIT 1
                        ''', (ircutils.toLower(channel),roundStart))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getQuestionByRound(self, roundNumber, channel):
            channel=ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviaquestion WHERE id=(SELECT tgl.line_num
                                                                FROM triviagameslog tgl
                                                                WHERE tgl.round_num=?
                                                                AND tgl.channel_canonical=?
                                                                ORDER BY id DESC
                                                                LIMIT 1)''', (roundNumber,channel))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getNumQuestionsNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            result = c.execute('''SELECT count(id) FROM triviaquestion
                            WHERE deleted=0 AND id NOT IN (SELECT tl.line_num FROM triviagameslog tl WHERE tl.channel=? AND tl.asked_at>=?)''',
                                    (channel,roundStart))
            rows = result.fetchone()[0]
            c.close()
            return rows

        def getUserRanks(self, username, channel):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = None
            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year

            query = '''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog'''
            arguments = []

            if channel is not None:
                query = '''%s where channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where username_canonical=?''' % (query)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where username_canonical=?''' % (query)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s ) limit 1''' % (query)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))
            data = []

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            query = '''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where year=?'''
            arguments = [year]

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where year=?
                                and username_canonical=?''' % (query)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where year=?
                                and username_canonical=?''' % (query)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s ) limit 1''' % (query)

            c.execute(query, tuple(arguments))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            query = '''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where month=?
                                and year=?'''
            arguments = [month, year]

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where month=?
                                and year=?
                                and username_canonical=?''' % (query)
            arguments.append(month)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where month=?
                                and year=?
                                and username=?''' % (query)
            arguments.append(month)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s ) limit 1''' % (query)

            c.execute(query, tuple(arguments))

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
                                where ('''
            arguments = []

            weekSql += weekSqlClause
            weekSql +='''
                                )'''

            if channel is not None:
                weekSql = '''%s and channel_canonical=?''' % (weekSql)
                arguments.append(channelCanonical)

            weekSql += '''group by username_canonical
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where username_canonical=?'''
            arguments.append(usernameCanonical)

            if channel is not None:
                weekSql = '''%s and channel_canonical=?''' % (weekSql)
                arguments.append(channelCanonical)

            weekSql += ''' and ('''
            weekSql += weekSqlClause
            weekSql += '''
                                    )
                                )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where username_canonical=?'''
            arguments.append(usernameCanonical)

            if channel is not None:
                weekSql = '''%s and channel_canonical=?''' % (weekSql)
                arguments.append(channelCanonical)

            weekSql += ''' and ('''
            weekSql += weekSqlClause
            weekSql += '''
                                )
                            ) limit 1'''
            c.execute(weekSql, tuple(arguments))

            rank = 0
            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    rank = d
                break
            data.append(rank)

            query = '''select tr.rank
                        from (
                            select count(tu2.id)+1 as rank
                            from (
                                select id, username, sum(points_made) as totalscore
                                from triviauserlog
                                where day=?
                                and month=?
                                and year=?'''
            arguments = [day, month, year]

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                            ) as tu2
                            where tu2.totalscore > (
                                select sum(points_made)
                                from triviauserlog
                                where day=?
                                and month=?
                                and year=?
                                and username_canonical=?''' % (query)
            arguments.append(day)
            arguments.append(month)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s )
                        ) as tr
                        where
                            exists(
                                select *
                                from triviauserlog
                                where day=?
                                and month=?
                                and year=?
                                and username_canonical=?''' % (query)
            arguments.append(day)
            arguments.append(month)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s ) limit 1''' % (query)

            c.execute(query, tuple(arguments))

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

        def getUser(self, username, channel):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = None
            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year

            c = self.conn.cursor()

            data = []
            data.append(username)
            data.append(username)

            query = '''select
                            sum(tl.points_made) as points,
                            sum(tl.num_answered) as answered
                        from triviauserlog tl
                        where tl.username_canonical=?'''
            arguments = [usernameCanonical]

            if channel is not None:
                query = '''%s and tl.channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s limit 1''' % (query)

            c.execute(query, tuple(arguments))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            query = '''select
                            sum(tl.points_made) as yearPoints,
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where
                            tl.username_canonical=?
                        and tl.year=?'''
            arguments = [usernameCanonical, year]

            if channel is not None:
                query = '''%s and tl.channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s limit 1''' % (query)

            c.execute(query, tuple(arguments))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            query = '''select
                            sum(tl.points_made) as yearPoints,
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where
                            tl.username_canonical=?
                        and tl.year=?
                        and tl.month=?'''
            arguments = [usernameCanonical, year, month]

            if channel is not None:
                query = '''%s and tl.channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s limit 1''' % (query)
            
            c.execute(query, tuple(arguments))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            query = '''select
                            sum(tl.points_made) as yearPoints,
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where
                            tl.username_canonical=?
                        and ('''

            d = datetime.date.today()
            weekday=d.weekday()
            d -= datetime.timedelta(weekday)
            for i in range(7):
                if i > 0:
                    query += ' or '
                query += '''
                            (tl.year=%d
                            and tl.month=%d
                            and tl.day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)

            query += ')'
            arguments = [usernameCanonical]

            if channel is not None:
                query = '''%s and tl.channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s limit 1''' % (query)
            
            c.execute(query, tuple(arguments))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break

            query = '''select
                            sum(tl.points_made) as yearPoints,
                            sum(tl.num_answered) as yearAnswered
                        from triviauserlog tl
                        where
                            tl.username_canonical=?
                        and tl.year=?
                        and tl.month=?
                        and tl.day=?'''
            arguments = [usernameCanonical, year, month, day]

            if channel is not None:
                query = '''%s and tl.channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s limit 1''' % (query)

            c.execute(query, tuple(arguments))

            for row in c:
                for d in row:
                    if d is None:
                        d=0
                    data.append(d)
                break
            for d in self.getUserRanks(username, channel):
                data.append(d)

            c.close()
            return data

        def getGame(self, channel):
            channel = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviagames
                        where channel_canonical=?
                        limit 1''', (channel,))
            data = None
            for row in c:
                data = row
                break
            c.close()
            return data

        def getNumUser(self, channel):
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            result = c.execute('select count(distinct(username_canonical)) from triviauserlog where channel_canonical=?', (channelCanonical,))
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
            c.execute('SELECT * FROM triviaquestion where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

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
                            and tl.month=%d
                            and tl.day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)
            c = self.conn.cursor()
            weekSql = '''select count(distinct(tl.username_canonical))
                        from triviauserlog tl
                        where channel_canonical=? and ('''
            weekSql += weekSqlString
            weekSql += ''')'''
            result = c.execute(weekSql, (channelCanonical,))
            rows = result.fetchone()[0]
            return rows

        def getDeleteById(self, id):
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviadelete where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getDeleteTop3(self, page=1, amount=3):
            if page < 1:
                page=1
            if amount < 1:
                amount=3
            page -= 1
            start = page * amount
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviadelete order by id desc limit ?, ?', (start, amount))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getReportById(self, id):
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviareport where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getReportTop3(self, page=1, amount=3):
            if page < 1:
                page=1
            if amount < 1:
                amount=3
            page -= 1
            start = page * amount
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviareport order by id desc limit ?, ?', (start, amount))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getTemporaryQuestionTop3(self, page=1, amount=3):
            if page < 1:
                page=1
            if amount < 1:
                amount=3
            page -= 1
            start = page * amount
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviatemporaryquestion order by id desc limit ?, ?', (start, amount))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getTemporaryQuestionById(self, id):
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviatemporaryquestion where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getEditById(self, id):
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviaedit where id=? limit 1', (id,))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def getNumUserActiveIn(self, channel, timeSeconds):
            channelCanonical = ircutils.toLower(channel)
            epoch = int(time.mktime(time.localtime()))
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviauserlog
                        where day=? and month=? and year=?
                        and channel_canonical=?
                        and last_updated>?''', (day, month, year, channelCanonical, (epoch-timeSeconds)))
            rows = result.fetchone()[0]
            c.close()
            return rows

        def gameExists(self, channel):
            channel = ircutils.toLower(channel)
            c = self.conn.cursor()
            result = c.execute('select count(id) from triviagames where channel_canonical=?', (channel,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def getEditTop3(self, page=1, amount=3):
            if page < 1:
                page=1
            if amount < 1:
                amount=3
            page -= 1
            start = page * amount
            c = self.conn.cursor()
            c.execute('SELECT * FROM triviaedit order by id desc limit ?, ?', (start, amount))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def loginExists(self, username):
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            result = c.execute('select count(id) from trivialogin where username_canonical=?', (usernameCanonical,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def insertDelete(self, username, channel, lineNumber):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('insert into triviadelete values (NULL, ?, ?, ?, ?, ?)',
                                    (username, usernameCanonical, lineNumber, channel, channelCanonical))
            self.conn.commit()

        def insertLogin(self, username, salt, isHashed, password, capability):
            usernameCanonical = ircutils.toLower(username)
            if self.loginExists(username):
                self.updateLogin(username, salt, isHashed, password, capability)
            if not isHashed:
                isHashed = 0
            else:
                isHashed = 1
            c = self.conn.cursor()
            c.execute('insert into trivialogin values (NULL, ?, ?, ?, ?, ?, ?)',
                                    (username, usernameCanonical, salt, isHashed, password, capability))
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
            c.execute('insert into triviauserlog values (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                    (username, score, numAnswered, day, month, year, epoch, timeTaken, scoreAvg, usernameCanonical, channel, channelCanonical))
            self.conn.commit()
            c.close()

        def insertUser(self, username, numEditted=0, numEdittedAccepted=0, numReported=0, numQuestionsAdded=0, numQuestionsAccepted=0):
            usernameCanonical = ircutils.toLower(username)
            if self.userExists(username):
                return self.updateUser(username, numEditted, numEdittedAccepted, numReported, numQuestionsAdded, numQuestionsAccepted)
            c = self.conn.cursor()
            c.execute('insert into triviausers values (NULL, ?, ?, ?, ?, ?, ?, ?, 0)', 
                            (
                                    username,
                                    numEditted,
                                    numEdittedAccepted,
                                    usernameCanonical,
                                    numReported,
                                    numQuestionsAdded,
                                    numQuestionsAccepted
                            )
                    )
            self.conn.commit()
            c.close()

        def insertGame(self, channel, numAsked=0, epoch=None):
            channelCanonical = ircutils.toLower(channel)
            if self.gameExists(channel):
                return self.updateGame(channel, numAsked)
            if epoch is None:
                epoch = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviagames values (NULL, ?, ?, ?, 0, 0, ?, 0, "", "")', (channel,numAsked,epoch,channelCanonical))
            self.conn.commit()
            c.close()

        def insertGameLog(self, channel, roundNumber, lineNumber, questionText, askedAt=None):
            channelCanonical = ircutils.toLower(channel)
            if askedAt is None:
                askedAt = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviagameslog values (NULL, ?, ?, ?, ?, ?, ?)', (channel,roundNumber,lineNumber,questionText,askedAt,channelCanonical))
            self.conn.commit()
            c.close()

        def insertReport(self, channel, username, reportText, questionNum, reportedAt=None):
            channelCanonical = ircutils.toLower(channel)
            usernameCanonical = ircutils.toLower(username)
            if reportedAt is None:
                reportedAt = int(time.mktime(time.localtime()))
            c = self.conn.cursor()
            c.execute('insert into triviareport values (NULL, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)',
                                        (channel,username,reportText,reportedAt,questionNum,usernameCanonical,channelCanonical))
            self.conn.commit()
            c.close()

        def insertQuestionsBulk(self, questions):
            c = self.conn.cursor()
            #skipped=0
            divData = self.chunk(questions) # divide into 10000 rows each
            for chunk in divData:
                c.executemany('''insert into triviaquestion values (NULL, ?, ?, 0, 0, 0)''',
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
            c.execute('insert into triviaedit values (NULL, ?, ?, NULL, ?, ?, ?, ?, ?)',
                                        (questionId,questionText,username,channel,createdAt, usernameCanonical, channelCanonical))
            self.conn.commit()
            c.close()

        def insertTemporaryQuestion(self, username, channel, question):
            c = self.conn.cursor()
            channelCanonical = ircutils.toLower(channel)
            usernameCanonical = ircutils.toLower(username)
            c.execute('insert into triviatemporaryquestion values (NULL, ?, ?, ?, ?, ?)',
                                        (username,channel,question,usernameCanonical,channelCanonical))
            self.conn.commit()
            c.close()

        def isQuestionDeleted(self, id):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviaquestion
                        where deleted=1 and id=?''', (id,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def isQuestionPendingDeletion(self, id):
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviadelete
                        where line_num=?''', (id,))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def makeDeleteTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviadelete (
                        id integer primary key autoincrement,
                        username text,
                        username_canonical text,
                        line_num integer,
                        channel text,
                        channel_canonical text
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeLoginTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table trivialogin (
                        id integer primary key autoincrement,
                        username text,
                        username_canonical text not null unique,
                        salt text,
                        is_hashed  integer not null default 1,
                        password text,
                        capability text
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeUserTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviausers (
                        id integer primary key autoincrement,
                        username text,
                        num_editted integer,
                        num_editted_accepted integer,
                        username_canonical text not null unique,
                        num_reported integer,
                        num_questions_added integer,
                        num_questions_accepted integer,
                        highest_streak integer
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
                        username_canonical text,
                        channel text,
                        channel_canonical text,
                        unique(username_canonical,channel_canonical, day, month, year) on conflict replace
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
                        channel text,
                        num_asked integer,
                        round_started integer,
                        last_winner text,
                        streak integer,
                        channel_canonical text not null unique,
                        longest_streak integer,
                        longest_streak_holder text,
                        longest_streak_holder_canonical text
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
                        asked_at integer,
                        channel_canonical text
                        )''')
                c.execute('''create index gamelograndomindex
                            on triviagameslog (channel, line_num, asked_at)
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
                        question_num integer,
                        username_canonical text,
                        channel_canonical text
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
                        question text,
                        username_canonical text,
                        channel_canonical text
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
                        deleted integer not null default 0,
                        num_answered integer,
                        num_missed integer
                        )''')
                c.execute('''create index questionrandomindex
                            on triviagameslog (id, deleted)
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
                        created_at text,
                        username_canonical text,
                        channel_canonical
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

        def removeDelete(self, deleteId):
            c = self.conn.cursor()
            c.execute('''delete from triviadelete
                        where id=?''', (deleteId,))
            self.conn.commit()
            c.close()

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

        def removeLogin(self, username):
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            c.execute('''delete from trivialogin
                        where username_canonical=?''', (usernameCanonical,))
            self.conn.commit()
            c.close()

        def removeReport(self, repId):
            c = self.conn.cursor()
            c.execute('''delete from triviareport
                        where id=?''', (repId,))
            self.conn.commit()
            c.close()

        def removeReportByQuestionNumber(self, id):
            c = self.conn.cursor()
            c.execute('''delete from triviareport
                        where question_num=?''', (id,))
            self.conn.commit()
            c.close()

        def removeEditByQuestionNumber(self, id):
            c = self.conn.cursor()
            c.execute('''delete from triviaedit
                        where question_id=?''', (id,))
            self.conn.commit()
            c.close()

        def removeDeleteByQuestionNumber(self, id):
            c = self.conn.cursor()
            c.execute('''delete from triviadelete
                        where line_num=?''', (id,))
            self.conn.commit()
            c.close()

        def removeTemporaryQuestion(self, id):
            c = self.conn.cursor()
            c.execute('''delete from triviatemporaryquestion
                        where id=?''', (id,))
            self.conn.commit()
            c.close()

        def removeUserLogs(self, username):
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            c.execute('''delete from triviauserlog
                        where username_canonical=?''', (usernameCanonical,))
            self.conn.commit()
            c.close()

        def restoreQuestion(self, id):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                deleted=0
                                where id=?''', (id,))
            self.conn.commit()
            c.close()

        def transferUserLogs(self, userFrom, userTo):
            userFromCanonical = ircutils.toLower(userFrom)
            userToCanonical = ircutils.toLower(userTo)
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
                                            and t3.channel_canonical=triviauserlog.channel_canonical
                                            and t3.username_canonical=?
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
                                            and t2.channel_canonical=triviauserlog.channel_canonical
                                            and t2.username_canonical=?
                                    )
                            ,0)
                    where id in (
                            select id
                            from triviauserlog tl
                            where username_canonical=?
                            and exists (
                                    select id
                                    from triviauserlog tl2
                                    where tl2.day=tl.day
                                    and tl2.month=tl.month
                                    and tl2.year=tl.year
                                    and tl2.channel_canonical=tl.channel_canonical
                                    and username_canonical=?
                            )
                    )
            ''', (userFromCanonical,userFromCanonical,userToCanonical,userFromCanonical))

            c.execute('''
                    update triviauserlog
                    set username=?,
                    username_canonical=?
                    where username_canonical=?
                    and not exists (
                            select 1
                            from triviauserlog tl
                            where tl.day=triviauserlog.day
                            and tl.month=triviauserlog.month
                            and tl.year=triviauserlog.year
                            and tl.channel_canonical=triviauserlog.channel_canonical
                            and tl.username_canonical=?
                    )
            ''',(userTo, userToCanonical, userFromCanonical, userToCanonical))
            self.conn.commit()

            self.removeUserLogs(userFrom)

        def userLogExists(self, username, channel, day, month, year):
            c = self.conn.cursor()
            args = (ircutils.toLower(username),ircutils.toLower(channel),day,month,year)
            result = c.execute('select count(id) from triviauserlog where username_canonical=? and channel_canonical=? and day=? and month=? and year=?', args)
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def userExists(self, username):
            c = self.conn.cursor()
            usr = (ircutils.toLower(username),)
            result = c.execute('select count(id) from triviausers where username_canonical=?', usr)
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def updateLogin(self, username, salt, isHashed, password, capability):
            if not self.loginExists(username):
                return self.insertLogin(username, salt, isHashed, password, capability)
            usernameCanonical = ircutils.toLower(username)
            if not isHashed:
                isHashed = 0
            else:
                isHashed = 1
            c = self.conn.cursor()
            c.execute('''update trivialogin set
                            username=?,
                            salt=?,
                            password=?,
                            capability=?
                            where username_canonical=?''', (username, salt, isHashed, password, capability, usernameCanonical)
                            )
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
            test = c.execute('''update triviauserlog set
                                username=?,
                                points_made = points_made+?,
                                average_time=( average_time * (1.0*num_answered/(num_answered+?)) + ? * (1.0*?/(num_answered+?)) ),
                                average_score=( average_score * (1.0*num_answered/(num_answered+?)) + ? * (1.0*?/(num_answered+?)) ),
                                num_answered = num_answered+?,
                                last_updated = ?
                                where username_canonical=?
                                and channel_canonical=?
                                and day=?
                                and month=?
                                and year=?''', (username,score,numAnswered,timeTaken,numAnswered,numAnswered,numAnswered,score,numAnswered,numAnswered,numAnswered,epoch,usernameCanonical,channelCanonical,day,month,year))
            self.conn.commit()
            c.close()

        def updateUser(self, username, numEditted=0, numEdittedAccepted=0, numReported=0, numQuestionsAdded=0, numQuestionsAccepted=0):
            if not self.userExists(username):
                return self.insertUser(username, numEditted, numEdittedAccepted, numReported, numQuestionsAdded, numQuestionsAccepted)
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            c.execute('''update triviausers set
                                username=?,
                                num_editted=num_editted+?,
                                num_editted_accepted=num_editted_accepted+?,
                                num_reported=num_reported+?,
                                num_questions_added=num_questions_added+?,
                                num_questions_accepted=num_questions_accepted+?
                                where username_canonical=?''', 
                                        (
                                                username, 
                                                numEditted, 
                                                numEdittedAccepted, 
                                                numReported,
                                                numQuestionsAdded, 
                                                numQuestionsAccepted, 
                                                usernameCanonical
                                        )
                                )
            self.conn.commit()
            c.close()

        def updateUserHighestStreak(self, username, streak):
            if not self.userExists(username):
                return self.insertUser(username)
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            c.execute('''update triviausers set
                            highest_streak=?
                            where highest_streak < ?
                            and username_canonical=?''', (streak, streak, usernameCanonical)
                            )
            self.conn.commit()
            c.close()

        def updateGame(self, channel, numAsked):
            if not self.gameExists(channel):
                return self.insertGame(channel, numAsked)
            c = self.conn.cursor()
            channelCanonical = ircutils.toLower(channel)
            test = c.execute('''update triviagames set
                                channel=?,
                                num_asked=?
                                where channel_canonical=?''', (channel, numAsked, channelCanonical))
            self.conn.commit()
            c.close()

        def updateGameLongestStreak(self, channel, lastWinner, streak):
            c = self.conn.cursor()
            channelCanonical = ircutils.toLower(channel)
            lastWinnerCanonical  = ircutils.toLower(lastWinner)
            test = c.execute('''update triviagames set
                                longest_streak=?,
                                longest_streak_holder=?,
                                longest_streak_holder_canonical=?
                                where channel_canonical=?
                                and longest_streak<?''', (streak, lastWinner, lastWinnerCanonical, channelCanonical, streak))
            self.conn.commit()
            c.close()

        def updateGameStreak(self, channel, lastWinner, streak):
            if not self.gameExists(channel):
                return self.insertGame(channel, 0, None)
            c = self.conn.cursor()
            channelCanonical = ircutils.toLower(channel)
            lastWinner  = ircutils.toLower(lastWinner)
            test = c.execute('''update triviagames set
                                last_winner=?,
                                streak=?
                                where channel_canonical=?''', (lastWinner, streak, channelCanonical))
            self.conn.commit()
            c.close()

        def updateGameRoundStarted(self, channel, lastRoundStarted):
            if not self.gameExists(channel):
                return self.insertGame(channel, numAsked)
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            test = c.execute('''update triviagames set
                                round_started=?
                                where channel_canonical=?''', (lastRoundStarted, channelCanonical))
            self.conn.commit()
            c.close()

        def updateQuestion(self, id, newQuestion):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                question=?
                                where id=?''', (newQuestion, id))
            self.conn.commit()
            c.close()

        def updateQuestionStats(self, id, timesAnswered, timesMissed):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                num_answered=num_answered+?,
                                num_missed=num_missed+?
                                where id=?''', (timesAnswered, timesMissed, id))
            self.conn.commit()
            c.close()

        def viewDayTop10(self, channel, numUpTo=10):
            numUpTo -= 10
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year

            query = '''select id,
                        username,
                        sum(points_made) as points,
                        sum(num_answered)
                        from triviauserlog
                        where day=?
                        and month=?
                        and year=?'''
            arguments = [day, month, year]

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                        order by points desc limit ?, 10''' % (query)
            arguments.append(numUpTo)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))
            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewAllTimeTop10(self, channel, numUpTo=10):
            numUpTo -= 10

            query = '''select id,
                        username,
                        sum(points_made) as points,
                        sum(num_answered)
                        from triviauserlog'''
            arguments = []

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s where channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                        order by points desc
                        limit ?, 10''' % (query)
            arguments.append(numUpTo)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewMonthTop10(self, channel, numUpTo=10, year=None, month=None):
            numUpTo -= 10
            d = datetime.date.today()
            if year is None or month is None:
                year = d.year
                month = d.month

            query = '''select id,
                        username,
                        sum(points_made) as points,
                        sum(num_answered)
                        from triviauserlog
                        where month=?
                        and year=?'''
            arguments = [month, year]

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                        order by points desc limit ?, 10''' % (query)
            arguments.append(numUpTo)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def viewYearTop10(self, channel, numUpTo=10, year=None):
            numUpTo -= 10
            d = datetime.date.today()
            if year is None:
                year = d.year

            query = '''select id,
                        username,
                        sum(points_made) as points,
                        sum(num_answered)
                        from triviauserlog
                        where year=?'''
            arguments = [year]

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                        order by points desc limit ?, 10''' % (query)
            arguments.append(numUpTo)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

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
                            and month=%d
                            and day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)

            query = '''select id,
                        username,
                        sum(points_made) as points,
                        sum(num_answered)
                        from triviauserlog
                        where (%s)''' % weekSqlString
            arguments = []

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s group by username_canonical
                        order by points desc limit ?, 10''' % (query)
            arguments.append(numUpTo)

            c = self.conn.cursor()
            c.execute(query, tuple(arguments))

            data = []
            for row in c:
                data.append(row)
            c.close()
            return data

        def wasUserActiveIn(self, username, channel, timeSeconds):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = ircutils.toLower(channel)
            epoch = int(time.mktime(time.localtime()))
            dateObject = datetime.date.today()
            day   = dateObject.day
            month = dateObject.month
            year  = dateObject.year
            c = self.conn.cursor()
            result = c.execute('''select count(*) from triviauserlog
                        where day=? and month=? and year=?
                        and username_canonical=?
                        and channel_canonical=?
                        and last_updated>?''', (day, month, year, usernameCanonical, channelCanonical, (epoch-timeSeconds)))
            rows = result.fetchone()[0]
            c.close()
            if rows > 0:
                return True
            return False

        def getVersion(self):
            c = self.conn.cursor();
            try:
                c.execute('''select version from triviainfo''')
                return c.fetchone()
            except:
                pass

        def makeInfoTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviainfo (
                    version integer
                    )''')
            except:
                pass

Class = TriviaTime
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
