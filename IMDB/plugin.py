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

import sys
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import requests
import json
import re
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('IMDB')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class IMDB(callbacks.Plugin):
    """Queries OMDB database for information about IMDB titles"""
    threaded = True

    def dosearch(self, query):
        try:
            searchurl = "https://www.google.com/search?&q={0} site:imdb.com/title/".format(query)
            ua = UserAgent()
            header = {'User-Agent':str(ua.random)}
            data = requests.get(searchurl, headers=header)
            soup = BeautifulSoup(data.text)
            elements = soup.select('.r a')
            url = elements[0]['href']
            url = re.split('https?://', url)[-1]
            url = re.sub("&rct=.*", "", url)
            url = "https://{0}".format(url)
        except Exception:
            return
        else:
            return url

    def imdb(self, irc, msg, args, query):
        """
        Queries OMDB api for query
        """
        apikey = self.registryValue('omdbAPI')
        url = self.dosearch(query)
        if url:
            imdb_id = url.split("/title/")[1].rstrip("/")
            omdb_url = "http://www.omdbapi.com/?i=%s&plot=short&r=json&tomatoes=true&apikey=%s" % (imdb_id, apikey)
        else:
            irc.reply("No results found for {0}".format(query))

        channel = msg.args[0]
        result = None
        ua = UserAgent()
        headers = {'User-Agent':str(ua.random)}

        self.log.info("IMDB: requesting %s" % omdb_url)

        try:
            request = requests.get(omdb_url, timeout=10, headers=headers)

            if request.status_code == requests.codes.ok:
                response = json.loads(request.text)

                not_found = "Error" in response
                unknown_error = response["Response"] != "True"

                if not_found or unknown_error:
                    self.log.info("IMDB: OMDB error for %s" % (omdb_url))
                else:
                    meta = None
                    tomato = None
                    imdb_template = self.registryValue("template")
                    if sys.version_info[0] < 3:
                        imdb_template = imdb_template.decode("utf-8")
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
                self.log.error("IMDB OMDB API %s - %s" % (request.status_code, request.text))

        except requests.exceptions.Timeout as e:
            self.log.error("IMDB Timeout: %s" % (str(e)))
        except requests.exceptions.ConnectionError as e:
            self.log.error("IMDB ConnectionError: %s" % (str(e)))
        except requests.exceptions.HTTPError as e:
            self.log.error("IMDB HTTPError: %s" % (str(e)))
        finally:
            if result is not None:
                irc.reply(result)
            else:
                irc.error(self.registryValue("noResultsMessage"))

    imdb = wrap(imdb, ['text'])

Class = IMDB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
