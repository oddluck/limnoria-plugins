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
import arrr
from bs4 import BeautifulSoup
import os
import random

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

    def ascii(self, irc, msg, args, optlist, text):
        """[--font <font>] [--fontlist] [<text>]
        text to ASCII art
        """
        channel = msg.args[0]
        optlist = dict(optlist)
        font = None
        words = []
        if text:
            text = text.strip()
            if '|' in text:
                words = text.split('|')
        if 'font' in optlist:
             font = optlist.get('font')
             if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(word.strip(), font))
                         for line in data.text.splitlines():
                             if line.strip():
                                 irc.reply(line, prefixNick=False)
             else:
                 data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(text, font))
                 for line in data.text.splitlines():
                     if line.strip():
                         irc.reply(line, prefixNick=False)
        elif 'fontlist' in optlist:
            fontlist = requests.get("https://artii.herokuapp.com/fonts_list")
            response = sorted(fontlist.text.split('\n'))
            irc.reply(str(response).replace('\'', '').replace('[', '').replace(']', ''))
        elif 'font' not in optlist:
            if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(word.strip()))
                         for line in data.text.splitlines():
                             if line.strip():
                                 irc.reply(line, prefixNick=False)
            else:
                data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(text))
                for line in data.text.splitlines():
                    if line.strip():
                        irc.reply(line, prefixNick=False)
    ascii = wrap(ascii, [getopts({'font':'something', 'fontlist':''}), additional('text')])

    def pirate(self, irc, msg, args, text):
        """<text>
        English to pirate translator.
        """
        channel = msg.args[0]
        pirate = arrr.translate(text)
        irc.reply(pirate)
    pirate = wrap(pirate, ['text'])

    def devexcuse(self, irc, msg, args):
        """
        Returns an excuse from http://developerexcuses.com
        """
        data = requests.get('http://developerexcuses.com')
        if not data:  # http fetch breaks.
            irc.reply("ERROR")
            return
        soup = BeautifulSoup(data.text)
        text = soup.find('center').getText()
        irc.reply("{0}".format(text))
    devexcuse = wrap(devexcuse)

    def _pigword(self, word):
        shouldCAP = (word[:1] == word[:1].upper())
        word = word.lower()
        letters = "qwertyuiopasdfghjklzxcvbnm"
        i = len(word) - 1
        while i >= 0 and letters.find(word[i]) == -1:
            i = i - 1
        if i == -1:
            return word
        punctuation = word[i+1:]
        word = word[:i+1]

        vowels = "aeiou"
        if vowels.find(word[0]) >= 0:
            word = word + "yay" + punctuation
        else:
            word = word[1:] + word[0] + "ay" + punctuation

        if shouldCAP:
            return word[:1].upper() + word[1:]
        else:
            return word

    def piglatin(self, irc, msg, args, optinput):
        """<text>
        Convert text from English to Pig Latin.
        """

        l = optinput.split(" ")
        for i in range(len(l)):
            l[i] = self._pigword(l[i])

        irc.reply(" ".join(l))
    piglatin = wrap(piglatin, [('text')])

    def bofh(self, irc, msg, args):
        """
        BOFH Excuse Generator
        """
        data = open("{0}/excuses.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        excuse = random.randrange(0, len(reply))
        irc.reply(reply[excuse])
    bofh = wrap(bofh)

    def rock(self, irc, msg, args):
        """takes no arguments
        Choose rock in Rock, Paper, Scissors.
        """
        botchoice2 = random.randint(1, 3)
        if botchoice2 == 1:
            botchoice = "rock"
        elif botchoice2 == 2:
            botchoice = "paper"
        elif botchoice2 == 3:
            botchoice = "scissors"
        userchoice = "rock"
        if botchoice == userchoice:
            irc.reply("I chose %s. Looks like we tied." % (botchoice))
        elif botchoice == "paper" and userchoice == "rock":
            irc.reply("I chose %s. Looks like I won." % (botchoice))
        elif botchoice == "scissors" and userchoice == "rock":
            irc.reply("I chose %s. Looks like you won." % (botchoice))
    rock = wrap(rock)

    def paper(self, irc, msg, args):
        """takes no arguments
        Choose paper in Rock, Paper, Scissors.
        """
        botchoice2 = random.randint(1, 3)
        if botchoice2 == 1:
            botchoice = "rock"
        elif botchoice2 == 2:
            botchoice = "paper"
        elif botchoice2 == 3:
            botchoice = "scissors"
        userchoice = "paper"
        if botchoice == userchoice:
            irc.reply("I chose %s. Looks like we tied." % (botchoice))
        elif botchoice == "scissors" and userchoice == "paper":
            irc.reply("I chose %s. Looks like I won." % (botchoice))
        elif botchoice == "rock" and userchoice == "paper":
            irc.reply("I chose %s. Looks like you won." % (botchoice))
    paper = wrap(paper)

    def scissors(self, irc, msg, args):
        """takes no arguments
        Choose scissors in Rock, Paper, Scissors.
        """
        botchoice2 = random.randint(1, 3)
        if botchoice2 == 1:
            botchoice = "rock"
        elif botchoice2 == 2:
            botchoice = "paper"
        elif botchoice2 == 3:
            botchoice = "scissors"
        userchoice = "scissors"
        if botchoice == userchoice:
            irc.reply("I chose %s. Looks like we tied." % (botchoice))
        elif botchoice == "rock" and userchoice == "scissors":
            irc.reply("I chose %s. Looks like I won." % (botchoice))
        elif botchoice == "paper" and userchoice == "scissors":
            irc.reply("I chose %s. Looks like you won." % (botchoice))
    scissors = wrap(scissors)
    
    def catgif(self, irc, msg, args):
        """
        Get a random cat .gif
        """
        try:
            response = utils.web.getUrl("http://edgecats.net/random").decode("utf8")
            # Expecting a link
            if "http" in response:
                irc.reply(response)
            else:
                self.log.error("Received unexpected response from http://edgecats.net/random")
        except:
            self.log.exception("Error fetching URL")
    catgif = wrap(catgif)

Class = Fun
