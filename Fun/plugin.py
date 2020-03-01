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
import random
import requests
from bs4 import BeautifulSoup
import codecs
import os
import collections

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
        data = requests.get("https://uselessfacts.jsph.pl/random.json?language=en").json()
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

    def devexcuse(self, irc, msg, args):
        """
        Returns an excuse from http://developerexcuses.com
        """
        data = requests.get('http://developerexcuses.com')
        if not data:  # http fetch breaks.
            irc.reply("ERROR")
            return
        soup = BeautifulSoup(data.content)
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
        BOFH (Bastard Operator From Hell) Excuse Generator
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
            response = utils.web.getUrl("http://edgecats.net/random").decode()
            # Expecting a link
            if "http" in response:
                irc.reply(response)
            else:
                self.log.error("Received unexpected response from http://edgecats.net/random")
        except:
            self.log.exception("Error fetching URL")
    catgif = wrap(catgif)
    
    def mitch(self, irc, msg, args):
        """
        Mitch Hedberg Jokes
        """
        data = open("{0}/mitch_hedberg.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        excuse = random.randrange(0, len(reply))
        irc.reply(reply[excuse])
    mitch = wrap(mitch)
    
    def chuck(self, irc, msg, args):
        """
        Chuck Norris Jokes
        """
        data = open("{0}/chuck_norris.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        excuse = random.randrange(0, len(reply))
        irc.reply(reply[excuse])
    chuck = wrap(chuck)
    
    def rodney(self, irc, msg, args):
        """
        Rodney Dangerfield Jokes
        """
        data = open("{0}/rodney_dangerfield.txt".format(os.path.dirname(os.path.abspath(__file__))))
        text = data.read()
        reply = text.splitlines()
        excuse = random.randrange(0, len(reply))
        irc.reply(reply[excuse])
    rodney = wrap(rodney)

    def rot(self, irc, msg, args, text):
        """<text>
        Encode text with ROT13
        """
        irc.reply(codecs.encode(text, "rot_13"))
    rot = wrap(rot, ['text'])

    def unrot(self, irc, msg, args, text):
        """<text>
        Decode ROT13 text
        """
        irc.reply(codecs.decode(text, "rot_13"))
    unrot = wrap(unrot, ['text'])

    def coin(self, irc, msg, args, optcoin):
        """[coin]
        Fetches current values for a given coin
        """
        coin_url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={coins}&tsyms=USD'
        coins = []
        coins.append(optcoin)
        coins_str = ','.join(c.upper() for c in coins)
        coin_data = requests.get(coin_url.format(coins=coins_str))
        coin_data = coin_data.json()
        if 'RAW' not in coin_data:
            irc.reply('ERROR: no coin found for {}'.format(optcoin))
            return
        output = []
        tmp = {}
        data = coin_data['RAW']
        data2 = collections.OrderedDict.fromkeys(sorted(data))
        for k,v in data.items():
            data2.update({k: v})
        output = self._parseCoins(data2, optcoin)
        irc.reply(' | '.join(t for t in output))
        return
    coin = wrap(coin, ['text'])

    def coins(self, irc, msg, args, optcoin):
        """
        Fetches current values for top 10 coins (+ dogecoin) trading by volume
        """
        volm_url = 'https://min-api.cryptocompare.com/data/top/totalvol?limit=10&tsym=USD'
        coin_url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={coins}&tsyms=USD'
        volm_data = requests.get(volm_url).json()
        coins = []
        for thing in volm_data['Data']:
            name = thing['CoinInfo']['Name']
            coins.append(name)
        coins.append('DOGE')
        coins_str = ','.join(c for c in coins)
        coin_data = requests.get(coin_url.format(coins=coins_str))
        coin_data = coin_data.json()
        output = []
        tmp = {}
        data = coin_data['RAW']
        tmp['BTC'] = data.pop('BTC')
        data2 = collections.OrderedDict.fromkeys(sorted(data))
        for k,v in data.items():
            data2.update({k: v})
        data2.update(tmp)
        data2.move_to_end('BTC', last=False)
        output = self._parseCoins(data2, optcoin)
        irc.reply(' | '.join(t for t in output))
        return
    coins = wrap(coins, [optional('somethingWithoutSpaces')])

    def _parseCoins(self, data, optmarket=None):

        ticker = []

        def _humifyCap(cap):
            if not cap:
                return cap
            if cap > 1000000000000:
                cap = cap / 1000000000000
                cap = '${:.2f}T'.format(cap)
                return cap
            elif cap > 1000000000:
                cap = cap / 1000000000
                cap = '${:.2f}B'.format(cap)
            elif cap > 1000000:
                cap = cap / 1000000
                cap = '${:.2f}M'.format(cap)
            else:
                cap = '${:.2f}'.format(cap)
                return cap
            return cap

        for symbol in data:
            name = symbol
            name = ircutils.bold(name)
            symbol = data[symbol]['USD']
            current_price = symbol['PRICE']
            change = symbol['CHANGEDAY']
            pct_change = symbol['CHANGEPCTDAY']
            high24 = '${:g}'.format(symbol['HIGH24HOUR'])
            low24 = '${:g}'.format(symbol['LOW24HOUR'])
            mcap = _humifyCap(symbol['MKTCAP'])
            if 0 < pct_change < 0.5:
                change = ircutils.mircColor('+{:g}'.format(change), 'yellow')
                pct_change = ircutils.mircColor('+{:.2g}%'.format(pct_change), 'yellow')
            elif pct_change >= 0.5:
                change = ircutils.mircColor('+{:g}'.format(change), 'green')
                pct_change = ircutils.mircColor('+{:.2g}%'.format(pct_change), 'green')
            elif 0 > pct_change > -0.5:
                change = ircutils.mircColor('{:g}'.format(change), 'orange')
                pct_change = ircutils.mircColor('{:.2g}%'.format(pct_change), 'orange')
            elif pct_change <= -0.5:
                change = ircutils.mircColor('{:g}'.format(change), 'red')
                pct_change = ircutils.mircColor('{:.2g}%'.format(pct_change), 'red')
            else:
                change = '{:g}'.format(change)
                pct_change = '{:g}%'.format(pct_change)
            string = '{} ${:g} {} ({})'.format(name, current_price, change, pct_change)
            if optmarket:
                if optmarket.lower() in name.lower():
                    string += ' :: \x02Market Cap:\x02 {} | \x0224hr High:\x02 {} | \x0224hr Low:\x02 {}'.format(
                        mcap, ircutils.mircColor(high24, 'green'), ircutils.mircColor(low24, 'red'))
                    ticker.append(string)
            else:
                ticker.append(string)
        return ticker

Class = Fun
