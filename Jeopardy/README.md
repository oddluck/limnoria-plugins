Come play in ##Jeopardy on Freenode. irc://chat.freenode.net/##Jeopardy



Fork of Trivia (https://github.com/ProgVal/Supybot-plugins/tree/master/Trivia) with option to use jservice.io (150K+ Jeopardy! questions, more if run locally) as trivia source plus additional features such as category selection, question history, and improved scoring and answer checking.

To run a local instance (385K+ questions) install my jservice fork from here https://github.com/oddluck/jService then point `plugins.jeopardy.jserviceUrl` to your own URL.

```
start --num (int) <category> (optionally specify number of questions or category name or ID#)
```
calling start a second time will add additional questions to the queue.
```
categories | return a list of popular Jeopardy! categories and their IDs
```
