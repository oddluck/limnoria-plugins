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
        
        # response headers from Postman go inside {} as 'key': 'value' format
        self.HEADERS = {
            
        }
        
        
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
        
        googs = ["GOOGL:US", "GOOG:US"]
        for symbol in data:
            if symbol['id'] in googs:
                name = symbol['shortName'].title()
            else:
                name = symbol['longName']
            name = ircutils.bold(name)
            current_price = symbol['price']
            change = symbol['priceChange1Day']
            pct_change = symbol['percentChange1Day']
            prv_close = symbol['previousClosingPriceOneTradingDayAgo']
            market_cap = _humifyCap(symbol.get('marketCap'))
            highYear = '${:.2f}'.format(symbol['highPrice52Week'])
            lowYear = '${:.2f}'.format(symbol['lowPrice52Week'])
            pe_ratio = symbol.get('priceEarningsRatio')
            ytd = symbol.get('totalReturnYtd')
            oneyr = symbol.get('totalReturn1Year')
            
            if pe_ratio:
                pe_ratio = ' | \x02P/E Ratio:\x02 ${:.2f}'.format(pe_ratio)
            else:
                pe_ratio = ''
                
            if market_cap:
                market_cap = ' | \x02Market Cap:\x02 {} | '.format(market_cap)
            else:
                market_cap = ' | '
            
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
                      '{}\x0252wk High:\x02 {} | \x0252wk Low:\x02 {}'
                      '{}').format(
                name, current_price, change, pct_change, prv_close, market_cap,
                ircutils.mircColor(highYear, 'green'), ircutils.mircColor(lowYear, 'red'), pe_ratio)
            if ytd:
                if ytd > 0:
                    ytd = ircutils.mircColor('{:+.2f}%'.format(ytd), 'green')
                elif ytd < 0:
                    ytd = ircutils.mircColor('{:.2f}%'.format(ytd), 'red')
                else:
                    ytd = '{:.2f}%'.format(ytd)
                string += ' | \x02YTD Return:\x02 {}'.format(ytd)

            if oneyr:
                if oneyr > 0:
                    oneyr = ircutils.mircColor('{:+.2f}%'.format(oneyr), 'green')
                elif oneyr < 0:
                    oneyr = ircutils.mircColor('{:.2f}%'.format(oneyr), 'red')
                else:
                    oneyr = '{:.2f}%'.format(oneyr)
                string += ' | \x021Yr Return:\x02 {}'.format(oneyr)
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
            ytd = symbol.get('totalReturnYtd')
            oneyr = symbol.get('totalReturn1Year')
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
                    
                    if ytd:
                        if ytd > 0:
                            ytd = ircutils.mircColor('{:+.2f}%'.format(ytd), 'green')
                        elif ytd < 0:
                            ytd = ircutils.mircColor('{:.2f}%'.format(ytd), 'red')
                        else:
                            ytd = '{:.2f}%'.format(ytd)
                        string += ' :: YTD Return: {}'.format(ytd)
                    
                    if oneyr:
                        if oneyr > 0:
                            oneyr = ircutils.mircColor('{:+.2f}%'.format(oneyr), 'green')
                        elif oneyr < 0:
                            oneyr = ircutils.mircColor('{:.2f}%'.format(oneyr), 'red')
                        else:
                            oneyr = '{:.2f}%'.format(oneyr)
                        string += ' :: 1Yr Return: {}'.format(oneyr)
                    
                    ticker.append(string)
            else:
                ticker.append(string)
        
        return ticker
    
    @wrap(['somethingWithoutSpaces'])
    def coin(self, irc, msg, args, optcoin):
        """Fetches current values for a given coin"""
        
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
        
        try:
            data = requests.get(url, headers=self.HEADERS).json()
        except:
            irc.reply('Something went wrong fetching data')
            return
        
        ticker = self._parsePrices(data, optmarket)
            
        irc.reply(' | '.join(t for t in ticker))
        return
    
    @wrap([commalist('text')])
    def ticker(self, irc, msg, args, optmarket):
        """Fetches current values for several commodities"""
        
        url = ('https://www.bloomberg.com/markets2/api/datastrip/'
               '{markets_to_fetch}'
               '?locale=en&customTickerList=true')
        
        search_url = ('https://search.bloomberg.com/lookup.json?'
                      'types=Company_Public,Index,Fund,Currency,'
                      'Commodity,Bond&exclude_subtypes=label:editorial'
                      '&group_size=3,3,3,3,3,3'
                      '&fields=name,slug,ticker_symbol,organization,title,primary_site'
                      '&query={query}')
        
        for idx,v in enumerate(optmarket):
            if v == 'google':
                optmarket[idx] = 'googl'
                optmarket.append('goog')
        
        mkts = []
        for m in optmarket:
            try:
                tmp_rank = 0
                tmp_symbol = ''
                search_data = requests.get(search_url.format(query=m.lower()), headers=self.HEADERS).json()
                for group in search_data:
                    if group['total_results'] == 0:
                        continue
                    for result in group['results']:
                        if result['score'] > tmp_rank:
                            tmp_symbol = result['ticker_symbol']
                            tmp_rank = result['score']
                if not tmp_symbol:
                    tmp_symbol = m.upper() + ":US"
                mkts.append(tmp_symbol)
            except:
                mkts.append(m.upper() + ':US')
        
        m = '{}'.format(','.join(i.upper() for i in mkts[:5]))
        
        url = url.format(markets_to_fetch=m)
        
        try:
            data = requests.get(url, headers=self.HEADERS).json()
        except:
            irc.reply('Something went wrong fetching data, or couldn\'t find provided symbol')
            return
        
        ticker = self._parseTickerPrices(data, optmarket)
            
        for symbol in ticker:
            irc.reply(symbol)
        return
    

Class = Stocks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
