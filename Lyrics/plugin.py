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
from bs4 import BeautifulSoup
import requests
import re
import pylyrics3
from fake_useragent import UserAgent

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
        searchurl = "https://www.google.com/search?&q={0} site:lyrics.wikia.com/wiki \"Lyrics\"".format(lyric)
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        data = requests.get(searchurl, headers=header)
        soup = BeautifulSoup(data.text)
        url = soup.find('cite').getText()
        title = soup.find("h3").getText()
        url = "http://{0}".format(url)
        return title, url

    def getlyrics(self, url):
        lyrics = pylyrics3.get_lyrics_from_url(url)
        lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
        return lyrics

    def lyric(self, irc, msg, args, lyric):
        """<text>
        Get song lyrics from Lyrics Wiki. Search powered by Google.
        """
        title, url = self.dosearch(lyric)
        if url:
            lyrics = self.getlyrics(url)
            irc.reply(title.replace(":", " - "))
            irc.reply(lyrics)
        else:
            irc.reply("No lyrics found... or some other error.")
    lyric = wrap(lyric, ['text'])

Class = Lyrics

