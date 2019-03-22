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
from fake_useragent import UserAgent

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

    def dosearch(self, search):
        try:
            searchurl = "https://www.google.com/search?&q={0} site:wikileaf.com/strain/".format(search)
            ua = UserAgent()
            header = {'User-Agent':str(ua.random)}
            data = requests.get(searchurl, headers=header)
            soup = BeautifulSoup(data.text)
            elements = soup.select('.r a')
            url = elements[0]['href']
        except Exception:
            return
        else:
            return url

    def strain(self, irc, msg, args, strain):
        """<strain>
        Returns strain information from WikiLeaf. Search powered by Google.
        """
        try:
            url = self.dosearch(strain)
        except Exception:
            irc.reply("No results found, what have you been smoking?")
        else:
            try:
                ua = UserAgent()
                header = {'User-Agent':str(ua.random)}
                data = requests.get(url, headers=header)
                soup = BeautifulSoup(data.text)
                name = re.sub('\s+', ' ', soup.find("h1", itemprop="name").getText())
                straininfo = re.sub('\s+', ' ', soup.find("div", class_="product-info-line cannabis").getText())
                description = re.sub('\s+', ' ', soup.find("div", itemprop="description").getText())
                thc = re.sub('\s+', ' ', soup.find_all("div", class_="product-container-header cf")[1].getText())
                reply = "\x02{0}\x0F | {1} | {2} | {3}".format(name.strip(), straininfo.strip(), thc.strip(), description.strip())
                del data, soup
                irc.reply(reply)
                irc.reply(url)
            except Exception:
                irc.reply("Unable to retrieve info from {0}".format(url))

    strain = wrap(strain, ['text'])

Class = WikiLeaf

