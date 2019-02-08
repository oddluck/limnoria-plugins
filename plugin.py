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

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weed')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Fun(callbacks.Plugin):
    """Uses API to retrieve information"""
    threaded = True

    def advice(self, irc, msg, args):
        """<user>
        Get some advice
        """

        channel = msg.args[0]
        data = requests.get("https://api.adviceslip.com/advice").json()
        irc.reply(data['slip']['advice'])

    advice = wrap(advice)

    def joke(self, irc, msg, args):
        """<user>
        Get a joke
        """

        channel = msg.args[0]
        headers = {
        'Accept': 'text/plain',
        }

        response = requests.get('https://icanhazdadjoke.com/', headers=headers, verify=False)

        irc.reply(response.text)

    joke = wrap(joke)

    def catfact(self, irc, msg, args):
        """<user>
        Get some advice
        """

        channel = msg.args[0]
        data = requests.get("https://catfact.ninja/fact").json()
        irc.reply(data['fact'])

    catfact = wrap(catfact)
    
Class = Fun
