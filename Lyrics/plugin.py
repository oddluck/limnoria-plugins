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
        try:
            searchurl = "https://www.google.com/search?&q={0} site:lyrics.wikia.com/wiki \"Lyrics\"".format(lyric)
            ua = UserAgent()
            header = {'User-Agent':str(ua.random)}
            data = requests.get(searchurl, headers=header)
            soup = BeautifulSoup(data.text)
            elements = soup.select('.r a')
            url = elements[0]['href']
            url = re.split('https?://', url)[-1]
            url = re.sub("&rct=.*", "", url)
            url = "https://{0}".format(url)
            title = soup.find("h3").getText()
        except Exception:
            return
        else:
            return title, url

    def getlyrics(self, url):
        try:
            lyrics = pylyrics3.get_lyrics_from_url(url)
            lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
        except Exception:
            lyrics = pylyrics3.get_lyrics_from_url(url)
            lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
        else:
            return lyrics

    def lyric(self, irc, msg, args, lyric):
        """<text>
        Get song lyrics from Lyrics Wiki. Search powered by Google.
        """
        try:
            title, url = self.dosearch(lyric)
        except Exception:
            irc.reply("No results found for {0}".format(lyric))
        else:
            try:
                lyrics = self.getlyrics(url)
                irc.reply(title.replace(":", " - "))
                irc.reply(lyrics)
            except Exception:
                irc.reply("Unable to retrieve lyrics from {0}".format(url))
    lyric = wrap(lyric, ['text'])

Class = Lyrics
