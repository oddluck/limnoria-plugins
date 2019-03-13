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
from gsearch.googlesearch import search
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

    def dosearch(self, lyric):
        data = search("{0} site:lyrics.wikia.com/wiki/".format(lyric))
        try:
            title, url = data[0]
            return title, url
        except:
            pass

    def getlyrics(self, url):
        lyrics = pylyrics3.get_lyrics_from_url(url)
        return lyrics

    def lyric(self, irc, msg, args, lyric):
        """<text>
        Get song lyrics from Lyrics Wiki. Search powered by Google.
        """
        retries = 0
        url = None
        while not url and retries <= 3:
            try:
                title, url = self.dosearch(lyric)
            except:
                retries += 1
        if url:
            lyrics = self.getlyrics(url)
            irc.reply(title.replace(":", " - "))
            irc.reply(lyrics.replace(" \n", ".").replace("\\", ""))
        else:
            irc.reply("No lyrics found... or some other error.")
    lyric = wrap(lyric, ['text'])

Class = Lyrics

