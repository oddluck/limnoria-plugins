###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
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
from unidecode import unidecode
from bs4 import BeautifulSoup
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('Jeopardy')

class Jeopardy(callbacks.Plugin):
    """Add the help for "@plugin help Jeopardy" here
    This should describe *how* to use this plugin."""
    threaded = True


    def __init__(self, irc):
        self.__parent = super(Jeopardy, self)
        self.__parent.__init__(irc)
        self.games = {}
        self.scores = {}
        questionfile = self.registryValue('questionFile')
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
        channel = ircutils.toLower(msg.args[0])
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if channel in self.games:
            self.games[channel].answer(msg)


    class Game:
        def __init__(self, irc, channel, num, categories, plugin):
            self.rng = random.Random()
            self.rng.seed()
            self.registryValue = plugin.registryValue
            self.irc = irc
            self.channel = channel
            self.num = num
            self.categories = categories
            self.numAsked = 0
            self.hints = 0
            self.games = plugin.games
            self.scores = plugin.scores
            self.scorefile = plugin.scorefile
            self.questionfile = self.registryValue('questionFile')
            self.points = self.registryValue('defaultPointValue')
            self.total = num
            self.active = True
            self.questions = []
            self.roundscores = {}
            self.unanswered = 0
            self.show = {}
            self.revealed = {}
            if self.questionfile != 'jservice.io':
                f = open(self.questionfile, 'r')
                line = f.readline()
                while line:
                    self.questions.append(line.strip('\n\r'))
                    line = f.readline()
                f.close()
            else:
                self.historyfile = self.registryValue('historyFile')
                if not os.path.exists(self.historyfile):
                    f = open(self.historyfile, 'w')
                    f.write('Nothing:Nothing\n')
                    f.close()
                with open(self.historyfile) as f:
                    history = f.read().splitlines()
                cluecount = self.num
                failed = 0
                if self.categories == 'random':
                    n = 0
                    while n <= self.num:
                        if n > self.num:
                            break
                        try:
                            data = requests.get("http://jservice.io/api/random").json()
                            for item in data:
                                if n > self.num:
                                    break
                                id = item['id']
                                question = re.sub('<[^<]+?>', '', unidecode(item['question'])).replace('\\', '').strip()
                                airdate = item['airdate'].split('T')
                                answer = re.sub('<[^<]+?>', '', unidecode(item['answer'])).replace('\\', '').strip()
                                category = unidecode(item['category']['title']).strip().title()
                                invalid = item['invalid_count']
                                points = self.points
                                if item['value']:
                                    points = int(item['value'])
                                else:
                                    points = self.points
                                if len(question) > 1 and airdate and answer and category and points and not invalid and "{0}:{1}".format(self.channel, id) not in history:
                                    self.questions.append("{0}:{1}*({2}) [${3}] \x02{4}: {5}\x0F*{6}*{7}".format(self.channel, id, airdate[0], str(points), category, question, answer, points))
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
                                data = requests.get("http://jservice.io/api/clues?&category={0}".format(category)).json()
                                cluecount = data[0]['category']['clues_count']
                                if cluecount > 100:
                                    data.extend(requests.get("http://jservice.io/api/clues?&category={0}&offset=100".format(category)).json())
                                if cluecount > 200:
                                    data.extend(requests.get("http://jservice.io/api/clues?&category={0}&offset=200".format(category)).json())
                                if cluecount > 300:
                                    data.extend(requests.get("http://jservice.io/api/clues?&category={0}&offset=300".format(category)).json())
                                if cluecount > 400:
                                    data.extend(requests.get("http://jservice.io/api/clues?&category={0}&offset=400".format(category)).json())
                                if cluecount > 500:
                                    data.extend(requests.get("http://jservice.io/api/clues?&category={0}&offset=500".format(category)).json())
                                if cluecount > 9:
                                    random.shuffle(data)
                                for item in data:
                                    if n > self.num or k > len(self.categories):
                                        break
                                    id = item['id']
                                    question = re.sub('<[^<]+?>', '', unidecode(item['question'])).replace('\\', '').strip()
                                    airdate = item['airdate'].split('T')
                                    answer = re.sub('<[^<]+?>', '', unidecode(item['answer'])).replace('\\', '').strip()
                                    category = unidecode(item['category']['title']).strip().title()
                                    invalid = item['invalid_count']
                                    points = self.points
                                    if item['value']:
                                        points = int(item['value'])
                                    else:
                                        points = self.points
                                    if len(question) > 1 and airdate and answer and category and points and not invalid and "{0}:{1}".format(self.channel, id) not in history and id not in asked:
                                        self.questions.append("{0}:{1}*({2}) [${3}] \x02{4}: {5}\x0F*{6}*{7}".format(self.channel, id, airdate[0], str(points), category, question, answer, points))
                                        asked.append(id)
                                        n += 1
                                k += 1
                            except Exception:
                                pass
                del data
            if self.registryValue('randomize', channel):
                random.shuffle(self.questions)
            try:
                schedule.removeEvent('next_%s' % self.channel)
            except KeyError:
                pass
            self.newquestion()


        def newquestion(self):
            inactiveShutoff = self.registryValue('inactiveShutoff',
                                                 self.channel)
            if self.num == 0:
                self.active = False
            elif self.unanswered > inactiveShutoff and inactiveShutoff >= 0:
                self.reply(_('Seems like no one\'s playing any more.'))
                self.active = False
            elif len(self.questions) == 0:
                self.reply(_('Oops! I ran out of questions!'))
                self.active = False
            if not self.active:
                self.stop()
                return
            self.id = None
            self.hints = 0
            self.num -= 1
            self.numAsked += 1
            sep = self.registryValue('questionFileSeparator')
            q = self.questions.pop(len(self.questions)-1).split(sep)
            if q[0].startswith('#'):
                self.id = q[0]
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
            color = self.registryValue('color', self.channel)
            def next_question():
                self.reply(_('\x03%s#%d of %d: %s') % (color, self.numAsked,
                                                self.total, self.q))
                ans = self.a[0]
                if "(" in self.a[0]:
                    a1, a2, a3 = re.match("(.*)\((.*)\)(.*)", self.a[0]).groups()
                    self.a.append(a1 + a3)
                    self.a.append(a2)
                blankChar = self.registryValue('blankChar', self.channel)
                blank = re.sub('\w', blankChar, ans)
                self.reply("HINT: {0}".format(blank))
                if self.id:
                    f = open(self.historyfile, 'a')
                    f.write("{0}\n".format(self.id))
                    f.close()
                def event():
                    self.timedEvent()
                timeout = self.registryValue('timeout', self.channel)
                numHints = self.registryValue('numHints', self.channel)
                eventTime = time.time() + timeout / (numHints + 1)
                if self.active:
                    schedule.addEvent(event, eventTime, 'next_%s' % self.channel)
            if self.numAsked > 1:
                delay = self.registryValue('delay', self.channel)
                delayTime = time.time() + delay
            else:
                delayTime = time.time()
            if self.active:
                schedule.addEvent(next_question, delayTime, 'new_%s' % self.channel)

        def stop(self):
            self.reply(_('Jeopardy! stopping.'))
            self.active = False
            try:
                schedule.removeEvent('next_%s' % self.channel)
                schedule.removeEvent('new_%s' % self.channel)
            except KeyError:
                pass
            scores = iter(self.roundscores.items())
            sorted = []
            for i in range(0, len(self.roundscores)):
                item = next(scores)
                sorted.append(item)
            def cmp(a, b):
                return b[1] - a[1]
            sorted.sort(key=lambda item: item[1], reverse=True)
            max = 3
            if len(sorted) < max:
                max = len(sorted)
                #self.reply('max: %d.  len: %d' % (max, len(sorted)))
            s = _('Top finishers:')
            if max > 0:
                recipients = []
                maxp = sorted[0][1]
                for i in range(0, max):
                    item = sorted[i]
                    s = _('%s (%s: %s)') % (s, str(item[0].split(':')[1]), item[1])
                self.reply(s)
            try:
                del self.games[dynamic.channel]
            except KeyError:
                return


        def timedEvent(self):
            if self.hints >= self.registryValue('numHints', self.channel):
                self.reply(_('No one got the answer! It was: %s') % self.a[0])
                self.unanswered += 1
                self.newquestion()
            else:
                self.hint()


        def hint(self):
            self.hints += 1
            ans = self.a[0]
            self.show.setdefault(self.id, None)
            self.revealed.setdefault(self.id, None)
            hintPercentage = self.registryValue('hintPercentage', self.channel)
            divider = int(len(re.sub('[^a-zA-Z0-9]+', '', ans)) * hintPercentage)
            blankChar = self.registryValue('blankChar', self.channel)
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
            self.reply(_('HINT: %s') % (''.join(self.show[self.id])))
            self.p = self.p // 2
            def event():
                self.timedEvent()
            timeout = self.registryValue('timeout', self.channel)
            numHints = self.registryValue('numHints', self.channel)
            eventTime = time.time() + timeout / (numHints + 1)
            if self.active:
                schedule.addEvent(event, eventTime, 'next_%s' % self.channel)


        def answer(self, msg):
            channel = msg.args[0]
            correct = False
            for ans in self.a:
                ans = ans.strip().lower()
                guess = msg.args[1].strip().lower()
                if guess == ans:
                    correct = True
                else:
                    answer = re.sub('^a |^an |^the ', '', ans)
                    answer = re.sub('[^a-zA-Z0-9]+', '', answer)
                    guess = re.sub('^a |^an |^the ', '', guess)
                    guess = re.sub('[^a-zA-Z0-9]+', '', guess)
                if guess == answer:
                    correct = True
                else:
                    dist = self.DL(guess, answer)
                    flexibility = self.registryValue('flexibility', self.channel)
                    if dist <= len(answer) / flexibility:
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
                self.reply(_("{0} got it! The full answer was: {1}. Points: {2} | Round Score: {3} | Total: {4}".format(msg.nick, self.a[0], self.p, self.roundscores[name], self.scores[name])))
                schedule.removeEvent('next_%s' % self.channel)
                self.writeScores()
                self.newquestion()


        def reply(self, s):
            self.irc.queueMsg(ircmsgs.privmsg(self.channel, s))


        def writeScores(self):
            f = open(self.scorefile, 'w')
            scores = iter(self.scores.items())
            for i in range(0, len(self.scores)):
                score = next(scores)
                f.write('%s %s\n' % (score[0], score[1]))
            f.close()


        def DL(self, seq1, seq2):
            oneago = None
            thisrow = list(range(1, len(seq2) + 1)) + [0]
            for x in range(len(seq1)):
                # Python lists wrap around for negative indices, so put the
                # leftmost column at the *end* of the list. This matches with
                # the zero-indexed strings and saves extra calculation.
                twoago, oneago, thisrow = oneago, thisrow, [0]*len(seq2)+[x+1]
                for y in range(len(seq2)):
                    delcost = oneago[y] + 1
                    addcost = thisrow[y - 1] + 1
                    subcost = oneago[y - 1] + (seq1[x] != seq2[y])
                    thisrow[y] = min(delcost, addcost, subcost)
                    # This block deals with transpositions
                    if x > 0 and y > 0 and seq1[x] == seq2[y - 1] and \
                            seq1[x-1] == seq2[y] and seq1[x] != seq2[y]:
                        thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
            return thisrow[len(seq2) - 1]

    @internationalizeDocstring
    def start(self, irc, msg, args, channel, optlist, categories):
        """[<channel>] [--num <number of questions>] [<category>, <category#2>, <category#3>, etc.]
        Starts a game of Jeopardy! Play a round with random questions or select a category by name or number.
        Use 'random' to start a round with a random categories."""
        optlist = dict(optlist)
        if 'num' in optlist:
            num = optlist.get('num')
        else:
            num = self.registryValue('defaultRoundLength', channel)
        if categories and categories.strip() != 'random':
            results = []
            categories = categories.strip().split(",")
            for category in categories:
                category = category.strip()
                if category.isdigit():
                    results.append(category)
                else:
                    url = "http://jservice.io/search?query={0}".format(category)
                    data = requests.get(url)
                    soup = BeautifulSoup(data.text)
                    searches = soup.find_all('a')
                    for i in range(len(searches)):
                        search = searches[i].get('href').split('/')[-1]
                        if search.isdigit():
                            results.append(search)
            if results:
                categories = results
            else:
                irc.reply("Error. Could not find any results for {0}".format(categories))
        elif categories and categories.strip() == 'random':
            seed = str(random.randint(0,184) * 100)
            data = requests.get("http://jservice.io/api/categories?count=100&offset={0}".format(int(seed))).json()
            random.shuffle(data)
            results = []
            for item in data:
                results.append(item['id'])
            if results:
                categories = results
            else:
                irc.reply("Error")
        else:
            categories = 'random'
        channel = ircutils.toLower(channel)
        if channel in self.games:
            if not self.games[channel].active:
                del self.games[channel]
                try:
                    schedule.removeEvent('next_%s' % channel)
                    schedule.removeEvent('new_%s' % channel)
                except KeyError:
                    pass
                irc.reply("This... is... Jeopardy!", prefixNick=False)
                self.games[channel] = self.Game(irc, channel, num, categories, self)
            else:
                self.games[channel].num += num
                self.games[channel].total += num
                irc.reply(_('%d questions added to active game!') % num)
        else:
            irc.reply("This... is... Jeopardy!", prefixNick=False)
            self.games[channel] = self.Game(irc, channel, num, categories, self)
        irc.noReply()
    start = wrap(start, ['channel', getopts({'num':'int'}), additional('text')])

    @internationalizeDocstring
    def stop(self, irc, msg, args, channel):
        """[<channel>]
        Stops a running game of Jeopardy!. <channel> is only necessary if the
        message isn't sent in the channel itself."""
        channel = ircutils.toLower(channel)
        try:
            schedule.removeEvent('new_%s' % channel)
        except KeyError:
            pass
        try:
            schedule.removeEvent('next_%s' % channel)
        except KeyError:
            irc.error(_('No Jeopardy! game started.'))
        if channel in self.games:
            if self.games[channel].active:
                self.games[channel].stop()
            else:
                del self.games[channel]
                irc.reply(_('Jeopardy! stopped.'))
        else:
            irc.noReply()
    stop = wrap(stop, ['channel'])


    def categories(self, irc, msg, args):
        """
        Returns list of popular jeopardy! categories and their category ID #
        """
        data = open("{0}/categories.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        irc.reply("Vist http://jservice.io/search to search for more categories. Add --cat <id_number> to the start command to select category.")
        irc.reply(str(reply).replace("[", "").replace("]", "").replace("'", ""))
    categories = wrap(categories)


Class = Jeopardy


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
