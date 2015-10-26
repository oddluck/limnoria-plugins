###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import requests
from urllib import quote_plus
import json

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

    def imdb(self, irc, msg, args, query):
        """
        Queries OMDB api for query
        """
        encoded_query = quote_plus(query)
        omdb_url = "http://www.omdbapi.com/?t=%s&y=&plot=short&r=json&tomatoes=true" % (encoded_query)
        channel = msg.args[0]
        result = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.60 Safari/537.36"
        }
        
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
                    imdb_template = imdb_template.replace("$title", response["Title"])
                    imdb_template = imdb_template.replace("$year", response["Year"])
                    imdb_template = imdb_template.replace("$country", response["Country"])
                    imdb_template = imdb_template.replace("$director", response["Director"])
                    imdb_template = imdb_template.replace("$plot", response["Plot"])
                    imdb_template = imdb_template.replace("$imdbID", response["imdbID"])
                    imdb_template = imdb_template.replace("$imdbRating", response["imdbRating"])
                    imdb_template = imdb_template.replace("$tomatoMeter", response["tomatoMeter"])
                    imdb_template = imdb_template.replace("$metascore", response["Metascore"])
                    
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
                irc.sendMsg(ircmsgs.privmsg(channel, result))
            else:
                irc.error(self.registryValue("noResultsMessage"))
    
    imdb = wrap(imdb, ['text'])
        
Class = IMDB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
