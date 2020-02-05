**Come play in ##Jeopardy on Freenode.**

irc://chat.freenode.net/##jeopardy


## This... is... Jeopardy!

Uses [jService](http://jservice.io) (150K+ Jeopardy! questions, more if run locally) as a trivia source.

To run a local instance (190K+ questions, can add more questions as episodes continue to air) install [my jService fork](https://github.com/oddluck/jService) then point `plugins.jeopardy.jserviceUrl` to your own URL.


## Commands

```
start [--num <int>] [--shuffle] [--no-hints] [--random-category] [category1, category2, etc,]
```
Calling the `start` command by itself will yield a round of random questions. Adding category names after the start command will search for specific categories by name. The `--random-category` option will return questions from a randomly selected category. Calling `start` while a game is running will add additional questions to the queue. Use `--shuffle` to randomize question order. Use `--no-hints` to disable hints for the round.

```
categories
```
Returns a list of popular Jeopardy! categories.

```
stats [--top <int>] [nick]
```
Returns game scores. Defaults to top 5 players. Use `--top` and a number to receive more top players. Specify a nick to get a score for the selected player.

```
question
```
Repeat the currently active question.

```
hint
```
Repeat the current hint.


## Config

```
config list plugins.jeopardy
```
List the config variables for the game.

```
config help plugins.jeopardy.<variable_name>
```
Get information about what game options the variable controls.


## Miscellaneous

Score and history files can be found in <bot_directory>/data/jeopardy/

Forked and significantly modified version of [this trivia plugin](https://github.com/ProgVal/Supybot-plugins/tree/master/Trivia).
