###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
#
###

import requests
import pendulum

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Odds')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Odds(callbacks.Plugin):
    """Fetches odds"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Odds, self)
        self.__parent.__init__(irc)
        
    @wrap([getopts({'nfl': '', 'mlb': '', 'nhl': '', 'nba': '',
                    'cfb': '', 'cbb': '', 'NFL': '', 'MLB': '',
                    'NHL': '', 'NBA': '', 'CFB': '', 'CBB': ''}), 
           optional('text')])
    def odds(self, irc, msg, args, optlist, opttext=None):
        """--<league> [<team>]
        Fetches odds for given league with an optional team to filter
        """
        
        optlist = dict(optlist)
        #print(optlist)
        validLeagues = ['--NFL', '--MLB', '--NHL', '--NBA', '--CFB', '--CBB']
        leagueMap = {'cfb': 1, 'nfl': 2, 'mlb': 3, 'nba': 4,
                     'cbb': 5, 'nhl': 6}
        idMap = {'1': 'CFB', '2': 'NFL', '3': 'MLB', '4': 'NBA',
                 '5': 'CBB', '6': 'NHL'}
        
        if not optlist:
            irc.reply(('Error: Must provide a valid league. '
                       'Valid leagues are: {}'.format(
                           ', '.join(x for x in validLeagues))))
            return
        
        leagues = []
        outputLeagues = []
        for key, value in optlist.items():
            league = key.lower() if value == True else None
            if league:
                leagues.append(leagueMap[league])
                outputLeagues.append(idMap[str(leagueMap[league])])
                
        base_url = 'https://therundown.io/api/v1/sports/{league}/events/{date}?offset=300'
        data = []
        today = pendulum.now('US/Pacific').format('YYYY-MM-DD')
        tdate = pendulum.now('US/Pacific')
        
        #if 6 in leagues:
        #    dates = [tdate.add(days=1).format('YYYY-MM-DD')]
        for idx, league in enumerate(leagues):
            #print(league)
            if league == 6:
                #print('one')
                headers = {'accept': 'application/json, text/plain, */*', 
                           'accept-encoding': 'gzip, deflate, br', 
                           'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8', 
                           'origin': 'https://www.oddsshark.com/',
                           'referer': 'https://www.oddsshark.com/nhl/odds', 
                           'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
            
                data.append(requests.get('https://io.oddsshark.com/ticker/nhl', headers=headers).json())
                
            elif league == 4:
                #print('one')
                headers = {'accept': 'application/json, text/plain, */*', 
                           'accept-encoding': 'gzip, deflate, br', 
                           'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8', 
                           'origin': 'https://www.oddsshark.com/',
                           'referer': 'https://www.oddsshark.com/nba/odds', 
                           'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
            
                data.append(requests.get('https://io.oddsshark.com/ticker/nba', headers=headers).json())
            else:
                #print('two')
                url = base_url.format(league=league, date=today)
                print(url)
                data.append(requests.get(url).json())
            
                if league == 2 or league == 1 or league == 3:
                    if league == 2 or league == 1:
                        dates = [tdate.add(days=1).format('YYYY-MM-DD'), tdate.add(days=2).format('YYYY-MM-DD'),
                                 tdate.add(days=3).format('YYYY-MM-DD'), tdate.add(days=4).format('YYYY-MM-DD'),
                                 tdate.add(days=5).format('YYYY-MM-DD'), tdate.add(days=6).format('YYYY-MM-DD')]
                    if league == 3:
                        dates = [tdate.add(days=1).format('YYYY-MM-DD'), tdate.add(days=2).format('YYYY-MM-DD'),
                                 tdate.add(days=3).format('YYYY-MM-DD'), tdate.add(days=4).format('YYYY-MM-DD')]
#                     if league == 6:
#                         dates
                    for nflday in dates:
                        url = base_url.format(league=league, date=nflday)
                        #print(url)
                        #tdata = requests.get(url).json()
                        data[idx]['events'].extend(requests.get(url).json()['events'])
        #print(data)
#         
#try:            
#             print(data[0], data[1])
#         except:
#             pass
            
        cleaned_data = self._parseData(data, opttext, leagues)
        
        if not cleaned_data:
            irc.reply('Error: No odds found for that query')
            return
        
        cleaned_data = self._sortData(cleaned_data)

        #print(outputLeagues)
        for idx, item in enumerate(cleaned_data):
            if item:
                if 'Games with' not in item:
                    if len(item) > 8:
                        if len(item) > 16:
                            split = len(item)//3
                            irc.reply('\x02{}:\x02 {}'.format(outputLeagues[idx], ' | '.join(x for x in item[:split])))
                            irc.reply('{}'.format(' | '.join(x for x in item[split:split+split])))
                            irc.reply('{}'.format(' | '.join(x for x in item[split+split:])))
                            return
                        split = len(item)//2
                        irc.reply('\x02{}:\x02 {}'.format(outputLeagues[idx], ' | '.join(x for x in item[:split])))
                        irc.reply('{}'.format(' | '.join(x for x in item[split:])))
                    else:
                        irc.reply('\x02{}:\x02 {}'.format(outputLeagues[idx], ' | '.join(x for x in item)))
                else:
                    irc.reply(item)
            else:
                irc.reply('\x02{}:\x02 {}'.format(outputLeagues[idx], 'No results found for that query'))
        
    def _parseData(self, data, team, leagues, tz=None):
        
        new_data = []
        
        #print(len(data['events']))
        #print(len(data))
        
        for idx, item in enumerate(data):
            #print(leagues[idx])
            if leagues[idx] in [4, 6]:
                if leagues[idx] == 6:
                    translate_team = {
                        'WAS': 'WSH', 'MON': 'MTL', 'CLB': 'CBJ',
                        'NJ': 'NJD', 'SJ': 'SJS', 'LA': 'LAK',
                        'TB': 'TBL', 'NAS': 'NSH', 'CAL': 'CGY',
                    }
                else:
                    translate_team = {'CHR': 'CHA', 'NY': 'NYK', 'SAN': 'SAS', 'PHO': 'PHX'}
                #print(item)
                today = pendulum.now()
                tmp_data = []
                no_odds_str = 'Games with no odds yet: '
                no_odds = []
                for event in item['matchups']:
                    if event['type'] != 'matchup':
                        continue
                    date = pendulum.parse(event['event_date']).format('M/D h:mm A')
                    home = event['home_short_name'] if event['home_short_name'] not in translate_team else translate_team[event['home_short_name']]
                    away = event['away_short_name'] if event['away_short_name'] not in translate_team else translate_team[event['away_short_name']]
                    shome = home
                    saway = away
                    home_spread = ''
                    away_spread = ''
                    if event['away_odds']:
                        if float(event['away_odds']) < 0:
                            saway = ircutils.bold(away)
                        elif float(event['home_odds']) < 0:
                            shome = ircutils.bold(home)
                    ou = '-' if not event['total'] else event['total']
                    
                    ml = '{}/{}'.format(
                        '-' if not event['away_odds'] else self._colorize(float(event['away_odds']), float(event['home_odds'])),
                        '-' if not event['home_odds'] else self._colorize(float(event['home_odds']), float(event['away_odds'])))
                    string = '{}{} @ {}{} ↕{} {} ({})'.format(
                        saway, away_spread, shome, home_spread,
                        ou, ml, date)
                    if ou == '-' and ml == '-/-' and (today.format('YYYY-MM-DD') in event['event_date'] or today.add(days=1).format('YYYY-MM-DD') in event['event_date']) and not team:
                        no_odds.append('{} @ {}'.format(away, home))
                    if team:
                        if today.format('YYYY-MM-DD') in event['event_date'] or today.add(days=1).format('YYYY-MM-DD') in event['event_date']:
                            if team.lower() == home.lower() or team.lower() == away.lower():
                                if ou != '-' and ml != '-/-':
                                    tmp_data.append(string)
                    else:
                        if today.format('YYYY-MM-DD') in event['event_date'] or today.add(days=1).format('YYYY-MM-DD') in event['event_date']:
                            if ou != '-' and ml != '-/-':
                                tmp_data.append(string)
                if tmp_data:
#                     if no_odds:
#                         tmp_data.append('{}{}'.format(no_odds_str, ', '.join(i for i in no_odds)))
                    new_data.append(tmp_data)
                    if no_odds:
                        new_data.append('{}{}'.format(no_odds_str, ', '.join(i for i in no_odds)))
                else:
                    new_data.append(None)
            else:
                tmp_data = []
                #print(len(item['events']))
                for event in item['events']:
                    #aff_id = '7' # default id
                    aff_id = None
                    for aff in event['lines']:
                        if 'Bookmaker' in event['lines'][aff]['affiliate']['affiliate_name']:
                            aff_id = aff
                    if not aff_id:
                        for aff in event['lines']:
                            aff_id = aff
                            break
                    if leagues[idx] == 2 or leagues[idx] == 1 or leagues[idx] == 3:
                        if tz:
                            date = pendulum.parse(event['event_date']).in_tz(tz).format('M/D h:mm A zz')
                        else:
                            date = pendulum.parse(event['event_date']).in_tz('US/Eastern').format('M/D h:mm A')
                    else:
                        if tz:
                            date = pendulum.parse(event['event_date']).in_tz(tz).format('h:mm A zz')
                        else:
                            date = pendulum.parse(event['event_date']).in_tz('US/Eastern').format('h:mm A')
                    home = event['teams_normalized'][1]['abbreviation']
                    away = event['teams_normalized'][0]['abbreviation']
                    home_name = event['teams_normalized'][1]['name']
                    away_name = event['teams_normalized'][0]['name']
                    check_spread = False
                    eventdate = pendulum.parse(event['lines'][aff_id]['spread']['date_updated'], strict=False).int_timestamp
                    updated = pendulum.parse(event['event_date'], strict=False).int_timestamp
                    #print(eventdate, updated)
                    if pendulum.parse(event['lines'][aff_id]['spread']['date_updated'], strict=False).int_timestamp > pendulum.parse(event['event_date'], strict=False).int_timestamp:
                        if leagues[idx] == 3:
                            check_spread == True
                    if (leagues[idx] != 3 and team):
                        home_spread = '[{}]'.format(
                            self._parseSpread(event['lines'][aff_id]['spread']['point_spread_home']))
                        away_spread = '[{}]'.format(
                            self._parseSpread(event['lines'][aff_id]['spread']['point_spread_away']))
                    else:
                        home_spread = ''
                        away_spread = ''
                    saway = away
                    shome = home
                    if check_spread:
                        moneyline_away = event['lines'][aff_id]['spread']['point_spread_away_money']
                        moneyline_home = event['lines'][aff_id]['spread']['point_spread_home_money']
                    else:
                        moneyline_away = event['lines'][aff_id]['moneyline']['moneyline_away']
                        moneyline_home = event['lines'][aff_id]['moneyline']['moneyline_home']
                        
                    if moneyline_away < 0:
                        saway = ircutils.bold(away)
                    elif moneyline_home < 0:
                        shome = ircutils.bold(home)
                    #print(event['lines'])
                    ou = '-' if event['lines'][aff_id]['total']['total_over'] == 0.0001 else event['lines'][aff_id]['total']['total_over']
                    ml = '{}/{}'.format(
                        self._colorize(moneyline_away, moneyline_home),
                        self._colorize(moneyline_home, moneyline_away))
                    string = '{}{} @ {}{} ↕{} {} ({})'.format(
                        saway, away_spread, shome, home_spread,
                        ou, ml, date)
                    if team:
                        print(team.lower(), home_name.lower(), away_name.lower())
                        if (team.lower() == home.lower() or team.lower() == away.lower()) or \
                           (team.lower() == home_name.lower() or team.lower() == away_name.lower()):
                            if ou != '-' and ml != '-/-':
                                tmp_data.append(string)
                    else:
                        if ou != '-' and ml != '-/-':
                            tmp_data.append(string)
                #print(tmp_data)
                if tmp_data:
                    new_data.append(tmp_data)
                else:
                    new_data.append(None)
                    
        #print(new_data)
            
        return new_data
    
    def _sortData(self, data):
        #print(data)
        for item in data:
            #print(item)
            if item:
                if 'Games with' not in item:
                #tmp = None
                #for game in item:
                #    if 'Games with' in game:
                #        tmp = item.pop()
                    item.sort(key=lambda x:pendulum.parse(
                        x.split('(')[1].replace(')',''), strict=False).int_timestamp)
                #if tmp:
                #    item.append(tmp)

        return data
    
    def _parseSpread(self, number):
        if number == 0.0001:
            number = 0
        if number > 0:
            number = '+{}'.format(number)
        else:
            number = number
            
        return number
    
    def _colorize(self, number, vs):
        if number == 0.0001:
            return '-'
        if number > 0:
            number = '+{}'.format(number)
            number = ircutils.mircColor(number, 'red')
        elif number < 0:
            if vs < 0:
                if number < vs:
                    number = '{}'.format(number)
                    number = ircutils.mircColor(number, 'green')
                else:
                    number = '{}'.format(number)
                    number = ircutils.mircColor(number, 'red')
            else:
                number = '{}'.format(number)
                number = ircutils.mircColor(number, 'green')
        else:
            number = number
            
        return number

Class = Odds


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
