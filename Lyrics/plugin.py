###
# Copyright (c) 2019 oddluck
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import re
import pylyrics3

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weed')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Lyrics(callbacks.Plugin):
    """Retrieves song lyrics"""
    threaded = True

    def lyric(self, irc, msg, args, lyric):
        """<text>
        Get song lyrics from Lyrics Wiki. Format searches as artist, song name
        """
        if ',' in lyric:
            lyric = lyric.split(',')
        else:
            irc.reply("Lyric searches must be formatted as artist, song name")
            return
        lyrics = pylyrics3.get_song_lyrics(lyric[0].strip(), lyric[1].strip())
        if lyrics and lyrics != 'None':
            lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
            irc.reply(lyrics)
        else:
            irc.reply("No results found")
    lyric = wrap(lyric, ['text'])

Class = Lyrics
