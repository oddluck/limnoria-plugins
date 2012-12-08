__author__ = 'Bear'

from plugin import *

def test_cards_will_be_unique():
    """
    Ensure that when a hand is created the proper cards are removed from the deck.
    """
    deck=Deck()
    hand_one = PlayerHand(deck)
    for card in hand_one.cardList:
        assert card.text not in deck.answerDb

def test_card_parsing():
    deck = Deck()
    for card in deck.answerDb:
        assert type(card) is Card
        assert type(card.id) is int
        assert type(card.type) is str
        assert card.type in ['answer', 'question']
        assert  type(card.text) is str
