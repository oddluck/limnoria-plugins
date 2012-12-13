###
# Copyright (c) 2012, James Scott
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
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks

from random import randint

import operator 

from cah import Game

import time

class Cah(callbacks.Plugin):
    """Add the help for "@plugin help Cah" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.games = {}

    ###### UTIL METHODS #######
    def _msg(self, irc, channel, msg):
        irc.queueMsg(ircmsgs.privmsg(channel, msg))
    
    def _printBlackCard(self, irc):
        channel = self.channel 
        try:
            self._reply()
        except KeyError:
            self._msg("game not running.")


    def _tallyVotes(self, votes):
        talliedVotes = {}
        for vote in votes.items():
            try:
                talliedVotes[vote] += 1
            except KeyError:
                talliedVotes[vote] = 1
        #find ties

        ties = []
        winningCanidate = None
        for canidate, count in votes.iteritems():
            if winningCanidate == None:
                winningCanidate = (canidate, votes)
            elif winningCanidate[1] < count:
                winningCanidate = (canidate, votes)
                ties = []
            elif winningCanidate[1] == count:
                if len(ties) == 0:
                    ties.append(winningCanidate)
                ties.append((canidate, votes))
            if len(ties) > 0:
                return (ties[randint(0, len(ties) -1)], true)
            else:

            return (winningCanidate, False)


 

    ###### PRE GAME LOGIC ########

    def startGame(self, irc, msg):
        channel = ircutils.toLower(msg.args[0])
        try:
            if self.games[channel]['canStart']:
                if len(self.players) < 2:
                    irc.reply("I need more players.")
                else:
                    self.games[channel]['canStart'] = False
                    self.games[channel]['game'] = Game(self.players, rounds)
                    #start game logic
                    self.nextRound()

        except KeyError:
            irc.reply("Game not running.")


    def playing(self, irc, msg):
        channel = ircutils.toLower(msg.args[0])
        try:
            nick = msg.nick
            game = self.games[channel]
            if channelGame['running'] == False:
                if len(game['players']) < game['maxPlayers']:
                    game['players'].append(nick)
                    irc.reply("Added, Spots left %d" % (game['maxplayers'] - len(game['players']),))
                else:
                    irc.reply("Too many players")
        except KeyError:
            irc.reply("Game not running.")


    def cah(self, irc, msg, numrounds=5):
        """Starts a cards against humanity game, takes
        an optional arguement of number of rounds"""
        channel = ircutils.toLower(msg.args[0])
        #TODO: this is prob needs fixing. 
        try:
            irc.reply("A game is running, please wait till it is finished to start a new one.")
        except:
            channelGame = {}
            channelGame['voting']   = False
            channelGame['canStart'] = False
            channelGame['running'] = False
            channelGame['rounds'] = 5
            channelGame['maxPlayers'] = 5
            channelGame['players']  = []
            self.games[channel] = channelGame
            irc.reply("Who wants to play Cards Aganst Humanity?", prefixNick=False)
            schedule.addEvent(startGame, time.time() + 60, "start_game_%s" % channel)

    ###### END PRE GAME LOGIC ######



    ###### VOTING ##############


    def startCardVote(self, irc, msg):
        channel = ircutils.toLower(msg.args[0])
        try:
            game = self.games[channel]
            game['votes'] = {}
            self._printBlackCard(game)
            self._printAnswers(game)
            self._msg(irc, channel, "Please Vote on your favorite. @votecard <number> to vote, the entire channel can vote.")
            schedule.addEvent(stopCardVote, time.time() + 60, "vote_%s" % channel)
        except:
            irc.reply("A Game is not running, or the time is not to vote.")

    def votecard(self, irc, msg, vote):
        channel = ircutils.toLower(msg.args[0])
        try:
            game = self.games[channel]
            if msg.nick in game['votes'].keys():
                irc.reply("You already voted! This isn't Chicago!")
            else:
                game['votes'][msg.nick] = vote
                irc.reply("vote cast")
        except:
            irc.reply("A Game is not running, or the time is not to vote.")      

    def stopCardVote(self, irc, msg):
        channel = ircutils.toLower(msg.args[0])
        try:
            #TODO: NOt quite done here
            game = self.games[channel]
            winner = self._tallyVotes(game['votes'])
            self._roundWinner(irc, winner)
        except:
            irc.reply("A Game is not running, or the time is not to vote.")
Class = Cah


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
