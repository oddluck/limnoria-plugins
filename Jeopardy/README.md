[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=T8E56M6SP9JH2)

**Come play in ##Jeopardy on Freenode.**

irc://chat.freenode.net/##jeopardy


## This... is... Jeopardy!

Uses [jService](http://jservice.io) (150K+ Jeopardy! questions, more if run locally) as a trivia source.

To run a local instance (190K+ questions, can add more questions as episodes continue to air) install [my jService fork](https://github.com/oddluck/jService) then point `plugins.jeopardy.jserviceUrl` to your own URL.


## Commands

```
start [channel] [--num <#>] [--timeout <#>] [--hints <#>] [--no-hints] [--random] [--shuffle] [--restart] [<category1>, <category2>, etc.]
```
`start` - start a round with random questions

`start <category name>, <category name>` - search for a category by name, separate multiple categories with commas

`--shuffle` - randomize category searches

`--num <# of questions>` - set the number of questions for the round

`--timeout <# of seconds to answer>` - set the time to answer the question, 0 to disable timeout

`--hint <# of hints>` - specify number of hints, 0 to disable them

`--no-hints` - set showHints and showBlank to False

`--random` - select a category at random

`--restart` - automatically restart a new round when the current round finishes (questions in restarted rounds will be random)

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
Repeat the current hint. If game set for no hints, show blanked out answer. If timeout disabled reveal the next hint.

```
skip
```
Skip the current question.

```
report
```
Report the current question as invalid e.g. audio/video based clues.


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
