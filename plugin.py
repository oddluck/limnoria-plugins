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
        self.logger = self.Logger(self)

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
        channel = msg.args[0]
        # Make sure that it is starting inside of a channel, not in pm
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        channelCanonical = ircutils.toLower(channel)

        kaosRemainingCommand= self.registryValue('commands.showHintCommandKAOS', channel)
        otherHintCommand  = self.registryValue('commands.extraHint', channel)

        game = self.getGame(irc, channel)

        if game is not None:
            # Look for command to list remaining KAOS
            if msg.args[1] == kaosRemainingCommand and game.question.find("KAOS:") == 0:
                irc.sendMsg(ircmsgs.notice(msg.nick, "'{0}' now also works for KAOS hints, check it out!".format(otherHintCommand)))
                game.getRemainingKAOS()
            elif msg.args[1] == otherHintCommand:
                if game.question.find("KAOS:") == 0:
                    game.getRemainingKAOS()
                else:
                    game.getOtherHint()
            else:
                # check the answer
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

    def handleVoice(self, irc, nick, username, channel):
        if not self.registryValue('voice.enableVoice'):
            return

        timeoutVoice = self.registryValue('voice.timeoutVoice')
        self.voiceTimeouts.setTimeout(timeoutVoice)
        usernameCanonical = ircutils.toLower(username)
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
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
        newGame = self.Game(irc, channel, self)
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
        
    def reply(self, irc, msg, outstr, prefixNick=True):
        if ircutils.isChannel(msg.args[0]):
            target = msg.args[0]
        else:
            target = msg.nick
        
        if prefixNick == False or ircutils.isNick(target):
            irc.sendMsg(ircmsgs.privmsg(target, outstr))
        else:
            irc.sendMsg(ircmsgs.privmsg(target, '%s: %s' % (msg.nick, outstr)))
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            delete = self.storage.getDeleteById(num)
        else:
            delete = self.storage.getDeleteById(num, channel)
            
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalstats'):
            edit = self.storage.getEditById(num)
        else:
            edit = self.storage.getEditById(num, channel)
            
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
            filename = self.registryValue('admin.quizfile')
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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

        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
            
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        if num is None or num < 10:
            num=10
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewDayTop10(None, num)
        else:
            tops = threadStorage.viewDayTop10(channel, num)
        
        if tops:
            offset = num-9
            topsList = ['Today\'s Top Players: ']
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
            topsText = ''.join(topsList)
            self.reply(irc, msg, topsText, prefixNick=False)
        else:
            self.reply(irc, msg, 'No players have played today.', prefixNick=False)
    day = wrap(day, ['channel', optional('int')])

    def delete(self, irc, msg, arg, user, channel, t, id, reason):
        """[<channel>] [<type "R" or "Q">] <question id> [<reason>]
        Deletes a question from the database. Type decides whether to delete
        by round number (r), or question number (q) (default round).
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        username = self.getUsername(msg.nick, hostmask)
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        elif points < 1:
            irc.error("You cannot give less than 1 point.")
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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

    def listedits(self, irc, msg, arg, channel, page):
        """[<channel>] [<page>]
        List edits pending approval.
        Channel is only required when using the command outside of a channel.
        """
        hostmask = msg.prefix
        if self.isTriviaMod(hostmask, channel) == False:
            irc.reply('You must be at least a TriviaMod in {0} to use this command.'.format(channel))
            return
        
        # Grab list from the database
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
    listedits = wrap(listedits, ['channel', optional('int')])

    def listreports(self, irc, msg, arg, user, channel, page):
        """[<channel>] [<page>]
        List reports pending edit.
        Channel is only required when using the command outside of a channel.
        """
        # Grab list from the database
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        totalUsersEver = threadStorage.getNumUser(channel)
        numActiveThisWeek = threadStorage.getNumActiveThisWeek(channel)
        infoText = ' TriviaTime v1.07 by Trivialand on Freenode: https://github.com/tannn/TriviaTime '
        self.reply(irc, msg, infoText, prefixNick=False)
        infoText = ' Time is %s ' % (time.asctime(time.localtime(),))
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        
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
        if num is None or num < 10:
            num=10
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewMonthTop10(None, num)
        else:
            tops = threadStorage.viewMonthTop10(channel, num)
        
        if tops:
            topsList = ['This Month\'s Top Players: ']
            offset = num-9
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
            topsText = ''.join(topsList)
            self.reply(irc, msg, topsText, prefixNick=False)
        else:
            self.reply(irc, msg, 'No players have played this month.', prefixNick=False)
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
        elif game.questionOver == False:
            self.reply(irc, msg, 'You must wait until the current question is over.')
        elif game.lastWinner != ircutils.toLower(username):
            self.reply(irc, msg, 'You are not currently the streak holder.')
        elif game.streak < minStreak:
            self.reply(irc, msg, 'You do not have a large enough streak yet (%i of %i).' % (game.streak, minStreak))
        else:
            self.reply(irc, msg, 'Onto the next question!', prefixNick=False)
            game.removeEvent()
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        # 3. Has the question already been repeated?
        # 4. Is the question currently blank?
        if game is None or game.active == False:
            self.reply(irc, msg, 'Trivia is not currently running.')
        elif game.questionOver == True:
            self.reply(irc, msg, 'No question is currently being asked.')
        elif game.questionRepeated == False and game.question != '':
            game.repeatQuestion()
            irc.noReply()
        else:
            irc.noReply()
    repeat = wrap(repeat, ['onlyInChannel'])

    def report(self, irc, msg, arg, user, channel, roundNum, text):
        """[channel] <round number> <report text>
        Provide a report for a bad question. Be sure to include the round number and the problem(s). 
        Channel is a optional parameter which is only needed when reporting outside of the channel
        """
        inp = text.strip()
        username = self.getUsername(msg.nick, msg.prefix)
        channelCanonical = ircutils.toLower(channel)
        game = self.getGame(irc, channel)
        if game is not None:
            numAsked = game.numAsked
            questionOver = game.questionOver
            if inp[:2] == 's/':
                if numAsked == roundNum and questionOver == False:
                    irc.reply('Sorry, you must wait until the current question is over to report it.')
                    return
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        question = threadStorage.getQuestionByRound(roundNum, channel)
        if question:
            if inp[:2] == 's/': # Regex
                regex = inp[2:].split('/')
                if len(regex) > 1:
                    threadStorage.updateUser(username, 1, 0)
                    newOne = regex[1]
                    oldOne = regex[0]
                    newQuestionText = question['question'].replace(oldOne, newOne)
                    threadStorage.insertEdit(question['id'], newQuestionText, username, channel)
                    irc.reply('Regex detected: Question edited!')
                    irc.sendMsg(ircmsgs.notice(username, 'NEW: %s' % (newQuestionText)))
                    irc.sendMsg(ircmsgs.notice(username, 'OLD: %s' % (question['question'])))
                    self.logger.doLog(irc, channel, "%s edited question #%i, NEW: '%s', OLD: '%s'" % (msg.nick, question['id'], newQuestionText, question['question']))
                else:
                    irc.error('Unable to process regex. Try again.')
            elif str.lower(utils.str.normalizeWhitespace(inp))[:6] == 'delete': # Delete
                if not threadStorage.questionIdExists(question['id']):
                    irc.error('That question does not exist.')
                elif threadStorage.isQuestionDeleted(question['id']):
                    irc.error('That question is already deleted.')
                elif threadStorage.isQuestionPendingDeletion(question['id']):
                    irc.error('That question is already pending deletion.')
                else:
                    reason = utils.str.normalizeWhitespace(inp)[6:]
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
            irc.error('Sorry, round %d could not be found in the database' % (roundNum))
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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

        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        timeSeconds = self.registryValue('skip.skipActiveTime', channel)
        totalActive = threadStorage.getNumUserActiveIn(channel, timeSeconds)
        channelCanonical = ircutils.toLower(channel)
        game = self.getGame(irc, channel)
        
        # Sanity checks
        if game is None or game.active == False:
            self.reply(irc, msg, 'Trivia is not currently running.')
            return
        elif game.questionOver == True:
            self.reply(irc, msg, 'No question is currently being asked.')
            return
        elif not threadStorage.wasUserActiveIn(username, channel, timeSeconds):
            self.reply(irc, msg, 'Only users who have answered a question in the last %s seconds can vote to skip.' % (timeSeconds))
            return
        elif usernameCanonical in game.skipVoteCount:
            self.reply(irc, msg, 'You can only vote to skip once.')
            return
        elif totalActive < 1:
            return

        # Ensure the game's skip timeout is set? and then check the user
        skipSeconds = self.registryValue('skip.skipTime', channel)
        game.skips.setTimeout(skipSeconds)
        if game.skips.has(usernameCanonical):
            self.reply(irc, msg, 'You must wait %d seconds to be able to skip again.' % (game.skips.getTimeLeft(usernameCanonical)))
            return

        # Update skip count
        game.skipVoteCount[usernameCanonical] = 1
        game.skips.append(usernameCanonical)
        self.reply(irc, msg, '%s voted to skip this question.' % username, prefixNick=False)
        percentAnswered = ((1.0*len(game.skipVoteCount))/(totalActive*1.0))

        # Check if skip threshold has been reached
        if percentAnswered >= self.registryValue('skip.skipThreshold', channel):        
            self.reply(irc, msg, 'Skipped question! (%d of %d voted)' % (len(game.skipVoteCount), totalActive), prefixNick=False)
            game.removeEvent()
            game.nextQuestion()
    skip = wrap(skip, ['onlyInChannel'])

    def stats(self, irc, msg, arg, channel, username):
        """ [<channel>] <username> 
            Show a player's rank, score & questions asked for day, month, and year.
            Channel is only required when using the command outside of a channel.
        """
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            stat = threadStorage.getUserStat(username, None)
            rank = threadStorage.getUserRank(username, None)
        else:
            stat = threadStorage.getUserStat(username, channel)
            rank = threadStorage.getUserRank(username, channel)
            
        if not stat:
            irc.reply("I couldn't find that user in the database.")
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
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        question = threadStorage.getQuestionById(num)
        if question:
            if question['deleted'] == 1:
                irc.reply('Info: This question is currently deleted.')
            irc.reply('Question #%d: %s' % (num, question['question']))
        else:
            irc.error('Question not found')
    showquestion = wrap(showquestion, ['user', 'channel', 'int'])

    def showround(self, irc, msg, arg, user, channel, num):
        """[<channel>] <round num>
        Show what question was asked during gameplay.
        Channel is only necessary when editing from outside of the channel.
        """
        game = self.getGame(irc, channel)
        if game is not None and num == game.numAsked and not game.questionOver:
            irc.error('The current question can\'t be displayed until it is over.')
        else:
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
            question = threadStorage.getQuestionByRound(num, channel)
            if question:
                irc.reply('Round %d: Question #%d: %s' % (num, question['id'], question['question']))
            else:
                irc.error('Round not found')
    showround = wrap(showround, ['user', 'channel', 'int'])

    def showreport(self, irc, msg, arg, user, channel, num):
        """[<channel>] [<report num>]
        Shows report information, if number is provided one record is shown, otherwise the last 3 are. 
        Channel is only necessary when editing from outside of the channel.
        """        
        if num is not None:
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
            if self.registryValue('general.globalstats'):
                report = threadStorage.getReportById(num)
            else:
                report = threadStorage.getReportById(num, channel)
            
            if report:
                irc.reply('Report #%d \'%s\' by %s on %s Q#%d '%(report['id'], report['report_text'], report['username'], report['channel'], report['question_num']))
                question = threadStorage.getQuestionById(report['question_num'])
                if question:
                    irc.error('Question could not be found.')
                else:
                    irc.reply('Question #%d: %s' % (question['id'], question['question']))
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
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
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
            dbLocation = self.registryValue('admin.sqlitedb')
            threadStorage = self.Storage(dbLocation)
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
        elif game.questionOver == False:
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
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
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
        if num is None or num < 10:
            num=10
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewWeekTop10(None, num)
        else:
            tops = threadStorage.viewWeekTop10(channel, num)
        
        if tops:
            topsList = ['This Week\'s Top Players: ']
            offset = num-9
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
            topsText = ''.join(topsList)
            self.reply(irc, msg, topsText, prefixNick=False)
        else:
            self.reply(irc, msg, 'No players have played this week.', prefixNick=False)
    week = wrap(week, ['channel', optional('int')])

    def year(self, irc, msg, arg, channel, num):
        """[<channel>] [<number>]
            Displays the top scores of the year. 
            Parameter is optional, display up to that number. (eg 20 - display 11-20)
            Channel is only required when using the command outside of a channel.
        """
        if num is None or num < 10:
            num=10
        dbLocation = self.registryValue('admin.sqlitedb')
        threadStorage = self.Storage(dbLocation)
        if self.registryValue('general.globalStats'):
            tops = threadStorage.viewYearTop10(None, num)
        else:
            tops = threadStorage.viewYearTop10(channel, num)
        
        if tops:
            topsList = ['This Year\'s Top Players: ']
            offset = num-9
            for i in range(len(tops)):
                topsList.append('\x02 #%d:\x02 %s %d ' % ((i+offset) , self.addZeroWidthSpace(tops[i]['username']), tops[i]['points']))
            topsText = ''.join(topsList)
            self.reply(irc, msg, topsText, prefixNick=False)
        else:
            self.reply(irc, msg, 'No players have played this year.', prefixNick=False)
    year = wrap(year, ['channel', optional('int')])

    #Game instance
    class Game:
        """
        Main game logic, single game instance for each channel.
        """
        def __init__(self, irc, channel, base):
            # constants
            self.unmaskedChars = " -'\"_=+&%$#@!~`[]{}?.,<>|\\/:;"
            
            # get utilities from base plugin
            self.base = base
            self.games = base.games
            self.storage = base.storage
            self.Storage = base.Storage
            self.registryValue = base.registryValue
            self.channel = channel
            self.irc = irc
            self.network = irc.network

            # reset stats
            self.skips = TimeoutList(self.registryValue('skip.skipTime', channel))
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
            
            channel = msg.args[0]
            # is it a user?
            username = self.base.getUsername(msg.nick, msg.prefix)
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
                        if streakBonus > pointsAdded * .5:
                            streakBonus = pointsAdded * .5
                    threadStorage.updateGameStreak(self.channel, self.lastWinner, self.streak)
                    threadStorage.updateUserHighestStreak(self.lastWinner, self.streak)
                    threadStorage.updateGameLongestStreak(self.channel, username, self.streak)
                    # Convert score to int
                    pointsAdded = int(pointsAdded)

                    # report correct guess, and show players streak
                    threadStorage.updateUserLog(username, self.channel, (pointsAdded+streakBonus), 1, timeElapsed)
                    self.lastAnswer = time.time()
                    self.sendMessage('DING DING DING, \x02%s\x02 got the correct answer, \x02%s\x02, in \x02%0.4f\x02 seconds for \x02%d(+%d)\x02 points!' % (username, correctAnswer, timeElapsed, pointsAdded, streakBonus))

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
                #self.base.handleVoice(self.irc, username, channel)

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
            if self.questionOver:
                return
            if len(self.answers) > 1:
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
            elif self.stopPending == True:
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
                self.sendMessage('There are no questions. Stopping. If you are an admin, use the addfile command to add questions to the database.')
                self.stop()
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

            self.sendQuestion()
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
            self.questionRepeated = True
            try:
                self.sendQuestion()
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
                        if answer.count(ans) == 0:
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
            return (question['id'], question['question'], question['num_answered'], question['num_missed'])

        def sendMessage(self, msg, color=None, bgcolor=None):
            """ <msg>, [<color>], [<bgcolor>]
            helper for game instance to send messages to channel
            """
            # no color
            self.irc.sendMsg(ircmsgs.privmsg(self.channel, ' %s ' % msg))

        def sendQuestion(self):
            question = self.question.rstrip()
            if question[-1:] != '?':
                question += '?'

            # bold the q, add color
            questionText = '\x02\x0303%s' % (question)

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
                c.execute('''SELECT COUNT(*) FROM triviatemporaryquestion''')
            else:
                c.execute('''SELECT COUNT(*) FROM triviatemporaryquestion
                             WHERE channel_canonical = ?''', (ircutils.toLower(channel),))
            row = c.fetchone()
            c.close()
            return row[0]

        def countDeletes(self, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT COUNT(*) FROM triviadelete''')
            else:
                c.execute('''SELECT COUNT(*) FROM triviadelete
                             WHERE channel_canonical = ?''', (ircutils.toLower(channel),))
            row = c.fetchone()
            c.close()
            return row[0]

        def countEdits(self, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT COUNT(*) FROM triviaedit''')
            else:
                c.execute('''SELECT COUNT(*) FROM triviaedit
                             WHERE channel_canonical = ?''', (ircutils.toLower(channel),))
            row = c.fetchone()
            c.close()
            return row[0]

        def countReports(self, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT COUNT(*) FROM triviareport''')
            else:
                c.execute('''SELECT COUNT(*) FROM triviareport
                             WHERE channel_canonical = ?''', (ircutils.toLower(channel),))
            row = c.fetchone()
            c.close()
            return row[0]
        
        def deleteQuestion(self, questionId):
            c = self.conn.cursor()
            test = c.execute('''UPDATE triviaquestion set
                                deleted=1
                                WHERE id=?''', (questionId,))
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

        def getRandomQuestionNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviaquestion
                         WHERE deleted=0 AND id NOT IN 
                            (SELECT tl.line_num FROM triviagameslog tl 
                             WHERE tl.channel_canonical=? AND tl.asked_at>=?)
                         ORDER BY random() LIMIT 1''', 
                         (ircutils.toLower(channel),roundStart))
            row = c.fetchone()
            c.close()
            return row

        def getQuestionById(self, id):
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviaquestion WHERE id=? LIMIT 1''', (id,))
            row = c.fetchone()
            c.close()
            return row

        def getQuestionByRound(self, roundNumber, channel):
            channel=ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviaquestion 
                         WHERE id=(SELECT tgl.line_num FROM triviagameslog tgl
                                   WHERE tgl.round_num=? AND tgl.channel_canonical=?
                                   ORDER BY id DESC LIMIT 1)''', (roundNumber,channel))
            row = c.fetchone()
            c.close()
            return row

        def getNumQuestionsNotAsked(self, channel, roundStart):
            c = self.conn.cursor()
            c.execute('''SELECT count(id) FROM triviaquestion
                         WHERE deleted=0 AND id NOT IN 
                            (SELECT tl.line_num FROM triviagameslog tl 
                             WHERE tl.channel=? AND tl.asked_at>=?)''', (channel,roundStart))
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
            row = c.fetchone()
            data['total'] = row[0] if row else 0

            # Retrieve year rank
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
            row = c.fetchone()
            data['year'] = row[0] if row else 0

            # Retrieve month rank
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
                                and username_canonical=?''' % (query)
            arguments.append(month)
            arguments.append(year)
            arguments.append(usernameCanonical)

            if channel is not None:
                query = '''%s and channel_canonical=?''' % (query)
                arguments.append(channelCanonical)

            query = '''%s ) limit 1''' % (query)

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
            row = c.fetchone()
            data['week'] = row[0] if row else 0

            # Retrieve day rank
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
            row = c.fetchone()
            if row:
                data['points_total'] = row[0]
                data['answer_total'] = row[1]
            
            # Retrieve year points and answered
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
            row = c.fetchone()
            if row:
                data['points_year'] = row[0]
                data['answer_year'] = row[1]

            # Retrieve month points and answered
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
            row = c.fetchone()
            if row:
                data['points_month'] = row[0]
                data['answer_month'] = row[1]

            # Retrieve week points and answered
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
            row = c.fetchone()
            if row:
                data['points_week'] = row[0]
                data['answer_week'] = row[1]

            # Retrieve day points and answered
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
            row = c.fetchone()
            if row:
                data['points_day'] = row[0]
                data['answer_day'] = row[1]

            c.close()
            return data

        def getGame(self, channel):
            channel = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT * FROM triviagames
                         WHERE channel_canonical=? LIMIT 1''', (channel,))
            row = c.fetchone()
            c.close()
            return row

        def getNumUser(self, channel):
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(DISTINCT(username_canonical)) FROM triviauserlog 
                         WHERE channel_canonical=?''', (channelCanonical,))
            row = c.fetchone()
            c.close()
            return row[0]

        def getNumQuestions(self):
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(*) FROM triviaquestion 
                         WHERE deleted=0''')
            row = c.fetchone()
            c.close()
            return row[0]

        def getNumKAOS(self):
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(*) FROM triviaquestion 
                         WHERE lower(substr(question,1,4))=?''',('kaos',))
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
                            and tl.month=%d
                            and tl.day=%d)''' % (d.year, d.month, d.day)
                d += datetime.timedelta(1)
            c = self.conn.cursor()
            weekSql = '''select count(distinct(tl.username_canonical))
                        from triviauserlog tl
                        where channel_canonical=? and ('''
            weekSql += weekSqlString
            weekSql += ''')'''
            c.execute(weekSql, (channelCanonical,))
            row = c.fetchone()
            c.close()
            return row[0]

        def getDeleteById(self, id, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT * FROM triviadelete 
                             WHERE id=? LIMIT 1''', (id,))
            else:
                c.execute('''SELECT * FROM triviadelete 
                             WHERE id=? AND channel_canonical=? 
                             LIMIT 1''', (id, ircutils.toLower(channel)))
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
                c.execute('''SELECT * FROM triviadelete 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (start, amount))
            else:
                c.execute('''SELECT * FROM triviadelete 
                             WHERE channel_canonical = ? 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (ircutils.toLower(channel), start, amount))
            rows = c.fetchall()
            c.close()
            return rows

        def getReportById(self, id, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT * FROM triviareport 
                             WHERE id=? LIMIT 1''', (id,))
            else:
                c.execute('''SELECT * FROM triviareport 
                             WHERE id=? AND channel_canonical=? 
                             LIMIT 1''', (id, ircutils.toLower(channel)))
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
                c.execute('''SELECT * FROM triviareport 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (start, amount))
            else:
                c.execute('''SELECT * FROM triviareport 
                             WHERE channel_canonical = ? 
                             ORDER BY id DESC LIMIT ?, ?''', 
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
                c.execute('''SELECT * FROM triviatemporaryquestion 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (start, amount))
            else:
                c.execute('''SELECT * FROM triviatemporaryquestion 
                             WHERE channel_canonical = ? 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (ircutils.toLower(channel), start, amount))
            rows = c.fetchall()
            c.close()
            return rows

        def getTemporaryQuestionById(self, id, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT * FROM triviatemporaryquestion 
                             WHERE id=? LIMIT 1''', (id,))
            else:
                c.execute('''SELECT * FROM triviatemporaryquestion 
                             WHERE id=? AND channel_canonical=? 
                             LIMIT 1''', (id, ircutils.toLower(channel)))
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
                c.execute('''SELECT * FROM triviaedit 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (start, amount))
            else:
                c.execute('''SELECT * FROM triviaedit 
                             WHERE channel_canonical = ? 
                             ORDER BY id DESC LIMIT ?, ?''', 
                             (ircutils.toLower(channel), start, amount))
            rows = c.fetchall()
            c.close()
            return rows
            
        def getEditById(self, id, channel=None):
            c = self.conn.cursor()
            if channel is None:
                c.execute('''SELECT * FROM triviaedit 
                             WHERE id=? LIMIT 1''', (id,))
            else:
                c.execute('''SELECT * FROM triviaedit 
                             WHERE id=? AND channel_canonical=? 
                             LIMIT 1''', (id, ircutils.toLower(channel)))
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
            c.execute('''SELECT COUNT(*) FROM triviauserlog
                         WHERE day=? AND month=? AND year=?
                               AND channel_canonical=?
                               AND last_updated>?''', 
                         (day, month, year, channelCanonical, (epoch-timeSeconds)))
            row = c.fetchone()
            c.close()
            return row[0]

        def gameExists(self, channel):
            channel = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(id) FROM triviagames 
                         WHERE channel_canonical=?''', (channel,))
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def loginExists(self, username):
            usernameCanonical = ircutils.toLower(username)
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(id) FROM trivialogin 
                         WHERE username_canonical=?''', (usernameCanonical,))
            rows = c.fetchone()
            c.close()
            return row[0] > 0

        def insertActivity(self, aType, activity, channel, network, timestamp=None):
            if timestamp is None:
                timestamp = int(time.mktime(time.localtime()))
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('insert into triviaactivity values (NULL, ?, ?, ?, ?, ?, ?)',
                                    (aType, activity, channel, channelCanonical, network, timestamp))
            self.conn.commit()

        def insertDelete(self, username, channel, lineNumber, reason):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('insert into triviadelete values (NULL, ?, ?, ?, ?, ?, ?)',
                                    (username, usernameCanonical, lineNumber, channel, channelCanonical, reason))
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
            c.execute('''INSERT INTO triviaedit VALUES (NULL, ?, ?, NULL, ?, ?, ?, ?, ?)''',
                            (questionId,questionText,username,channel,createdAt, usernameCanonical, channelCanonical))
            self.conn.commit()
            c.close()

        def insertTemporaryQuestion(self, username, channel, question):
            c = self.conn.cursor()
            channelCanonical = ircutils.toLower(channel)
            usernameCanonical = ircutils.toLower(username)
            c.execute('''INSERT INTO triviatemporaryquestion VALUES (NULL, ?, ?, ?, ?, ?)''',
                            (username,channel,question,usernameCanonical,channelCanonical))
            self.conn.commit()
            c.close()

        def isQuestionDeleted(self, id):
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(*) FROM triviaquestion
                         WHERE deleted=1 AND id=?''', (id,))
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def isQuestionPendingDeletion(self, id):
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(*) FROM triviadelete
                         WHERE line_num=?''', (id,))
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def makeActivityTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviaactivity (
                        id integer primary key autoincrement,
                        type text,
                        activity text,
                        channel text,
                        channel_canonical text,
                        network text,
                        timestamp integer
                        )''')
            except:
                pass
            self.conn.commit()
            c.close()

        def makeDeleteTable(self):
            c = self.conn.cursor()
            try:
                c.execute('''create table triviadelete (
                        id integer primary key autoincrement,
                        username text,
                        username_canonical text,
                        line_num integer,
                        channel text,
                        channel_canonical text,
                        reason text
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
            c.execute('''SELECT COUNT(id) FROM triviaquestion 
                         WHERE question=? OR question_canonical=?''', 
                         (question,question))
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def questionIdExists(self, id):
            c = self.conn.cursor()
            c.execute('''SELECT COUNT(id) FROM triviaquestion 
                         WHERE id=?''', (id,))
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def removeOldActivity(self,count=100):
            c = self.conn.cursor()
            c.execute('''delete from triviaactivity
                        where id not in (
                            select id
                            from triviaactivity
                            order by id desc
                            limit ?
                        )''', (count,))
            self.conn.commit()
            c.close()

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

        def removeUserLogs(self, username, channel):
            usernameCanonical = ircutils.toLower(username)
            channelCanonical = ircutils.toLower(channel)
            c = self.conn.cursor()
            c.execute('''delete from triviauserlog
                        where username_canonical=?
                        and channel_canonical=?''', 
                        (usernameCanonical, channelCanonical))
            self.conn.commit()
            c.close()

        def restoreQuestion(self, id):
            c = self.conn.cursor()
            test = c.execute('''update triviaquestion set
                                deleted=0
                                where id=?''', (id,))
            self.conn.commit()
            c.close()

        def transferUserLogs(self, userFrom, userTo, channel):
            userFromCanonical = ircutils.toLower(userFrom)
            userToCanonical = ircutils.toLower(userTo)
            channelCanonical = ircutils.toLower(channel)
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
                                            and t3.channel_canonical=?
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
                                            and t2.channel_canonical=?
                                            and t2.username_canonical=?
                                    )
                            ,0)
                    where id in (
                            select id
                            from triviauserlog tl
                            where channel_canonical=?
                            and username_canonical=?
                            and exists (
                                    select id
                                    from triviauserlog tl2
                                    where tl2.day=tl.day
                                    and tl2.month=tl.month
                                    and tl2.year=tl.year
                                    and tl2.channel_canonical=?
                                    and tl2.username_canonical=?
                            )
                    )
            ''', (channelCanonical, userFromCanonical,
                  channelCanonical, userFromCanonical, 
                  channelCanonical, userToCanonical,
                  channelCanonical, userFromCanonical))

            c.execute('''
                    update triviauserlog
                    set username=?,
                    username_canonical=?
                    where username_canonical=?
                    and channel_canonical=?
                    and not exists (
                            select 1
                            from triviauserlog tl
                            where tl.day=triviauserlog.day
                            and tl.month=triviauserlog.month
                            and tl.year=triviauserlog.year
                            and tl.channel_canonical=?
                            and tl.username_canonical=?
                    )
            ''', (userTo, userToCanonical, userFromCanonical, 
                  channelCanonical, channelCanonical, userToCanonical))
            self.conn.commit()

            self.removeUserLogs(userFrom, channel)

        def userLogExists(self, username, channel, day, month, year):
            c = self.conn.cursor()
            args = (ircutils.toLower(username),ircutils.toLower(channel),day,month,year)
            c.execute('''SELECT COUNT(id) FROM triviauserlog 
                         WHERE username_canonical=? AND channel_canonical=? 
                               AND day=? AND month=? and year=?''', args)
            row = c.fetchone()
            c.close()
            return row[0] > 0

        def userExists(self, username):
            c = self.conn.cursor()
            usr = (ircutils.toLower(username),)
            c.execute('''SELECT COUNT(id) FROM triviausers 
                         WHERE username_canonical=?''', usr)
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
            c.execute('''update trivialogin set
                            username=?,
                            salt=?,
                            is_hashed=?,
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

            query = '''SELECT id, username,
                              SUM(points_made) AS points,
                              SUM(num_answered) AS num
                       FROM triviauserlog
                       WHERE day=? AND month=? AND year=?'''
            arguments = [day, month, year]

            if channel is not None:
                channelCanonical = ircutils.toLower(channel)
                query = '''%s and channel_canonical=?''' % (query)
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

            query = '''SELECT id, username,
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

            query = '''SELECT id, username,
                              SUM(points_made) AS points,
                              SUM(num_answered) AS num
                       FROM triviauserlog
                       WHERE month=? AND year=?'''
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

            query = '''SELECT id, username,
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

            query = '''SELECT id, username, 
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
            c.execute('''SELECT count(*) FROM triviauserlog
                         WHERE day=? AND month=? AND year=? 
                               AND username_canonical=? AND channel_canonical=?
                               AND last_updated>?''', 
                         (day, month, year, usernameCanonical, channelCanonical, (epoch-timeSeconds)))
            row = c.fetchone()
            c.close()
            return row[0] > 0

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

Class = TriviaTime
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
