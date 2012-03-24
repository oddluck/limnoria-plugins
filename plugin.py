###
# Copyright (c) 2012, Mike Mueller <mike@subfocal.net>
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

def info(message):
    log.info('Wordgames: ' + message)

def error(message):
    log.error('Wordgames: ' + message)

class WordgamesError(Exception): pass

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
        game = self.games.get(channel)
        if game:
            game.handle_message(msg)

    def wordshrink(self, irc, msgs, args, channel, difficulty):
        """[easy|medium|hard|evil] (default: easy)

        Start a word-shrink game. Make new words by dropping one letter from
        the previous word and rearranging the remaining letters.
        """
        if difficulty not in ['easy', 'medium', 'hard', 'evil']:
            irc.reply('Difficulty must be easy, medium, hard, or evil.')
        else:
            self._start_game(WordShrink, irc, channel, difficulty)
    wordshrink = wrap(wordshrink,
        ['channel', optional('somethingWithoutSpaces', 'easy')])

    def wordtwist(self, irc, msgs, args, channel, difficulty):
        """[easy|medium|hard|evil] (default: easy)

        Start a word-twist game. Make new words by changing one letter in
        the previous word.
        """
        if difficulty not in ['easy', 'medium', 'hard', 'evil']:
            irc.reply('Difficulty must be easy, medium, hard, or evil.')
        else:
            self._start_game(WordTwist, irc, channel, difficulty)
    wordtwist = wrap(wordtwist,
        ['channel', optional('somethingWithoutSpaces', 'easy')])

    def wordquit(self, irc, msgs, args, channel):
        """(takes no arguments)

        Stop any currently running word game.
        """
        game = self.games.get(channel)
        if game and game.is_running():
            game.stop()
        else:
            irc.reply('No word game currently running.')
    wordquit = wrap(wordquit, ['channel'])

    def _get_words(self):
        try:
            regexp = re.compile(self.registryValue('wordRegexp'))
        except Exception, e:
            raise WordgamesError("Bad value for wordRegexp: %s" % str(e))
        path = self.registryValue('wordFile')
        try:
            wordFile = file(path)
        except Exception, e:
            raise WordgamesError("Unable to open word file: %s" % path)
        return filter(regexp.match, map(str.strip, wordFile.readlines()))

    def _start_game(self, Game, irc, channel, *args, **kwargs):
        try:
            game = self.games.get(channel)
            if game and game.is_running():
                irc.reply('A word game is already running here.')
                game.show()
            else:
                words = self._get_words()
                self.games[channel] = Game(words, irc, channel, *args, **kwargs)
                self.games[channel].start()
        except WordgamesError, e:
            irc.reply('Wordgames error: %s' % str(e))
            irc.reply('Please check the configuration and try again. ' +
                      'See README for help.')

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

class WordChain(BaseGame):
    "Base class for word-chain games like WordShrink and WordTwist."

    class Settings:
        """
        Parameters affecting the behavior of this class:

           puzzle_lengths: Number of words allowed in the puzzle, including
                           start and end word. List of integers.
           word_lengths:   Word lengths allowed in the puzzle. List of integers
                           or None for the default (3 letters or more).
           num_solutions:  A limit to the number of possible solutions, or
                           None for unlimited.
        """
        def __init__(self, puzzle_lengths, word_lengths=None,
                     num_solutions=None):
            self.puzzle_lengths = puzzle_lengths
            self.word_lengths = word_lengths
            self.num_solutions = num_solutions

    def __init__(self, words, irc, channel, settings):
        super(WordChain, self).__init__(words, irc, channel)
        self.settings = settings
        self.solution_length = random.choice(settings.puzzle_lengths)
        self.solution = []
        self.solutions = []
        self.word_map = {}
        if settings.word_lengths:
            self.words = filter(lambda w: len(w) in settings.word_lengths,
                                self.words)
        else:
            self.words = filter(lambda w: len(w) >= 3, self.words)
        self.build_word_map()

    def start(self):
        super(WordChain, self).start()
        happy = False
        # Build a puzzle
        while not happy:
            self.solution = []
            while len(self.solution) < self.solution_length:
                self.solution = [random.choice(self.words)]
                for i in range(1, self.solution_length):
                    values = self.word_map[self.solution[-1]]
                    values = filter(lambda w: w not in self.solution, values)
                    if not values: break
                    self.solution.append(random.choice(values))
            self.solutions = []
            self._find_solutions()
            # Enforce maximum solutions limit (difficulty parameter)
            happy = True
            if self.settings.num_solutions and \
                    len(self.solutions) not in self.settings.num_solutions:
                happy = False
            # Ensure no solution is trivial
            for solution in self.solutions:
                if self.is_trivial_solution(solution):
                    happy = False
                    break
        self.show()
        # For debugging purposes
        solution_set = set(map(lambda s: self._join_words(s), self.solutions))
        if len(solution_set) != len(self.solutions):
            info('Oops, only %d of %d solutions are unique.' %
                    (len(solution_set), len(self.solutions)))

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
        super(WordChain, self).stop()
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

    # Override in game class
    def build_word_map(self):
        "Build a map of word -> [word1, word2] for all valid transitions."
        pass

    # Override in game class
    def is_trivial_solution(self, solution):
        return False

    def _get_successors(self, word):
        "Lookup a word in the map and return list of possible successor words."
        return self.word_map.get(word, [])

    def _find_solutions(self, seed=None):
        "Recursively find and save all solutions for the puzzle."
        if seed is None:
            seed = [self.solution[0]]
            self.solutions = []
            self._find_solutions(seed)
        elif len(seed) == len(self.solution) - 1:
            if self.solution[-1] in self._get_successors(seed[-1]):
                self.solutions.append(seed + [self.solution[-1]])
        else:
            words = self._get_successors(seed[-1])
            for word in words:
                if word in seed:
                    continue
                if word == self.solution[-1]:
                    self.solutions.append(seed + [word])
                else:
                    self._find_solutions(seed + [word])

    def _join_words(self, words):
        sep = "%s > %s" % (LGREEN, YELLOW)
        text = words[0] + sep
        text += sep.join(words[1:-1])
        text += sep + LGRAY + words[-1]
        return text

    def _valid_solution(self, nick, words):
        # Ignore things that don't look like attempts to answer
        if len(words) != len(self.solution):
            return False
        # Check for incorrect start/end words
        if words[0] != self.solution[0]:
            self.send('%s: %s is not the starting word.' % (nick, words[0]))
            return False
        if words[-1] != self.solution[-1]:
            self.send('%s: %s is not the final word.' % (nick, words[-1]))
            return False
        # Check dictionary
        for word in words:
            if word not in self.words:
                self.send("%s: %s is not a word I know." % (nick, word))
                return False
        # Enforce pairwise relationships
        for i in range(0, len(words)-1):
            if words[i+1] not in self._get_successors(words[i]):
                self.send("%s: %s does not follow from %s." %
                        (nick, words[i+1], words[i]))
                return False
        return True

class WordShrink(WordChain):
    def __init__(self, words, irc, channel, difficulty):
        assert difficulty in ['easy', 'medium', 'hard', 'evil'], "Bad mojo."
        settings = {
            'easy':   WordChain.Settings([4], range(3, 10), range(10, 100)),
            'medium': WordChain.Settings([5], range(4, 12), range(5, 12)),
            'hard':   WordChain.Settings([6], range(5, 14), range(2, 5)),
            'evil':   WordChain.Settings([7], range(6, 16), range(1, 3)),
        }
        super(WordShrink, self).__init__(
            words, irc, channel, settings[difficulty])

    def build_word_map(self):
        "Build a map of word -> [word1, word2] for all valid transitions."
        keymap = {}
        for word in self.words:
            s = "".join(sorted(word))
            if s in keymap:
                keymap[s].append(word)
            else:
                keymap[s] = [word]
        self.word_map = {}
        for word1 in self.words:
            s = "".join(sorted(word1))
            if s in self.word_map:
                self.word_map[word1] = self.word_map[s]
            else:
                self.word_map[s] = self.word_map[word1] = []
                keys = set()
                for i in range(0, len(s)):
                    keys.add(s[0:i] + s[i+1:])
                for key in keys:
                    for word2 in keymap.get(key, []):
                        self.word_map[s].append(word2)

    def is_trivial_solution(self, solution):
        "Consider pure substring solutions trivial."
        for i in range(0, len(solution)-1):
            for j in range(i+1, len(solution)):
                if solution[i].find(solution[j]) >= 0:
                    return True
        return False

class WordTwist(WordChain):
    def __init__(self, words, irc, channel, difficulty):
        assert difficulty in ['easy', 'medium', 'hard', 'evil'], "Bad mojo."
        settings = {
            'easy':   WordChain.Settings([4], [3, 4], range(10, 100)),
            'medium': WordChain.Settings([5], [4, 5], range(5, 12)),
            'hard':   WordChain.Settings([6], [4, 5, 6], range(2, 5)),
            'evil':   WordChain.Settings([7], [4, 5, 6], range(1, 3)),
        }
        super(WordTwist, self).__init__(
            words, irc, channel, settings[difficulty])

    def build_word_map(self):
        "Build the map of word -> [word1, word2, ...] for all valid pairs."
        keymap = {}
        wildcard = '*'
        for word in self.words:
            for pos in range(0, len(word)):
                key = word[0:pos] + wildcard + word[pos+1:]
                if key not in keymap:
                    keymap[key] = [word]
                else:
                    keymap[key].append(word)
        self.word_map = {}
        for word in self.words:
            self.word_map[word] = []
            for pos in range(0, len(word)):
                key = word[0:pos] + wildcard + word[pos+1:]
                self.word_map[word] += filter(
                    lambda w: w != word, keymap.get(key, []))

    def is_trivial_solution(self, solution):
        "If it's possible to get there in fewer hops, this is trivial."
        return len(solution) < self.solution_length

Class = Wordgames

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
