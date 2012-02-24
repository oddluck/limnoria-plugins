###
# Copyright (c) 2012, Mike Mueller <mike.mueller@panopticdev.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Do whatever you want
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.schedule as schedule
import supybot.log as log
import supybot.world as world

import random
import re

WHITE = '\x0300'
GREEN = '\x0303'
RED = '\x0305'
YELLOW = '\x0307'
LYELLOW = '\x0308'
LGREEN = '\x0309'
LCYAN = '\x0311'
LBLUE = '\x0312'
LGRAY = '\x0315'

def error(message):
    log.error('Wordgames: ' + message)

class Wordgames(callbacks.Plugin):
    "Please see the README file to configure and use this plugin."

    def __init__(self, irc):
        self.__parent = super(Wordgames, self)
        self.__parent.__init__(irc)
        self.games = {}

    def die(self):
        self.__parent.die()

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if channel in self.games:
            self.games[channel].handle_message(msg)

    def wordshrink(self, irc, msgs, args, channel, length):
        """[length] (default: 4)

        Start a word-shrink game. Make new words by dropping one letter from
        the previous word.
        """
        try:
            if channel in self.games and self.games[channel].is_running():
                irc.reply('A word game is already running here.')
                self.games[channel].show()
            elif length < 4 or length > 7:
                irc.reply('Please use a length between 4 and 7.')
            else:
                self.games[channel] = WordShrink(
                    self._get_words(), irc, channel, length)
                self.games[channel].start()
        except Exception, e:
            irc.reply(str(e))
    wordshrink = wrap(wordshrink, ['channel', optional('int', 4)])

    def wordtwist(self, irc, msgs, args, channel, length):
        """[length] (default: 4)

        Start a word-twist game. Make new words by changing one letter in
        the previous word.
        """
        try:
            if channel in self.games and self.games[channel].is_running():
                irc.reply('A word game is already running here.')
                self.games[channel].show()
            elif length < 4 or length > 7:
                irc.reply('Please use a length between 4 and 7.')
            else:
                self.games[channel] = WordTwist(
                    self._get_words(), irc, channel, length)
                self.games[channel].start()
        except Exception, e:
            irc.reply(str(e))
    wordtwist = wrap(wordtwist, ['channel', optional('int', 4)])

    def wordquit(self, irc, msgs, args, channel):
        """(takes no arguments)

        Stop any currently running word game.
        """
        if channel in self.games and self.games[channel].is_running():
            self.games[channel].stop()
            del self.games[channel]
        else:
            irc.reply('No word game currently running.')
    wordquit = wrap(wordquit, ['channel'])

    def _get_words(self):
        return map(str.strip, file(self.registryValue('wordFile')).readlines())

class BaseGame(object):
    "Base class for the games in this plugin."

    def __init__(self, words, irc, channel):
        self.words = words
        self.irc = irc
        self.channel = channel
        self.running = False

    def gameover(self):
        "The game is finished."
        self.running = False

    def start(self):
        "Start the current game."
        self.running = True

    def stop(self):
        "Shut down the current game."
        self.running = False

    def show(self):
        "Show the current state of the game."
        pass

    def is_running(self):
        return self.running

    def announce(self, msg):
        "Announce a message with the game title prefix."
        text = '%s%s%s:%s %s' % (
            LBLUE, self.__class__.__name__, WHITE, LGRAY, msg)
        self.send(text)

    def send(self, msg):
        "Relay a message to the channel."
        self.irc.queueMsg(ircmsgs.privmsg(self.channel, msg))

    def handle_message(self, msg):
        "Handle incoming messages on the channel."
        pass

    def _join_words(self, words):
        sep = "%s > %s" % (LGREEN, YELLOW)
        text = words[0] + sep
        text += sep.join(words[1:-1])
        text += sep + LGRAY + words[-1]
        return text

class WordShrink(BaseGame):
    def __init__(self, words, irc, channel, length):
        super(WordShrink, self).__init__(words, irc, channel)
        self.solution_length = length
        self.solution = []
        self.solutions = []

    def start(self):
        super(WordShrink, self).start()
        singular_words = filter(lambda s: s[-1] != 's', self.words)
        while len(self.solution) < self.solution_length:
            self.solution = []
            word = ''
            for i in range(0, self.solution_length):
                words = singular_words
                if self.solution:
                    words = filter(
                        lambda s: self._is_subset(s, self.solution[-1]), words)
                else:
                    words = filter(
                        lambda s: len(s) >= 2+self.solution_length, words)
                if not words: break
                self.solution.append(random.choice(words))
        self._find_solutions()
        self.show()

    def show(self):
        words = [self.solution[0]]
        for word in self.solution[1:-1]:
            words.append("-" * len(word))
        words.append(self.solution[-1])
        self.announce(self._join_words(words))
        num = len(self.solutions)
        self.send("(%s%d%s possible solution%s)" %
                  (WHITE, num, LGRAY, '' if num == 1 else 's'))

    def stop(self):
        super(WordShrink, self).stop()
        self.announce(self._join_words(self.solution))

    def handle_message(self, msg):
        words = map(str.strip, msg.args[1].split('>'))
        for word in words:
            if not re.match(r"^[a-z]+$", word):
                return
        if len(words) == len(self.solution) - 2:
            words = [self.solution[0]] + words + [self.solution[-1]]
        if self._valid_solution(msg.nick, words):
            if self.running:
                self.announce("%s%s%s got it!" % (WHITE, msg.nick, LGRAY))
                self.announce(self._join_words(words))
                self.gameover()
            else:
                self.send("%s: Your solution is also valid." % msg.nick)

    def _is_subset(self, word1, word2):
        "Determine if word1 is word2 minus one letter."
        if len(word1) != len(word2) - 1:
            return False
        for c in "abcdefghijklmnopqrstuvwxyz":
            if word1.count(c) > word2.count(c):
                return False
        return True

    def _find_solutions(self, seed=None):
        "Recursively find and save all solutions for the puzzle."
        if seed is None:
            seed = [self.solution[0]]
            self._find_solutions(seed)
        elif len(seed) == len(self.solution) - 1:
            if self._is_subset(self.solution[-1], seed[-1]):
                self.solutions.append(seed + [self.solution[-1]])
        else:
            length = len(seed[-1]) - 1
            words = filter(lambda s: len(s) == length, self.words)
            words = filter(lambda s: self._is_subset(s, seed[-1]), words)
            for word in words:
                self._find_solutions(seed + [word])

    def _valid_solution(self, nick, words):
        # Ignore things that don't look like attempts to answer
        if len(words) != len(self.solution):
            return False
        # Check for incorrect start/end words
        if len(words) == len(self.solution):
            if words[0] != self.solution[0]:
                self.send('%s: %s is not the starting word.' % (nick, words[0]))
                return False
            if words[-1] != self.solution[-1]:
                self.send('%s: %s is not the final word.' % (nick, words[-1]))
                return False
        # Add the start/end words (if not present) to simplify the test logic
        if len(words) == len(self.solution) - 2:
            words = [self.solution[0]] + words + [self.solution[-1]]
        for word in words:
            if word not in self.words:
                self.send("%s: %s is not a word I know." % (nick, word))
                return False
        for i in range(0, len(words)-1):
            if not self._is_subset(words[i+1], words[i]):
                self.send("%s: %s is not a subset of %s." %
                        (nick, words[i+1], words[i]))
                return False
        return True

class WordTwist(BaseGame):
    def __init__(self, words, irc, channel, length):
        super(WordTwist, self).__init__(words, irc, channel)
        self.solution_length = length
        self.solution = []
        self.solutions = []

    def start(self):
        super(WordTwist, self).start()
        while True:
            while len(self.solution) < self.solution_length:
                self.solution = []
                word = ''
                words = filter(lambda s: len(s) >= 4, self.words)
                for i in range(0, self.solution_length):
                    if self.solution:
                        words = filter(
                            lambda s: self._valid_pair(s, self.solution[-1]),
                            self.words)
                    if not words: break
                    self.solution.append(random.choice(words))
            self.solutions = []
            self._find_solutions()
            if min(map(len, self.solutions)) == self.solution_length:
                break
            else:
                self.solution = []
        self.show()

    def show(self):
        words = [self.solution[0]]
        for word in self.solution[1:-1]:
            words.append("-" * len(word))
        words.append(self.solution[-1])
        self.announce(self._join_words(words))
        num = len(self.solutions)
        self.send("(%s%d%s possible solution%s)" %
                  (WHITE, num, LGRAY, '' if num == 1 else 's'))

    def stop(self):
        super(WordTwist, self).stop()
        self.announce(self._join_words(self.solution))

    def handle_message(self, msg):
        words = map(str.strip, msg.args[1].split('>'))
        for word in words:
            if not re.match(r"^[a-z]+$", word):
                return
        if len(words) == len(self.solution) - 2:
            words = [self.solution[0]] + words + [self.solution[-1]]
        if self._valid_solution(msg.nick, words):
            if self.running:
                self.announce("%s%s%s got it!" % (WHITE, msg.nick, LGRAY))
                self.announce(self._join_words(words))
                self.gameover()
            else:
                self.send("%s: Your solution is also valid." % msg.nick)

    def _valid_pair(self, word1, word2):
        "Determine if word2 is a one-letter twist of word1."
        if len(word1) != len(word2):
            return False
        differences = 0
        for c1, c2 in zip(word1, word2):
            if c1 != c2:
                differences += 1
        return differences == 1

    def _find_solutions(self, seed=None):
        "Recursively find and save all solutions for the puzzle."
        if seed is None:
            seed = [self.solution[0]]
            self._find_solutions(seed)
        elif len(seed) == len(self.solution) - 1:
            if self._valid_pair(self.solution[-1], seed[-1]):
                self.solutions.append(seed + [self.solution[-1]])
        else:
            words = filter(lambda s: self._valid_pair(s, seed[-1]), self.words)
            for word in words:
                if word == self.solution[-1]:
                    self.solutions.append(seed + [word])
                else:
                    self._find_solutions(seed + [word])

    def _valid_solution(self, nick, words):
        # Ignore things that don't look like attempts to answer
        if len(words) != len(self.solution):
            return False
        # Check for incorrect start/end words
        if len(words) == len(self.solution):
            if words[0] != self.solution[0]:
                self.send('%s: %s is not the starting word.' % (nick, words[0]))
                return False
            if words[-1] != self.solution[-1]:
                self.send('%s: %s is not the final word.' % (nick, words[-1]))
                return False
        # Add the start/end words (if not present) to simplify the test logic
        if len(words) == len(self.solution) - 2:
            words = [self.solution[0]] + words + [self.solution[-1]]
        for word in words:
            if word not in self.words:
                self.send("%s: %s is not a word I know." % (nick, word))
                return False
        for i in range(0, len(words)-1):
            if not self._valid_pair(words[i+1], words[i]):
                self.send("%s: %s is not a twist of %s." %
                        (nick, words[1], words[0]))
                return False
        return True

Class = Wordgames

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
