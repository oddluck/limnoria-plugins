from random import choice

class CardsAgainstHumanity:

	__init__(self)
	self.answerDb = ["Coat hanger abortions", "Man meat", "Autocannibalism", "Vigorous jazz hands", "Flightless birds", "Pictures of boobs", "Doing the right thing", "Hunting accidents", "A cartoon camel enjoying the smooth", "The violation of our most basic human rights", "Viagra", "Self-loathing", "Spectacular abs", "An honest cop with nothing left to lose", "Abstinence", "A balanced breakfast", "Mountain Dew Code Red", "Concealing a boner", "Roofies", "Tweeting"]

	def drawCard(self):
		hand = []
		while len(hand) < 5:
			answerCard = choice(self.answerDb)
			hand.append(answerCard)
			self.answerDb.remove(answerCard)	
		return hand

print drawCard()
