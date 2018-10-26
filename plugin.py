###
# Copyright (c) 2018, cottongin
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

import requests
import datetime
import pendulum
import collections

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Stocks')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Stocks(callbacks.Plugin):
    """Plugin to fetch various market information"""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Stocks, self)
        self.__parent.__init__(irc)
        #self._google_api_key = self.registryValue('GoogleAPIKey')
        self._stock_api_key = self.registryValue('StocksAPIKey')
        
        self.HEADERS = {
            'Host': 'www.bloomberg.com',
            'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 11151.4.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.8 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.bloomberg.com/quote/INDU:IND',
            'Cookie': 'pxvid=ddebe760-c7f5-11e8-a682-73308eefdc23; _user-status=anonymous; agent_id=e0d13978-3eec-4c24-9ee2-e272d579c309; session_id=eee20924-ece1-4d7a-b35b-8ac6dc1d68b2; session_key=91bf3c15262d3327089818fad49b32f4e8505340; _pxvid=ddebe760-c7f5-11e8-a682-73308eefdc23; bb_geo_info={"country":"US","region":"US"}|1541093477988; _user-ip=172.56.7.187; _px2=eyJ1IjoiNGM0MzQ5ZjAtZDg3ZC0xMWU4LThkMGEtY2I0ZWMwN2I1YzdmIiwidiI6ImRkZWJlNzYwLWM3ZjUtMTFlOC1hNjgyLTczMzA4ZWVmZGMyMyIsInQiOjE1NDA0ODk4NzI3NDcsImgiOiIxMmNlYTc1MjE3MzE1MjQzZjFlZmNiYzgwOTE4MTAyZTlhODA5MWI0ZWVlYzZmYTMyYzlhODEzMGZmMjc2NzBjIn0=; _px3=16001718995882c0a708e91edfaf00e90c29b7ffa91a674b632d3d9352ac415c:tJVcHrOc8q5ZweBYZcDl6l4B1qCkFMYuQRXhfttgXGJutOTDn8PeIvwArsE30/a0bmS8sfFccSueLNnEPNXkjg==:1000:xmySGbKaaKn0QMZr3ZhABwVQOlQaDTxZ4BpBgiWoDzLKPxTiaCC9YjI6TlJL3FePznBOhu4ADhDRLUWkMrqYPUnhsGFuaiehhcNgtSkSOofaagxZK8YVH/jf5t5iUVIB6GkZ93c8e1+wmvQuS1Bie+MbmmP2P2Duyujx+In5LFQ=; _pxde=eee12b269f681eeaffaa85ced50bdf6970ad1606518f09164005dab05e61cafe:eyJ0aW1lc3RhbXAiOjE1NDA0ODk1ODg3MjksImlwY19pZCI6W119',
        }
        
        #if len(self._google_api_key) <= 1:
        #    irc.reply("This plugin requires a Google API key to shorten URLs, please add yours via the configuration")
        #    return
        if len(self._stock_api_key) <= 1:
            irc.reply("This plugin requires a Stocks API key to fetch data, please add yours via the configuration")
            return
        
    def die(self):
        self.__parent.die()
        
        
    def _parseDelta(self, value):
        """parses delta and returns formatted string"""
        
        if value > 0:
            value = '{:.2f}'.format(value)
            value = ircutils.mircColor(value, 'green')
        elif value < 0:
            value = '{:.2f}'.format(value)
            value = ircutils.mircColor(value, 'red')
        else:
            value = '---'
            
        return value
        
    def _parsePct(self, value):
        """parses delta and returns formatted string"""
        
        if value > 0:
            value = '↑{:.2f}%'.format(value)
            value = ircutils.mircColor(value, 'green')
        elif value < 0:
            value = '↓{:.2f}%'.format(value)
            value = ircutils.mircColor(value, 'red')
        else:
            value = '---'
            
        return value
    
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
            print(data[symbol])
            name = symbol
            name = ircutils.bold(name)
            symbol = data[symbol]['USD']
            current_price = symbol['PRICE']
            change = symbol['CHANGEDAY']
            pct_change = symbol['CHANGEPCTDAY']
            high24 = '${:g}'.format(symbol['HIGH24HOUR'])
            low24 = '${:g}'.format(symbol['LOW24HOUR'])
            mcap = _humifyCap(symbol['MKTCAP'])
            #prv_close = symbol['previousClosingPriceOneTradingDayAgo']
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
    
    def _parseTickerPrices(self, data, optmarket):
        
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
            name = symbol['longName']
            name = ircutils.bold(name)
            current_price = symbol['price']
            change = symbol['priceChange1Day']
            pct_change = symbol['percentChange1Day']
            prv_close = symbol['previousClosingPriceOneTradingDayAgo']
            market_cap = _humifyCap(symbol['marketCap'])
            highYear = '${:.2f}'.format(symbol['highPrice52Week'])
            lowYear = '${:.2f}'.format(symbol['lowPrice52Week'])
            pe_ratio = symbol['priceEarningsRatio']
            
            if pe_ratio:
                pe_ratio = ' | \x02P/E Ratio:\x02 ${:.2f}'.format(pe_ratio)
            else:
                pe_ratio = ''
            
            if 0 < pct_change < 0.5:
                change = ircutils.mircColor('+{:.2f}'.format(change), 'yellow')
                pct_change = ircutils.mircColor('+{:.2f}%'.format(pct_change), 'yellow')
            elif pct_change >= 0.5:
                change = ircutils.mircColor('+{:.2f}'.format(change), 'green')
                pct_change = ircutils.mircColor('+{:.2f}%'.format(pct_change), 'green')
            elif 0 > pct_change > -0.5:
                change = ircutils.mircColor('{:.2f}'.format(change), 'orange')
                pct_change = ircutils.mircColor('{:.2f}%'.format(pct_change), 'orange')
            elif pct_change <= -0.5:
                change = ircutils.mircColor('{:.2f}'.format(change), 'red')
                pct_change = ircutils.mircColor('{:.2f}%'.format(pct_change), 'red')
            else:
                change = '{:.2f}'.format(change)
                pct_change = '{:.2f}%'.format(pct_change)
            string = ('{} ${:.2f} {} ({}) :: \x02Previous Close:\x02 ${:.2f}'
                      ' | \x02Market Cap:\x02 {} | \x0252wk High:\x02 {} | \x0252wk Low:\x02 {}'
                      '{}').format(
                name, current_price, change, pct_change, prv_close, market_cap,
                ircutils.mircColor(highYear, 'green'), ircutils.mircColor(lowYear, 'red'), pe_ratio)
            ticker.append(string)
        
        return ticker
    
    def _parsePrices(self, data, optmarket=None):
        
        ticker = []
        
        for symbol in data:
            name = symbol['shortName']
            name = name.replace('COMPOSITE INDEX', '').strip()
            if name == "Generic 1st 'SI' Future":
                name = 'Silver'
            elif name == "Generic 1st 'NG' Future":
                name = 'Natural Gas'
            elif 'WTI Crude' in name:
                name = 'Oil'
            elif 'S&P/TSX' in name:
                name = 'TSX'
            elif 'HANG SENG' in name:
                name = 'SEHK'
            elif 'NYSE' in name:
                name = 'NYSE'
            else:
                name = symbol['shortName']
            name = ircutils.bold(name)
            current_price = symbol['price']
            change = symbol['priceChange1Day']
            pct_change = symbol['percentChange1Day']
            prv_close = symbol['previousClosingPriceOneTradingDayAgo']
            if 0 < pct_change < 0.5:
                change = ircutils.mircColor('+{:.2f}'.format(change), 'yellow')
                pct_change = ircutils.mircColor('+{:.2f}%'.format(pct_change), 'yellow')
            elif pct_change >= 0.5:
                change = ircutils.mircColor('+{:.2f}'.format(change), 'green')
                pct_change = ircutils.mircColor('+{:.2f}%'.format(pct_change), 'green')
            elif 0 > pct_change > -0.5:
                change = ircutils.mircColor('{:.2f}'.format(change), 'orange')
                pct_change = ircutils.mircColor('{:.2f}%'.format(pct_change), 'orange')
            elif pct_change <= -0.5:
                change = ircutils.mircColor('{:.2f}'.format(change), 'red')
                pct_change = ircutils.mircColor('{:.2f}%'.format(pct_change), 'red')
            else:
                change = '{:.2f}'.format(change)
                pct_change = '{:.2f}%'.format(pct_change)
            string = '{} ${:.2f} {} ({})'.format(name, current_price, change, pct_change)
            if optmarket:
                if optmarket.lower() in symbol['shortName'].lower():
                    string += ' :: Previous Close: {:.2f}'.format(prv_close)
                    ticker.append(string)
            else:
                ticker.append(string)
        
        return ticker
    
    @wrap(['somethingWithoutSpaces'])
    def coin(self, irc, msg, args, optcoin):
        """Fetches current values for a given coin"""
        
        #volm_url = 'https://min-api.cryptocompare.com/data/top/totalvol?limit=10&tsym=USD'
        coin_url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={coins}&tsyms=USD'
        
        #volm_data = requests.get(volm_url).json()
        
        coins = []
        coins.append(optcoin)
            
        #coins.append('DOGE')
        coins_str = ','.join(c.upper() for c in coins)
        
        coin_data = requests.get(coin_url.format(coins=coins_str))
        print(coin_data.url)
        coin_data = coin_data.json()
        
        output = []
        
        tmp = {}
        data = coin_data['RAW']
        #print(data)
        #tmp['BTC'] = data.pop('BTC')
                
        #print(tmp)
        
        #data = sorted(data)
        data2 = collections.OrderedDict.fromkeys(sorted(data))
        for k,v in data.items():
            data2.update({k: v})
        #data2.update(tmp)
        #print(data.keys())
        #data2.move_to_end('BTC', last=False)
        #print(data.items())
        #print(data2)
        
        output = self._parseCoins(data2, optcoin)
            
        irc.reply(' | '.join(t for t in output))
        return
    
    @wrap([optional('somethingWithoutSpaces')])
    def coins(self, irc, msg, args, optcoin):
        """Fetches current values for top 10 coins (+ dogecoin) trading by volume"""
        
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
        #print(coin_data.url)
        coin_data = coin_data.json()
        
        output = []
        
        tmp = {}
        data = coin_data['RAW']
        #print(data)
        tmp['BTC'] = data.pop('BTC')
                
        #print(tmp)
        
        #data = sorted(data)
        data2 = collections.OrderedDict.fromkeys(sorted(data))
        for k,v in data.items():
            data2.update({k: v})
        data2.update(tmp)
        #print(data.keys())
        data2.move_to_end('BTC', last=False)
        #print(data.items())
        print(data2)
        
        output = self._parseCoins(data2, optcoin)
            
        irc.reply(' | '.join(t for t in output))
        return
        
        
    @wrap([optional('somethingWithoutSpaces')])
    def markets(self, irc, msg, args, optmarket):
        """Fetches current values for several markets"""
        
        url = ('https://www.bloomberg.com/markets2/api/datastrip/'
               '{markets_to_fetch}'
               '?locale=en&customTickerList=true')
        
        m = 'INDU:IND,SPX:IND,CCMP:IND,NYA:IND,UKX:IND,NKY:IND,SPTSX:IND,HSI:IND'
        
        url = url.format(markets_to_fetch=m)
        
        try:
            data = requests.get(url, headers=self.HEADERS).json()
        except:
            irc.reply('Something went wrong fetching data')
            return
        
        ticker = self._parsePrices(data, optmarket)
            
        irc.reply(' | '.join(t for t in ticker))
        return
    
    @wrap([optional('somethingWithoutSpaces')])
    def commodities(self, irc, msg, args, optmarket):
        """Fetches current values for several commodities"""
        
        url = ('https://www.bloomberg.com/markets2/api/datastrip/'
               '{markets_to_fetch}'
               '?locale=en&customTickerList=true')
        
        m = 'CL1:COM,NG1:COM,GC1:COM,SI1:COM'
        
        url = url.format(markets_to_fetch=m)
        print(url)
        
        try:
            data = requests.get(url, headers=self.HEADERS).json()
        except:
            irc.reply('Something went wrong fetching data')
            return
        
        ticker = self._parsePrices(data, optmarket)
            
        irc.reply(' | '.join(t for t in ticker))
        return
    
    @wrap([commalist('somethingWithoutSpaces')])
    def ticker(self, irc, msg, args, optmarket):
        """Fetches current values for several commodities"""
        
        url = ('https://www.bloomberg.com/markets2/api/datastrip/'
               '{markets_to_fetch}'
               '?locale=en&customTickerList=true')
        
        print(optmarket)
        
        m = '{}'.format(','.join(i.upper()+':US' for i in optmarket[:5]))
        
        url = url.format(markets_to_fetch=m)
        print(url)
        
        try:
            data = requests.get(url, headers=self.HEADERS).json()
        except:
            irc.reply('Something went wrong fetching data')
            return
        
        ticker = self._parseTickerPrices(data, optmarket)
            
        for symbol in ticker:
            irc.reply(symbol)
        return
        
#     @wrap
#     def djia(self, irc, msg, args):
#         """Fetches current value of the Dow Jones Industrial Average"""
        
#         url = 'https://api.iextrading.com/1.0/stock/dia/quote'
#         today = datetime.date.today().strftime("%Y-%m-%d")
#         yesterday = pendulum.yesterday().strftime("%Y-%m-%d")
#         now = pendulum.now('US/Eastern')
        
#         try:
#             data = requests.get(url)
#             data = data.json()
#         except:
#             irc.reply('Something went wrong fetching data.')
#             return
        
#         #print(today)
#         #print(data['Time Series (Daily)']['{}'.format(str(today))])
# #         try:
# #             today_data = data['Time Series (Daily)']['{}'.format(str(today))]
# #             yesterday_data = data['Time Series (Daily)']['{}'.format(str(yesterday))]
# #         except:
# #             irc.reply("Something went wrong parsing data")
# #             return
        
#         prices = {}
#         company = data['companyName']
#         prices['open'] = data['previousClose']
#         prices['current'] = data['latestPrice']
#         prices['delta'] = self._parseDelta(prices['current'] - prices['open'])
#         prices['%'] = self._parsePct(((prices['current'] - prices['open']) / prices['open']) * 100)
        
#         reply_str = "\x02{} for {}:\x02 {:.2f} :: {} ({}) :: Previous close: {:.2f}".format(company, today, prices['current'],
#                                                                        prices['delta'],
#                                                                        prices['%'],
#                                                                        prices['open'])
#         irc.reply(reply_str)
        
#     @wrap(['text'])
#     def ticker(self, irc, msg, args, symbol):
#         """Fetches current value of the provided ticker symbol"""
        
#         url = 'https://api.iextrading.com/1.0/stock/{}/quote'
#         today = datetime.date.today().strftime("%Y-%m-%d")
#         yesterday = pendulum.yesterday().strftime("%Y-%m-%d")
#         now = pendulum.now('US/Eastern')
        
#         try:
#             data = requests.get(url.format(symbol))
#         except Exception as err:
#             print(err)
#             irc.reply('Something went wrong fetching data.')
#             return
        
#         if data.text == 'Unknown symbol':
#             irc.reply(data.text)
#             return
#         else:
#             try:
#                 data = data.json()
#             except:
#                 irc.reply('Something went wrong parsing data.')
#                 return
#         #print(data.text)
        
#         #print(today)
#         #print(data['Time Series (Daily)']['{}'.format(str(today))])
# #         try:
# #             today_data = data['Time Series (Daily)']['{}'.format(str(today))]
# #             yesterday_data = data['Time Series (Daily)']['{}'.format(str(yesterday))]
# #         except:
# #             irc.reply("Something went wrong parsing data, is your symbol valid?")
# #             return
        
#         prices = {}
#         company = data['companyName']
#         prices['open'] = data['previousClose']
#         prices['current'] = data['latestPrice']
#         prices['delta'] = self._parseDelta(prices['current'] - prices['open'])
#         prices['%'] = self._parsePct(((prices['current'] - prices['open']) / prices['open']) * 100)
        
#         reply_str = "\x02{} for {}:\x02 {:.2f} :: {} ({}) :: Previous close: {:.2f}".format(company, today, prices['current'],
#                                                                        prices['delta'],
#                                                                        prices['%'],
#                                                                        prices['open'])
#         irc.reply(reply_str)

Class = Stocks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
