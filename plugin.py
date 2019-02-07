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
import json
import re

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weed')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Weed(callbacks.Plugin):
    """Uses API to retrieve information"""
    threaded = True

    def strain(self, irc, msg, args, strain):
        """<strain>
        Searches API based on user input
        """
        
        response1 = None
        response2 = None
        channel = msg.args[0]
        strain = re.sub('[^\w\:\"\#\-\.\' ]', '', strain).casefold()
        strain_api = self.registryValue('strain_api')
                
        url = "http://strainapi.evanbusse.com/{0}/strains/search/name/{1}".format(strain_api, strain)
        
        data = requests.get(url).json()
        
        for item in data:
            if item['desc'] is not None and item['name'].casefold() == strain:
                name = ircutils.bold(item['name'])
                type = ircutils.bold(item['race'])
                desc = item['desc']
                response1 = "{0} :: {1} :: {2}".format(name, type, desc)
                break
        for item in data:
            if item['desc'] is not None and item['name'].casefold() != strain:
                name = ircutils.bold(item['name'])
                type = ircutils.bold(item['race'])
                desc = item['desc']
                response2 = "{0} :: {1} :: {2}".format(name, type, desc)
                break
        if  response1 != None:
            irc.reply(response1)
        elif response1 == None and response2 != None:
            irc.reply(response2)
        else:
            irc.reply('No results found, what have you been smoking?')

    strain = wrap(strain, ['text'])
    
Class = Weed


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
