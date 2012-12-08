__author__ = 'Bear'

from plugin import *

def test_cards_will_be_unique():
    """
    Ensure that when a hand is created the proper cards are removed from the deck.
    """
    deck=CardsAgainstHumanity()
    hand_one = PlayerHand(deck)
    for card in hand_one.cardList:
        assert card.cardText not in deck.answerDb
