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


from bs4 import BeautifulSoup
from ftfy import fix_text
from jinja2 import Template
from supybot.commands import *
import math
import os
import random
import re
import requests
import string
import supybot.callbacks as callbacks
import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.log as log
import supybot.plugins as plugins
import supybot.schedule as schedule
import supybot.utils as utils
import textdistance
import time

from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('Jeopardy')


class Jeopardy(callbacks.Plugin):
    """Add the help for "@plugin help Jeopardy" here
    This should describe *how* to use this plugin."""
    threaded = True


    def __init__(self, irc):
        self.__parent = super(Jeopardy, self)
        self.__parent.__init__(irc)
        self.games = requests.structures.CaseInsensitiveDict()
        self.history = requests.structures.CaseInsensitiveDict()
        self.jserviceUrl = self.registryValue('jserviceUrl').strip('/')


    def doPrivmsg(self, irc, msg):
        channel = msg.channel
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if self.registryValue('enabled', channel) and channel in self.games:
            self.games[channel].answer(msg)


    class Game:
        def __init__(self, irc, channel, num, hints, timeout, shuffle, categories, restart, showHints, showBlank, showTime, plugin):
            self.registryValue = plugin.registryValue
            self.active = True
            self.answered = 0
            self.blankChar = self.registryValue('blankChar', channel)
            self.categories = categories
            self.channel = channel
            self.correct = True
            self.correct_template = Template(self.registryValue("template.correct", channel))
            self.currentHint = ''
            self.delay = self.registryValue('delay', channel)
            self.directory = conf.supybot.directories.data.dirize("jeopardy/")
            self.flexibility = self.registryValue('flexibility', channel)
            self.games = plugin.games
            self.hint_template = Template(self.registryValue("template.hint", channel))
            self.history = plugin.history
            self.historyFile = "{0}/history_{1}.txt".format(self.directory, channel)
            self.irc = irc
            self.jserviceUrl = plugin.jserviceUrl
            self.num = num
            self.numAsked = 0
            self.numClues = num
            self.numHints = hints
            self.points = self.registryValue('defaultPointValue')
            self.question = ''
            self.question_template = Template(self.registryValue("template.question", channel))
            self.questions = []
            self.reduction = self.registryValue('hintReduction', self.channel)
            self.restart = restart
            self.roundscores = requests.structures.CaseInsensitiveDict()
            self.scoreFile = "{0}/scores_{1}.txt".format(self.directory, channel)
            self.scores = requests.structures.CaseInsensitiveDict()
            self.showBlank = showBlank
            self.showHints = showHints
            self.showTime = showTime
            self.shuffled = shuffle
            self.skip_template = Template(self.registryValue("template.skip", channel))
            self.stop_template = Template(self.registryValue("template.stop", channel))
            self.time_template = Template(self.registryValue("template.time", channel))
            self.timeout = timeout
            self.total = num
            self.unanswered = 0
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            if self.registryValue('keepHistory', channel):
                if not os.path.exists(self.historyFile):
                    f = open(self.historyFile, 'w')
                    f.close()
                if not self.history.get(channel):
                    self.history[channel] = []
                    f = open(self.historyFile, 'r')
                    lines = f.readlines()
                    for line in lines:
                        self.history[channel].append(int(line))
                    f.close()
            if not os.path.exists(self.scoreFile):
                f = open(self.scoreFile, 'w')
                f.close()
            if not self.scores:
                f = open(self.scoreFile, 'r')
                lines = f.readlines()
                for line in lines:
                    (name, score) = line.split(' ')
                    self.scores[name] = int(score)
                f.close()
            cluecount = self.num
            if self.categories == 'random':
                n = 0
                asked = []
                while n <= self.num:
                    if n == self.num:
                        break
                    try:
                        if self.jserviceUrl == 'http://jservice.io':
                            data = requests.get("{0}/api/random".format(self.jserviceUrl), timeout=5).json()
                        else:
                            data = requests.get("{0}/api/random?count={1}".format(self.jserviceUrl, self.num + 5), timeout=5).json()
                        for item in data:
                            if n == self.num:
                                break
                            id = item['id']
                            clue = item['question'].strip()
                            airdate = item['airdate'].split('T')[0]
                            answer = item['answer'].strip()
                            category = string.capwords(item['category']['title'])
                            invalid = item['invalid_count']
                            points = self.points
                            if item['value']:
                                points = int(item['value'])
                            else:
                                points = self.points
                            if self.registryValue('keepHistory', channel):
                                if clue and airdate and answer and category and not invalid and id not in asked and id not in self.history[channel]:
                                    q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                    q = self.normalize(q)
                                    self.questions.append(q)
                                    asked.append(id)
                                    n += 1
                            else:
                                if clue and airdate and answer and category and not invalid and id not in asked:
                                    q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                    q = self.normalize(q)
                                    self.questions.append(q)
                                    asked.append(id)
                                    n += 1
                    except Exception:
                        continue
            else:
                n = 0
                k = 0
                asked = []
                while n <= self.num:
                    if n == self.num or k > len(self.categories):
                        break
                    for category in self.categories:
                        if n == self.num or k > len(self.categories):
                            break
                        try:
                            category = int(category)
                            data = requests.get("{0}/api/clues?category={1}".format(self.jserviceUrl, category)).json()
                            cluecount = data[0]['category']['clues_count']
                            if cluecount < self.num and len(self.categories) == 1:
                                self.num = cluecount
                            if cluecount > 100:
                                data.extend(requests.get("{0}/api/clues?&category={1}&offset=100".format(self.jserviceUrl, category), timeout=5).json())
                            if cluecount > 200:
                                data.extend(requests.get("{0}/api/clues?&category={1}&offset=200".format(self.jserviceUrl, category), timeout=5).json())
                            if cluecount > 300:
                                data.extend(requests.get("{0}/api/clues?&category={1}&offset=300".format(self.jserviceUrl, category), timeout=5).json())
                            if cluecount > 400:
                                data.extend(requests.get("(0}/api/clues?&category={1}&offset=400".format(self.jserviceUrl, category), timeout=5).json())
                            if cluecount > 500:
                                data.extend(requests.get("{0}/api/clues?&category={1}&offset=500".format(self.jserviceUrl, category), timeout=5).json())
                            j = 0
                            for item in data:
                                if n == self.num or k > len(self.categories):
                                    break
                                elif shuffle and k == len(self.categories):
                                    shuffle = False
                                    k = 0
                                    pass
                                elif shuffle and j >= self.num * 0.2:
                                    break
                                id = item['id']
                                clue = item['question'].strip()
                                airdate = item['airdate'].split('T')[0]
                                answer = item['answer'].strip()
                                category = string.capwords(item['category']['title'])
                                invalid = item['invalid_count']
                                points = self.points
                                if item['value']:
                                    points = int(item['value'])
                                else:
                                    points = self.points
                                if self.registryValue('keepHistory', channel):
                                    if clue and airdate and answer and category and not invalid and id not in asked and id not in self.history[channel]:
                                        q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                        q = self.normalize(q)
                                        self.questions.append(q)
                                        asked.append(id)
                                        n += 1
                                        j += 1
                                else:
                                    if clue and airdate and answer and category and not invalid and id not in asked:
                                        q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                        q = self.normalize(q)
                                        self.questions.append(q)
                                        asked.append(id)
                                        n += 1
                                        j += 1
                            k += 1
                        except Exception:
                            continue
            del data
            if self.shuffled or self.registryValue('randomize', channel):
                random.shuffle(self.questions)
            else:
                self.questions = self.questions[::-1]
            self.total = len(self.questions)
            self.num = len(self.questions)
            self.newquestion()


        def normalize(self, q):
            q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).replace(r"\'", "'").replace(r'\"', '"')
            q = re.sub('([,;:.!?)])(\w|\"|\'|\()(?![.\'])', '\g<1> \g<2>', q)
            q = re.sub('(\$\d+[,.]) (\d+)', '\g<1>\g<2>', q)
            q = " ".join(q.split())
            return q


        def newquestion(self):
            if not self.active:
                return
            self.clear()
            inactiveShutoff = self.registryValue('inactiveShutoff', self.channel)
            if self.num == 0 or self.answered == self.total or self.numAsked == self.total:
                self.stop()
                return
            elif self.unanswered > inactiveShutoff and inactiveShutoff > 0:
                self.reply('Seems like no one\'s playing any more. Jeopardy! stopped.')
                self.stop()
                return
            elif len(self.questions) == 0:
                self.reply('Oops! I ran out of questions!')
                self.stop()
                return
            self.show = {}
            self.revealed = {}
            self.id = None
            self.hints = 0
            self.shown = 0
            self.num -= 1
            self.numAsked += 1
            q = self.questions.pop(len(self.questions)-1).split('|')
            question = {}
            self.id = q[0]
            question['airdate'] = q[1]
            self.p = int(q[2])
            question['category'] = q[3]
            question['clue'] = q[4]
            self.a = q[5]
            question['points'], question['number'], question['total'] = self.p, self.numAsked, self.total
            self.question = self.question_template.render(question)
            ans = re.sub('\(\d of\)', '', self.a)
            self.a = [ans]
            if "(" in self.a[0]:
                a1, a2, a3 = re.match("(.*)\((.*)\)(.*)", self.a[0]).groups()
                self.a.append(a1 + a3)
                self.a.append(a2)
            def next_question():
                self.clear()
                self.blank = re.sub('\w', self.blankChar, self.a[0])
                self.currentHint = self.blank
                self.correct = False
                self.reply(self.question)
                self.endTime = time.time() + self.timeout
                self.waitTime = self.timeout / (self.numHints + 1)
                if self.registryValue('keepHistory', self.channel):
                    self.history[self.channel].append(int(self.id))
                if self.timeout > 0:
                    def event():
                        self.timedEvent()
                    def noTime():
                        self.end()
                    schedule.addEvent(noTime, self.endTime, 'end_%s' % self.channel)
                    if self.showBlank:
                        self.hint()
                    elif self.timeout > 0 and self.showHints or self.showTime:
                        eventTime = time.time() + self.waitTime
                        schedule.addEvent(event, eventTime, 'event_%s' % self.channel)
                elif self.showBlank:
                    self.hint()
            if self.numAsked > 1 and self.delay > 0:
                delayTime = time.time() + self.delay
                schedule.addEvent(next_question, delayTime, 'clue_%s' % self.channel)
            else:
                next_question()


        def clear(self):
            try:
                schedule.removeEvent('event_%s' % self.channel)
            except:
                pass
            try:
                schedule.removeEvent('clue_%s' % self.channel)
            except:
                pass
            try:
                schedule.removeEvent('end_%s' % self.channel)
            except:
                pass


        def stop(self):
            self.write()
            self.clear()
            if self.registryValue('showScores', self.channel):
                scores = iter(self.roundscores.items())
                sorted = []
                for i in range(0, len(self.roundscores)):
                    item = next(scores)
                    sorted.append(item)
                sorted.sort(key=lambda item: item[1], reverse=True)
                max = 3
                if len(sorted) < max:
                    max = len(sorted)
                s = _('Top finishers:')
                if max > 0:
                    for i in range(0, max):
                        item = sorted[i]
                        s = _('%s (%s: %s)') % (s, item[0], item[1])
                    self.reply('{0}'.format(s))
            if self.restart and self.active:
                def event():
                    self.__init__(self.irc, self.channel, self.numClues, self.numHints, self.timeout, False, 'random', self.restart, self.showHints, self.showBlank, self.ShowTime, self)
                delayTime = time.time() + self.delay
                schedule.addEvent(event, delayTime, 'clue_%s' % self.channel)
            else:
                self.active = False


        def timedEvent(self):
            if not self.active or self.timeout == 0:
                return
            if self.showHints:
                self.hint()
            elif self.showTime:
                reply = self.time_template.render(time = round(self.endTime - time.time()))
                self.reply(reply)
                if self.timeout > 0:
                    def event():
                        self.timedEvent()
                    eventTime = time.time() + self.waitTime
                    schedule.addEvent(event, eventTime, 'event_%s' % self.channel)


        def end(self):
            if not self.active or self.timeout == 0:
                return
            reply = self.skip_template.render(answer = self.a[0])
            self.reply(reply)
            self.unanswered += 1
            self.corect = True
            self.answered += 1
            self.clear()
            self.newquestion()


        def hint(self):
            if not self.active:
                return
            try:
                schedule.removeEvent('event_%s' % self.channel)
            except:
                pass
            if self.hints <= self.numHints and self.hints > 0:
                ans = self.a[0]
                self.show.setdefault(self.id, None)
                self.revealed.setdefault(self.id, None)
                hintPercentage = self.registryValue('hintPercentage', self.channel)
                divider = round(len(re.sub('[^a-zA-Z0-9]+', '', ans)) * hintPercentage)
                if not self.show[self.id]:
                    self.show[self.id] = list(self.blank)
                if not self.revealed[self.id]:
                    self.revealed[self.id] = list(range(len(self.show[self.id])))
                i = 0
                while i < divider and len(self.revealed[self.id]) > 1:
                    try:
                        rand = self.revealed[self.id].pop(random.randint(0,len(self.revealed[self.id])) - 1)
                        if self.show[self.id][rand] == self.blankChar:
                            self.show[self.id][rand] = list(ans)[rand]
                            i += 1
                    except:
                        break
                self.currentHint = "{0}".format(''.join(self.show[self.id]))
            if self.hints > 0:
                self.p -= int(self.p * self.reduction)
            def event():
                self.timedEvent()
            if self.timeout > 0 and self.showHints or self.showTime:
                eventTime = time.time() + self.waitTime
                schedule.addEvent(event, eventTime, 'event_%s' % self.channel)
                reply = self.hint_template.render(hint = self.currentHint, time = round(self.endTime - time.time()))
            else:
                reply = self.hint_template.render(hint = self.currentHint, time = None)
            self.reply(reply)
            self.hints += 1


        def answer(self, msg):
            if not self.active:
                return
            if not self.correct:
                channel = msg.channel
                for ans in self.a:
                    ans = " ".join(ans.split()).strip().lower()
                    guess = " ".join(msg.args[1].split()).strip().lower()
                    if guess == ans:
                        self.correct = True
                        break
                    elif not self.correct and len(ans) > 2:
                        answer = re.sub('[^a-zA-Z0-9 ]+', '', ans)
                        answer = re.sub('^a |^an |^the |^or ', '', answer).replace(' ', '')
                        guess = re.sub('[^a-zA-Z0-9 ]+', '', guess)
                        guess = re.sub('^a |^an |^the |^or ', '', guess).replace(' ', '')
                    elif not self.correct:
                        answer = re.sub('[^a-zA-Z0-9]+', '', ans)
                        guess = re.sub('[^a-zA-Z0-9]+', '', guess)
                    if not self.correct and guess == answer:
                        self.correct = True
                        break
                    elif not self.correct and self.flexibility < 1 and self.flexibility > 0.5:
                        dist = textdistance.jaro_winkler(guess, answer)
                        log.debug("Jeopardy: guess: {0}, answer: {1}, length: {2}, distance: {3}, flexibility: {4}".format(guess, answer, len(answer), dist, self.flexibility))
                        if dist >= self.flexibility:
                            self.correct = True
                            break
                        elif dist < self.flexibility and ',' in self.a[0] or '&' in self.a[0]:
                            dist = textdistance.jaccard(guess, answer)
                            if dist >= self.flexibility:
                                self.correct = True
                                break
                if self.correct:
                    if not msg.nick in self.scores:
                        self.scores[msg.nick] = 0
                    self.scores[msg.nick] += self.p
                    if not msg.nick in self.roundscores:
                        self.roundscores[msg.nick] = 0
                    self.roundscores[msg.nick] += self.p
                    self.unanswered = 0
                    reply = self.correct_template.render(nick = msg.nick, answer = self.a[0], points = self.p, round = self.roundscores[msg.nick], total = self.scores[msg.nick])
                    self.reply(reply)
                    self.correct = True
                    self.answered += 1
                    self.clear()
                    self.newquestion()


        def reply(self, s):
            if self.registryValue('useBold', self.channel):
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, ircutils.bold(s)))
            else:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, s))


        def write(self):
            f = open(self.scoreFile, 'w')
            scores = iter(self.scores.items())
            for i in range(0, len(self.scores)):
                score = next(scores)
                f.write('%s %s\n' % (score[0], score[1]))
            f.close()

            if self.registryValue('keepHistory', self.channel):
                f = open(self.historyFile, 'w')
                history = iter(self.history[self.channel])
                for i in range(0, len(self.history[self.channel])):
                    id = next(history)
                    f.write('%s\n' % (id))
                f.close()


    @internationalizeDocstring
    def start(self, irc, msg, args, channel, optlist, categories):
        """[channel] [--num <#>] [--no-hints] [--shuffle] [<category1>, <category2>, etc.]
        Play Jeopardy! with random questions or search categories by name.
        --num for number of questions.
        --no-hints to disable automatic hint replies.
        --shuffle to randomize questions from search results.
        """
        if not channel:
            channel = msg.channel
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        if not self.registryValue('enabled', channel):
            return
        if channel in self.games:
            if self.games[channel].active:
                if self.registryValue('useBold', channel):
                    irc.reply(ircutils.bold("There is already a Jeopardy! game running in {0}.".format(channel)))
                else:
                    irc.reply("There is already a Jeopardy! game running in {0}.".format(channel))
                return
        showBlank = self.registryValue('showBlank', channel)
        showHints = self.registryValue('showHints', channel)
        showTime = self.registryValue('showTime', channel)
        optlist = dict(optlist)
        if 'num' in optlist:
            num = optlist.get('num')
        else:
            num = self.registryValue('defaultRoundLength', channel)
        if 'shuffle' in optlist:
            shuffle = True
        else:
            shuffle = False
        if 'no-hints' in optlist:
            showHints = False
            showBlank = False
        if 'hints' in optlist:
            hints = optlist.get('hints')
        else:
            hints = self.registryValue('numHints', channel)
        if 'timeout' in optlist:
            timeout = optlist.get('timeout')
        else:
            timeout = self.registryValue('timeout', channel)
        if timeout == 0:
            showHints = False
            showTime = False
        if 'restart' in optlist:
            restart = True
        else:
            restart = self.registryValue('autoRestart', channel)
        if 'random-category' in optlist:
            if self.jserviceUrl == 'http://jservice.io':
                seed = random.randint(0,184) * 100
            else:
                seed = random.randint(0,250) * 100
            data = requests.get("{0}/api/categories?count=100&offset={1}".format(self.jserviceUrl, int(seed)), timeout=5).json()
            random.shuffle(data)
            results = []
            for item in data:
                if item['clues_count'] > 9:
                    results.append(item['id'])
            if not results:
                results = 'random'
        elif categories:
            results = []
            categories = categories.strip().split(",")
            for category in categories:
                category = category.strip()
                if category.isdigit():
                    results.append(category)
                else:
                    url = "{0}/search?query={1}".format(self.jserviceUrl, category)
                    data = requests.get(url, timeout=5)
                    soup = BeautifulSoup(data.text)
                    searches = soup.find_all('a')
                    for i in range(len(searches)):
                        search = searches[i].get('href').split('/')[-1]
                        if search.isdigit():
                            results.append(search)
            if not results:
                if self.registryValue('useBold', channel):
                    irc.reply(ircutils.bold("Error. Could not find any results for {0}".format(categories)), prefixNick = False)
                else:
                    irc.reply("Error. Could not find any results for {0}".format(categories), prefixNick = False)
                return
            elif results and 'shuffle' in optlist:
                random.shuffle(results)
        else:
            results = 'random'
        if self.registryValue('useBold', channel):
            irc.reply(ircutils.bold("This... is... Jeopardy!"), prefixNick = False)
        else:
            irc.reply("This... is... Jeopardy!", prefixNick = False)
        self.games[channel] = self.Game(irc, channel, num, hints, timeout, shuffle, results, restart, showHints, showBlank, showTime, self)
        irc.noReply()
    start = wrap(start, ['channel', getopts({'num':'int', 'hints':'int', 'timeout':'int', 'no-hints':'', 'shuffle':'', 'random':'', 'restart':''}), additional('text')])


    @internationalizeDocstring
    def stop(self, irc, msg, args, channel):
        """[<channel>]
        Stops a running game of Jeopardy!. <channel> is only necessary if the
        message isn't sent in the channel itself."""
        if not channel:
            channel = msg.channel
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        if self.games.get(channel):
            if self.games[channel].active:
                if self.games[channel].correct:
                    reply = self.games[channel].stop_template.render()
                    self.games[channel].reply(reply)
                else:
                    reply = self.games[channel].stop_template.render(answer = self.games[channel].a[0])
                    self.games[channel].reply(reply)
            try:
                self.games[channel].active = False
                self.games[channel].stop()
            except:
                return
        else:
            return
    stop = wrap(stop, ['channel'])


    def categories(self, irc, msg, args):
        """
        Returns list of popular jeopardy! categories and their category ID #
        """
        data = open("{0}/categories.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        if self.registryValue('useBold', msg.channel):
            irc.reply(ircutils.bold("Add category name to the start command to select a category by name."), prefixNick = False)
            irc.reply(ircutils.bold(", ".join(reply)), prefixNick = False)
        else:
            irc.reply("Add category name to the start command to select a category by name.", prefixNick = False)
            irc.reply(", ".join(reply), prefixNick = False)
    categories = wrap(categories)


    def stats(self, irc, msg, args, channel, optlist, nick):
        """[channel] [--top <int>] [<nick>]
        Returns Jeopardy! player stats. Supply a nick to get stats for a specific player. Use --top to set number of players to list.
        Defaults to current channel and top 5 players if no options given.
        """
        optlist = dict(optlist)
        if not channel:
            channel = msg.channel
        if 'top' in optlist:
            top = optlist.get('top')
        else:
            top = 5
        try:
            if nick:
                try:
                    total = self.games[channel].scores[nick]
                    self.games[channel].reply("Total score for {0} in {1}: {2}".format(nick, channel, total))
                except KeyError:
                    self.games[channel].reply("No scores found for {0} in {1}".format(nick, channel))
            else:
                sorted_x = []
                sorted_x = sorted(self.games[channel].scores.items(), key=lambda kv: kv[1], reverse=True)
                if len(sorted_x) < top:
                    top = len(sorted_x)
                if top > 0:
                    totals = ""
                    for i in range(0, top):
                        item = sorted_x[i]
                        totals += "#{0} ({1}: {2}), ".format(i+1, item[0], item[1])
                    self.games[channel].reply("Top {0} Jeopardy! players for {1}:".format(top, channel))
                    self.games[channel].reply(totals.strip(', '))
                else:
                    return
        except KeyError:
            scores = requests.structures.CaseInsensitiveDict()
            scoreFile = "{0}/jeopardy/scores_{1}.txt".format(conf.supybot.directories.data, channel)
            if not os.path.exists(scoreFile):
                return
            if nick:
                f = open(scoreFile, 'r')
                line = f.readline()
                while line:
                    (name, score) = line.split(' ')
                    scores[name] = int(score.strip('\r\n'))
                    line = f.readline()
                f.close()
                try:
                    total = scores[nick]
                    self.games[channel].reply("Total score for {0} in {1}: {2}".format(nick, channel, total))
                except KeyError:
                    self.games[channel].reply("No scores found for {0} in {1}".format(nick, channel))
            else:
                f = open(scoreFile, 'r')
                line = f.readline()
                while line:
                    (name, score) = line.split(' ')
                    scores[name] = int(score.strip('\r\n'))
                    line = f.readline()
                f.close()
                sorted_x = []
                sorted_x = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
                if len(sorted_x) < top:
                    top = len(sorted_x)
                if top > 0:
                    totals = ""
                    for i in range(0, top):
                        item = sorted_x[i]
                        totals += "#{0} ({1}: {2}), ".format(i+1, item[0], item[1])
                    self.games[channel].reply("Top {0} Jeopardy! players for {1}:".format(top, channel))
                    self.games[channel].reply(totals.strip(', '))
                else:
                    return
    stats = wrap(stats, ['channel', getopts({'top':'int'}), additional('text')])


    def question(self, irc, msg, args):
        """
        Repeat the current question.
        """
        channel = msg.channel
        if channel in self.games:
            if self.games[channel].active:
                self.games[channel].reply(self.games[channel].question)
            else:
                return
        else:
            return
    question = wrap(question)


    def hint(self, irc, msg, args):
        """
        Show hint. If timeout = 0 force a new hint. If game set for no hints, show the blanked out answer.
        Otherwise repeat the latest hint.
        """
        channel = msg.channel
        if channel in self.games:
            if not self.games[channel].active:
                return
            else:
                self.games[channel].hint()

    hint = wrap(hint)


    def report(self, irc, msg, args):
        """
        Report the current question as invalid and skip to the next one. Only use this command if a question is unanswerable (e.g. audio/video clues)
        """
        channel = msg.channel
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        if channel in self.games:
            if self.games[channel].active:
                r = requests.post('{0}/api/invalid'.format(self.jserviceUrl), data = {'id':self.games[channel].id})
                if r.status_code == 200:
                    self.games[channel].reply('Question successfully reported. (Answer: {0})'.format(self.games[channel].a[0]))
                else:
                    self.games[channel].reply('Error. Question not reported. (Answer: {0})'.format(self.games[channel].a[0]))
                self.games[channel].end()
    report = wrap(report)


    def skip(self, irc, msg, args):
        """
        Skip the current question.
        """
        channel = msg.channel
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        if channel in self.games:
            if self.games[channel].active:
                self.games[channel].end()
    skip = wrap(skip)


Class = Jeopardy


