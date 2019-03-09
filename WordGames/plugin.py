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

from .trie import Trie
from functools import reduce

DEBUG = False

WHITE = '\x0300'
GREEN = '\x0303'
LRED = '\x0304'
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

def point_str(value):
    "Return 'point' or 'points' depending on value."
    return 'point' if value == 1 else 'points'

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
        # Freenode (ircd-seven)
        elif 'TARGMAX' in irc.state.supported:
            # TARGMAX looks like "...,WHOIS:1,PRIVMSG:4,NOTICE:4,..."
            regexp = r'.*PRIVMSG:(\d+).*'
            match = re.match(regexp, irc.state.supported['TARGMAX'])
            if match:
                result = int(match.group(1))
        else:
            debug('Unable to find max targets, using default (1).')
    except Exception as e:
        error('Detecting max targets: %s. Using default (1).' % str(e))
    return result

class WordgamesError(Exception): pass

class Difficulty:
    EASY = 0
    MEDIUM = 1
    HARD = 2
    EVIL = 3

    VALUES = [EASY, MEDIUM, HARD, EVIL]
    NAMES = ['easy', 'medium', 'hard', 'evil']

    @staticmethod
    def name(value):
        return Difficulty.NAMES[value]

    @staticmethod
    def value(name):
        try:
            return Difficulty.VALUES[Difficulty.NAMES.index(name)]
        except ValueError:
            raise WordgamesError('Unrecognized difficulty value: %s' % name)

class Wordgames(callbacks.Plugin):
    "Please see the README file to configure and use this plugin."

    def inFilter(self, irc, msg):
        # Filter out private messages to the bot when they don't use the
        # command prefix and the nick is currently playing a guessing game.
        try:
            channel = msg.args[0]
            commandChars = conf.supybot.reply.whenAddressedBy.chars
            if msg.command == 'PRIVMSG' and msg.args[1][0] not in str(commandChars):
                if not irc.isChannel(channel) and msg.nick:
                    game = self._find_player_game(msg.nick)
                    if game and 'guess' in dir(game):
                        game.guess(msg.nick, msg.args[1])
                        return None
        except:
            return
        # In all other cases, default to normal message handling
        return self.parent.inFilter(irc, msg)

    def __init__(self, irc):
        # Tech note: Save a reference to my parent class because Supybot's
        # Owner plugin will reload this module BEFORE calling die(), which
        # means super() calls will fail with a TypeError. I consider this a
        # bug in Supybot.
        self.parent = super(Wordgames, self)
        self.parent.__init__(irc)
        self.games = {}

    def die(self):
        for channel, game in self.games.items():
            if game.is_running():
                game.stop(now=True)
        self.parent.die()

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

    def worddle(self, irc, msgs, args, channel, command):
        """[command]

        Play a Worddle game. Commands: [easy|medium|hard|evil | stop|stats]
        (default: start with configured difficulty).
        """
        try:
            # Allow deprecated 'join' command:
            if not command or command == 'join' or command in Difficulty.NAMES:
                difficulty = Difficulty.value(
                    self.registryValue('worddleDifficulty'))
                if command in Difficulty.NAMES:
                    difficulty = Difficulty.value(command)
                game = self.games.get(channel)
                if game and game.is_running():
                    if game.__class__ == Worddle:
                        if command:
                            irc.reply('Joining the game. (Ignored "%s".)' %
                                command)
                        game.join(msgs.nick)
                    else:
                        irc.reply('Current word game is not Worddle!')
                else:
                    delay = self.registryValue('worddleDelay')
                    duration = self.registryValue('worddleDuration')
                    self._start_game(Worddle, irc, channel, msgs.nick,
                        delay, duration, difficulty)
            elif command == 'stop':
                # Alias for @wordquit
                self._stop_game(irc, channel)
            elif command == 'stats':
                game = self.games.get(channel)
                if not game or game.__class__ != Worddle:
                    irc.reply('No Worddle game available for stats.')
                elif game.is_running():
                    irc.reply('Please wait until the game finishes.')
                else:
                    game.stats()
            else:
                irc.reply('Unrecognized command to worddle.')
        except WordgamesError as e:
            irc.reply('Wordgames error: %s' % str(e))
            irc.reply('Please check the configuration and try again. ' +
                      'See README for help.')
    worddle = wrap(worddle,
        ['channel', optional(('literal',
            Difficulty.NAMES + ['join', 'stop', 'stats']))])
    # Alias for misspelling of the game name
    wordle = worddle

    def wordshrink(self, irc, msgs, args, channel, difficulty):
        """[easy|medium|hard|evil] (default: medium)

        Start a word-shrink game. Make new words by dropping one letter from
        the previous word and rearranging the remaining letters.
        """
        if difficulty not in ['easy', 'medium', 'hard', 'evil']:
            irc.reply('Difficulty must be easy, medium, hard, or evil.')
        else:
            self._start_game(WordShrink, irc, channel, difficulty)
    wordshrink = wrap(wordshrink,
        ['channel', optional('somethingWithoutSpaces', 'medium')])

    def wordtwist(self, irc, msgs, args, channel, difficulty):
        """[easy|medium|hard|evil] (default: medium)

        Start a word-twist game. Make new words by changing one letter in
        the previous word.
        """
        if difficulty not in ['easy', 'medium', 'hard', 'evil']:
            irc.reply('Difficulty must be easy, medium, hard, or evil.')
        else:
            self._start_game(WordTwist, irc, channel, difficulty)
    wordtwist = wrap(wordtwist,
        ['channel', optional('somethingWithoutSpaces', 'medium')])

    def wordquit(self, irc, msgs, args, channel):
        """(takes no arguments)

        Stop any currently running word game.
        """
        self._stop_game(irc, channel)
    wordquit = wrap(wordquit, ['channel'])

    def _find_player_game(self, player):
        "Find a game (in any channel) that lists player as an active player."
        my_game = None
        for game in list(self.games.values()):
            if game.is_running() and 'players' in dir(game):
                if player in game.players:
                    my_game = game
                    break
        return my_game

    def _get_words(self):
        try:
            regexp = re.compile(self.registryValue('wordRegexp'))
        except Exception as e:
            raise WordgamesError("Bad value for wordRegexp: %s" % str(e))
        path = self.registryValue('wordFile')
        try:
            wordFile = open(path)
        except Exception as e:
            raise WordgamesError("Unable to open word file: %s" % path)
        return list(filter(regexp.match, list(map(str.strip, wordFile.readlines()))))

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
        except WordgamesError as e:
            # Get rid of the game in case it's in an indeterminate state
            if channel in self.games: del self.games[channel]
            irc.reply('Wordgames error: %s' % str(e))
            irc.reply('Please check the configuration and try again. ' +
                      'See README for help.')

    def _stop_game(self, irc, channel):
        game = self.games.get(channel)
        if game and game.is_running():
            game.stop()
        else:
            irc.reply('No word game currently running.')

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

    def stop(self, now=False):
        """
        Shut down the current game. If now is True, do not pass go, do not
        announce anything, just stop anything that needs stopping.
        """
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
    POINT_VALUES = {
        3: 1,
        4: 1,
        5: 2,
        6: 3,
        7: 5,
    }
    MAX_POINTS = 11 # 8 letters or longer
    MESSAGES = {
        'chat':     '%s%%(nick)s%s says: %%(text)s' % (WHITE, LGRAY),
        'joined':   '%s%%(nick)s%s joined the game.' % (WHITE, LGRAY),
        'gameover': ("%s::: Time's Up :::%s Check %s%%(channel)s%s " +
                     "for results.") %
                    (LRED, LGRAY, WHITE, LGRAY),
        'players':  'Current Players: %(players)s',
        'ready':    '%sGet Ready!' % WHITE,
        'result':   ('%s%%(nick)s%s %%(verb)s %s%%(points)d%s ' +
                     'point%%(plural)s (%%(words)s)') %
                    (WHITE, LGRAY, LGREEN, LGRAY),
        'startup': ('Starting in %%(seconds)d seconds, ' +
                     'use "%s%%(commandChar)sworddle%s" to play!') %
                    (WHITE, LGRAY),
        'stopped':  'Game stopped.',
        'stopped2':  ('%s::: Game Stopped :::%s') % (LRED, LGRAY),
        'warning':  '%s%%(seconds)d%s seconds remaining...' % (LYELLOW, LGRAY),
        'welcome1': ('%s::: New Game :::%s (%s%%(difficulty)s%s: ' +
                     '%s%%(min_length)d%s letters or longer)') %
                    (LGREEN, LGRAY, WHITE, LGRAY, WHITE, LGRAY),
        'welcome2': ('%s%%(nick)s%s, write your answers here, e.g.: ' +
                     'cat dog ...') % (WHITE, LGRAY),
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

        def __eq__(self, other):
            return ((self.get_score()) == (other.get_score()))

        def __ne__(self, other):
            return ((self.get_score()) != (other.get_score()))

        def __lt__(self, other):
            return ((self.get_score()) < (other.get_score()))

        def __le__(self, other):
            return ((self.get_score()) <= (other.get_score()))

        def __gt__(self, other):
            return ((self.get_score()) > (other.get_score()))

        def __ge__(self, other):
            return ((self.get_score()) >= (other.get_score()))

        def __repr__(self):
            return "%s %s" % (self.get_score(), other.get_score())

        def get_score(self):
            score = 0
            for word in self.unique:
                score += Worddle.POINT_VALUES.get(len(word), Worddle.MAX_POINTS)
            return score

        def render_words(self, longest_len=0):
            "Return the words in this result, colorized appropriately."
            words = sorted(list(self.unique) + list(self.dup))
            words_text = ''
            last_color = LGRAY
            for word in words:
                color = LCYAN if word in self.unique else GRAY
                if color != last_color:
                    words_text += color
                    last_color = color
                if len(word) == longest_len:
                    word += LYELLOW + '*'
                    last_color = LYELLOW
                words_text += '%s ' % word
            if not words_text:
                words_text = '%s-none-' % (GRAY)
            words_text = words_text.strip() + LGRAY
            return words_text

    class Results:
        "Represents results for all players."

        def __init__(self):
            self.player_results = {}

        def add_player_words(self, player, words):
            unique = set()
            dup = set()
            for word in words:
                bad = False
                for result in list(self.player_results.values()):
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

        def sorted_results(self):
            return sorted(list(self.player_results.values()), reverse=True)

    def __init__(self, words, irc, channel, nick, delay, duration, difficulty):
        # See tech note in the Wordgames class.
        self.parent = super(Worddle, self)
        self.parent.__init__(words, irc, channel)
        self.delay = delay
        self.duration = duration
        self.difficulty = difficulty
        self.max_targets = get_max_targets(irc)
        self._handle_difficulty()
        self.board = self._generate_board()
        self.event_name = 'Worddle.%d' % id(self)
        self.init_time = time.time()
        self.longest_len = len(max(self.board.solutions, key=len))
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
            self._broadcast('chat', self.players, nick=nick, text=text)
            return
        guesses = set(map(str.lower, text.split()))
        accepted = [s for s in guesses if s in self.board.solutions]
        rejected = [s for s in guesses if s not in self.board.solutions]
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
            self._broadcast('welcome1', [nick], now=True,
                difficulty=Difficulty.name(self.difficulty),
                min_length=self.min_length)
            self._broadcast('welcome2', [nick], now=True, nick=nick)
            self._broadcast('joined', self.players, nick=nick)
            self.players.append(nick)
            self.player_answers[nick] = set()
            if self.state == Worddle.State.ACTIVE:
                self._display_board(nick)
            else:
                self._broadcast('players', [nick])
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
        self.announce('Solutions: ' + ' '.join(sorted(self.board.solutions)))

    def start(self):
        self.parent.start()
        self._broadcast('startup', [self.channel], True, seconds=self.delay)
        self.join(self.starter)
        self._schedule_next_event()

    def stop(self, now=False):
        self.parent.stop()
        self.state = Worddle.State.DONE
        try:
            schedule.removeEvent(self.event_name)
        except KeyError:
            pass
        if not now:
            self._broadcast('stopped', [self.channel])
            self._broadcast('stopped2', self.players)

    def stats(self):
        assert self.state == Worddle.State.DONE
        points = 0
        for word in self.board.solutions:
            points += Worddle.POINT_VALUES.get(len(word), Worddle.MAX_POINTS)
        longest_words = [w for w in self.board.solutions if len(w) == self.longest_len]
        self.announce(('There were %s%d%s possible words, with total point'
            ' value %s%d%s. The longest word%s: %s%s%s.') %
            (WHITE, len(self.board.solutions), LGRAY, LGREEN, points, LGRAY,
            ' was' if len(longest_words) == 1 else 's were',
             LCYAN, (LGRAY + ', ' + LCYAN).join(longest_words), LGRAY))

    def _broadcast_text(self, text, recipients=None, now=False):
        """
        Broadcast the given string message to the recipient list (default is
        all players, not the game channel). Set now to bypass Supybot's queue
        and send the message immediately.
        """
        if recipients is None:
            recipients = self.players
        for i in range(0, len(recipients), self.max_targets):
            targets = ','.join(recipients[i:i+self.max_targets])
            self.announce_to(targets, text, now)

    def _broadcast(self, name, recipients=None, now=False, **kwargs):
        """
        Broadcast the message named by 'name' using the constants defined
        in MESSAGES to the specified recipient list.  If recipients is
        unspecified, default is all players (game channel not included).
        Keyword args should be provided for any format substitution in this
        particular message.
        """
        # Automatically provide some dictionary values
        kwargs['channel'] = self.channel
        kwargs['commandChar'] = str(conf.supybot.reply.whenAddressedBy.chars)[0]
        kwargs['players'] = "%s%s%s" % \
            (WHITE, (LGRAY + ', ' + WHITE).join(self.players), LGRAY)
        if 'points' in kwargs:
            kwargs['plural'] = '' if kwargs['points'] == 1 else 's'
        formatted = Worddle.MESSAGES[name] % kwargs
        self._broadcast_text(formatted, recipients, now)

    def _handle_difficulty(self):
        self.min_length = {
            Difficulty.EASY:   3,
            Difficulty.MEDIUM: 4,
            Difficulty.HARD:   5,
            Difficulty.EVIL:   6,
        }[self.difficulty]

    def _get_ready(self):
        self.state = Worddle.State.READY
        self._broadcast('ready', now=True)
        self._schedule_next_event()

    def _begin_game(self):
        self.state = Worddle.State.ACTIVE
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        self._display_board()
        self._schedule_next_event()

    def _schedule_next_event(self):
        """
        (Re)schedules the next game event (start, time left warning, end)
        as appropriate.
        """
        # Unschedule any previous event
        try:
            schedule.removeEvent(self.event_name)
        except KeyError:
            pass
        if self.state == Worddle.State.PREGAME:
            # Schedule "get ready" message
            schedule.addEvent(self._get_ready,
                self.init_time + self.delay, self.event_name)
        elif self.state == Worddle.State.READY:
            # Schedule game start
            schedule.addEvent(self._begin_game,
                self.init_time + self.delay + 3, self.event_name)
        elif self.state == Worddle.State.ACTIVE:
            if self.warnings:
                # Warn almost half a second early, in case there is a little
                # latency before the event is triggered. (Otherwise a 30 second
                # warning sometimes shows up as 29 seconds remaining.)
                warn_time = self.end_time - self.warnings[0] - 0.499
                schedule.addEvent(
                    self._time_warning, warn_time, self.event_name)
                self.warnings = self.warnings[1:]
            else:
                # Schedule game end
                schedule.addEvent(
                    self._end_game, self.end_time, self.event_name)

    def _time_warning(self):
        seconds = round(self.start_time + self.duration - time.time())
        self._broadcast('warning', now=True, seconds=seconds)
        self._schedule_next_event()

    def _end_game(self):
        self.gameover()
        self.state = Worddle.State.DONE

        # Compute results
        results = Worddle.Results()
        for player, answers in self.player_answers.items():
            results.add_player_words(player, answers)

        # Notify players
        for result in list(results.player_results.values()):
            self._broadcast('gameover', [result.player], now=True)

        # Announce results
        player_results = results.sorted_results()
        high_score = player_results[0].get_score()
        tie = len(player_results) > 1 and \
              player_results[1].get_score() == high_score
        for result in player_results:
            score = result.get_score()
            verb = "got"
            if score == high_score:
                if tie:
                    verb = "%stied%s with" % (LYELLOW, LGRAY)
                elif high_score > 0:
                    verb = "%swins%s with" % (LGREEN, LGRAY)
            words_text = result.render_words(longest_len=self.longest_len)
            self._broadcast('result', [self.channel], nick=result.player,
                    verb=verb, points=score, words=words_text)

    def _display_board(self, nick=None):
        "Display the board to everyone or just one nick if specified."
        commandChar = str(conf.supybot.reply.whenAddressedBy.chars)[0]
        help_msgs = [''] * Worddle.BOARD_SIZE
        help_msgs[1] = '%sLet\'s GO!' % (WHITE)
        help_msgs[2] = '%s%s%s seconds left!' % \
            (LYELLOW, int(round(self.end_time - time.time())), LGRAY)
        for row, help_msg in zip(self.board.render(), help_msgs):
            text = '   %s     %s' % (row, help_msg)
            if nick:
                self.announce_to(nick, text, now=True)
            else:
                self._broadcast_text(text, self.players + [self.channel], True)

    def _generate_board(self):
        "Generate several boards and return the most bountiful board."
        attempts = 5
        wordtrie = Trie()
        list(map(wordtrie.add, self.words))
        boards = [WorddleBoard(wordtrie, Worddle.BOARD_SIZE, self.min_length)
            for i in range(0, attempts)]
        board_quality = lambda b: len(b.solutions)
        return max(boards, key=board_quality)

class WorddleBoard(object):
    "Represents the board in a Worddle game."

    def __init__(self, wordtrie, n, min_length):
        "Generate a new n x n Worddle board."
        self.size = n
        self.min_length = min_length
        self.rows = self._generate_rows()
        self.solutions = self._find_solutions(wordtrie)

    def render(self):
        "Render the board for display in IRC as a list of strings."
        result = []
        for row in self.rows:
            text = LGREEN + '  '.join(row) + ' ' # Last space pad in case of Qu
            text = text.replace('Q ', 'Qu')
            result.append(text)
        return result

    def _find_solutions(self, wordtrie, visited=None, row=0, col=0, prefix=''):
        "Discover and return the set of all solutions for the current board."
        result = set()
        if visited == None:
            for row in range(0, self.size):
                for col in range(0, self.size):
                    result.update(
                        self._find_solutions(wordtrie, [], row, col, ''))
        else:
            visited = visited + [(row, col)]
            current = prefix + self.rows[row][col].lower()
            if current[-1] == 'q': current += 'u'
            node = wordtrie.find_prefix(current)
            if node:
                if node['*'] and len(current) >= self.min_length:
                    result.add(current)
                # Explore all 8 directions out from here
                offsets = [(-1, -1), (-1, 0), (-1, 1),
                           ( 0, -1),          ( 0, 1),
                           ( 1, -1), ( 1, 0), ( 1, 1)]
                for offset in offsets:
                    point = (row + offset[0], col + offset[1])
                    if point in visited: continue
                    if point[0] < 0 or point[0] >= self.size: continue
                    if point[1] < 0 or point[1] >= self.size: continue
                    result.update(self._find_solutions(
                        wordtrie, visited, point[0], point[1], current))
        return result

    def _generate_rows(self):
        "Randomly generate a Worddle board (a list of lists)."
        letters = reduce(add, (list(map(mul,
                list(Worddle.FREQUENCY_TABLE.keys()),
                list(Worddle.FREQUENCY_TABLE.values())))))
        rows = []
        values = random.sample(letters, self.size**2)
        for i in range(0, self.size):
            start = self.size * i
            end = start + self.size
            rows.append(values[start:end])
        return rows

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
        # See tech note in the Wordgames class.
        self.parent = super(WordChain, self)
        self.parent.__init__(words, irc, channel)
        self.settings = settings
        self.solution_length = random.choice(settings.puzzle_lengths)
        self.solution = []
        self.solutions = []
        self.word_map = {}
        if settings.word_lengths:
            self.words = [w for w in self.words if len(w) in settings.word_lengths]
        else:
            self.words = [w for w in self.words if len(w) >= 3]
        self.build_word_map()

    def start(self):
        # Build a puzzle
        attempts = 100000 # Prevent infinite loops
        while attempts:
            self.solution = []
            while len(self.solution) < self.solution_length:
                attempts -= 1
                if attempts == 0:
                    raise WordgamesError(('Unable to generate %s puzzle. This' +
                        ' is either a bug, or the word file is too small.') %
                        self.__class__.__name__)
                self.solution = [random.choice(self.words)]
                for i in range(1, self.solution_length):
                    values = self.word_map[self.solution[-1]]
                    values = [w for w in values if w not in self.solution]
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
            if happy:
                break
        if not happy:
            raise WordgamesError(('Unable to generate %s puzzle meeting the ' +
                'game parameters. This is probably a bug.') %
                self.__class__.__name__)

        # Start the game
        self.show()
        self.parent.start()

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

    def stop(self, now=False):
        self.parent.stop()
        if not now:
            self.announce(self._join_words(self.solution))

    def handle_message(self, msg):
        words = list(map(str.strip, msg.args[1].split('>')))
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
            'easy':   WordChain.Settings([4], list(range(3, 9)), list(range(15, 100))),
            'medium': WordChain.Settings([5], list(range(4, 10)), list(range(8, 25))),
            'hard':   WordChain.Settings([6], list(range(4, 12)), list(range(4, 12))),
            'evil':   WordChain.Settings([7], list(range(4, 15)), list(range(1, 10))),
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
            'easy':   WordChain.Settings([4], [3, 4], list(range(10, 100))),
            'medium': WordChain.Settings([5], [4, 5], list(range(5, 12))),
            'hard':   WordChain.Settings([6], [4, 5, 6], list(range(2, 5))),
            'evil':   WordChain.Settings([7], [4, 5, 6], list(range(1, 3))),
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
                self.word_map[word] += [w for w in keymap.get(key, []) if w != word]

    def is_trivial_solution(self, solution):
        "If it's possible to get there in fewer hops, this is trivial."
        return len(solution) < self.solution_length

Class = Wordgames

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
