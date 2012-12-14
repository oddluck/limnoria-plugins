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
import supybot.ircmsgs as ircmsgs
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
        self.__parent = super(Cah, self)
        self.__parent.__init__(irc)
        self.games = {}

    class CahGame(object):
        """docstring for Game"""
        def __init__(self, irc, channel, numrounds = 5):
            self.irc = irc
            self.channel = channel
            self.game = None
            self.canStart = False
            self.voting = False
            self.canStart = False
            self.roundRunning = False
            self.running =  False
            self.rounds = numrounds
            self.maxPlayers= 5
            self.players = []
        
        def initGame(self):
            schedule.addEvent(self.startgame, time.time() + 60, "start_game_%s" % self.channel)

        ###### UTIL METHODS ##########
      
        def _msg(self, recip, msg):
            self.irc.queueMsg(ircmsgs.privmsg(recip,msg))
        
        def _printBlackCard(self, recip):
            response = "Question: %s"
            cah = self.game
            self._msg(recip, response % cah.question.text)

        def _msgHandToPlayer(self, nick):
            response = "Your cards: %s  Please respond with @card <number> [number]"
            enumeratedHand = []
            cah = self.game
            for position, card in enumerate(cah.players[nick].card_list):
                enumeratedHand.append("%s: %s " % (position + 1, ircutils.bold(card.text)))
            self._printBlackCard(nick)
            self._msg(nick, response % ', '.join(enumeratedHand))

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
                    #TODO: WAT?
                    pass

                return (winningCanidate, False)
        ###### END UTIL METHODS #######

        ###### PRE GAME LOGIC ########

        def startgame(self):
            #heh fix this
            game = self 
            if game.canStart:
                if len(game.players) < 2:
                    self._msg(channel, "I need more players.")
                else:
                    game.canStart = False
                    game.running = True
                    game.game = Game(game.players, game.rounds)
                    #start game logic
                    self.nextround()        

        ###### END PRE GAME LOGIC ######

        ###### START GAME LOGIC ########

        def nextround(self):
            channel = self.channel
            game = self
            cah = game.game
            try:
                cah.next_round()
                #Print Black Card to channel.
                self._printBlackCard(self.channel)
                for nick in self.players:
                    self._msgHandToPlayer(nick)
                self._msg(channel, "The white cards have been PMed to the players, you have 60 seconds to choose.")
                #TODO: do we need a round flag?
                schedule.addEvent(self.endround, time.time() + 60, "round_%s" % channel)
            except Exception as e:
                #TODO: add no more round logic
                print e
                pass



        def card(self):
            channel = ircutils.toLower(msg.args[0])
            #TODO: Card decision logic

        def endround(self):
            channel = self.channel
            try:
                game = self
                if game.roundRunning:
                    game.roundRunning= False
                    self._msg(channel, "Card Submittion Completed.")
                    self.startcardvote()
                else:
                    self_msg(channel, "No round active.")
            except KeyError:
                self_msg(channel, "A Game is not running.")

        ###### END GAME LOGIC #########

    ###### VOTING ##############

        def startcardvote(self):
            channel = self.channel
            try:
                game = self
                game.votes = {}
                self._printBlackCard(game)
                self._printAnswers(game)
                self._msg(channel, "Please Vote on your favorite. @votecard <number> to vote, the entire channel can vote.")
                schedule.addEvent(self.stopcardvote, time.time() + 60, "vote_%s" % channel)
            except:
                self._msg(channel, "A Game is not running, or the time is not to vote.")



        def stopcardvote(self):
            try:
                #TODO: NOt quite done here
                game = self
                winner = self._tallyVotes(game.votes)
                self._roundWinner(winner)
            except:
                irc.reply("A Game is not running, or the time is not to vote.")
        ###### END VOTING LOGIC ######

        def close(self):
            try:
                schedule.removeEvent("round_%s" % self.channel)
            except:
                pass
            try:
                schedule.removeEvent("vote_%s" % self.channel)
            except:
                pass
            try:        
                schedule.removeEvent("start_game_%s" % self.channel)
            except:
                pass  
    Class = CahGame

    ###### CHANNEL COMMANDS ######
    def forcestartgame(self, irc, msg, args):
        channel = ircutils.toLower(msg.args[0])
        if channel in self.games:
            try:        
                schedule.removeEvent("start_game_%s" % self.channel)
            except:
                pass                
            self.games[channel].startgame()
        else:
            irc.reply("Game not running.")

    def playing(self, irc, msg, args):
        channel = ircutils.toLower(msg.args[0])
        nick = msg.nick

        if channel in self.games:
            game = self.games[channel]

            if game.running == False:
                if nick in game.players:
                    irc.reply("You already are playing.")
                else:
                    if len(game.players) < game.maxPlayers:
                        game.players.append(nick)
                        irc.reply("Added, Spots left %d/%d, Current Players %s" % (game.maxPlayers - len(game.players), game.maxPlayers, ', '.join(game.players)))
                    else:
                        irc.reply("Too many players")
                if len(game.players) > 1:
                    game.canStart = True
        else:
            irc.reply("Game not running.")

    def cah(self, irc, msg, args):
        """Starts a cards against humanity game, takes
        an optional arguement of number of rounds"""
        channel = ircutils.toLower(msg.args[0])
        #TODO: this is prob needs fixing. 
        if len(args) < 1:
            numrounds = 5
        else:
            numrounds = args[0]

        if channel in self.games:
            irc.reply("There is a game running currently.")
        else:
            irc.reply("Who wants to play Cards Aganst Humanity? To play reply with: @playing", prefixNick=False)
            self.games[channel] = self.CahGame(irc, channel, numrounds)
            self.games[channel].initGame()
            


    def scah(self, irc, msg, args):
        channel = ircutils.toLower(msg.args[0])
        if channel in self.games:
            self.games[channel].close()
            self.games.pop(channel)
            irc.reply("Game stopped.")
        else:
            irc.reply("Game not running.")


    def votecard(self, irc, msg, args, vote):
        channel = ircutils.toLower(msg.args[0])
        try:
            game = self.games[channel]
            if msg.nick in game.voteskeys():
                irc.reply("You already voted! This isn't Chicago!")
            else:
                game.votes[msg.nick] = vote
                irc.reply("Cote cast")
        except:
            irc.reply("A Game is not running, or the time is not to vote.")      

    ###### END CHANNEL COMMANDS ######

    
Class = Cah


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
