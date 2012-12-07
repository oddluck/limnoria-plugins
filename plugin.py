from random import choice

class CardsAgainstHumanity(object):
    def __init__(self):
        self.answerDb = ["Coat hanger abortions", "Man meat", "Autocannibalism", "Vigorous jazz hands", "Flightless birds", "Pictures of boobs", "Doing the right thing", "Hunting accidents", "A cartoon camel enjoying the smooth", "The violation of our most basic human rights", "Viagra", "Self-loathing", "Spectacular abs", "An honest cop with nothing left to lose", "Abstinence", "A balanced breakfast", "Mountain Dew Code Red", "Concealing a boner", "Roofies", "Tweeting"]

    def drawCard(self):
        hand = []
        while len(hand) < 5:
            answerCard = choice(self.answerDb)
            hand.append(answerCard)
            self.answerDb.remove(answerCard)
        return hand

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

    def displayAnswer(self)

    def cardSubmit(self):
        for player in self.playerList:
            if player !=  self.currentJudge:
                cardInput = None
                cardRange = range(5)
                while cardInput not in cardRange:
                    try:                               
                        cardInput = int(raw_input('%s Pick a Card: ' % player)) - 1
                    except: ValueError:
                        pass
            
class PlayerHand(CardsAgainstHumanity):
    def __init__(self):
        self.cardList = []

    def showHand

cah = CardsAgainstHumanity()


print cah.drawCard()
