###
# Copyright (c) 2014, KgBot
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
import supybot.schedule as schedule
import json
import random
import time

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('BlackJack')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class BlackJack(callbacks.Plugin):
    """Add the help for "@plugin help BlackJack" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(BlackJack, self)
        self.__parent.__init__(irc)
        # Dictionary of players, holds important things about each player.
        self.players = {}
        # List of scheduled games
        self.events = []
        self.minStake = 10
        self.maxStake = 50
        
    def _isScheduled(self, name):
        """ Checks to see if player is already playing game."""
        if name in self.events:
            return True
        else:
            return False
        
    def _waitingPlayerAction(self, player):
        """ Checks to see if player has got his first 2 cards and now we're waiting for him to hit/stand or double."""
        if player in self.players.keys() and self.players[player]["waitingAction"] == True:
            return True
        else:
            return False
        
    def _deal(self, who, player):
        _allowed_whos = ["player", "bank"]
        if who in _allowed_whos:
            cards = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K"]
            card = random.choice(cards)
            # Because we J/Q/K are not numbers we must convert them to 10's, but this is not nice, and we must implement
            # 2 types of cards here, one that will be answered to player and one that will be added to score
            if card == "J" or card == "Q" or card == "K":
                card = 10
            if who == "player":
                if card == 1:
                # If 11 + score is bigger then 21 1 will be 1
                    if self.players[player]["score"] + 11 > 21:
                        card = 1
                    # If 1 + score is less then 21 1 will be 11
                    else:
                        card = 11
                self.players[player]["score"] = self.players[player]["score"] + card
                # Returns card because we might want to tell the player which card he's got.
                return card
            else:
                if card == 1:
                    if self.players[player]["bankScore"] + 11 > 21:
                        card = 1
                    else:
                        card = 11
                self.players[player]["bankScore"] = self.players[player]["bankScore"] + card
                return card
            
    def _finishGame(self, irc, player):
        self.players[player]["waitingAction"] = False
        playerScore = self.players[player]["score"]
        bankScore = self.players[player]["bankScore"]
        if playerScore == 21 and bankScore != 21:
            self._playerWins(irc, player)
        elif playerScore == 21 and bankScore == 21:
            irc.reply("This is push, nobody wins.")
            self._push(player)
        elif bankScore == 21 and playerScore != 21:
            self._bankWins(irc, player)
        elif playerScore < 21 and playerScore > bankScore:
            self._playerWins(irc, player)
        elif bankScore < 21 and bankScore > playerScore:
            self._bankWins(irc, player)
        elif playerScore == bankScore:
            irc.reply("This is push, nobody wins.")
            self._push(player)
        elif playerScore > 21 and bankScore < 21:
            self._bankWins(irc, player)
        else:
            self._playerWins(irc, player)
            
    def _removeScheduledGame(self, name):
        try:
            schedule.removeEvent(name)
            self.events.remove(name)
        except:
            try:
                self.events.remove(name)
            except:
                pass
            
    def _push(self, player):
        stake = self.players[player]["stake"]
        chips = Chips()
        chips._addChips(player, stake)
        game_name = "game_%s" % player
        self._removeScheduledGame(game_name)
            
    def _playerWins(self, irc, player, blackjack=False):
        game_name = "game_%s" % player
        if blackjack:
            amount = self._blackjackPrize(self.players[player]["stake"])
        else:
            amount = self.players[player]["stake"] * 2
        chips = Chips()
        chips._addChips(player, amount)
        irc.reply("Congrats, you have won and you got %s chips." % amount)
        self._removeScheduledGame(game_name)
        
    def _bankWins(self, irc, player):
        game_name = "game_%s" % player
        irc.reply("Sorry but you've lost this time.")
        self._removeScheduledGame(game_name)
            
    def _playerChips(self, player):
        """ Return number of chips that player has."""
        chipsClass = Chips()
        chips = chipsClass._getChips(player)
        return chips
    
    def _finishBank(self, irc, player):
        if player in self.players.keys():
            while(self.players[player]["bankScore"] < 17):
                card = self._deal("bank", player)
                irc.reply("Dealer has got \x02%s\x02, and his score is \x02%s\x02." % (card, self.players[player]["bankScore"]))
            self._finishGame(irc, player)
    
    def _addNewPlayer(self, player, stake):
        """ Adds new player and needed things to self.players dictionary."""
        self.players[player] = {}
        # This is set because this is the best way to check if player is playing when he wants to hit/double/stand
        self.players[player]["waitingAction"] = False
        # We must keep track of players score after each card is dealt
        self.players[player]["score"] = 0
        # Also we must keep track of bank score
        self.players[player]["bankScore"] = 0
        # And we need to know how much the player wants to stake
        self.players[player]["stake"] = stake
        # We must also remove initial stake from player, just like he put it on table
        chips = Chips()
        chips._removeChips(player, stake)
        
    def _scheduleNewGame(self, command, when, name, player, irc):
        # Here we're adding game name to the list of games, from where we check who's playing and who's not
        self.events.append(name)
        # Here we schedule the command to run after 10s and to finish game
        schedule.addEvent(command, time.time() + when, name, args=(irc, player))
        
    def _checkBlackjack(self, irc, player):
        """ Checking to see if enyone has blackjack after first two cards are dealt."""
        if player in self.players.keys():
            if self.players[player]["score"] == 21 and self.players[player]["bankScore"] != 21:
                self._playerWins(irc, player, True)
            elif self.players[player]["bankScore"] == 21 and self.players[player]["score"] != 21:
                self._bankWins(irc, player)
            else:
                return
            
    def _blackjackPrize(self, stake):
        # BlackJack prize is not same as regular prize. It is 3:1 so we must calculate it
        halfStake = stake / 2
        newStake = (stake * 2) + halfStake
        return newStake
    
    
    def blackjack(self, irc, msg, args, stake):
        """<stake> - amount of stake, between 10 and 50
        
        Starts a new game."""
        # Because nicks are case-insensitive we must turn nick to lower version.
        player = str(msg.nick).lower()
        # Nicks are uniqe and we will use nick for scheduling game.
        game_name = "game_%s" % player
        # Checks if player has any chips.
        chips = self._playerChips(player)
        # If this is True player is already playing blackjack and only one game is allowed per player.
        if self._isScheduled(game_name):
            irc.reply("You can play only one instance of the game in same time.")
        # If player does not have chips he can't play, logical.
        elif chips == "NoChipsFile" or chips == False or chips == None:
            irc.reply("You can't play blackjack because you don't have enough chips. If you think this is some mistake notify admins.")
        else:
            # If player has enough chips to backup his stake we can start a game.
            if stake >= self.minStake and stake <= self.maxStake and stake <= chips:
                # Now is good time to add new player and actually start a game.
                self._addNewPlayer(player, stake)
                self._startNewGame(irc, player)
            else:
                irc.reply("Something is wrong with your stake, maybe it's too high or too low, or maybe you don't have enough chips.")
    blackjack = wrap(blackjack, ["int"])
    
    def _startNewGame(self, irc, player):
        # We deal first card to the player
        playerFirstCard = self._deal('player', player)
        # And we must tell the player which card he got
        irc.reply("Your first card is %s" % playerFirstCard)
        # We must also deal first card to the bank
        bankFirstCard = self._deal('bank', player)
        # And player shouldn't know which is the dealers first card
        irc.reply("Dealer has got his first card, face down.")
        # Now we deal second card to the player
        playerSecondCard = self._deal('player', player)
        # And we have to tell the player what's his second card, and also what's his score
        irc.reply("Your second card is %s, and you're score is %s" % (playerSecondCard, self.players[player]["score"]))
        # Bank just got it's second card
        bankSecondCard = self._deal('bank', player)
        # Player needs to know which is dealer's second card
        irc.reply("Dealer has got his second card %s, his score is now \x02%s\02.What are you gonna do, stand, hit or double. You have 20 seconds to decide." % (bankSecondCard, self.players[player]["bankScore"]))
        # Now we wait for user to hit/double/stand and our bot must know that he's waiting for player action
        self.players[player]["waitingAction"] = True
        # Each game will wait 10s for user input and then it'll end the game if nothing happens, and we must schedule it
        self._scheduleNewGame(self._finishBank, 20, "game_%s" % player, player, irc)
        # We must check if somebody has got blackjack after first 2 cards
        self._checkBlackjack(irc, player)
    
    def hit(self, irc, msg, args):
        """Takes no arguments
        
        Hit!!!"""
        player = str(msg.nick).lower()
        if self._waitingPlayerAction(player) == True:
            game_name = "game_%s" % player
            self._removeScheduledGame(game_name)
            card = self._deal('player', player)
            irc.reply("You've got %s, and your score is %s." % (card, self.players[player]["score"]))
            if self.players[player]["score"] > 21:
                irc.reply("You're busted.")
                self._bankWins(irc, player)
            else:
                self._scheduleNewGame(self._finishBank, 20, game_name, player, irc)
        else:
            irc.reply("You're not playing blackjack at this moment. Start a new game with +blackjack 50")
    hit = wrap(hit)
    
    def double(self, irc, msg, args):
        """Takes no arguments
        
        Double!!!!"""
        player = str(msg.nick).lower()
        if self._waitingPlayerAction(player) == True:
            stake = self.players[player]["stake"]
            chips = self._playerChips(player)
            if chips != False and chips != None and chips != "NoChipsFile" and chips >= stake:
                game_name = "game_%s" % player
                self._removeScheduledGame(game_name)
                chipsClass = Chips()
                chipsClass._removeChips(player, stake)
                self.players[player]["stake"] = stake * 2
                irc.reply("Your stake was %s, and now it is %s." % (stake, self.players[player]["stake"]))
                card = self._deal('player', player)
                irc.reply("You've got %s, and your score is %s" % (card, self.players[player]["score"]))
                if self.players[player]["score"] > 21:
                    irc.reply("You're busted.")
                    self._bankWins(irc, player)
                else:
                    self._finishBank(irc, player)
            else:
                irc.reply("You don't have enough chips for double stake.")
        else:
            irc.reply("You're not playing blackjack at this moment. Start a new game with +blackjack 50")
    double = wrap(double)
    
    def stand(self, irc, msg, args):
        """Takes no arguments.
        
        Stand!!!"""
        player = str(msg.nick).lower()
        if self._waitingPlayerAction(player) == True:
            self._finishBank(irc, player)
        else:
            irc.reply("You're not playing blackjack at this moment. Start a new game with +blackjack 50")
    stand = wrap(stand)

class Chips():
    def __init__(self):
        try:
            with open("G:\\supybot\\plugins\\BlackJack\\local\\chips.json", "r") as chipsFile:
                self.players = json.load(chipsFile)
        except:
            self.players = False
            
    def _getChips(self, player):
        if self.players:
            if player in self.players.keys():
                try:
                    return self.players[player]["chips"]
                except:
                    return False
            else:
                return None
        else:
            return "NoChipsFile"
        
    def _addChips(self, player, amount):
        if self.players:
            if player in self.players.keys():
                self.players[player]["chips"] = self.players[player]["chips"] + amount
                self._saveChips()
            else:
                self.players[player] = {}
                self.players[player]["chips"] = amount
                self._saveChips()
        else:
            return "NoChipsFile"
        
    def _removeChips(self, player, amount):
        if self.players:
            if player in self.players.keys():
                self.players[player]["chips"] = self.players[player]["chips"] - amount
                self._saveChips()
                
    def _saveChips(self):
        with open("G:\\supybot\\plugins\\BlackJack\\local\\chips.json", "w") as chips:
            json.dump(self.players, chips, indent=4)
    
    
Class = BlackJack


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
