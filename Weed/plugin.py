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
                id = item['id']
                name = ircutils.bold(item['name'])
                type = ircutils.bold(item['race'])
                desc = item['desc']
                url2 = "http://strainapi.evanbusse.com/{0}/strains/data/flavors/{1}".format(strain_api, id)
                data2 = requests.get(url2).json()
                flavor1 = data2[0]
                flavor2 = data2[1]
                flavor3 = data2[2]
                response1 = "{0} | {1} | Flavors: {2}, {3}, {4} | {5}".format(name, type, flavor1, flavor2, flavor3, desc)
                break
        for item in data:
            if item['desc'] is not None and item['name'].casefold() != strain:
                id = item['id']
                name = ircutils.bold(item['name'])
                type = ircutils.bold(item['race'])
                desc = item['desc']
                url2 = "http://strainapi.evanbusse.com/{0}/strains/data/flavors/{1}".format(strain_api, id)
                data2 = requests.get(url2).json()
                flavor1 = data2[0]
                flavor2 = data2[1]
                flavor3 = data2[2]
                response2 = "{0} | {1} | Flavors: {2}, {3}, {4} | {5}".format(name, type.title(), flavor1, flavor2, flavor3, desc)
                break
        if  response1 != None:
            irc.reply(response1)
        elif response1 == None and response2 != None:
            irc.reply(response2)
        else:
            irc.reply('No results found, what have you been smoking?')

    strain = wrap(strain, ['text'])
    
Class = Weed
