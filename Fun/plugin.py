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
import html

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
        """
        Get some advice
        """

        channel = msg.args[0]
        data = requests.get("https://api.adviceslip.com/advice").json()
        irc.reply(data['slip']['advice'])

    advice = wrap(advice)

    def joke(self, irc, msg, args):
        """
        Get a joke
        """

        channel = msg.args[0]
        headers = {
        'Accept': 'application/json',
        }
        data = requests.get('https://icanhazdadjoke.com/', headers=headers).json()
        irc.reply(data['joke'].replace('\n', '').replace('\r', '').replace('\t', ''))

    joke = wrap(joke)

    def catfact(self, irc, msg, args):
        """
        Cat fact
        """

        channel = msg.args[0]
        data = requests.get("https://catfact.ninja/fact").json()
        irc.reply(data['fact'])

    catfact = wrap(catfact)

    def useless(self, irc, msg, args):
        """
        Useless fact
        """

        channel = msg.args[0]
        data = requests.get("http://randomuselessfact.appspot.com/random.json?language=en").json()
        irc.reply(data['text'])

    useless = wrap(useless)

    def buzz(self, irc, msg, args):
        """
        Corporate buzzord generator
        """
        channel = msg.args[0]
        data = requests.get("https://corporatebs-generator.sameerkumar.website").json()
        irc.reply(data['phrase'])
    buzz = wrap(buzz)

    def startup(self, irc, msg, args):
        """
        Startup generator
        """
        channel = msg.args[0]
        data = requests.get("http://itsthisforthat.com/api.php?json").json()
        vowels = ('a','e','i','o','u','A','E','I','O','U')
        if data['this'].startswith(vowels):
            response = "So, Basically, It\'s Like An {0} for {1}".format(data['this'], data['that'])
        else:
            response = "So, Basically, It\'s Like A {0} for {1}".format(data['this'], data['that'])
        irc.reply(response)
    startup = wrap(startup)

    def insult(self, irc, msg, args, nick):
        """[<nick>]
        Insult generator. Optionally send insult to <nick> (<nick> must be in channel).
        """
        channel = msg.args[0]
        data = requests.get("https://insult.mattbas.org/api/en/insult.json").json()
        if nick:
            response = "{0}: {1}".format(nick, data['insult'])
            irc.reply(response, prefixNick=False)
        else:
            irc.reply(data['insult'])

    insult = wrap(insult, [additional('nickInChannel')])

    
Class = Fun
