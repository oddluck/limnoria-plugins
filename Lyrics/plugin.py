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
import re, random
import pylyrics3


try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("Weed")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Lyrics(callbacks.Plugin):
    """Retrieves song lyrics"""

    threaded = True

    def dosearch(self, irc, channel, text):
        google = None
        ddg = None
        title = None
        match = None
        if self.registryValue("google", channel) > 0:
            google = irc.getCallback("google")
            if not google:
                log.error("Lyrics: Error: Google search enabled but plugin not loaded.")
        if self.registryValue("ddg", channel) > 0:
            ddg = irc.getCallback("ddg")
            if not ddg:
                log.error("Lyrics: Error: DDG search enabled but plugin not loaded.")
        if not google and not ddg:
            log.error("Lyrics: Google and DDG plugins not loaded.")
            return None, None
        query = "site:lyrics.fandom.com/wiki/ %s" % text
        pattern = re.compile(r"https?://lyrics.fandom.com/wiki/.*")
        for i in range(1, 3):
            if match:
                break
            if google and self.registryValue("google", channel) == i:
                try:
                    results = google.decode(google.search(query, irc.network, channel))
                    for r in results:
                        try:
                            match = re.search(pattern, r["url"])
                        except TypeError:
                            match = re.search(pattern, r.link)
                        if match:
                            try:
                                title = r["title"].replace(":", " - ").split("|")[0]
                            except TypeError:
                                title = r.title.replace(":", " - ").split("|")[0]
                            log.debug(
                                "Lyrics: found link using Google search: %s"
                                % match.group(0)
                            )
                            break
                except:
                    pass
            elif self.registryValue("ddg", channel) == i:
                try:
                    results = ddg.search_core(
                        query,
                        channel_context=channel,
                        max_results=10,
                        show_snippet=False,
                    )
                    for r in results:
                        match = re.search(pattern, r[2])
                        if match:
                            title = r[0].replace(":", " - ").split("|")[0]
                            log.debug(
                                "Lyrics: found link using DDG: %s" % match.group(0)
                            )
                            break
                except:
                    pass
        if match and title:
            return title, match.group(0)
        else:
            return None, None

    def getlyrics(self, query, retries=0):
        lyrics = None
        if retries < 3:
            if "lyrics.fandom.com/wiki/" in query:
                try:
                    log.debug("Lyrics: requesting {0}".format(query))
                    lyrics = pylyrics3.get_lyrics_from_url(query)
                except Exception:
                    pass
            else:
                try:
                    log.debug("Lyrics: requesting {0}".format(query))
                    query = query.split(",", 1)
                    lyrics = pylyrics3.get_song_lyrics(
                        query[0].strip(), query[1].strip()
                    )
                except Exception:
                    pass
            if lyrics:
                lyrics = re.sub(r"(?<!\.|\!|\?)\s+\n", ".", lyrics)
                lyrics = re.sub(r"\s+\n", "", lyrics)
                return lyrics
            else:
                self.getLyrics(query, retries + 1)
        else:
            log.info("Lyrics: maximum number of retries (3) reached.")
        return

    def lyric(self, irc, msg, args, lyric):
        """<query>
        Get song lyrics from Lyrics Wiki.
        """
        title = None
        url = None
        title, url = self.dosearch(irc, msg.channel, lyric)
        if url and title and "lyrics.fandom.com/wiki/" in url:
            try:
                lyrics = self.getlyrics(url)
                if lyrics:
                    irc.reply(title + " | " + lyrics, prefixNick=False)
                else:
                    irc.reply("Unable to retrieve lyrics from {0}".format(url))
                    return
            except Exception:
                irc.reply("Unable to retrieve lyrics from {0}".format(url))
                return
        else:
            if "," in lyric:
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

    lyric = wrap(lyric, ["text"])
    lyrics = lyric


Class = Lyrics
