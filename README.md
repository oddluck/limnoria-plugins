This plugin will be a feature packed trivia script for [Supybot][] in the future. Developers will need to refer to [TriviaTime][] for more information.
This plugin has been started but is not finished. For developers use only. Not ready for use.

# Plans
## Main Priority

* require minimum amount of points for autovoice

* New Style design

* allow shuffling of questions

* move databases to inside the TriviaTime plugin folder

* when reaching the end of questions, restart the question numbers per [Concept][] page

* extra points for streaks

* We plan on keeping track of players’ scores by their usernames. Should they want to change usernames and keep their scores, they will need to register to the bot. Supybots are already capable of keeping track of users across nicknames and hosts (per owner’s configuration)

* Store question in an SQL file. Create a system of assigning number to the question. That question number will only be used for reporting and when the question is displayed by the bot. If the question is reported, it will be assigned a new number for reporting. When edited, it will use the new report number.

* create live PHP website showing scores and to track reports

and much more, based off of BogusTrivia and Trivia (supybot plugin)

  [TriviaTime]: http://trivialand.org/triviatime/
  [Supybot]: http://sourceforge.net/projects/supybot/
  [Concept]: http://trivialand.org/triviatime/concept/
