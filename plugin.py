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

from operator import add, mul
import random
import re
import time

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.schedule as schedule
import supybot.log as log
import supybot.world as world

from trie import Trie

DEBUG = False

WHITE = '\x0300'
GREEN = '\x0303'
RED = '\x0305'
YELLOW = '\x0307'
LYELLOW = '\x0308'
LGREEN = '\x0309'
LCYAN = '\x0311'
LBLUE = '\x0312'
GRAY = '\x0314'
LGRAY = '\x0315'

def debug(message):
    log.debug('Wordgames: ' + message)

def info(message):
    log.info('Wordgames: ' + message)

def error(message):
    log.error('Wordgames: ' + message)

# Ideally Supybot would do this for me. It seems that all IRC servers have
# their own way of reporting this information...
def get_max_targets(irc):
    # Default: Play it safe
    result = 1
    # Look for known maxtarget strings
    try:
        # Inspircd
        if 'MAXTARGETS' in irc.state.supported:
            result = int(irc.state.supported['MAXTARGETS'])
        # FreenodeA (ircd-seven)
        elif 'TARGMAX' in irc.state.supported:
            # TARGMAX looks like "...,WHOIS:1,PRIVMSG:4,NOTICE:4,..."
            regexp = r'.*PRIVMSG:(\d+).*'
            match = re.match(regexp, irc.state.supported['TARGMAX'])
            if match:
                result = int(match.group(1))
                print 'Determined max targets:', result
        else:
            debug('Unable to find max targets, using default (1).')
    except Exception, e:
        error('Detecting max targets: %s. Using default (1).' % str(e))
    return result

class WordgamesError(Exception): pass

class Wordgames(callbacks.Plugin):
    "Please see the README file to configure and use this plugin."

    def inFilter(self, irc, msg):
        # Filter out private messages to the bot when they don't use the
        # command prefix and the nick is currently playing a guessing game.
        channel = msg.args[0]
        commandChars = conf.supybot.reply.whenAddressedBy.chars
        if msg.command == 'PRIVMSG' and msg.args[1][0] not in str(commandChars):
            if not irc.isChannel(channel) and msg.nick:
                game = self._find_player_game(msg.nick)
                if game and 'guess' in dir(game):
                    game.guess(msg.nick, msg.args[1])
                    return None
        # In all other cases, default to normal message handling
        return self.__parent.inFilter(irc, msg)

    def __init__(self, irc):
        self.__parent = super(Wordgames, self)
        self.__parent.__init__(irc)
        self.games = {}

    def die(self):
        # Ugly, but we need to ensure that the game actually stops
        try:
            schedule.removeEvent(Worddle.NAME)
        except KeyError: pass
        except Exception, e:
            error("In die(): " + str(e))
        self.__parent.die()

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        game = self.games.get(channel)
        if game:
            game.handle_message(msg)

    if DEBUG:
        def wordsolve(self, irc, msgs, args, channel):
            "Show solution(s) for the currently running game."
            game = self.games.get(channel)
            if game and game.is_running():
                game.solve()
            else:
                irc.reply('No game is currently running.')
        wordsolve = wrap(wordsolve, ['channel'])

    def worddle(self, irc, msgs, args, channel, join):
        """[join]

        Start a Worddle game or join a running game."""
        delay = self.registryValue('worddleDelay')
        duration = self.registryValue('worddleDuration')
        if join:
            if join == 'join':
                game = self.games.get(channel)
                if game and game.is_running():
                    if game.__class__ == Worddle:
                        game.join(msgs.nick)
                    else:
                        irc.reply('Current word game is not Worddle!')
                else:
                    irc.reply('No game is currently running.')
            else:
                irc.reply('Unrecognized option to worddle.')
        else:
            self._start_game(Worddle, irc, channel, msgs.nick, delay, duration)
    worddle = wrap(worddle, ['channel', optional('somethingWithoutSpaces', '')])
    # Alias for misspelling of the game name
    wordle = worddle

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

    def _find_player_game(self, player):
        "Find a game (in any channel) that lists player as an active player."
        my_game = None
        for game in self.games.values():
            if game.is_running() and 'players' in dir(game):
                if player in game.players:
                    my_game = game
                    break
        return my_game

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

    def solve(self):
        "Show solution(s) for current game."
        pass

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

    def announce(self, text, now=False):
        """
        Announce a message with the game title prefix. Set now to bypass
        Supybot's queue, sending the message immediately.
        """
        self.announce_to(self.channel, text, now)

    def announce_to(self, dest, text, now=False):
        "Announce to a specific destination (nick or channel)."
        new_text = '%s%s%s:%s %s' % (
            LBLUE, self.__class__.__name__, WHITE, LGRAY, text)
        self.send_to(dest, new_text, now)

    def send(self, text, now=False):
        """
        Send a message to the game's channel. Set now to bypass supybot's
        queue, sending the message immediately.
        """
        self.send_to(self.channel, text, now)

    def send_to(self, dest, text, now=False):
        "Send to a specific destination (nick or channel)."
        method = self.irc.sendMsg if now else self.irc.queueMsg
        method(ircmsgs.privmsg(dest, text))

    def handle_message(self, msg):
        "Handle incoming messages on the channel."
        pass

class Worddle(BaseGame):
    "The Worddle game implementation."

    BOARD_SIZE = 4
    NAME = 'worddle' # Unique identifier for supybot events
    FREQUENCY_TABLE = {
        19: 'E',
        13: 'T',
        12: 'AR',
        11: 'INO',
        9:  'S',
        6:  'D',
        5:  'CHL',
        4:  'FMPU',
        3:  'GY',
        2:  'W',
        1:  'BJKQVXZ',
    }

    class State:
        PREGAME = 0
        READY = 1
        ACTIVE = 2
        DONE = 3

    class PlayerResult:
        "Represents result for a single player."

        def __init__(self, player, unique=None, dup=None):
            self.player = player
            self.unique = unique if unique else set()
            self.dup = dup if dup else set()

        def __cmp__(self, other):
            return cmp(self.get_score(), other.get_score())

        def get_score(self):
            return sum(map(len, self.unique))

        def render(self):
            words = sorted(list(self.unique) + list(self.dup))
            words_text = ''
            for word in words:
                if word in self.unique:
                    color = LCYAN
                else:
                    color = GRAY
                words_text += '%s%s%s ' % (color, word, LGRAY)
            if not words_text:
                words_text = '%s-none-%s' % (GRAY, LGRAY)
            return '%s%s%s gets %s%d%s points (%s)' % \
                    (WHITE, self.player, LGRAY, LGREEN, self.get_score(),
                     LGRAY, words_text.strip())

    class Results:
        "Represents results for all players."

        def __init__(self):
            self.player_results = {}

        def add_player_words(self, player, words):
            unique = set()
            dup = set()
            for word in words:
                bad = False
                for result in self.player_results.values():
                    if word in result.unique:
                        result.unique.remove(word)
                        result.dup.add(word)
                        bad = True
                    elif word in result.dup:
                        bad = True
                if bad:
                    dup.add(word)
                else:
                    unique.add(word)
            self.player_results[player] = \
                    Worddle.PlayerResult(player, unique, dup)

        def render(self):
            "Return a list of messages to send to IRC."
            return [r.render()
                for r in sorted(self.player_results.values(), reverse=True)]

        def winners(self):
            result_list = sorted(self.player_results.values())
            high_score = result_list[-1].get_score()
            return filter(lambda r: r.get_score() == high_score, result_list)

    def __init__(self, words, irc, channel, nick, delay, duration):
        super(Worddle, self).__init__(words, irc, channel)
        self._generate_board()
        self._generate_wordtrie()
        self.delay = delay
        self.duration = duration
        self.init_time = time.time()
        self.max_targets = get_max_targets(irc)
        self.solutions = self._find_solutions()
        self.starter = nick
        self.state = Worddle.State.PREGAME
        self.players = []
        self.player_answers = {}
        self.warnings = [30, 10, 5]
        while self.warnings[0] >= duration:
            self.warnings = self.warnings[1:]

    def guess(self, nick, text):
        # This can't happen right now, but it might be useful some day
        if nick not in self.players:
            self.join(nick)
        # Pre-game messages are relayed as chatter (not treated as guesses)
        if self.state < Worddle.State.ACTIVE:
            if self.state == Worddle.State.PREGAME:
                if len(self.players) > 1:
                    self._broadcast("%s%s%s says: %s" %
                        (WHITE, nick, LGRAY, text), ignore=[self.channel, nick])
                    self.send_to(nick, "Message sent to other players.")
                else:
                    self.send_to(nick,
                        "Message not sent (no one else is playing yet).")
            else:
                self.send_to(nick, "Relax! The game hasn't started yet!")
            return
        guesses = set(map(str.lower, text.split()))
        accepted = filter(lambda s: s in self.solutions, guesses)
        rejected = filter(lambda s: s not in self.solutions, guesses)
        if len(accepted) > 3:
            message = '%sGreat!%s' % (LGREEN, WHITE)
        elif len(accepted) > 0:
            message = '%sOk!' % WHITE
        else:
            message = '%sOops!%s' % (RED, LGRAY)
        if accepted:
            message += ' You got: %s%s' % (' '.join(sorted(accepted)), LGRAY)
            self.player_answers[nick].update(accepted)
        if rejected:
            message += ' (not accepted: %s)' % ' '.join(sorted(rejected))
        self.send_to(nick, message)

    def join(self, nick):
        assert self.is_running()
        assert self.state != Worddle.State.DONE
        if nick not in self.players:
            self.players.append(nick)
            self.player_answers[nick] = set()
            self.announce_to(nick, '-- %sNew Game%s --' %
                (WHITE, LGRAY), now=True)
            self.announce_to(nick,
                "%s%s%s, here's your workspace. Just say: word1 word2 ..." %
                (WHITE, nick, LGRAY), now=True)
            self._broadcast('%s%s%s joined the game.' % (WHITE, nick, LGRAY),
                ignore=[nick])
            if self.state == Worddle.State.ACTIVE:
                self._display_board(nick)
            else:
                self.announce_to(nick, 'Current Players: %s%s' %
                    (WHITE, (LGRAY + ', ' + WHITE).join(self.players)))
            # Keep at least 5 seconds on the pre-game clock if someone joins
            if self.state == Worddle.State.PREGAME:
                time_left = self.init_time + self.delay - time.time()
                if time_left < 5:
                    self.delay += (5 - time_left)
                self._schedule_next_event()
        else:
            self.send('%s: You have already joined the game.' % nick)

    def show(self):
        # Not sure if this is really useful.
        #if self.state == Worddle.State.ACTIVE:
        #    self._display_board(self.channel)
        pass

    def solve(self):
        self.announce('Solutions: ' + ' '.join(sorted(self.solutions)))

    def start(self):
        super(Worddle, self).start()
        commandChar = str(conf.supybot.reply.whenAddressedBy.chars)[0]
        self.announce('The game will start in %s%d%s seconds...' %
                (LYELLOW, self.delay, LGRAY), now=True)
        self.announce('Use "%s%sworddle join%s" to join the game.'
                % (WHITE, commandChar, LGRAY), now=True)
        self.join(self.starter)
        self._schedule_next_event()

    def stop(self):
        super(Worddle, self).stop()
        try:
            schedule.removeEvent(Worddle.NAME)
        except KeyError:
            pass
        self._broadcast('Game stopped.')

    def _broadcast(self, text, now=False, ignore=None):
        """
        Broadcast a message to channel and all players. Set now to bypass
        Supybot's queue and send the message immediately.  ignore is a list
        of names who should NOT receive the message.
        """
        recipients = [self.channel] + self.players
        if ignore:
            recipients = filter(lambda r: r not in ignore, recipients)
        for i in range(0, len(recipients), self.max_targets):
            targets = ','.join(recipients[i:i+self.max_targets])
            self.announce_to(targets, text, now)

    def _get_ready(self):
        self.state = Worddle.State.READY
        self._broadcast('%sGet Ready!' % WHITE, now=True, ignore=[self.channel])
        self._schedule_next_event()

    def _begin_game(self):
        self.state = Worddle.State.ACTIVE
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        commandChar = str(conf.supybot.reply.whenAddressedBy.chars)[0]
        self._display_board()
        self._broadcast("%sLet's GO!%s You have %s%d%s seconds!" %
            (WHITE, LGRAY, LYELLOW, self.duration, LGRAY),
            now=True, ignore=[self.channel])
        self.announce('%sGame Started!%s Use "%s%sworddle join%s" to play!' %
                (WHITE, LGRAY, WHITE, commandChar, LGRAY))
        self._schedule_next_event()

    def _schedule_next_event(self):
        """
        (Re)schedules the next game event (start, time left warning, end)
        as appropriate.
        """
        # Unschedule any previous event
        try:
            schedule.removeEvent(Worddle.NAME)
        except KeyError:
            pass
        if self.state == Worddle.State.PREGAME:
            # Schedule "get ready" message
            schedule.addEvent(self._get_ready,
                self.init_time + self.delay, Worddle.NAME)
        elif self.state == Worddle.State.READY:
            # Schedule game start
            schedule.addEvent(self._begin_game,
                self.init_time + self.delay + 3, Worddle.NAME)
        elif self.state == Worddle.State.ACTIVE:
            if self.warnings:
                # Warn almost half a second early, in case there is a little
                # latency before the event is triggered. (Otherwise a 30 second
                # warning sometimes shows up as 29 seconds remaining.)
                warn_time = self.end_time - self.warnings[0] - 0.499
                schedule.addEvent(self._time_warning, warn_time, Worddle.NAME)
                self.warnings = self.warnings[1:]
            else:
                # Schedule game end
                schedule.addEvent(self._end_game, self.end_time, Worddle.NAME)

    def _time_warning(self):
        seconds = round(self.start_time + self.duration - time.time())
        message = '%s%d%s seconds remaining...' % (LYELLOW, seconds, LGRAY)
        self._broadcast(message, now=True)
        self._schedule_next_event()

    def _end_game(self):
        self.gameover()
        self.state = Worddle.State.DONE
        self.announce("%sTime's up!" % WHITE, now=True)

        # Compute results
        results = Worddle.Results()
        for player, answers in self.player_answers.iteritems():
            results.add_player_words(player, answers)

        # Notify players
        for result in results.player_results.values():
            self.announce_to(result.player,
                ("%sTime's up!%s You scored %s%d%s points! Check "
                "%s%s%s for complete results.") %
                (WHITE, LGRAY, LGREEN, result.get_score(), LGRAY, WHITE,
                self.channel, LGRAY), now=True)

        # Announce game results in channel
        for message in results.render():
            self.announce(message)
        winners = results.winners()
        winner_names = [("%s%s%s" % (WHITE, r.player, LGRAY)) for r in winners]
        message = ', '.join(winner_names[:-1])
        if len(winners) > 1:
            message += ' and '
        message += winner_names[-1]
        if len(winners) > 1:
            message += ' tied '
        else:
            message += ' wins '
        message += 'with %s%d%s points!' %(WHITE, winners[0].get_score(), LGRAY)
        self.announce(message)

    def _display_board(self, nick=None):
        "Display the board to everyone or just one nick if specified."
        for row in self.board:
            text = LGREEN + '  ' + '  '.join(row) + ' '
            text = text.replace('Q ', 'Qu').rstrip()
            if nick:
                self.announce_to(nick, text, now=True)
            else:
                self._broadcast(text, now=True)

    def _find_solutions(self, visited=None, row=0, col=0, prefix=''):
        "Discover and return the set of all solutions for the current board."
        result = set()
        if visited == None:
            for row in range(0, Worddle.BOARD_SIZE):
                for col in range(0, Worddle.BOARD_SIZE):
                    result.update(self._find_solutions([], row, col, ''))
        else:
            visited = visited + [(row, col)]
            current = prefix + self.board[row][col].lower()
            if current[-1] == 'q': current += 'u'
            node = self.wordtrie.find(current)
            if node:
                if node.complete and len(current) > 2:
                    result.add(current)
                # Explore all 8 directions out from here
                offsets = [(-1, -1), (-1, 0), (-1, 1),
                           ( 0, -1),          ( 0, 1),
                           ( 1, -1), ( 1, 0), ( 1, 1)]
                for offset in offsets:
                    point = (row + offset[0], col + offset[1])
                    if point in visited: continue
                    if point[0] < 0 or point[0] >= Worddle.BOARD_SIZE: continue
                    if point[1] < 0 or point[1] >= Worddle.BOARD_SIZE: continue
                    result.update(self._find_solutions(
                        visited, point[0], point[1], current))
        return result

    def _generate_board(self):
        "Randomly generate a Worddle board (a list of lists)."
        letters = reduce(add, (map(mul,
                Worddle.FREQUENCY_TABLE.keys(),
                Worddle.FREQUENCY_TABLE.values())))
        self.board = []
        values = random.sample(letters, Worddle.BOARD_SIZE**2)
        for i in range(0, Worddle.BOARD_SIZE):
            start = Worddle.BOARD_SIZE * i
            end = start + Worddle.BOARD_SIZE
            self.board.append(values[start:end])

    def _generate_wordtrie(self):
        "Populate self.wordtrie with the dictionary words."
        self.wordtrie = Trie()
        map(self.wordtrie.add, self.words)

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

    def solve(self):
        show = 3
        for solution in self.solutions[:show]:
            self.announce(self._join_words(solution))
        not_shown = len(self.solutions) - show
        if not_shown > 0:
            self.announce('(%d more solution%s not shown.)' %
                    (not_shown, 's' if not_shown > 1 else ''))

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
