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
    """Uses API to retrieve information"""
    threaded = True

    def strain(self, irc, msg, args, strain):
        """<strain>
        Searches API based on user input
        """
        strain = strain.replace(" ", "-").replace("#", "").lower()
        url = "https://www.wikileaf.com/strain/{0}".format(strain)
        data = requests.get(url)
        if not data:  # http fetch breaks.
            irc.reply("ERROR")
            return
        try:
            soup = BeautifulSoup(data.text)
            name = re.sub('\s+', ' ', soup.find("h1", itemprop="name").getText())
            description = re.sub('\s+', ' ', soup.find("div", itemprop='description').getText())
            thc = re.sub('\s+', ' ', soup.find_all("div", class_="product-container-header cf")[1].getText())
            reply = "\x02{0}\x0F | {1} | {2}".format(name.strip(), thc.strip(), description.strip())
            irc.reply(reply)
        except:
            irc.reply('No results found, what have you been smoking?')

    strain = wrap(strain, ['text'])

Class = WikiLeaf

