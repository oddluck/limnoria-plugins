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
import requests
import re
from bs4 import BeautifulSoup

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WikiLeaf')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class WikiLeaf(callbacks.Plugin):
    """Retrieve Marjuana Strain Information From WikiLeaf"""
    threaded = True

    def strain(self, irc, msg, args, strain):
        """<strain>
        Returns strain information from WikiLeaf. Searches powered by DuckDuckGo.
        """
        strain = strain.replace(" ", "-").replace("#", "").lower()
        searchurl = "https://duckduckgo.com/html/?q={0} site: wikileaf.com/strain".format(strain)
        try:
            search = requests.get(searchurl)
            soup = BeautifulSoup(search.text)
            url = re.sub('\s+', '', soup.find("a", class_="result__url").getText())
            data = requests.get("https://{0}".format(url))
            if not data:  # http fetch breaks.
                irc.reply("ERROR")
                return
            soup = BeautifulSoup(data.text)
            name = re.sub('\s+', ' ', soup.find("h1", itemprop="name").getText())
            straininfo = re.sub('\s+', ' ', soup.find("div", class_="product-info-line cannabis").getText())
            description = re.sub('\s+', ' ', soup.find("div", itemprop="description").getText())
            thc = re.sub('\s+', ' ', soup.find_all("div", class_="product-container-header cf")[1].getText())
            reply = "\x02{0}\x0F | {1} | {2} | {3}".format(name.strip(), straininfo.strip(), thc.strip(), description.strip())
            irc.reply(reply)
        except:
            irc.reply("No results found, what have you been smoking?")

    strain = wrap(strain, ['text'])

Class = WikiLeaf

