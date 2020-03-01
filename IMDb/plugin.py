###
# Copyright (c) 2015, butterscotchstallion
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
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import supybot.log as log
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('IMDb')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class IMDb(callbacks.Plugin):
    """Queries OMDB database for information about IMDb titles"""
    threaded = True

    def dosearch(self, query):
        try:
            url = None
            searchurl = "https://www.google.com/search?&q="
            searchurl += quote_plus("{0} site:imdb.com/title/".format(query))
            ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
            header = {'User-Agent':str(ua.random)}
            data = requests.get(searchurl, headers=header, timeout=10)
            data.raise_for_status()
            soup = BeautifulSoup(data.content)
            elements = soup.select('.r a')
            url = urljoin(elements[0]['href'], urlparse(url).path)
        except Exception:
            pass
        return url

    def imdb(self, irc, msg, args, query):
        """<title>
        Queries the OMDB api about an IMDb title.
        """
        channel = msg.channel
        url = None
        result = None
        apikey = self.registryValue('omdbAPI')
        if self.registryValue("googleSearch", channel):
            url = self.dosearch(query)
        if url and 'imdb.com/title/' in url:
            imdb_id = url.split("/title/")[1].rstrip("/")
            omdb_url = "http://www.omdbapi.com/?i=%s&plot=short&r=json&apikey=%s" % (imdb_id, apikey)
            log.debug("IMDb: requesting %s" % omdb_url)
        else:
            omdb_url = "http://www.omdbapi.com/?t=%s&plot=short&r=json&apikey=%s" % (query, apikey)
        try:
            request = requests.get(omdb_url, timeout=10)
            if request.status_code == requests.codes.ok:
                response = request.json()
                not_found = "Error" in response
                unknown_error = response["Response"] != "True"
                if not_found or unknown_error:
                    log.debug("IMDb: OMDB error for %s" % (omdb_url))
                else:
                    meta = None
                    tomato = None
                    imdb_template = self.registryValue("template", channel)
                    imdb_template = imdb_template.replace("$title", response["Title"])
                    imdb_template = imdb_template.replace("$year", response["Year"])
                    imdb_template = imdb_template.replace("$country", response["Country"])
                    imdb_template = imdb_template.replace("$director", response["Director"])
                    imdb_template = imdb_template.replace("$plot", response["Plot"])
                    imdb_template = imdb_template.replace("$imdbID", response["imdbID"])
                    imdb_template = imdb_template.replace("$imdbRating", response["imdbRating"])
                    for rating in response["Ratings"]:
                        if rating["Source"] == "Rotten Tomatoes":
                            tomato = rating["Value"]
                        if rating["Source"] == "Metacritic":
                            meta = "{0}%".format(rating["Value"].split('/')[0])
                    if meta:
                        imdb_template = imdb_template.replace("$metascore", meta)
                    else:
                        imdb_template = imdb_template.replace("$metascore", "N/A")
                    if tomato:
                        imdb_template = imdb_template.replace("$tomatoMeter", tomato)
                    else:
                        imdb_template = imdb_template.replace("$tomatoMeter", "N/A")
                    imdb_template = imdb_template.replace("$released",response["Released"])
                    imdb_template = imdb_template.replace("$genre",response["Genre"])
                    imdb_template = imdb_template.replace("$released",response["Released"])
                    imdb_template = imdb_template.replace("$awards",response["Awards"])
                    imdb_template = imdb_template.replace("$actors",response["Actors"])
                    imdb_template = imdb_template.replace("$rated",response["Rated"])
                    imdb_template = imdb_template.replace("$runtime",response["Runtime"])
                    imdb_template = imdb_template.replace("$writer",response["Writer"])
                    imdb_template = imdb_template.replace("$votes",response["imdbVotes"])
                    imdb_template = imdb_template.replace("$boxOffice",response["BoxOffice"])
                    imdb_template = imdb_template.replace("$production",response["Production"])
                    imdb_template = imdb_template.replace("$website",response["Website"])
                    imdb_template = imdb_template.replace("$poster",response["Poster"])
                    result = imdb_template
            else:
                log.error("IMDb OMDB API %s - %s" % (request.status_code, request.content.decode()))
        except requests.exceptions.Timeout as e:
            log.error("IMDb Timeout: %s" % (str(e)))
        except requests.exceptions.ConnectionError as e:
            log.error("IMDb ConnectionError: %s" % (str(e)))
        except requests.exceptions.HTTPError as e:
            log.error("IMDb HTTPError: %s" % (str(e)))
        finally:
            if result is not None:
                irc.reply(result, prefixNick=False)
            else:
                irc.error(self.registryValue("noResultsMessage", channel))
    imdb = wrap(imdb, ['text'])

Class = IMDb

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
