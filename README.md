Supybot Word Games Plugin
=========================

This is a plugin for the popular IRC bot Supybot that implements a few
word games to play in your IRC channel.

Typical installation process:

1. Clone this git repository in your downloads directory.
2. Create a symlink called `Wordgames` in supybot/plugins pointing to it.
3. In IRC, load Wordgames.

**Note:** These games rely on a dictionary file (not included).  On
Ubuntu, you can normally just install the `wamerican` package.  See
the Configurable Variables section to customize.

Commands
--------

The following commands are exposed by this plugin:

`worddle [easy|medium|hard|evil | stop|stats]`

> Play a Worddle game.  With no argument, a new game will start with the
> default difficulty (see worddleDifficulty in the Configuration section).
> If a game is already started, you will join the game in progress.
>
> In addition, you may use the following subcommands:
>
>     easy     minimum acceptable word length: 3 (overrides config)
>     medium   minimum acceptable word length: 4      "       "
>     hard     minimum acceptable word length: 5      "       "
>     evil     minimum acceptable word length: 6      "       "
>     stop     Stop a currently running game (alias for @wordquit)
>     stats    Display some post-game statistics about the board

`wordshrink [difficulty]`

> Start a new WordShrink game.  Difficulty values: easy [medium] hard evil

`wordtwist [difficulty]`

> Start a new WordTwist game.  Difficulty values: easy [medium] hard evil

`wordquit`

> Shut down any currently running game. One solution will be displayed for
> the word chain games, to satisfy your curiosity.

Game Rules
----------

### Worddle

Worddle is a clone of a well-known puzzle game involving a 4x4 grid of
randomly-placed letters.  It's a timed, multiplayer game where you compete
to find words that your opponents didn't find.

When you start a new game, or join an existing game, the bot will send you a
private message indicating that you are playing.  All your guesses must be
sent to the bot in this private conversation, so your opponents can't see your
guesses.  At the end of the game, the results will be presented in the channel
where the game was started.

To be a valid guess, words must:

* be made of adjacent letters on the board (in all 8 directions, diagonals ok)
* be at least 3 letters in length (or 4, or 5, etc. depending on the level)
* appear in the dictionary file.

At the end of the game, if a word was found by multiple players, it is not
counted.  The remaining words contribute to your score using these values:

     Length | Value
    --------+-------
      3, 4  | 1 point
      5     | 2 points
      6     | 3 points
      7     | 5 points
      8+    | 11 points

### WordShrink

WordShrink and WordTwist are word chain (or word ladder) style games.
A puzzle will be presented in the form:

    word1 > --- > --- > word4

... and your job is to come up with a response of the form `word2 > word3`
that completes the puzzle.  (You can optionally include the start and end
words in your response, as long as each word is separated by a greater-than
sign.)

In WordShrink, each word must be made by removing one letter from the
preceding word and rearranging the letters to form a new word.  Example
session:

    <mike> @wordshrink
    <supybot> WordShrink: lights > ----- > ---- > sit
    <supybot> (12 possible solutions)
    <mike> sight > this
    <supybot> WordShrink: mike got it!
    <supybot> WordShrink: lights > sight > this > sit
    <ben> lights > hilts > hits > sit
    <supybot> ben: Your solution is also valid.

### WordTwist

WordTwist is very similar to WordShrink, except that the way you manipulate
the words to solve the puzzle is changed.  In WordTwist, you change exactly
one letter in each successive word to form a new word (no rearranging is
allowed).  Example session:

    <mike> @wordtwist medium
    <supybot> WordTwist: mass > ---- > ---- > ---- > jade
    <supybot> (5 possible solutions)
    <mike> mars > mare > made
    <supybot> WordTwist: mike got it!
    <supybot> WordTwist: mass > mars > mare > made > jade

Configuration Variables
-----------------------

`plugins.Wordgames.wordFile`

> Path to the dictionary file.
>  
> Default: `/usr/share/dict/american-english`

`plugins.Wordgames.wordRegexp`

> A regular expression defining what a valid word looks like.  This will
> be used to filter words from the dictionary file that contain undesirable
> characters (proper names, hyphens, accents, etc.).  You will probably have
> to quote the string when setting, e.g.:
>
>     @config plugins.Wordgames.wordRegexp "^[a-x]+$"
>
> (No words containing 'y' or 'z' would be allowed by this.)
>
> Default: `^[a-z]+$`

`plugins.Wordgames.worddleDelay`

> The length (in seconds) of the pre-game period where players can join a
> new Worddle game.
>
> Default: `15`

`plugins.Wordgames.worddleDuration`

> The length (in seconds) of the active period of a Worddle game, when
> players can submit guesses.
>
> Default: `90`

`plugins.Wordgames.worddleDifficulty`

> The default difficulty for a Worddle game.
>
> Default: `easy` (words must be 3 letters or longer)

A Technical Note About Worddle
------------------------------

This game sends a lot of PRIVMSGs (between the channel and all the players,
the messages add up).  It attempts to send them in a single PRIVMSG if
possible to combine targets.

Supybot: I run Supybot with the latest git (there are show-stopper bugs in
0.83.4.1) and the Twisted driver (but Socket should work as well).

IRC Server: I had to tune my IRC server to handle this game, due to the large
amount of messages it sends.  You may find that it has problems on your server
due to flood controls (bot may be either fake lagged or kicked from the
server).  If the game seems extremely slow, it is either an old Supybot or the
server is throttling you.

I would like to add an option to tune the verbosity of the game to mitigate
this for restrictive servers.

Credit
------

Copyright 2012 Mike Mueller <mike@subfocal.net>
Released under the WTF public license: http://sam.zoy.org/wtfpl/

Thanks to Ben Schomp <ben@benschomp.com> for the inspiration and QA testing.
