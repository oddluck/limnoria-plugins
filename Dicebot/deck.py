###
# Copyright (c) 2008, Anatoly Popov
# Copyright (c) 2008, Andrey Rahmatullin
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

import random

class Deck:
    """
    54-card deck simulator.

    This class represents a standard 54-card deck (with 2 different Jokers)
    and supports shuffling and drawing.
    """
    titles = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['♣', '♦', '♥', '♠']

    def __init__(self):
        """
        Initialize a new deck and shuffle it.
        """
        self.deck = []
        self.base_deck = ['Black Joker', 'Red Joker'] + [t + s
                                                         for t in self.titles
                                                         for s in self.suits]
        self.shuffle()

    def shuffle(self):
        """
        Restore and shuffle the deck.

        All cards are returned to the deck and then shuffled randomly.
        """
        new_deck = self.base_deck[:]
        random.shuffle(new_deck)
        self.deck = new_deck

    def __next__(self):
        """
        Draw the top card from the deck and return it.

        Drawn card is removed from the deck. If it was the last card, deck is
        shuffled.
        """
        card = self.deck.pop()
        if not self.deck:
            self.shuffle()
        return card
