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
import json, random, re
from string import Template

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("IMDb")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class lowercase_dict(dict):
    def __getitem__(self, name):
        return dict.__getitem__(self, name.lower())


class lowercase_template(Template):
    def safe_substitute(self, mapping=None, **kws):
        if mapping is None:
            mapping = {}
        m = lowercase_dict((k.lower(), v) for k, v in mapping.items())
        m.update(lowercase_dict((k.lower(), v) for k, v in kws.items()))
        return Template.safe_substitute(self, m)


class IMDb(callbacks.Plugin):
    """Queries OMDB database for information about IMDb titles"""

    threaded = True

    def dosearch(self, irc, channel, text):
        google = None
        ddg = None
        match = None
        if self.registryValue("google", channel) > 0:
            google = irc.getCallback("google")
            if not google:
                log.error("IMDb: Error: Google search enabled but plugin not loaded.")
        if self.registryValue("ddg", channel) > 0:
            ddg = irc.getCallback("ddg")
            if not ddg:
                log.error("IMDb: Error: DDG search enabled but plugin not loaded.")
        if not google and not ddg:
            log.error("IMDb: Google and DDG plugins not loaded.")
            return
        query = "site:www.imdb.com/title/ %s" % text
        pattern = re.compile(r"https?://www.imdb.com/title/tt\d+/$")
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
                            log.debug(
                                "IMDb: found link using Google search: %s"
                                % match.group(0)
                            )
                            break
                except:
                    pass
            elif ddg and self.registryValue("ddg", channel) == i:
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
                            log.debug(
                                "IMDb: found link using DDG search %s" % match.group(0)
                            )
                            break
                except:
                    pass
        if match:
            return match.group(0)
        else:
            return

    def imdb(self, irc, msg, args, query):
        """<title>
        Queries the OMDB API about an IMDb title. Search by title name or IMDb ID.
        """
        url = None
        response = None
        result = None
        if not self.registryValue("omdbAPI"):
            irc.error("Error: You must set an OMDB API key to use this plugin.")
            return
        id = re.match(r"tt\d+", query.strip())
        if id:
            url = "http://imdb.com/title/{0}".format(id.group(0))
        if not id:
            url = self.dosearch(irc, msg.channel, query)
        if url:
            id = url.split("/title/")[1].rstrip("/")
            url = "http://www.omdbapi.com/?" + utils.web.urlencode(
                {
                    "i": id,
                    "plot": "short",
                    "r": "json",
                    "apikey": self.registryValue("omdbAPI"),
                }
            )
            log.debug("IMDb: requesting %s" % url)
        else:
            url = "http://www.omdbapi.com/?" + utils.web.urlencode(
                {
                    "t": query,
                    "plot": "short",
                    "r": "json",
                    "apikey": self.registryValue("omdbAPI"),
                }
            )
            log.debug("IMDb: requesting %s" % url)
        request = utils.web.getUrl(url).decode()
        response = json.loads(request)
        if response["Response"] != "False" and not response.get("Error"):
            imdb_template = lowercase_template(
                self.registryValue("template", msg.channel)
            )
            response["logo"] = self.registryValue("logo", msg.channel)
            response["tomatometer"] = "N/A"
            response["metascore"] = "N/A"
            for rating in response["Ratings"]:
                if rating["Source"] == "Rotten Tomatoes":
                    response["tomatometer"] = rating["Value"]
                if rating["Source"] == "Metacritic":
                    response["metascore"] = "{0}%".format(rating["Value"].split("/")[0])
            result = imdb_template.safe_substitute(response)
        elif response.get("Error"):
            log.debug("IMDb: OMDB API: %s" % response["Error"])
        if result:
            irc.reply(result, prefixNick=False)
        else:
            irc.error(self.registryValue("noResultsMessage", msg.channel))

    imdb = wrap(imdb, ["text"])


Class = IMDb

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
