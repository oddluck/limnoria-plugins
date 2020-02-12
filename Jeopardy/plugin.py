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


import re
import os
import time
import math
import random
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks
import supybot.conf as conf
import supybot.log as log
import string
import requests
from ftfy import fix_text
from bs4 import BeautifulSoup
from jinja2 import Template
import textdistance
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
        def __init__(self, irc, channel, num, hints, shuffle, categories, plugin):
            self.registryValue = plugin.registryValue
            self.irc = irc
            self.channel = channel
            self.num = num
            self.numHints = hints
            self.categories = categories
            self.numAsked = 0
            self.hints = 0
            self.games = plugin.games
            self.scores = requests.structures.CaseInsensitiveDict()
            self.jserviceUrl = plugin.jserviceUrl
            self.points = self.registryValue('defaultPointValue')
            self.blankChar = self.registryValue('blankChar', self.channel)
            self.total = num
            self.questions = []
            self.roundscores = requests.structures.CaseInsensitiveDict()
            self.unanswered = 0
            self.show = {}
            self.revealed = {}
            self.shuffled = shuffle
            self.correct = False
            self.answered = 0
            self.active = True
            self.history = plugin.history
            self.question = ''
            self.currentHint = ''
            self.flexibility = self.registryValue('flexibility', channel)
            self.question_template = Template(self.registryValue("template.question", channel))
            self.hint_template = Template(self.registryValue("template.hint", channel))
            self.correct_template = Template(self.registryValue("template.correct", channel))
            self.skip_template = Template(self.registryValue("template.skip", channel))
            self.stop_template = Template(self.registryValue("template.stop", channel))
            self.directory = conf.supybot.directories.data.dirize("jeopardy/")
            self.historyFile = "{0}/history_{1}.txt".format(self.directory, channel)
            self.scoreFile = "{0}/scores_{1}.txt".format(self.directory, channel)
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
                                    q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).replace(r"\'", "'").replace(r'\"', '"')
                                    q = re.sub('([,;:.!?])(\w|\"|\'|\()(?!\.)', '\g<1> \g<2>', q)
                                    q = re.sub('(\$\d+[,.]) (\d+)', '\g<1>\g<2>', q)
                                    q = " ".join(q.split())
                                    self.questions.append(q)
                                    asked.append(id)
                                    n += 1
                            else:
                                if clue and airdate and answer and category and not invalid and id not in asked:
                                    q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                    q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).replace(r"\'", "'").replace(r'\"', '"')
                                    q = re.sub('([,;:.!?])(\w|\"|\'|\()(?!\.)', '\g<1> \g<2>', q)
                                    q = re.sub('(\$\d+[,.]) (\d+)', '\g<1>\g<2>', q)
                                    q = " ".join(q.split())
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
                                category = item['category']['title'].strip()
                                invalid = item['invalid_count']
                                points = self.points
                                if item['value']:
                                    points = int(item['value'])
                                else:
                                    points = self.points
                                if self.registryValue('keepHistory', channel):
                                    if clue and airdate and answer and category and not invalid and id not in asked and id not in self.history[channel]:
                                        q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                        q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).replace(r"\'", "'").replace(r'\"', '"')
                                        q = re.sub('([,;:.!?])(\w|\"|\'|\()(?!\.)', '\g<1> \g<2>', q)
                                        q = re.sub('(\$\d+[,.]) (\d+)', '\g<1>\g<2>', q)
                                        q = " ".join(q.split())
                                        self.questions.append(q)
                                        asked.append(id)
                                        n += 1
                                        j += 1
                                else:
                                    if clue and airdate and answer and category and not invalid and id not in asked:
                                        q = "{0}|{1}|{2}|{3}|{4}|{5}".format(id, airdate, points, category, clue, answer)
                                        q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).replace(r"\'", "'").replace(r'\"', '"')
                                        q = re.sub('([,;:.!?])(\w|\"|\'|\()(?!\.)', '\g<1> \g<2>', q)
                                        q = re.sub('(\$\d+[,.]) (\d+)', '\g<1>\g<2>', q)
                                        q = " ".join(q.split())
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


        def newquestion(self):
            if not self.active:
                return
            inactiveShutoff = self.registryValue('inactiveShutoff', self.channel)
            if len(self.questions) == 0:
                self.reply('Oops! I ran out of questions!')
                self.stop()
                return
            elif self.num == 0 or self.answered == self.total or self.numAsked == self.total:
                self.stop()
                return
            elif self.unanswered > inactiveShutoff and inactiveShutoff > 0:
                self.reply('Seems like no one\'s playing any more. Jeopardy! stopped.')
                self.stop()
                return
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
            def next_question():
                if not self.active:
                    return
                self.question = self.question_template.render(question)
                self.reply(self.question)
                if self.registryValue('keepHistory', self.channel):
                    self.history[self.channel].append(int(self.id))
                ans = re.sub('\(\d of\)', '', self.a)
                self.a = [ans]
                self.correct = False
                if "(" in self.a[0]:
                    a1, a2, a3 = re.match("(.*)\((.*)\)(.*)", self.a[0]).groups()
                    self.a.append(a1 + a3)
                    self.a.append(a2)
                if self.numHints > 0:
                    blank = re.sub('\w', self.blankChar, ans)
                    self.currentHint = self.hint_template.render(hint = blank)
                    self.reply(self.currentHint)
                def event():
                    self.timedEvent()
                timeout = self.registryValue('timeout', self.channel)
                eventTime = time.time() + timeout / (self.numHints + 1)
                schedule.addEvent(event, eventTime, 'next_%s' % self.channel)
            if self.numAsked > 1:
                delay = self.registryValue('delay', self.channel)
                delayTime = time.time() + delay
            else:
                delayTime = time.time()
            if self.active:
                schedule.addEvent(next_question, delayTime, 'new_%s' % self.channel)


        def stop(self):
            self.write()
            try:
                schedule.removeEvent('next_%s' % self.channel)
                schedule.removeEvent('new_%s' % self.channel)
            except KeyError:
                pass
            if self.registryValue('autoRestart', self.channel) and self.active:
                num = self.registryValue('defaultRoundLength', self.channel)
                hints = self.registryValue('numHints', self.channel)
                self.__init__(self.irc, self.channel, num, hints, False, 'random', self)
            elif not self.registryValue('autoRestart', self.channel):
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
                self.active = False
                try:
                    del self.games[self.channel].questions, self.games[self.channel].roundscores
                except:
                    return
            else:
                try:
                    del self.games[self.channel].questions, self.games[self.channel].roundscores
                except:
                    return


        def timedEvent(self):
            if not self.active:
                return
            if self.hints >= self.numHints:
                self.reply('No one got the answer! It was: {0}'.format(self.a[0]))
                self.unanswered += 1
                self.corect = True
                self.answered += 1
                self.newquestion()
            else:
                self.hint()


        def hint(self):
            if not self.active:
                return
            self.hints += 1
            ans = self.a[0]
            self.show.setdefault(self.id, None)
            self.revealed.setdefault(self.id, None)
            hintPercentage = self.registryValue('hintPercentage', self.channel)
            reduction = self.registryValue('hintReduction', self.channel)
            divider = round(len(re.sub('[^a-zA-Z0-9]+', '', ans)) * hintPercentage)
            blank = re.sub('\w', self.blankChar, ans)
            if not self.show[self.id]:
                self.show[self.id] = list(blank)
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
            hint = "{0}".format(''.join(self.show[self.id]))
            self.currentHint = self.hint_template.render(hint = hint)
            self.reply(self.currentHint)
            self.p -= int(self.p * reduction)
            def event():
                self.timedEvent()
            timeout = self.registryValue('timeout', self.channel)
            eventTime = time.time() + timeout / (self.numHints + 1)
            schedule.addEvent(event, eventTime, 'next_%s' % self.channel)


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
                    elif not self.correct and self.flexibility < 1:
                        dist = textdistance.jaro_winkler(guess, answer)
                        log.debug("Jeopardy: guess: {0}, answer: {1}, length: {2}, distance: {3}, flexibility: {4}".format(guess, answer, len(answer), dist, self.flexibility))
                        if dist >= self.flexibility:
                            self.correct = True
                        elif dist < flexibility and ',' in self.a[0] or '&' in self.a[0]:
                            dist = textdistance.jaccard(guess, answer)
                            if dist >= flexibility:
                                self.correct = True
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
                    try:
                        schedule.removeEvent('next_%s' % channel)
                        schedule.removeEvent('new_%s' % channel)
                    except KeyError:
                        pass
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
        """[<channel>] [--num <number of questions>] [--no-hints] [--random-category] [--shuffle] [<category1>, <category2>, <category3>, etc.]
        Play a round of Jeopardy! with random questions or select a category by name/number.
        Use --no-hints to disable showing answer hints for the round.
        Use --random-category to start a round with a randomly selected category.
        Use --num to set the number of questions.
        Use --shuffle to randomize questions from manually selected categories."""
        if not channel:
            channel = msg.channel
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        if not self.registryValue('enabled', channel):
            return
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
            hints = 0
        else:
            hints = self.registryValue('numHints', channel)
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
        else:
            results = 'random'
        if results and 'shuffle' in optlist:
            random.shuffle(results)
        if channel in self.games:
            if not self.games[channel].active:
                try:
                    schedule.removeEvent('next_%s' % channel)
                    schedule.removeEvent('new_%s' % channel)
                except KeyError:
                    pass
                self.games[channel].reply("This... is... Jeopardy!")
                self.games[channel] = self.Game(irc, channel, num, hints, shuffle, results, self)
            else:
                self.games[channel].num += num
                self.games[channel].total += num
                self.games[channel].reply(_('%d questions added to active game!') % num)
        else:
            if not self.registryValue('autoRestart', channel):
                if self.registryValue('useBold', channel):
                    irc.reply(ircutils.bold("This... is... Jeopardy!"), prefixNick = False)
                else:
                    irc.reply("This... is... Jeopardy!", prefixNick = False)
            self.games[channel] = self.Game(irc, channel, num, hints, shuffle, results, self)
        irc.noReply()
    start = wrap(start, ['channel', getopts({'num':'int',  'no-hints':'', 'shuffle':'', 'random-category':''}), additional('text')])


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
        Repeat the latest hint. If game set for no hints, show the blanked out answer.
        """
        channel = msg.channel
        if channel in self.games:
            if self.games[channel].active and self.games[channel].numHints > 0:
                self.games[channel].reply(self.games[channel].currentHint)
            elif self.games[channel].active and self.games[channel].numHints == 0:
                blank = re.sub('\w', self.games[channel].blankChar, self.games[channel].a[0])
                hint = self.hint_template.render(hint = blank)
                self.games[channel].reply(hint)
                if self.games[channel].shown == 0:
                    reduction = self.registryValue('hintReduction', channel)
                    self.games[channel].p -= int(self.games[channel].p * reduction)
                    self.games[channel].shown += 1
            else:
                return
        else:
            return
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
                self.games[channel].unanswered = 0
                self.games[channel].correct = True
                self.games[channel].answered += 1
                self.games[channel].newquestion()
                try:
                    schedule.removeEvent('next_%s' % channel)
                except KeyError:
                    pass
            else:
                return
        else:
            return
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
                reply = self.games[channel].skip_template.render(answer = self.games[channel].a[0])
                self.games[channel].reply(reply)
                self.games[channel].unanswered = 0
                self.games[channel].correct = True
                self.games[channel].answered += 1
                self.games[channel].newquestion()
                try:
                    schedule.removeEvent('next_%s' % channel)
                except KeyError:
                    pass
            else:
                return
        else:
            return
    skip = wrap(skip)


Class = Jeopardy
