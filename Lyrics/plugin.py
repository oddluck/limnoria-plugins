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
import random

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
            searchurl += "{0} site:lyrics.fandom.com/wiki/".format(lyric)
            agents = self.registryValue("userAgents")
            ua = random.choice(agents)
            header = {'User-Agent': ua}
            data = requests.get(searchurl, headers=header, timeout=10)
            data.raise_for_status()
            log.debug(data.content.decode())
            soup = BeautifulSoup(data.content)
            elements = soup.select('.r a')
            title = soup.find("h3").getText().replace(":", " - ").split('|')[0]
            url = elements[0]['href']
        except Exception:
            pass
        return title, url

    def getlyrics(self, query):
        lyrics = None
        if 'lyrics.fandom.com/wiki/' in query:
            try:
                log.debug("Lyrics: requesting {0}".format(query))
                lyrics = pylyrics3.get_lyrics_from_url(query)
                lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
            except Exception:
                pass
        else:
            try:
                log.debug("Lyrics: requesting {0}".format(query))
                query = query.split(',', 1)
                lyrics = pylyrics3.get_song_lyrics(query[0].strip(), query[1].strip())
                lyrics = re.sub('(?<!\.|\!|\?)\s\\n', '.', lyrics).replace(" \n", "")
            except Exception:
                pass
        return lyrics

    def lyric(self, irc, msg, args, lyric):
        """<query>
        Get song lyrics from Lyrics Wiki.
        """
        channel = msg.channel
        title = None
        url = None
        if self.registryValue("googleSearch", channel):
            title, url = self.dosearch(lyric)
        if url and title and 'lyrics.fandom.com/wiki/' in url:
            try:
                lyrics = self.getlyrics(url)
                if lyrics:
                    irc.reply(title, prefixNick=False)
                    irc.reply(lyrics, prefixNick=False)
                else:
                    irc.reply("Unable to retrieve lyrics from {0}".format(url))
                    return
            except Exception:
                irc.reply("Unable to retrieve lyrics from {0}".format(url))
                return
        else:
            if ',' in lyric:
                try:
                    lyrics = self.getlyrics(lyric)
                    if lyrics:
                        irc.reply(lyrics, prefixNick=False)
                    else:
                        irc.reply("Unable to retrieve lyrics for {0}".format(lyric))
                        return
                except Exception:
                    irc.reply("Unable to retrieve lyrics for {0}".format(lyric))
                    return
            else:
                irc.reply("Searches must be formatted as <artist>, <song title>")
                return
    lyric = wrap(lyric, ['text'])

Class = Lyrics
