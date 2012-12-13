__author__ = 'Bear'

from cah import *

def test_cards_will_be_unique(deck=None, player_list = None):
    """
    Ensure that when a hand is created the proper cards are removed from the deck.
    """
    if deck is None:
        deck=Deck()
    if player_list is None:
        player_list = {'one': PlayerHand(deck),'two': PlayerHand(deck) }
    for value in player_list.values():
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
            assert type(card) is Card
            assert type(card.id) is int
            assert type(card.type) is str
            assert card.type in ['answer', 'question']
            assert  type(card.text) is str
            assert card.text.find('\n') is -1
            if card.type is 'question':
                assert type(card.answers) is int

def test_game():
    game = Game(['Bear','Swim', 'Jazz'])
    test_cards_will_be_unique(deck=game.deck, player_list= game.players)
    for player in game.players.keys():
        hand = game.players[player]
        test_player_hand(hand)


def test_player_hand(hand=None):
    if hand is None:
        hand = PlayerHand(Deck())
    assert type(hand) is PlayerHand
    for count, card in enumerate(hand.card_list):
        assert count < 5
        assert type(card) is Card
