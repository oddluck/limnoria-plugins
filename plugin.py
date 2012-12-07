from random import choice

class CardsAgainstHumanity(object):
    def __init__(self):
        self.answerDb = ["Coat hanger abortions", "Man meat", "Autocannibalism", "Vigorous jazz hands", "Flightless birds", "Pictures of boobs", "Doing the right thing", "Hunting accidents", "A cartoon camel enjoying the smooth", "The violation of our most basic human rights", "Viagra", "Self-loathing", "Spectacular abs", "An honest cop with nothing left to lose", "Abstinence", "A balanced breakfast", "Mountain Dew Code Red", "Concealing a boner", "Roofies", "Tweeting"]
        self.questionDb = ["Who is foo?"]
    def drawCard(self, typeOfCard):
        typeMap = {'answer': self.answerDb, 'question': self.questionDb}
        cardType = typeMap[typeOfCard]
        cardText = choice(cardType)
        cardType.remove(cardText)
        card = Card(1, typeOfCard, cardText)
        return card

class Card(object):
    def __init__(self, cardId, cardType, cardText):
        self.cardId = cardId
        self.cardType = cardType
        self.cardText = cardText

class GameRound(CardsAgainstHumanity):
    def __init__(self):
        self.playerOne = str(raw_input('Player 1 Name: '))
        self.playerTwo = str(raw_input('Player 2 Name: '))
        self.playerThree = str(raw_input('Player 3 Name: '))
        self.playerFour = str(raw_input('Player 4 Name: '))
        self.playerList = (playerOne, playerTwo, playerThree, playerFour)
        self.availJudge = playerList
        self.spentJudge = ()
        self.currentJudge = playerOne

    def round(self):
        print "%s is Judging!" % currentJudge
        print "Question Card: %s" % questionCard
        cardSubmit()
        displayAnswers()

    def displayAnswer(self):
        pass

    def cardSubmit(self):
        for player in self.playerList:
            if player !=  self.currentJudge:
                cardInput = None
                cardRange = range(5)
                while cardInput not in cardRange:
                    try:                               
                        cardInput = int(raw_input('%s Pick a Card: ' % player)) - 1
                    except ValueError:
                        pass
            
class PlayerHand(object):
    def __init__(self, deck):
        self.deck = deck
        self.cardList = self.dealHand()

    def dealHand(self):
        hand = []
        while len(hand) < 5:
            card = self.deck.drawCard('answer')
            hand.append(card)
        return hand
            
    def showHand(self):
        for index, card in enumerate(self.cardList):
            print '%s: %s' % (index + 1, card.cardText)



if __name__=="__main__":
    cah = CardsAgainstHumanity()
    print cah.drawCard('answer').cardText
    jazz_hand = PlayerHand(cah)
    bear_hand = PlayerHand(cah)
    print "Bear's hand:"
    bear_hand.showHand()
    print "\nJazz's hand"
    jazz_hand.showHand()

