###
# Copyright (c) 2012, James Scott
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
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

__author__ = 'Bear'

from .cah import *

def test_cards_will_be_unique(deck=None, player_list = None):
    """
    Ensure that when a hand is created the proper cards are removed from the deck.
    """
    if deck is None:
        deck=Deck()
    if player_list is None:
        player_list = {'one': PlayerHand(deck),'two': PlayerHand(deck) }
    for value in list(player_list.values()):
        for card in value.card_list:
            assert card.text not in deck.answerDb

def test_card_parsing(deck=None):
    """
    This test checks that the cards in a deck are correctly built Card objects
    """
    if deck is None:
        deck = Deck()
    for deck_type in [deck.answerDb, deck.questionDb]:
        for card in deck_type:
            test_card(card)

def test_game():
    game = Game(['Bear','Swim', 'Jazz'])
    test_cards_will_be_unique(deck=game.deck, player_list= game.players)
    for player in list(game.players.keys()):
        hand = game.players[player]
        test_player_hand(hand)
    test_round_advancement(game)



def test_round_advancement(game=None):
    if game is None:
        game = Game(['Bear','Swim', 'Jazz'])
    assert game.round is None
    assert game.question is None
    while round < game.round_limit:
        bot_gets = game.next_round()
        assert isinstance(bot_gets, dict)
        assert 'question' in bot_gets
        assert 'question' in game
        assert 'hands' in bot_gets
        test_end_round(game)

def build_end_round_data(game):
    winner = choice(list(game.players.keys()))
    cards_played = {}
    #Get random cards from player's hand to satisfy the question card
    for player in list(game.players.keys()):
        player_cards = game.players[player].card_list[:game.question.answers]
        cards_played[player] = player_cards #player_cards is a deque object -> tuple(list,maxlen)
    return {'winner': winner, 'cards_played': cards_played}

def test_end_round(game=None):
    if game is None:
        game = Game(['Bear','Swim', 'Jazz'])
        game.next_round()
        game.question.answers = 2
    fake_end_round = build_end_round_data(game)
    game.end_round(fake_end_round['winner'],fake_end_round['cards_played'])
    for player in list(game.players.keys()):
        assert len(game.players[player].card_list) == 5
        if isinstance(fake_end_round['cards_played'][player], Card):
            fake_end_round['cards_played'][player] = list(fake_end_round['cards_played'][player])
        for card in fake_end_round['cards_played'][player]:
            assert card not in game.players[player].card_list
    assert fake_end_round['winner'] in game.score


def test_player_hand(hand=None):
    if hand is None:
        hand = PlayerHand(Deck())
    assert type(hand) is PlayerHand
    for count, card in enumerate(hand.card_list):
        assert count < 5
        assert type(card) is Card

def test_card(card=None):
    if card is None:
        card = Deck().drawCard('question')
    assert type(card) is Card
    assert type(card.id) is int
    assert type(card.type) is str
    assert card.type in ['answer', 'question']
    assert  type(card.text) is str
    assert card.text.find('\n') is -1
    if card.type is 'question':
        assert type(card.answers) is int
