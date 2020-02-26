###
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.log as log
from bs4 import BeautifulSoup
import requests
import re
import pylyrics3
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse, quote_plus

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
            url = None
            title = None
            searchurl = "https://www.google.com/search?&q="
            searchurl += quote_plus("{0} site:lyrics.fandom.com/wiki/".format(lyric))
            ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
            header = {'User-Agent':str(ua.random)}
            data = requests.get(searchurl, headers=header, timeout=10)
            data.raise_for_status()
            soup = BeautifulSoup(data.text)
            elements = soup.select('.r a')
            title = soup.find("h3").getText().replace(":", " - ").split('|')[0]
            url = urljoin(elements[0]['href'], urlparse(url).path)
        except Exception:
            pass
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
        title, url = self.dosearch(lyric)
        if not title or not url:
            irc.reply("No results found for {0}".format(lyric))
        else:
            try:
                lyrics = self.getlyrics(url)
                irc.reply(title)
                irc.reply(lyrics)
            except Exception:
                irc.reply("Unable to retrieve lyrics from {0}".format(url))
    lyric = wrap(lyric, ['text'])

Class = Lyrics
