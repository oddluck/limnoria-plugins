**Come play in ##Jeopardy on Freenode.**

irc://chat.freenode.net/##jeopardy


## This... is... Jeopardy!

Uses [jService](http://jservice.io) (150K+ Jeopardy! questions, more if run locally) as a trivia source.

To run a local instance (190K+ questions, can add more questions as episodes continue to air) install [my jService fork](https://github.com/oddluck/jService) then point `plugins.jeopardy.jserviceUrl` to your own URL.

To configure replies, see the [templates](#templates) section.


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
^ Returns a list of popular Jeopardy! categories.

```
stats [--top <int>] [nick]
```
^ Returns game scores. Defaults to top 5 players. Use `--top` and a number to receive more top players. Specify a nick to get a score for the selected player.

```
question
```
^ Repeat the currently active question.

```
hint
```
^ Display the next hint. If max hints reached, repeat the latest hint. If max hints is 0, show blanked out answer.

```
skip
```
^ Skip the current question.

```
report
```
^ Report the current question as invalid e.g. audio/video based clues.


## Config

```
config list plugins.jeopardy
```
^ List the config variables for the game.

```
config help plugins.jeopardy.<variable_name>
```
^ Get information about what game options the variable controls.

```
config [channel #channel] plugins.jeopardy.blankChar *
```
^ The character used for a blank when displaying hints

```
config [channel #channel] plugins.jeopardy.numHints 3
```
^ The number of hints to be given for each question

```
config [channel #channel] plugins.jeopardy.delay 4
```
^ The number of seconds to delay between questions

```
config [channel #channel] plugins.jeopardy.timeout 90
```
^ The number of seconds to allow for each question

```
config [channel #channel] plugins.jeopardy.hintPercentage 0.25
```
^ The fraction of the answer that should be revealed with each hint

```
config [channel #channel] plugins.jeopardy.hintReduction 0.5
```
^ The percentage by which to reduce points with each hint reveal

```
config [channel #channel] plugins.jeopardy.flexibility 0.94
```
^ The minimum similarity score of the answer checker. Uses jaro-winkler distance, 1.0 is identical/disabled. (Sane values > 0.90)

```
config [channel #channel] plugins.jeopardy.inactiveShutoff 5
```
^ The number of questions that can go unanswered before the game stops automatically

```
config plugins.jeopardy.jserviceUrl http://jservice.io
```
^ Set an alternate URL where jservice can be accessed at, for example a locally run jservice instance: http://127.0.0.1:3000

```
config [channel #channel] plugins.jeopardy.defaultRoundLength 10
```
^ The default number of questions to be asked in a round

```
config [channel #channel] plugins.jeopardy.randomize True
```
^ This will determine whether or not the bot will randomize the questions

```
config [channel #channel] plugins.jeopardy.requireOps False
```
^ This will determine whether or not the user must be a channel operator to start/stop the game

```
config [channel #channel] plugins.jeopardy.enabled True
```
^ This will determine whether or not the game is enabled for a given channel

```
config [channel #channel] plugins.jeopardy.defaultPointValue 500
```
^ The default point value for questions if no point value is given

```
config [channel #channel] plugins.jeopardy.autoRestart False
```
^ Start a new round of random questions after the current round has ended

```
config [channel #channel] plugins.jeopardy.keepHistory True
```
^ Keep a history of previously asked questions and don't repeat them

```
config [channel #channel] plugins.jeopardy.useBold True
```
^ Use bold in replies

```
config [channel #channel] plugins.jeopardy.showScores True
```
^ Show scores at the end of the round

```
config [channel #channel] plugins.jeopardy.showBlank True
```
^ Show first (blank) hint with the question. Overrides showHints only for this reply

```
config [channel #channel] plugins.jeopardy.showTime True
```
^ Show time remaining messages when not showing hints

```
config [channel #channel] plugins.jeopardy.showHints True
```
^ Show hint messages automatically. Overrides showTime


## Templates

```
config list plugins.jeopardy.template
```
^ List the config variables for the templates.

```
config help plugins.jeopardy.template.<variable_name>
```
^ Get information about what template the variable controls.

```
config [channel #channel] plugins.jeopardy.template.correct "\x0313{{nick}}\x03 got it! The full answer was: {{answer}}. Points: \x0309{{points}}\x03 | Round Score: \x0309{{round}}\x03 | Total: \x0309{{total}}"
```
^ Template for correct answer replies

```
config [channel #channel] plugins.jeopardy.template.hint "HINT: {{hint}}{% if time %} | ({{time}} seconds remaining){% endif %}"
```
^ Template for hint reply

```
config [channel #channel] plugins.jeopardy.template.question "#{{number}} of {{total}}: \x0313({{airdate}}) \x0309[${{points}}] \x0310\x1f{{category}}\x1f: {{clue}}"
```
^ Template for question reply

```
config [channel #channel] plugins.jeopardy.template.skip "No one got the answer! It was: {{answer}}"
```
^ Template for reply when question unanswered after timeout or the 'skip' command used

```
config [channel #channel] plugins.jeopardy.template.stop "Jeopardy! stopped.{% if answer %} (Answer: {{answer}}){% endif %}"
```
^ Template for reply when using the 'stop' command

```
config [channel #channel] plugins.jeopardy.template.time "{{time}} seconds remaining. [.hint] [.question] [.skip]"
```
^ Template for time remaining reply when plugins.jeopardy.showTime = True



## Miscellaneous

Score and history files can be found in <bot_directory>/data/jeopardy/

Forked and significantly modified version of [this trivia plugin](https://github.com/ProgVal/Supybot-plugins/tree/master/Trivia).
