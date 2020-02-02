###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2019, oddluck
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
import string
import random
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks
import requests
import re
from ftfy import fix_text
from bs4 import BeautifulSoup
import jellyfish
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
        self.scores = requests.structures.CaseInsensitiveDict()
        global stopped
        stopped = requests.structures.CaseInsensitiveDict()
        questionfile = self.registryValue('questionFile')
        self.noHints = False
        global jserviceUrl
        jserviceUrl = self.registryValue('jserviceUrl').strip('/')
        if not os.path.exists(questionfile) and questionfile != 'jservice.io':
            f = open(questionfile, 'w')
            f.write(('If you\'re seeing this question, it means that the '
                     'questions file that you specified wasn\'t found, and '
                     'a new one has been created.  Go get some questions!%s'
                     'No questions found') %
                    self.registryValue('questionFileSeparator'))
            f.close()
        self.scorefile = self.registryValue('scoreFile')
        if not os.path.exists(self.scorefile):
            f = open(self.scorefile, 'w')
            f.close()
        f = open(self.scorefile, 'r')
        line = f.readline()
        while line:
            (name, score) = line.split(' ')
            self.scores[name] = int(score.strip('\r\n'))
            line = f.readline()
        f.close()


    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if self.registryValue('enabled', channel) and channel in self.games:
            self.games[channel].answer(msg)


    class Game:
        def __init__(self, irc, channel, num, hints, shuffle, categories, plugin):
            self.rng = random.Random()
            self.rng.seed()
            self.registryValue = plugin.registryValue
            self.irc = irc
            self.num = num
            self.numHints = hints
            self.categories = categories
            self.numAsked = 0
            self.hints = 0
            self.games = plugin.games
            self.scores = plugin.scores
            self.scorefile = plugin.scorefile
            self.questionfile = self.registryValue('questionFile')
            self.points = self.registryValue('defaultPointValue')
            self.total = num
            self.questions = []
            self.roundscores = requests.structures.CaseInsensitiveDict()
            self.unanswered = 0
            self.show = {}
            self.revealed = {}
            self.shuffled = shuffle
            self.answered = False
            stopped[channel] = False
            if self.questionfile != 'jservice.io':
                f = open(self.questionfile, 'r')
                line = f.readline()
                while line:
                    self.questions.append(line.strip('\n\r'))
                    line = f.readline()
                f.close()
            else:
                try:
                    self.history.setdefault(channel, default=[])
                except:
                    self.history = {}
                    self.history.setdefault(channel, [])
                cluecount = self.num
                if self.categories == 'random':
                    n = 0
                    while n <= self.num:
                        if n > self.num:
                            break
                        try:
                            if jserviceUrl == 'http://jservice.io':
                                data = requests.get("{0}/api/random".format(jserviceUrl), timeout=5).json()
                            else:
                                data = requests.get("{0}/api/random?count={1}".format(jserviceUrl, self.num + 5), timeout=5).json()
                            for item in data:
                                if n > self.num:
                                    break
                                id = item['id']
                                clue = item['question'].strip()
                                airdate = item['airdate'].split('T')
                                answer = item['answer'].strip()
                                category = item['category']['title'].strip().upper()
                                invalid = item['invalid_count']
                                points = self.points
                                if item['value']:
                                    points = int(item['value'])
                                else:
                                    points = self.points
                                if len(clue) > 1 and airdate and answer and category and not invalid and id not in self.history[channel]:
                                    q = "#{0}*({1}) [${2}] \x02{3}: {4}\x0F*{5}*{6}".format(id, airdate[0], str(points), category, clue, answer, points)
                                    q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).encode('utf-8').decode('unicode_escape')
                                    q = " ".join(q.split())
                                    self.questions.append(q)
                                    n += 1
                        except Exception:
                            continue
                else:
                    n = 0
                    k = 0
                    asked = []
                    while n <= self.num:
                        if n > self.num or k > len(self.categories):
                            break
                        for i in range(len(self.categories)):
                            if n > self.num or k > len(self.categories):
                                break
                            try:
                                category = int(self.categories[i])
                                data = requests.get("{0}/api/clues?&category={1}".format(jserviceUrl, category)).json()
                                cluecount = data[0]['category']['clues_count']
                                if cluecount > 100:
                                    data.extend(requests.get("{0}/api/clues?&category={1}&offset=100".format(jserviceUrl, category), timeout=5).json())
                                if cluecount > 200:
                                    data.extend(requests.get("{0}/api/clues?&category={1}&offset=200".format(jserviceUrl, category), timeout=5).json())
                                if cluecount > 300:
                                    data.extend(requests.get("{0}/api/clues?&category={1}&offset=300".format(jserviceUrl, category), timeout=5).json())
                                if cluecount > 400:
                                    data.extend(requests.get("(0}/api/clues?&category={1}&offset=400".format(jserviceUrl, category), timeout=5).json())
                                if cluecount > 500:
                                    data.extend(requests.get("{0}/api/clues?&category={1}&offset=500".format(jserviceUrl, category), timeout=5).json())
                                j = 0
                                for item in data:
                                    if n > self.num or k > len(self.categories):
                                        break
                                    elif self.shuffled and k == len(self.categories):
                                        self.shuffled = False
                                        k = 0
                                        pass
                                    elif self.shuffled and j > self.num * 0.2:
                                        break
                                    id = item['id']
                                    clue = item['question'].strip()
                                    airdate = item['airdate'].split('T')
                                    answer = item['answer'].strip()
                                    category = item['category']['title'].strip().upper()
                                    invalid = item['invalid_count']
                                    points = self.points
                                    if item['value']:
                                        points = int(item['value'])
                                    else:
                                        points = self.points
                                    if len(clue) > 1 and airdate and answer and category and not invalid and id not in self.history[channel]:
                                        q = "#{0}*({1}) [${2}] \x02{3}: {4}\x0F*{5}*{6}".format(id, airdate[0], str(points), category, clue, answer, points)
                                        q = re.sub('<[^<]+?>', '', fix_text(q, normalization='NFKC')).encode('utf-8').decode('unicode_escape')
                                        q = " ".join(q.split())
                                        self.questions.append(q)
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
            self.newquestion(channel)


        def newquestion(self, channel):
            inactiveShutoff = self.registryValue('inactiveShutoff', channel)
            if self.num == 0:
                stopped[channel] = True
            elif self.unanswered > inactiveShutoff and inactiveShutoff > 0:
                self.reply(channel, 'Seems like no one\'s playing any more.')
                stopped[channel] = True
            elif len(self.questions) == 0:
                self.reply(channel, 'Oops! I ran out of questions!')
                stopped[channel] = True
            if stopped[channel]:
                self.stop(channel)
                return
            self.id = None
            self.hints = 0
            self.num -= 1
            self.numAsked += 1
            sep = self.registryValue('questionFileSeparator')
            q = self.questions.pop(len(self.questions)-1).split(sep)
            if q[0].startswith('#'):
                self.id = q[0].strip('#')
                self.q = q[1]
                self.a = [q[2]]
                if q[3]:
                    self.p = int(q[3])
                else:
                    self.p = self.points
            else:
                self.q = q[0]
                self.a = [q[1]]
                if q[2]:
                    self.p = int(q[2])
                else:
                    self.p = self.points
            color = self.registryValue('color', channel)
            def next_question():
                if not stopped[channel]:
                    global question
                    question = {}
                    global hint
                    hint = {}
                    if not self.registryValue('autoRestart', channel):
                        question[channel] = "\x03{0}#{1} of {2}: {3}".format(color, self.numAsked, self.total, self.q)
                    else:
                        question[channel] = "\x03{0}{1}".format(color, self.q)
                    self.reply(channel, question[channel])
                    ans = self.a[0]
                    self.answered = False
                    if "(" in self.a[0]:
                        a1, a2, a3 = re.match("(.*)\((.*)\)(.*)", self.a[0]).groups()
                        self.a.append(a1 + a3)
                        self.a.append(a2)
                    if self.numHints > 0:
                        blankChar = self.registryValue('blankChar', channel)
                        blank = re.sub('\w', blankChar, ans)
                        hint[channel] = "HINT: {0}".format(blank)
                        self.reply(channel, hint[channel])
                    if self.id:
                        self.history[channel].append(self.id)
                    def event():
                        self.timedEvent(channel)
                    timeout = self.registryValue('timeout', channel)
                    eventTime = time.time() + timeout / (self.numHints + 1)
                    if not stopped[channel]:
                        schedule.addEvent(event, eventTime, 'next_%s' % channel)
            if self.numAsked > 1:
                delay = self.registryValue('delay', channel)
                delayTime = time.time() + delay
            else:
                delayTime = time.time()
            if not stopped[channel]:
                schedule.addEvent(next_question, delayTime, 'new_%s' % channel)


        def stop(self, channel):
            try:
                schedule.removeEvent('next_%s' % channel)
                schedule.removeEvent('new_%s' % channel)
            except KeyError:
                pass
            scores = iter(self.roundscores.items())
            sorted = []
            for i in range(0, len(self.roundscores)):
                item = next(scores)
                sorted.append(item)
            sorted.sort(key=lambda item: item[1], reverse=True)
            max = 3
            if len(sorted) < max:
                max = len(sorted)
            if not self.registryValue('autoRestart', channel):
                s = _('Top finishers:')
                if max > 0:
                    for i in range(0, max):
                        item = sorted[i]
                        s = _('%s (%s: %s)') % (s, str(item[0].split(':')[1]), item[1])
                    self.reply(channel, s)
            if self.registryValue('autoRestart', channel) and not stopped[channel]:
                num = self.registryValue('defaultRoundLength', channel)
                hints = self.registryValue('numHints', channel)
                self.__init__(self.irc, channel, num, hints, False, 'random', self)
            else:
                stopped[channel] = True
                try:
                    del self.games[channel]
                except KeyError:
                    return


        def timedEvent(self, channel):
            if self.hints >= self.numHints:
                self.reply(channel, 'No one got the answer! It was: {0}'.format(self.a[0]))
                self.unanswered += 1
                self.answered = True
                self.newquestion(channel)
            else:
                self.hint(channel)


        def hint(self, channel):
            self.hints += 1
            ans = self.a[0]
            self.show.setdefault(self.id, None)
            self.revealed.setdefault(self.id, None)
            hintPercentage = self.registryValue('hintPercentage', channel)
            reduction = self.registryValue('hintReduction', channel)
            divider = round(len(re.sub('[^a-zA-Z0-9]+', '', ans)) * hintPercentage)
            blankChar = self.registryValue('blankChar', channel)
            blank = re.sub('\w', blankChar, ans)
            if not self.show[self.id]:
                self.show[self.id] = list(blank)
            if not self.revealed[self.id]:
                self.revealed[self.id] = list(range(len(self.show[self.id])))
            i = 0
            while i < divider and len(self.revealed[self.id]) > 1:
                try:
                    rand = self.revealed[self.id].pop(random.randint(0,len(self.revealed[self.id])) - 1)
                    if self.show[self.id][rand] == blankChar:
                        self.show[self.id][rand] = list(ans)[rand]
                        i += 1
                except:
                    break
            hint[channel] = "HINT: {0}".format(''.join(self.show[self.id]))
            self.reply(channel, hint[channel])
            self.p -= int(self.p * reduction)
            def event():
                self.timedEvent(channel)
            timeout = self.registryValue('timeout', channel)
            eventTime = time.time() + timeout / (self.numHints + 1)
            if not stopped[channel]:
                schedule.addEvent(event, eventTime, 'next_%s' % channel)


        def answer(self, msg):
            if not self.answered:
                channel = msg.args[0]
                correct = False
                for ans in self.a:
                    ans = " ".join(ans.strip()).lower()
                    guess = " ".join(msg.args[1]).strip().lower()
                    if guess == ans:
                        correct = True
                    elif not correct and len (ans) > 2:
                        answer = re.sub('[^a-zA-Z0-9 ]+', '', ans)
                        answer = re.sub('^a |^an |^the ', '', answer).replace(' ', '')
                        guess = re.sub('[^a-zA-Z0-9 ]+', '', guess)
                        guess = re.sub('^a |^an |^the ', '', guess).replace(' ', '')
                    else:
                        answer = ans
                    if not correct and guess == answer:
                        correct = True
                    elif not correct:
                        dist = jellyfish.jaro_winkler(guess, answer)
                        flexibility = self.registryValue('flexibility', channel)
                        #self.reply(channel, "guess: {0}, answer: {1}, length: {2}, distance: {3}, flexibility: {4}".format(guess, answer, len(answer), dist, flexibility))
                        if dist >= flexibility:
                            correct = True
                if correct:
                    name = "{0}:{1}".format(channel, msg.nick)
                    if not name in self.scores:
                        self.scores[name] = 0
                    self.scores[name] += self.p
                    if not name in self.roundscores:
                        self.roundscores[name] = 0
                    self.roundscores[name] += self.p
                    self.unanswered = 0
                    self.reply(channel, "{0} got it! The full answer was: {1}. Points: {2} | Round Score: {3} | Total: {4}".format(msg.nick, self.a[0], self.p, self.roundscores[name], self.scores[name]))
                    self.answered = True
                    try:
                        schedule.removeEvent('next_%s' % channel)
                        schedule.removeEvent('new_%s' % channel)
                    except KeyError:
                        pass
                    self.writeScores()
                    self.newquestion(channel)


        def reply(self, channel, s):
            self.irc.queueMsg(ircmsgs.privmsg(channel, s))


        def writeScores(self):
            f = open(self.scorefile, 'w')
            scores = iter(self.scores.items())
            for i in range(0, len(self.scores)):
                score = next(scores)
                f.write('%s %s\n' % (score[0], score[1]))
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
            channel = msg.args[0]
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
            self.noHints = True
        else:
            hints = self.registryValue('numHints', channel)
            self.noHints = False
        if 'random-category' in optlist:
            if jserviceUrl == 'http://jservice.io':
                seed = random.randint(0,184) * 100
            else:
                seed = random.randint(0,250) * 100
            data = requests.get("{0}/api/categories?count=100&offset={1}".format(jserviceUrl, int(seed)), timeout=5).json()
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
                    url = "{0}/search?query={1}".format(jserviceUrl, category)
                    data = requests.get(url, timeout=5)
                    soup = BeautifulSoup(data.text)
                    searches = soup.find_all('a')
                    for i in range(len(searches)):
                        search = searches[i].get('href').split('/')[-1]
                        if search.isdigit():
                            results.append(search)
            if not results:
                irc.reply("Error. Could not find any results for {0}".format(categories))
                return
        else:
            results = 'random'
        if results and 'shuffle' in optlist:
            random.shuffle(results)
        if channel in self.games:
            if not self.games[channel].active:
                del self.games[channel]
                try:
                    schedule.removeEvent('next_%s' % channel)
                    schedule.removeEvent('new_%s' % channel)
                except KeyError:
                    pass
                if not self.registryValue('autoRestart', channel):
                    irc.reply("This... is... Jeopardy!", prefixNick=False)
                self.games[channel] = self.Game(irc, channel, num, hints, shuffle, results, self)
            else:
                self.games[channel].num += num
                self.games[channel].total += num
                irc.reply(_('%d questions added to active game!') % num)
        else:
            if not self.registryValue('autoRestart', channel):
                irc.reply("This... is... Jeopardy!", prefixNick=False)
            self.games[channel] = self.Game(irc, channel, num, hints, shuffle, results, self)
        irc.noReply()
    start = wrap(start, ['channel', getopts({'num':'int',  'no-hints':'', 'shuffle':'', 'random-category':''}), additional('text')])


    @internationalizeDocstring
    def stop(self, irc, msg, args, channel):
        """[<channel>]
        Stops a running game of Jeopardy!. <channel> is only necessary if the
        message isn't sent in the channel itself."""
        if not channel:
            channel = msg.args[0]
        if self.registryValue('requireOps', channel) and msg.nick not in irc.state.channels[channel].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
            return
        stopped[channel] = True
        try:
            self.games[channel].stop(channel)
            irc.reply(_('Jeopardy! stopped.'))
        except:
            return
    stop = wrap(stop, ['channel'])


    def categories(self, irc, msg, args):
        """
        Returns list of popular jeopardy! categories and their category ID #
        """
        data = open("{0}/categories.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        irc.reply("Add category name to the start command to select a category by name.")
        irc.reply(str(reply).replace("[", "").replace("]", "").replace("'", ""))
    categories = wrap(categories)


    def stats(self, irc, msg, args, channel, optlist, nick):
        """[channel] [--top <int>] [<nick>]
        Returns Jeopardy! player stats. Supply a nick to get stats for a specific player. Use --top to set number of players to list.
        Defaults to current channel and top 5 players if no options given.
        """
        optlist = dict(optlist)
        if not channel:
            channel = msg.args[0]
        if 'top' in optlist:
            top = optlist.get('top')
        else:
            top = 5
        scores = requests.structures.CaseInsensitiveDict()
        if nick:
            f = open(self.scorefile, 'r')
            line = f.readline()
            while line:
                (name, score) = line.split(' ')
                if name.startswith(channel):
                    scores[name] = int(score.strip('\r\n'))
                line = f.readline()
            f.close()
            name = "{0}:{1}".format(channel, nick)
            try:
                total = scores[name]
                irc.reply("Total score for {0} in {1}: {2}".format(nick, channel, total), prefixNick=False)
            except KeyError:
                irc.reply("No scores found for {0} in {1}".format(nick, channel), prefixNick=False)
        else:
            f = open(self.scorefile, 'r')
            line = f.readline()
            while line:
                (name, score) = line.split(' ')
                name = name.split(':')
                if name[0] == channel:
                    name = name[1]
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
                irc.reply("Top {0} Jeopardy! players for {1}:".format(top, channel), prefixNick=False)
                irc.reply(totals.strip(', '), prefixNick=False)
            else:
                return
    stats = wrap(stats, ['channel', getopts({'top':'int'}), additional('text')])


    def question(self, irc, msg, args):
        """
        Repeat the current question.
        """
        channel = msg.args[0]
        if channel in self.games:
            if self.games[channel].active:
                irc.reply(question[channel])
            else:
                return
        else:
            return
    question = wrap(question)


    def hint(self, irc, msg, args):
        """
        Repeat the latest hint.
        """
        channel = msg.args[0]
        if channel in self.games:
            if self.games[channel].active and not self.noHints:
                irc.reply(hint[channel])
            else:
                return
        else:
            return
    hint = wrap(hint)

Class = Jeopardy


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
