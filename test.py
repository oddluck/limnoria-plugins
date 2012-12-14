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
            test_card(card)

def test_game():
    game = Game(['Bear','Swim', 'Jazz'])
    test_cards_will_be_unique(deck=game.deck, player_list= game.players)
    for player in game.players.keys():
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
        assert bot_gets.has_key('question')
        assert game.has_key('question')
        assert bot_gets.has_key('hands')
        test_end_round(game)

def build_end_round_data(game):
    winner = choice(game.players.keys())
    cards_played = {}
    #Get random cards from player's hand to satisfy the question card
    for player in game.players.keys():
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
    for player in game.players.keys():
        assert len(game.players[player].card_list) == 5
        if isinstance(fake_end_round['cards_played'][player], Card):
            fake_end_round['cards_played'][player] = list(fake_end_round['cards_played'][player])
        for card in fake_end_round['cards_played'][player]:
            assert card not in game.players[player].card_list
    assert game.score.has_key(fake_end_round['winner'])


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
