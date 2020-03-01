###
# Copyright (c) 2018, cottongin
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

from supybot import utils, plugins, ircutils, callbacks, schedule, conf
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Soccer')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x
    
# Non-supybot imports
import requests
import pendulum
import pickle
import json

class Soccer(callbacks.Plugin):
    """Fetches soccer scores and other information"""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Soccer, self)
        self.__parent.__init__(irc)
        
        self.PICKLEFILE = conf.supybot.directories.data.dirize("soccer-leagues.db")
        
        self.BASE_API_URL = ('http://site.api.espn.com/apis/site/v2/sports/'
                             'soccer/{league}/scoreboard?lang=en&region=us&'
                             'dates={date}&league={league}')
        # http://site.api.espn.com/apis/site/v2/sports/soccer/eng.2/scoreboard
        # ?lang=en&region=us&calendartype=whitelist
        # &limit=100&dates=20181028&league=eng.2
        
        self.FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow',
                           'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            
        try:
            with open(self.PICKLEFILE, 'rb') as handle:
                self.LEAGUE_MAP = pickle.load(handle)
        except:
            self.LEAGUE_MAP = {
                'epl': 'eng.1', 'mls': 'usa.1', 'ecl': 'eng.2', 'uefac': 'uefa.champions',
                'uefae': 'uefa.europa', 'efac': 'eng.fa', 'carabao': 'eng.league_cup',
                'liga': 'esp.1', 'bundesliga': 'ger.1', 'seriea': 'ita.1', 'ligue': 'fra.1',
                'bbva': 'mex.1', 'fifawc': 'fifa.world', 'wc': 'fifa.world', 'nations': 'uefa.nations',
                'concacaf': 'concacaf.nations.league_qual', 'africa': 'caf.nations_qual',
                'cl': 'eng.2',
            }
        
        # TO-DO / think about:
        """
        def periodicCheckGames():
            self.CFB_GAMES = self._fetchGames(None, '')
            
        periodicCheckGames()
        
        try:  # check scores.
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchCFBscores')
        except AssertionError:
            try:
                schedule.removeEvent('fetchCFBscores')
            except KeyError:
                pass
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchCFBscores')
        """
    def _dumpDB(self, db):
        with open(self.PICKLEFILE, 'wb') as handle:
            pickle.dump(db, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return
    
    @wrap(['admin','text'])
    def addleague(self, irc, msg, args, league):
        """<nickname> <espn league>
        Adds <espn league> to bot's leagues database"""
        
        league = league.lower()
        league = league.split()
        
        if len(league) > 2:
            return
        if league[0] in self.LEAGUE_MAP:
            irc.reply('Already in database')
            return
        self.LEAGUE_MAP[league[0]] = league[1]
        self._dumpDB(self.LEAGUE_MAP)
        irc.replySuccess()
        return
    
    @wrap(['admin','text'])
    def remleague(self, irc, msg, args, league):
        """<nickname>
        Removes <nickname> from bot's leagues database"""
        
        league = league.lower()
        league_t = league.split()
        
        if len(league_t) > 1:
            return
        if league not in self.LEAGUE_MAP:
            irc.reply('Not found in database')
            return
        self.LEAGUE_MAP.pop(league, None)
        self._dumpDB(self.LEAGUE_MAP)
        irc.replySuccess()
        return
        
    @wrap([getopts({'date': 'somethingWithoutSpaces',
                    'league': 'somethingWithoutSpaces',
                    'tz': 'somethingWithoutSpaces'}), optional('text')])
    def soccer(self, irc, msg, args, options, filter_team=None):
        """--league <league> (--date <date>) (team)
        Fetches soccer scores for given team on date in provided league, defaults to current 
        day if no date is provided and all teams in league if no team provided.
        """
        
        now = pendulum.now()
        today = now.in_tz('US/Eastern').format('YYYYMMDD')
        
        options = dict(options)
        date = options.get('date')
        league = options.get('league')
        tz = options.get('tz') or 'US/Eastern'
        
        if date:
            date = self._parseDate(date)
            date = pendulum.parse(date, strict=False).format('YYYYMMDD')
        else:
            date = today
            
        if filter_team:
            filter_team = filter_team.lower()  
            if filter_team in self.LEAGUE_MAP and not league:
                league = self.LEAGUE_MAP[filter_team]
                filter_team = None
            
        if not league:
            irc.reply('ERROR: You must provide a league via --league <league>')
            doc = irc.getCallback('Soccer').soccer.__doc__ 
            doclines = doc.splitlines()
            s = '%s' % (doclines.pop(0))
            if doclines:
                help = ' '.join(doclines)
                s = '(%s) -- %s' % (ircutils.bold(s), help)
                s = utils.str.normalizeWhitespace(s)
            irc.reply(s)
            vl = ', '.join(k for k in self.LEAGUE_MAP)
            irc.reply('Valid leagues: {}'.format(vl))
            return
        
        mapped_league = self.LEAGUE_MAP.get(league.lower())
        
        if not mapped_league and '.' not in league:
            irc.reply('ERROR: {} not found in valid leagues: {}'.format(
                league, ', '.join(k for k in self.LEAGUE_MAP)))
            return
        elif not mapped_league:
            mapped_league = league.lower()
        
        url = self.BASE_API_URL.format(date=date, league=mapped_league)
        
        try:
            data = requests.get(url)
        except:
            irc.reply('Something went wrong fetching data from {}'.format(
                data.url))
            return
        
        data = json.loads(data.content)
        
        if 'leagues' not in data:
            irc.reply('ERROR: {} not found in valid leagues: {}'.format(
                league, ', '.join(k for k in self.LEAGUE_MAP)))
            return
        
        league_name = ircutils.bold(data['leagues'][0]['name'])
        
        if not data['events']:
            irc.reply('No matches found')
            return
        
        comps = []
        for event in data['events']:
            comps.append(event['competitions'][0])
            
        #print(comps)
        single = False
        if len(comps) == 1:
            single = True
        matches = []
        for match in comps:
            #print(match)
            time = pendulum.parse(match['date'], strict=False).in_tz(tz).format('h:mm A zz')
            long_time = pendulum.parse(match['date'], strict=False).in_tz(tz).format('ddd MMM Do h:mm A zz')
            teams_abbr = [match['competitors'][0]['team']['abbreviation'].lower(), 
                          match['competitors'][1]['team']['abbreviation'].lower()]
            for team in match['competitors']:
                if team['homeAway'] == 'home':
                    home = team['team']['shortDisplayName'] 
                    home_abbr = team['team']['abbreviation']
                    home_score = team['score']
                elif team['homeAway'] == 'away':
                    away = team['team']['shortDisplayName'] 
                    away_abbr = team['team']['abbreviation']
                    away_score = team['score']
            clock = match['status']['displayClock']
            final = match['status']['type']['completed']
            status = match['status']['type']['shortDetail']
            if final:
                status = ircutils.mircColor(status, 'red')
            if status == 'HT':
                status = ircutils.mircColor(status, 'orange')
            state = match['status']['type']['state']
            
            if state == 'pre':
                #
                if not filter_team and not single:
                    string = '{1} - {0} {2}'.format(away_abbr, home_abbr, time)
                else:
                    string = '{1} - {0}, {2}'.format(away, home, long_time)
            elif state == 'in':
                #
                if away_score > home_score:
                    away = ircutils.bold(away)
                    away_abbr = ircutils.bold(away_abbr)
                    away_score = ircutils.bold(away_score)
                elif home_score > away_score:
                    home = ircutils.bold(home)
                    home_abbr = ircutils.bold(home_abbr)
                    home_score = ircutils.bold(home_score)
                if not filter_team and not single:
                    string = '{2} {3}-{1} {0} {4}'.format(away_abbr, away_score, home_abbr, home_score, clock)
                else:
                    string = '{2} {3}-{1} {0} {4}'.format(away, away_score, home, home_score, clock)
            elif state == 'post':
                #
                if away_score > home_score:
                    away = ircutils.bold(away)
                    away_abbr = ircutils.bold(away_abbr)
                    away_score = ircutils.bold(away_score)
                elif home_score > away_score:
                    home = ircutils.bold(home)
                    home_abbr = ircutils.bold(home_abbr)
                    home_score = ircutils.bold(home_score)
                if not filter_team and not single:
                    string = '{2} {3}-{1} {0} {4}'.format(away_abbr, away_score, home_abbr, home_score, status)
                else:
                    string = '{2} {3}-{1} {0} {4}'.format(away, away_score, home, home_score, status)
            else:
                if not filter_team and not single:
                    string = '{1} - {0} {2}'.format(away_abbr, home_abbr, time)
                else:
                    string = '{1} - {0}, {2}'.format(away, home, long_time)
                    
            if filter_team:
                #print(filter_team, string)
                if filter_team in string.lower() or filter_team in teams_abbr:
                    matches.append(string)
            else:
                matches.append(string)
                
        if not matches:
            irc.reply('No matches found')
            return
        
        irc.reply('{}: {}'.format(league_name, ' | '.join(s for s in matches)))
        
        return
                
    
    def _parseDate(self, string):
        """parse date"""
        date = string[:3].lower()
        if date in self.FUZZY_DAYS or string.lower() in self.FUZZY_DAYS:
            if date == 'yes':
                date_string = pendulum.yesterday('US/Eastern').format('YYYYMMDD')
                return date_string
            elif date == 'tod' or date == 'ton':
                date_string = pendulum.now('US/Eastern').format('YYYYMMDD')
                return date_string
            elif date == 'tom':
                date_string = pendulum.tomorrow('US/Eastern').format('YYYYMMDD')
                return date_string
            elif date == 'sun':
                date_string = pendulum.now('US/Eastern').next(pendulum.SUNDAY).format('YYYYMMDD')
                return date_string
            elif date == 'mon':
                date_string = pendulum.now('US/Eastern').next(pendulum.MONDAY).format('YYYYMMDD')
                return date_string
            elif date == 'tue':
                date_string = pendulum.now('US/Eastern').next(pendulum.TUESDAY).format('YYYYMMDD')
                return date_string
            elif date == 'wed':
                date_string = pendulum.now('US/Eastern').next(pendulum.WEDNESDAY).format('YYYYMMDD')
                return date_string
            elif date == 'thu':
                date_string = pendulum.now('US/Eastern').next(pendulum.THURSDAY).format('YYYYMMDD')
                return date_string
            elif date == 'fri':
                date_string = pendulum.now('US/Eastern').next(pendulum.FRIDAY).format('YYYYMMDD')
                return date_string
            elif date == 'sat':
                date_string = pendulum.now('US/Eastern').next(pendulum.SATURDAY).format('YYYYMMDD')
                return date_string
            else:
                return string
        else:
            return string
        


Class = Soccer


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
