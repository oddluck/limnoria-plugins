###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
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
                    imdb_template = imdb_template.replace("$tomatoMeter", response["tomatoMeter"])
                    imdb_template = imdb_template.replace("$metascore", response["Metascore"])
                    imdb_template = imdb_template.replace("$released",response["Released"])
                    imdb_template = imdb_template.replace("$genre",response["Genre"])
                    imdb_template = imdb_template.replace("$released",response["Released"])
                    imdb_template = imdb_template.replace("$awards",response["Awards"])
                    imdb_template = imdb_template.replace("$actors",response["Actors"])
                    imdb_template = imdb_template.replace("$rated",response["Rated"])
                    imdb_template = imdb_template.replace("$runtime",response["Runtime"])
                    imdb_template = imdb_template.replace("$writer",response["Writer"])

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
