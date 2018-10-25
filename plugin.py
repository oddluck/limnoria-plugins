# MLBScores
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('MLBScores')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

import requests
import httplib2
import pendulum
import re
import datetime
import pytz
import time
import dateutil.parser
import urllib
import collections
import jellyfish
from operator import itemgetter
# from pprint import pprint
# from pybaseball import playerid_lookup
# from pybaseball import pitching_stats_bref
# from pybaseball import batting_stats_bref


class MLBScores(callbacks.Plugin):
    """Plugin to fetch MLB scores from the MLB.com API"""
    threaded = True

    def dprint(self, thing, override=False):
        """debug print"""
        if self._DEBUG == True or override:
            print(thing)
        return
    
    def __init__(self, irc):
        self.__parent = super(MLBScores, self)
        self.__parent.__init__(irc)
        
        self._DEBUG = False

        self._HTTP = httplib2.Http('.cache')

        self._SCOREBOARD_ENDPOINT = ('https://statsapi.mlb.com/api/v1/schedule'
                                     '?sportId=1&date={}'
                                     '&hydrate=team(leaders(showOnPreview('
                                     'leaderCategories=[homeRuns,runsBattedIn,'
                                     'battingAverage],statGroup=[pitching,'
                                     'hitting]))),linescore(matchup,runners),'
                                     'flags,liveLookin,review,broadcasts(all),'
                                     'decisions,person,probablePitcher,stats,'
                                     'homeRuns,previousPlay,game(content('
                                     'media(featured,epg),summary),tickets),'
                                     'seriesStatus(useOverride=true)')

        self._FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow',
                            'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

        #pendulum.set_formatter('alternative')

        self._TEAM_BY_TRI, self._TEAM_BY_ID = self._getTeams()
        self._STATUSES = self._getStatuses()
        self._ACTIVE_PLAYERS = self._fetchActivePlayers()

        self._TEAM_BY_NICK = {'fish': 'MIA', 'poop': 'NYY', 'goat': 'BOS',
                              'best': 'BOS', 'worst': 'NYY', '💩': 'NYY'}
        
        self._player_aliases = {'buttholz':       'Clay Buchholz',
                                'sucker punch':   'Gary Sanchez',
                                'sucker puncher': 'Gary Sanchez',
                                'big sexy':       'Bartolo Colon',
                                'sexx dragon':    'Joe Mauer',
                                'big papi':       'David Ortiz',
                                'dp':             'dustin pedroia',
                                'lil dp':         'dustin pedroia',
                                'panda':          'pablo sandoval',
                                'gap tooth':      'aaron judge',
                                'jv':             'justin verlander',
                                'comebacker':     'justin verlander',
                                'justdongs':      'jd martinez',
                                'justdongers':    'jd martinez',
                                'erod':           'eduardo rodriguez',
                                'jdmart':         'jd martinez',
                                'starlord':       'alex wilson',
                                'machado':        'dixon machado',
                                'douchebag':      'manny machado',
                                'strikeouts mcgee': 'giancarlo stanton',
                                'k machine':      'giancarlo stanton',
                                'swings and misses': 'giancarlo stanton',
                                'calendario':     'candelario',
                                'scrabble':       'marc rzepczynski',
                                'mr_pink':        'Enyel De Los Santos',
                                'jbj':            'jackie bradley jr.',
        }
        
        def periodicCheckGames():
            #print('MLBScores: Periodic check')
            self.MLB_GAMES = self._fetchGames(None, None)
            #print(self.CFB_GAMES)
            
        def periodicCheckPlayers():
            self._ACTIVE_PLAYERS = self._fetchActivePlayers()
            
        periodicCheckGames()
        
        try:  # check scores.
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchMLBscores')
        except AssertionError:
            try:
                schedule.removeEvent('fetchMLBscores')
            except KeyError:
                pass
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchMLBscores')
            
        try:  # check active rosters.
            schedule.addPeriodicEvent(periodicCheckPlayers, 3600, now=False, name='fetchMLBplayers')
        except AssertionError:
            try:
                schedule.removeEvent('fetchMLBplayers')
            except KeyError:
                pass
            schedule.addPeriodicEvent(periodicCheckPlayers, 3600, now=False, name='fetchMLBplayers')
        
    def _shortenUrl(self, url):
        """Shortens a long URL into a short one."""
        
        # Get a API key from bit.ly
        api_key = self.registryValue('bitlyAPIKey')
        
        url_enc = urllib.parse.quote_plus(url)
        api_url = 'https://api-ssl.bitly.com/v3/shorten?access_token={}&longUrl={}&format=txt'

        try:
            url = requests.get(api_url.format(api_key, url_enc))
            return url.text.strip()
        except:
            return url

    def _getTeams(self):
        """fetches teams and tricodes"""

        url = 'https://statsapi.mlb.com/api/v1/teams?sportId=1'

        data = requests.get(url).json()

        tmp1 = {}
        tmp2 = {}
        for team in data['teams']:
            tmp1[team['abbreviation']] = team['id']
            tmp2[str(team['id'])] = team['abbreviation']
        
        return tmp1, tmp2

    def _getStatuses(self):

        url = 'http://statsapi.mlb.com/api/v1/gameStatus'

        data = requests.get(url).json()

        tmp = {}
        for status in data:
            tmp[status['statusCode']] = status['detailedState']

        return tmp
    
    @wrap(['text'])
    def recap(self, irc, msg, args, irc_args):
        """<team> [<date>]
        Returns MLB Recap Videos
        """

        team, date, tz = self._parseInput(irc_args)
        date = pendulum.parse(date)
        if date is None:
            date = datetime.datetime.now().strftime("%y-%m-%d")
            hdate = datetime.datetime.now().strftime("%m/%d/%y")
        else:
#             team, date, tz = self._parseInput(irc_args)
#             for form in ["%d%b", "%d %b", "%b%d", "%b %d", "%d%B", "%d %B", "%b%B", "%b %B", "%B %d", "%B%d", "%Y%m%d", "%Y-%m-%d", "%m%d"]:
#                 result = self.api_get_date(date, form)
#                 if result is not None:
#                     break
#             if result is None:
#                 return("Use the following format: Apr10 or 10Apr or YYYYMMDD")

            day = str(date.day)
            month = str(date.month)
            year = date.year

            if year == 1900:
                year = 2018

            if (year < 2016):
                irc.reply("Sorry, the API only back dates until 2016")
                return
            if len(day) == 1:
                day = "0{}".format(day)
            if len(month) == 1:
                month = "0{}".format(month)

            date = "{}-{}-{}".format(year, month, day)
            hdate = "{}/{}/{}".format(month, day, str(year)[2:])

        #team = self.MLBFindTeam(team.upper(), 0)
#         if len(team) > 3:
#             irc.reply(team)
#             return
        #print(team)
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={}&hydrate=linescore(matchup,runners),game(content(media(featured,epg),summary),tickets)&teamId={}".format(date, team)
        content = requests.get(url).json()
        recap = False
        try:
            for each in content['dates'][0]['games']:
                home = int(each['teams']['home']['team']['id'])
                away = int(each['teams']['away']['team']['id'])
                #print(team, home, away)
                if int(team) == home or int(team) == away:
                    newurl = "https://statsapi.mlb.com/api/v1/game/{}/content".format(each['gamePk'])
                    newcontent = requests.get(newurl).json()
                    url = newcontent['media']['epgAlternate'][4]['items'][0]['playbacks'][3]['url']
                    duration = newcontent['media']['epgAlternate'][4]['items'][0]['duration']
                    duration = datetime.datetime.strptime(duration, "%H:%M:%S").strftime("%Mm%Ss").lstrip("0").lstrip("m")
                    away_s = each['teams']['away']['score']
                    home_s = each['teams']['home']['score']
                    headline = "{} {} @ {} {}".format(self._TEAM_BY_ID[str(away)], away_s, self._TEAM_BY_ID[str(home)], home_s)
                    blurb = newcontent['media']['epgAlternate'][4]['items'][0]['blurb']
                    date, info = blurb.split(":")
                    url = self._shortenUrl(url)
                    irc.reply("\x02Recap: {}\x02 |{}".format(headline, info))
                    recap = True
                    for items in newcontent['media']['epgAlternate'][4]['items'][0]['playbacks']:
                        if items['name'] == 'FLASH_2500K_1280X720':
                            mp4 = self._shortenUrl(items['url'])
                        if items['name'] == 'HTTP_CLOUD_WIRED_WEB':
                            hls = self._shortenUrl(items['url'])
                    irc.reply("\x02MP4\x02: {} | \x02HLS\x02: {} | \x02{}\x02".format(mp4, hls, duration))
        except Exception as e:
            #print(e)
            irc.reply("\x02{}\x02: No recap video available for {}".format(hdate, self._TEAM_BY_ID[team]))

    @wrap
    def mlbwildcard(self, irc, msg, args):
        """Fetches wildcard standings for MLB"""
        
        url = 'https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={season}&standingsTypes=wildCard&hydrate=division,conference,sport,league,team(nextSchedule(team,gameType=[R,F,D,L,W,C],inclusive=false),previousSchedule(team,gameType=[R,F,D,L,W,C],inclusive=true))'
        season = pendulum.now().year
        url = url.format(season=season)
        
        try:
            data = requests.get(url)
            data = data.json()
        except:
            irc.reply('Error fetching standings')
            return
        
        al_data = data['records'][0]
        nl_data = data['records'][1]
        
        alwc = []
        nlwc = []
        
        al = self._blue(self._bold(al_data['league']['abbreviation'] + 'WC'))
        nl = self._red(self._bold(nl_data['league']['abbreviation'] + 'WC'))
        
        # BOS +2.5 (W-L) W2 | NYY - (W-L) W2 | 
        
        for team in al_data['teamRecords']:
            string = '{} {} {} {}{}'
            string = string.format(
                self._bold('{:3}'.format(team['team']['abbreviation'])),
                '-' + team['wildCardGamesBack'] if ('-' not in team['wildCardGamesBack'] and '+' not in team['wildCardGamesBack']) else team['wildCardGamesBack'],
                '({}-{})'.format(team['wins'], team['losses']),
                self._green(team['streak']['streakCode']) if 'W' in team['streak']['streakCode'] else self._red(team['streak']['streakCode']),
                ' E#{}'.format(team['wildCardEliminationNumber']) if '-' not in team['wildCardEliminationNumber'] else ''
            )
            if team['wildCardEliminationNumber'] != 'E':
                alwc.append(string)
            
        for team in nl_data['teamRecords']:
            string = '{} {} {} {}{}'
            string = string.format(
                self._bold('{:3}'.format(team['team']['abbreviation'])),
                '-' + team['wildCardGamesBack'] if ('-' not in team['wildCardGamesBack'] and '+' not in team['wildCardGamesBack']) else team['wildCardGamesBack'],
                '({}-{})'.format(team['wins'], team['losses']),
                self._green(team['streak']['streakCode']) if 'W' in team['streak']['streakCode'] else self._red(team['streak']['streakCode']),
                ' E#{}'.format(team['wildCardEliminationNumber']) if '-' not in team['wildCardEliminationNumber'] else ''
            )
            if team['wildCardEliminationNumber'] != 'E':
                nlwc.append(string)
            
        al_string = '{}: {}'.format(al, ' | '.join(string for string in alwc))
        nl_string = '{}: {}'.format(nl, ' | '.join(string for string in nlwc))
        irc.reply(al_string)
        irc.reply(nl_string)
    
    
    @wrap([optional('text')])
    def mlbstandings(self, irc, msg, args, irc_args=None):
        """[<division>]
        Fetches standings for given division, defaults to all divisions if not provided
        """
        
        valid_leagues = ['ALE', 'ALW', 'ALC',
                         'NLE', 'NLW', 'NLC']
        table = False
        if irc_args:
            if '--table' in irc_args:
                table = True
                irc_args = irc_args.replace('--table', '')
                irc_args = irc_args.strip()
            if irc_args.upper() not in valid_leagues:
                irc.reply('Error: invalid league')
                return
        
        now = pendulum.now().year
        url = ('https://statsapi.mlb.com/api/v1/standings?leagueId=103,104'
               '&season={season}&standingsTypes=regularSeason'
               '&hydrate=division,conference,sport,league,team'
               '(nextSchedule(team,gameType=[R,F,D,L,W,C],inclusive=false),'
               'previousSchedule(team,gameType=[R,F,D,L,W,C],inclusive=true))')
        url = url.format(season=now)
        
        try:
            data = requests.get(url)
            data = data.json()
        except:
            irc.reply('Error fetching standings')
            return
        
        #print(data['records'][0])
        
        data = data['records']
        
        # ALE: BOS - (103-50) L2 | NYY -10 (94-50) W2 | 
        
        standings = collections.OrderedDict()
        divisions = {}
        for league in data:
            abbrv = league['division']['abbreviation']
            short_name = league['division']['nameShort']
            divisions[abbrv] = short_name
            standings[abbrv] = []
            for team in league['teamRecords']:
                tmp = collections.OrderedDict()
                tmp['team_abbrv'] = team['team']['abbreviation']
                tmp['games_back'] = team['divisionGamesBack']
                tmp['record'] = '({}-{})'.format(team['wins'], team['losses'])
                tmp['wins'] = team['wins']
                tmp['losses'] = team['losses']
                tmp['streak'] = team['streak']['streakCode']
                tmp['clinched'] = team['clinchIndicator'] if team['clinched'] else ''
                tmp['pct'] = team['leagueRecord']['pct']
                tmp['enum'] = team['eliminationNumber']
                tmp['wcgb'] = team['wildCardGamesBack']
                for split in team['records']['splitRecords']:
                    if 'lastTen' in split['type']:
                        tmp['last10'] = '{}-{}'.format(split['wins'], split['losses'])
                tmp['rs'] = team['runsScored']
                tmp['ra'] = team['runsAllowed']
                tmp['diff'] = team['runDifferential']
                tmp['xwl'] = '{}-{}'.format(team['records']['expectedRecords'][0]['wins'], team['records']['expectedRecords'][0]['losses'])
                tmp['home'] = '{}-{}'.format(team['records']['splitRecords'][0]['wins'], team['records']['splitRecords'][0]['losses'])
                tmp['away'] = '{}-{}'.format(team['records']['splitRecords'][1]['wins'], team['records']['splitRecords'][1]['losses'])
                tmp['.500'] = '{}-{}'.format(team['records']['splitRecords'][7]['wins'], team['records']['splitRecords'][7]['losses'])
                try:
                    if team['team']['abbreviation'] == team['team']['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['abbreviation']:
                        nextStr = 'at {}'.format(team['team']['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['team']['abbreviation'])
                    else:
                        nextStr = 'vs {}'.format(team['team']['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['abbreviation'])
                    tmp['next'] = '{} {}'.format(
                        pendulum.parse(team['team']['nextGameSchedule']['dates'][0]['date']).format('MMM D'),
                        nextStr                    
                    )
                except:
                    tmp['next'] = '-'
                tmp['team'] = team['team']['shortName']
                standings[abbrv].append(tmp)
                
        #print(standings['ALE'][0])
        #print(divisions)
        #irc.reply(standings['ALE']
        for league in standings:
            if not irc_args or (irc_args and not table):
                reply_string = '{}: '.format(self._bold(self._blue(league)) if 'A' in league else self._bold(self._red(league)))
                tmp_strings = []
                for idx, team in enumerate(standings[league]):
                    tmp_string = '{} {} {} {}'.format(
                        self._bold('{:3}'.format(team['team_abbrv'])),
                        '-' + '{:4}'.format(team['games_back']) if '-' not in team['games_back'] else team['games_back'],
                        team['record'],
                        self._green(team['streak']) if 'W' in team['streak'] else self._red(team['streak']))
                    tmp_strings.append(tmp_string)

                reply_string += ' | '.join(string for string in tmp_strings)
                if irc_args:
                    if irc_args.upper() == league:
                        irc.reply(reply_string)
                        return
                else:
                    irc.reply(reply_string)   
            else:
                if irc_args.upper() == league:
                    max_width = 0
                    for team in standings[league]:
                        if max_width < len(team['clinched'] + team['team']):
                            max_width = len(team['clinched'] + team['team'])
                    league_width = max_width - len(divisions[irc_args.upper()]) + 2
                    header = '{}{:{width}} W   L   PCT   GB   E#  WCGB  L10 STRK  RS   RA  DIFF  X-W/L    Home   Away  >.500  Next Game'
                    header = header.format(divisions[irc_args.upper()], ' ', width=league_width)
                    irc.reply(header)
                    for team in standings[league]:
                        reply_string = '{:{width}} {:3} {:3}  {}  {:^4}  {}   {:^4}  {}  {}  {}  {}  {:^4}  {:7} {}  {}  {}  {}'
                        reply_string = reply_string.format(
                            team['clinched'] + team['team'],
                            team['wins'], team['losses'],
                            team['pct'],
                            team['games_back'],
                            team['enum'],
                            team['wcgb'],
                            team['last10'],
                            team['streak'],
                            team['rs'],
                            team['ra'],
                            team['diff'],
                            team['xwl'],
                            team['home'],
                            team['away'],
                            team['.500'],
                            team['next'],
                            width=max_width
                        )
                        irc.reply(reply_string)
    

    @wrap([optional('text')])
    def mlb(self, irc, msg, args, irc_args=None):
        """[<team tri code>] [<date>]
        Fetches scores for given team and/or date. Defaults to today and all
        teams if no input provided"""

        tv = False
        if irc_args:
            if '--tv' in irc_args:
                tv = True
                irc_args = irc_args.replace('--tv','')
            if 'was' in irc_args:
                irc_args = irc_args.replace('was', 'wsh')

        team, date, tz = self._parseInput(irc_args)
        #print(team)
        #print(date)

        if not self.MLB_GAMES or date:
            #print('MLBScores: No cached scores, pulling fresh')
            self.MLB_GAMES = self._fetchGames(team, date)

        if not self.MLB_GAMES:
            irc.reply('No games found')
            return

        games = self._parseGames(self.MLB_GAMES, date, team)
        if not games:
            irc.reply('No games found')
            return
        games = self._sortGames(games)

        reply_string = self._replyAsString(team, games, tz, tv)

        # what = type(reply_string)
        # print(what)

        # print(reply_string)

        if type(reply_string) is tuple or type(reply_string) is list:
            for string in reply_string:
                irc.reply(string)
        else:
            irc.reply(reply_string)
            
        if date:
            self.MLB_GAMES = self._fetchGames(team)
            
    def _sanitizeName(self, name):
        """ Sanitize name. """

        name = name.lower()  # lower.
        #name = name.strip('.')  # remove periods.
        name = name.strip('-')  # remove dashes.
        name = name.strip("'")  # remove apostrophies.
        # possibly strip jr/sr/III suffixes in here?
        return name
    
    def _pf(self, irc, db, pname):
        """<e|r|s> <player>

        Find a player's page via google ajax. Specify DB based on site.
        """
        #print(pname)
        #print(self._player_aliases[pname.lower()])
        #print(pname.lower() in self._player_aliases)
        if pname.lower() in self._player_aliases:
            #print('hi')
            pname = self._player_aliases[pname.lower()]
        # sanitize.
        pname = self._sanitizeName(pname)
        print(pname)
        # db.
        if db == "e":  # espn.
            #splitsfix = '-site:espn.go.com/mlb/player/splits/'
            burl = "site:espn.go.com/mlb/player/ {0}".format(pname)
        elif db == "r":  # rworld.
            burl = "site:www.rotoworld.com/player/mlb/ %s" % pname
        elif db == "s":  # st.
            burl = "site:www.spotrac.com/mlb/ %s" % pname
        elif db == "br":  # br.
            burl = "site:www.baseball-reference.com/ %s" % pname

        try:
            goog = irc.getCallback("Google")
            if goog:
                try:
                    search = goog.search('{0}'.format(burl),'#reddit-baseball',{'smallsearch': True})
                    search = goog.decode(search)
                    if search:
                        #print(search[0])
                        url = search[0]['url']
                        title = search[0]['title']
                        title = title.replace('<b>', '')
                        title = title.replace('</b>', '')
                        title = title.strip()
                        if pname.title() in title:
                            title = title.split(pname.title())[0]
                            title += pname.title()
                        else:
                            title = title.split('-')[0]
                            title = title.strip()
                        #print(title)
                        #print(url)
                        #results = search[0].next_sibling.next_sibling
                        #link = results.a.get('href')
                        #print(link)
                        return title
                except:
                    self.log.exception("ERROR :: _pf :: failed to get link for {0}".format(burl))
                    return None
        except Exception as e:
            self.log.info("ERROR :: _pf :: {0}".format(e))
            return None
            
    def _similarPlayers(self, optname):
        """Return a dict containing the five most similar players based on optname."""
        
        activeplayers = self._ACTIVE_PLAYERS
        # test length as sanity check.
        if len(activeplayers) == 0:
            self.log.info("ERROR: _similarPlayers :: length 0. Could not find any players in players source")
            return None
        # ok, finally, lets go.
        optname = str(self._sanitizeName(optname))  # sanitizename.
        
        jaro, damerau = [], []  # empty lists to put our results in.
        # now we create the container to iterate over.
        names = [{'fullname': str(self._sanitizeName(k)), 'id':v['id']} for k,v in activeplayers.items()]  # full_name # last_name # first_name
        #print(type(optname))
        # iterate over the entries.
        for row in names:  # list of dicts.
            jaroscore = jellyfish.jaro_distance(optname, row['fullname'])  # jaro.
            damerauscore = jellyfish.damerau_levenshtein_distance(optname, row['fullname'])  # dld
            jaro.append({'jaro': jaroscore, 'fullname': row['fullname'], 'id': row['id']})  # add dict to list.
            damerau.append({'damerau': damerauscore, 'fullname': row['fullname'], 'id': row['id']})  # ibid.
        # now, we do two "sorts" to find the "top5" matches. reverse is opposite on each.
        jarolist = sorted(jaro, key=itemgetter('jaro'), reverse=True)[0:5]  # bot five.
        dameraulist = sorted(damerau, key=itemgetter('damerau'), reverse=False)[0:5]  # top five.
        # we now have two lists, top5 sorted, and need to do some further things.
        # now, lets iterate through both lists. match if both are in it. (better matches)
        matching = [k for k in jarolist if k['id'] in [f['id'] for f in dameraulist]]
        # now, test if we have anything. better matches will have more.
        if len(matching) == 0:  # we have NO matches. grab the top two from jaro/damerau (for error str)
            matching = [jarolist[0], dameraulist[0], jarolist[1], dameraulist[1]]
            self.log.info("_similarPlayers :: NO MATCHES for {0} :: {1}".format(optname, matching))
        # return matching now.
        return matching
    
    def _fetchActivePlayers(self):
        
        api_base = 'http://statsapi.mlb.com'
        roster_url = '/api/v1/teams/{team}/roster/active'
        
        players = {}
        for team in self._TEAM_BY_ID:
            url = api_base + roster_url.format(team=team)
            #print(url)
            tmp = requests.get(url).json()
            for player in tmp['roster']:
                if 'Pitcher' in player['position']['type']:
                    stat_type = 'pitching'
                else:
                    stat_type = 'hitting'
                players[player['person']['fullName']] = {'id': player['person']['id'], 
                                                         'url': player['person']['link'],
                                                         'team': player['parentTeamId'],
                                                         'stat': stat_type}
        self._ACTIVE_PLAYERS = players
        return players
            
    @wrap(['text'])
    def fstats(self, irc, msg, args, optplayer):
        """<player name>
        Fetches current/previous game fielding stats for given player"""
        
        api_base = 'http://statsapi.mlb.com'
        roster_url = '/api/v1/teams/{team}/roster/active'
        stats_url_current = '/api/v1/people/{personId}/stats/game/current'
        stats_url_game = '/api/v1/people/{personId}/stats/game/{gamePk}'
        sched_url = ('/api/v1/teams/{teamId}?hydrate=previousSchedule('
                     'gameType=[E,S,R,A,F,D,L,W]),nextSchedule(gameType=[E,S,R,A,F,D,L,W])')
        
        if not self._ACTIVE_PLAYERS:
            players = self._fetchActivePlayers()
        else:
            players = self._ACTIVE_PLAYERS
        #print(players)
        
        if optplayer.title() not in players:
            test = self._pf(irc, 'r', optplayer)
            if test:
                optplayer = test
            if optplayer.title() not in players:
                similar_players = self._similarPlayers(optplayer.lower())
                #print(similar_players)
                if similar_players:
                    for item in similar_players:
                        if item['fullname'].title() in players:
                            optplayer = item['fullname']
                            break
                if optplayer.title() not in players:
                    irc.reply('ERROR: {} not found on any active roster, check spelling/input'.format(optplayer.title()))
                    return
        
        if optplayer.title() not in players:
            irc.reply('ERROR: {} not found on any active roster, check spelling/input'.format(optplayer.title()))
            return
        
        player = players[optplayer.title()]
        
        #irc.reply('{}{}'.format(api_base, stats_url_current.format(personId=player['id'])))
        #irc.reply('{}{}'.format(api_base, sched_url.format(teamId=player['team'])))
        
        current = False
        tmp = requests.get('{}{}'.format(api_base, stats_url_current.format(personId=player['id'])))
        print(tmp.url)
        tmp = tmp.json()
        if not tmp['stats']:
            # no current game
            tmp = requests.get('{}{}'.format(api_base, sched_url.format(teamId=player['team']))).json()
            try:
                if tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['status']['abstractGameState'] == 'Final':
                    gamePk = tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gamePk']
                    gameDate = pendulum.parse(tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameDate'],
                                             strict=False).in_tz('US/Eastern').format('MMM Do')
                else:
                    gamePk = tmp['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gamePk']
                    gameDate = pendulum.parse(tmp['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gameDate'],
                                             strict=False).in_tz('US/Eastern').format('MMM Do')
            except:
                irc.reply('ERROR: No current/previous game fielding stats found for {}'.format(optplayer.title()))
                return
        else:
            current = True
            #TBD
            
        #print(gamePk)
        
        url = api_base + stats_url_game.format(personId=player['id'], gamePk=gamePk)
        #irc.reply(url)
        print(url)
        tmp = requests.get(url).json()
            
        if not tmp['stats']:
            irc.reply('ERROR: No current/previous game fielding stats found for {}'.format(optplayer.title()))
            return
        
        stats = []
        for thing in tmp['stats']:
            if 'type' not in thing:
                stats = thing
                break
                
        #print(stats)
        if not stats:
            irc.reply('ERROR: No current/previous game fielding stats found for {}'.format(optplayer.title()))
            return
        
        fielding_stat_headers = collections.OrderedDict()
        fielding_stat_headers['chances'] = 'Chances'
        fielding_stat_headers['errors'] = 'Errors'
        fielding_stat_headers['putOuts'] = 'Put Outs'
        fielding_stat_headers['assists'] = 'Assists'
        fielding_stat_headers['passedBall'] = 'Passed Balls'
        fielding_stat_headers['fielding'] = 'Fielding'
        
        stat_line = collections.OrderedDict({})
        for thing in stats['splits']:
            #print(thing)
            if thing['group'] == 'fielding':
                if not thing['stat']:
                    stat_line['ERROR'] = 'No fielding stats available for {} in current or previous game'.format(optplayer.title())
                    break
                for s in fielding_stat_headers:
                    #print(s)
                    if s in thing['stat']:
                        try:
                            stat_line[fielding_stat_headers[s]] = thing['stat'][s]
                        except:
                            stat_line[fielding_stat_headers[s]] = None
                    #print(stat_line)
                try:
                    pct = (stat_line['Put Outs'] + stat_line['Assists']) / stat_line['Chances']
                    stat_line['Fielding'] = '{:.3f}'.format(pct)
                except ZeroDivisionError:
                    pass
                        
        #print(stat_line)
        #for (k,v) in stat_line.items():
        #    print(k,v)
        
        stat_string = ' '.join('{}: {}'.format(self._bold(k),v) for k,v in stat_line.items())
        
        irc.reply('{} ({}) {}'.format(self._bold(self._blue(optplayer.title())), gameDate, stat_string))
        
        return
    
    @wrap(['text'])
    def mlbgamestats(self, irc, msg, args, optplayer):
        """<player name>
        Fetches current/previous game stats for given player"""
        
        api_base = 'http://statsapi.mlb.com'
        roster_url = '/api/v1/teams/{team}/roster/active'
        stats_url_current = '/api/v1/people/{personId}/stats/game/current'
        stats_url_game = '/api/v1/people/{personId}/stats/game/{gamePk}'
        sched_url = ('/api/v1/teams/{teamId}?hydrate=previousSchedule('
                     'gameType=[E,S,R,A,F,D,L,W]),nextSchedule(gameType=[E,S,R,A,F,D,L,W])')
        
        if not self._ACTIVE_PLAYERS:
            players = self._fetchActivePlayers()
        else:
            players = self._ACTIVE_PLAYERS
        #print(players)
        
        if optplayer.title() not in players:
            test = self._pf(irc, 'r', optplayer)
            if test:
                optplayer = test
            if optplayer.title() not in players:
                similar_players = self._similarPlayers(optplayer.lower())
                #print(similar_players)
                if similar_players:
                    for item in similar_players:
                        if item['fullname'].title() in players:
                            optplayer = item['fullname']
                            break
                if optplayer.title() not in players:
                    irc.reply('ERROR: {} not found on any active roster, check spelling/input'.format(optplayer.title()))
                    return
        
        player = players[optplayer.title()]
        print(optplayer.title(), player)
        
        #irc.reply('{}{}'.format(api_base, stats_url_current.format(personId=player['id'])))
        #irc.reply('{}{}'.format(api_base, sched_url.format(teamId=player['team'])))
        
        current = False
        tmp = requests.get('{}{}'.format(api_base, stats_url_current.format(personId=player['id'])))
        print(tmp.url)
        tmp = tmp.json()
        if not tmp['stats']:
            # no current game
            tmp = requests.get('{}{}'.format(api_base, sched_url.format(teamId=player['team']))).json()
            if tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['status']['abstractGameState'] == 'Final':
                gamePk = tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gamePk']
                gameDate = pendulum.parse(tmp['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameDate'],
                                         strict=False).in_tz('US/Eastern').format('MMM Do')
            else:
                gamePk = tmp['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gamePk']
                gameDate = pendulum.parse(tmp['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gameDate'],
                                         strict=False).in_tz('US/Eastern').format('MMM Do')
            url = api_base + stats_url_game.format(personId=player['id'], gamePk=gamePk)
            #irc.reply(url)
            print(url)
            tmp = requests.get(url).json()
        else:
            current = True
            #TBD
            gameDate = pendulum.now().in_tz('US/Eastern').format('MMM Do')
        #print(gamePk)
        
        
            
        if not tmp['stats']:
            irc.reply('ERROR: No current/previous game stats found for {}'.format(optplayer.title()))
            return
        
        stats = []
        for thing in tmp['stats']:
            if 'type' not in thing:
                stats = thing
                break
                
        #print(stats)
        if not stats:
            irc.reply('ERROR: No current/previous game stats found for {}'.format(optplayer.title()))
            return
        
        hitting_stat_headers = collections.OrderedDict()
        hitting_stat_headers['atBats'] = 'AB'
        hitting_stat_headers['hits'] = 'H'
        hitting_stat_headers['runs'] = 'R'
        hitting_stat_headers['baseOnBalls'] = 'BB'
        hitting_stat_headers['strikeOuts'] = 'SO'
        hitting_stat_headers['doubles'] = '2B'
        hitting_stat_headers['triples'] = '3B'
        hitting_stat_headers['homeRuns'] = 'HR'
        hitting_stat_headers['stolenBases'] = 'SB'
        hitting_stat_headers['caughtStealing'] = 'CS'
        hitting_stat_headers['totalBases'] = 'TB'
        hitting_stat_headers['rbi'] = 'RBI'
        hitting_stat_headers['avg'] = 'AVG'
        
        pitching_stat_headers = collections.OrderedDict()
        pitching_stat_headers['inningsPitched'] = 'IP'
        pitching_stat_headers['battersFaced'] = 'BF'
        pitching_stat_headers['hits'] = 'H'
        pitching_stat_headers['baseOnBalls'] = 'BB'
        pitching_stat_headers['strikeOuts'] = 'K'
        pitching_stat_headers['pitchesThrown'] = '#P'
        pitching_stat_headers['balls'] = 'B-S'
        pitching_stat_headers['strikes'] = 'B-S'
        pitching_stat_headers['hitBatsmen'] = 'HBP'
        pitching_stat_headers['earnedRuns'] = 'ER'
        pitching_stat_headers['runs'] = 'R'
        pitching_stat_headers['homeRuns'] = 'HR'
        pitching_stat_headers['flyOuts'] = 'FO'
        pitching_stat_headers['groundOuts'] = 'GO'
        pitching_stat_headers['era'] = 'gERA'
        
        stat_line = collections.OrderedDict({})
        for thing in stats['splits']:
            #print(thing)
            if player['stat'] == thing['group']:
                if not thing['stat']:
                    stat_line['ERROR'] = 'No stats available for {} in current or previous game'.format(optplayer.title())
                    break
                if player['stat'] == 'hitting':
                    for s in hitting_stat_headers:
                        #print(s)
                        if s in thing['stat']:
                            try:
                                stat_line[hitting_stat_headers[s]] = thing['stat'][s]
                            except:
                                stat_line[hitting_stat_headers[s]] = None
                    avg = stat_line['H'] / stat_line['AB']
                    avg = '{:.3f}'.format(avg)
                    stat_line['AVG'] = avg
                elif player['stat'] == 'pitching':
                    for s in pitching_stat_headers:
                        #print(s)
                        if s in thing['stat']:
                            try:
                                if s == 'balls' or s == 'strikes':
                                    stat_line['B-S'] = '{}-{}'.format(thing['stat']['balls'], thing['stat']['strikes'])
                                else:
                                    stat_line[pitching_stat_headers[s]] = thing['stat'][s]
                            except:
                                stat_line[pitching_stat_headers[s]] = None
                    try:
                        era = '{:.2f}'.format((stat_line['ER']/float(stat_line['IP']))*9)
                    except:
                        if float(stat_line['IP']) == 0.0 and stat_line['ER'] > 0:
                            era = '∞'
                        else:
                            era = '0.00'
                    stat_line['gERA'] = era
                        
        #print(stat_line)
        #for (k,v) in stat_line.items():
        #    print(k,v)
        
        stat_string = ' '.join('{}: {}'.format(self._bold(k),v) for k,v in stat_line.items())
        
        irc.reply('{} ({}) {}'.format(self._bold(self._blue(optplayer.title())), gameDate, stat_string))
        
        return
            
    @wrap([getopts({'active': '',}), 'text'])
    def mlbroster(self, irc, msg, args, optlist, opttype):
        """<--active> <team> <type>
        Fetches roster for given <team> filtered by <type>"""
        
        optlist = dict(optlist)
        positions = {'pitchers': 'Pitcher', 'infielders': 'Infielder',
                     'catchers': 'Catcher', 'outfielders': 'Outfielder'}
        
        base_url = 'http://statsapi.mlb.com/api/v1/teams/{team}/roster/{roster}'
        api_base = 'http://statsapi.mlb.com'
        
        try:
            team = opttype.split()[0].upper()
        except:
            irc.reply('Invalid input')
            return
        try:
            filter_ = opttype.split()[1]
        except:
            filter_ = None
        #print(filter_)
        try:
            filter_ = filter_.lower()
            filter_ = positions[filter_]
        except:
            if filter_:
                filter_ = filter_.title()
        
        if team not in self._TEAM_BY_TRI:
            irc.reply('ERROR: Invalid team. Valid teams: {}'.format(', '.join(i for i in self._TEAM_BY_TRI)))
            return
        team_id = self._TEAM_BY_TRI[team]
        
        url = base_url.format(team=team_id, roster='active')
        
        data = requests.get(url).json()
        
        #print(data.json())
        roster = []
        tmp = data['roster']
        tmp = sorted(tmp, key=lambda k: k['person']['fullName'].split()[-1])
        #print(tmp)
        for player in tmp:
            num = self._red('#{}'.format(player['jerseyNumber']))
            name = player['person']['fullName']
            info_url = player['person']['link']
            #print(api_base + info_url)
            info = requests.get(api_base + info_url).json()
            bats = info['people'][0]['batSide']['code']
            pits = info['people'][0]['pitchHand']['code']
            string = '{} {} (B:{} T:{})'.format(num, name, bats, pits)
            if filter_:
                if player['position']['type'] == filter_:
                    roster.append(string)
            else:
                roster.append(string)
                
        if not roster:
            irc.reply('Nothing found for that query')
            return
        else:
            irc.reply(', '.join(i for i in roster))
        return
            
    @wrap
    def mlbdaysleft(self, irc, msg, args):
        """How many days are left in the current MLB season"""
        
        now = pendulum.now()
        end = pendulum.parse('2018-09-30')
        left = end-now
        
        irc.reply("There are {} days left in the {} MLB season.".format(left.days, end.year))
            
#     @wrap(['text'])
#     def mlbstats(self, irc, msg, args, player):
#         """<player>
#         Fetches current season stats for the <player> provided.
#         """
        
#         data = batting_stats_bref()
        
#         #print(data.head())
    
    @wrap(['text'])
    def mlbgame2(self, irc, msg, args, player):
        """<player>
        Fetches current game stats for the <player> provided.
        """
        #player = player.upper()
        team, date, tz = self._parseInput(player)
        
        if date:
            test = pendulum.parse(date)
            now = pendulum.now().format('YYYY-MM-DD')
            now = pendulum.parse(now)
            k = (test > now)
            #print(date, ' | ', k, ' | ', pendulum.now())
            if k:
                #irc_args = '{} {}'.format(team, date)
                #self.mlb(msg, args, irc_args)
                irc.reply("Sorry I can't predict the future.")
                return

#         if not team:
#             irc.reply('No team provided.')
#             return

        games = self._fetchGames(team, date)

        if not games:
            irc.reply('No games found')
            return

        games = self._parseGames(games, date)
        games = self._sortGames(games)
        
        #print(games)
        
            
    @wrap(['text'])
    def lineup2(self, irc, msg, args, team):
        """<team tri code>
        Fetches lineup for the game <team> is playing
        """
        abbv = team.upper()
        team, date, tz = self._parseInput(team)
        
        if date:
            test = pendulum.parse(date)
            now = pendulum.now().format('YYYY-MM-DD')
            now = pendulum.parse(now)
            k = (test > now)
            #print(date, ' | ', k, ' | ', pendulum.now())
            if k:
                #irc_args = '{} {}'.format(team, date)
                #self.mlb(msg, args, irc_args)
                irc.reply("Sorry I can't predict the future.")
                return

        if not team:
            irc.reply('No team provided.')
            return

        games = self._fetchGames(team, date)

        if not games:
            irc.reply('No games found')
            return

        games = self._parseGames(games, date)
        games = self._sortGames(games)
        
        lineup_url = 'http://statsapi.mlb.com/api/v1/game/{}/boxscore'.format(games[0]['id'])
        lineup_url_2 = 'https://statsapi.mlb.com/api/v1/schedule?gamePk={}&language=en&hydrate=lineups,person,probablePitcher,team(leaders(showOnPreview(leaderCategories=[homeRuns,runsBattedIn,battingAverage],statGroup=[pitching,hitting])))'.format(games[0]['id'])
        print(lineup_url, lineup_url_2)
        
        try:
            data = requests.get(lineup_url).json()
            data2 = requests.get(lineup_url_2).json()
        except:
            irc.reply('Something went wrong fetching game data.')
            return
        #print(team)
        lineup = []
        tmp_plyr_data = []
        opp_id = None
        #try:
        teams = data['teams']
        lineups = data2['dates'][0]['games'][0]['lineups']
        #print(lineups)
        ppitchers = data2['dates'][0]['games'][0]['teams']
        for item in teams:
            if int(team) == teams[item]['team']['id']:
                #print('h/a: ', item)
                if item == 'home':
                    opp_t = 'away'
                    hora = item
                elif item == 'away':
                    opp_t = 'home'
                    hora = item
                #print('pitcher: ', opp_t)
                battingOrder = teams[item]['battingOrder']
                tmp_plyr_data = teams[item]['players']
                vs_name = teams[opp_t]['team']['abbreviation']
                
                #pprint(teams[opp_t])
                if teams[opp_t]['pitchers']:
                    opp_id = teams[opp_t]['pitchers'][-1]
                    hm_id = teams[item]['pitchers'][-1]
                    #print('teams')
                else:
                    opp_id = ppitchers[opp_t]['probablePitcher']['id']
                    hm_id = ppitchers[item]['probablePitcher']['id']
                    #print('ppitchers')
                break
        #print(tmp_plyr_data)
        if lineups:
            #print('Got a lineup')
            tstr = '{}Players'.format(hora)
            #print(lineups)
            try:
                lineups = lineups[tstr]
            except:
                irc.reply('No lineup found')
                return
            for idx, player in enumerate(lineups):
                if battingOrder:
                    if int(player['id']) != int(battingOrder[idx]):
                        player['id'] = int(battingOrder[idx])
                #print(idx, player)
                plyr_url = 'http://statsapi.mlb.com/api/v1/people/{}'.format(player['id'])
                #print(plyr_url)
                n_player_data = requests.get(plyr_url).json()
                for pid in tmp_plyr_data:
                    if str(player['id']) in str(pid):
                        player_data = tmp_plyr_data[pid]
                bats = n_player_data['people'][0]['batSide']['code']
                name = player_data['person']['fullName']
                try:
                    post = lineups[idx]['primaryPosition']['abbreviation']
                except:
                    post = player_data['position']['abbreviation']
                if idx == 9:
                    bats = n_player_data['people'][0]['pitchHand']['code']
                    tmp = '\x02\x0312{}\x03\x02 {} ({})'.format('P', name, bats)
                else:
                    tmp = '\x02\x0312{}\x03\x02 {} ({}) {}'.format(idx+1, name, bats, post)
                lineup.append(tmp)
       
            #umps = item['value']
            if opp_id:
                pitcher_url = 'http://statsapi.mlb.com/api/v1/people/{}'.format(opp_id)
                #print(pitcher_url)
                pitcher_data = requests.get(pitcher_url).json()
                pitch_name = pitcher_data['people'][0]['fullName']
                pitches = pitcher_data['people'][0]['pitchHand']['code']
                for pplayer in data['teams'][opp_t]['players']:
                    if str(opp_id) in pplayer:
                        era = data['teams'][opp_t]['players'][pplayer]['seasonStats']['pitching']['era']
                pitcher = '{} ({}) {}'.format(pitch_name, pitches, era)
            else:
                pitcher = ''
                
            if hm_id and len(lineup) == 9:
                pitcher_url = 'http://statsapi.mlb.com/api/v1/people/{}'.format(hm_id)
                #print(pitcher_url)
                pitcher_data = requests.get(pitcher_url).json()
                pitch_name = pitcher_data['people'][0]['fullName']
                pitches = pitcher_data['people'][0]['pitchHand']['code']
                for pplayer in data['teams'][hora]['players']:
                    if str(hm_id) in pplayer:
                        era = data['teams'][hora]['players'][pplayer]['seasonStats']['pitching']['era']
                hm_pitcher = ' :: \x02\x0312{}\x03\x02 {} ({}) {}'.format('P', pitch_name, pitches, era)
            else:
                hm_pitcher = ''
#         except:
#             irc.reply('Something went wrong parsing game data.')
#             return
        
        if not lineup:
            irc.reply('No lineup found yet, game active?')
            return
        
        irc.reply('{} Lineup vs {} - \x02{}\x02 :: {}{}'.format(abbv, vs_name, pitcher, ', '.join(plr for plr in lineup), hm_pitcher))
        
            
    @wrap(['text'])
    def umps(self, irc, msg, args, team):
        """<team tri code>
        Fetches umpires for the game <team> is playing
        """
        team, date, tz = self._parseInput(team)
        
        if date:
            test = pendulum.parse(date)
            now = pendulum.now().format('YYYY-MM-DD')
            now = pendulum.parse(now)
            k = (test > now)
            #print(date, ' | ', k, ' | ', pendulum.now())
            if k:
                #irc_args = '{} {}'.format(team, date)
                #self.mlb(msg, args, irc_args)
                irc.reply("Sorry I can't predict the future.")
                return

        if not team:
            irc.reply('No team provided.')
            return

        games = self._fetchGames(team, date)

        if not games:
            irc.reply('No games found')
            return

        games = self._parseGames(games, date)
        games = self._sortGames(games)
        
        ump_url = 'http://statsapi.mlb.com/api/v1/game/{}/boxscore'.format(games[0]['id'])
        #print(ump_url)
        
        try:
            data = requests.get(ump_url).json()
        except:
            irc.reply('Something went wrong fetching game data.')
            return
        
        umps = None
        try:
            for item in data['info']:
                if item['label'] == 'Umpires':
                    umps = item['value']
                    break
        except:
            irc.reply('Something went wrong parsing game data.')
            return
        
        if not umps:
            irc.reply('No umpires found yet, game active?')
            return
        
        irc.reply('Umpires: {}'.format(umps))
        

    @wrap([optional('text')])
    def mlbpitcher(self, irc, msg, args, irc_args=None):
        """<team tri code> [<date>]
        Fetches pitcher(s) for given team and/or date. Defaults to today
        if no input provided"""

        override = False
        starter_only = False
        if irc_args:
            if '--all' in irc_args:
                override = True
                irc_args = irc_args.replace('--all', '')
            if 'was' in irc_args:
                irc_args = irc_args.replace('was', 'wsh')
            if '--starter' in irc_args:
                starter_only = True
                override = True
                irc_args = irc_args.replace('--starter', '')
                

        team, date, tz = self._parseInput(irc_args)
        
        if date:
            test = pendulum.parse(date)
            now = pendulum.now().format('YYYY-MM-DD')
            now = pendulum.parse(now)
            k = (test > now)
            #print(date, ' | ', k, ' | ', pendulum.now())
            if k:
                #irc_args = '{} {}'.format(team, date)
                #self.mlb(msg, args, irc_args)
                irc.reply("Sorry I can't predict the future.")
                return

        if not team:
            irc.reply('No team provided.')
            return

        games = self._fetchGames(team, date)

        if not games:
            irc.reply('No games found')
            return

        games = self._parseGames(games, date)
        games = self._sortGames(games)

        pitchers = self._fetchPitchers(games, team, override)

        if not pitchers:
            irc.reply('No pitchers found, has game started yet?')
            return
        
        #print(pitchers)

        # if len(pitchers) == 2:
        #     if 'Game 2' in pitchers[1]:
        #         irc.reply('No pitchers found, has game started yet?')
        #         return

        reply_string = self._replyPitchersAsString(pitchers)

        # if len(reply_string) > 3:
        #     print(reply_string)
        #     if 'Game 2' in reply_string[-1]:
        #         reply_string.append('Not started yet')

        # what = type(reply_string)
        # print(what)

        #print(reply_string)

        if type(reply_string) is tuple or type(reply_string) is list or type(reply_string) is dict:
            if type(reply_string) is dict:
                for string in reply_string:
                    irc.reply('\x02{}\x02'.format(string))
                    if starter_only:
                        irc.reply(reply_string[string][0])
                    else:
                        for pit in reply_string[string]:
                            irc.reply(pit)
            else:
                if starter_only:
                    irc.reply(reply_string[0])
                else:
                    for string in reply_string:
                        irc.reply(string)
        else:
            irc.reply(reply_string)
            
    @wrap(['text'])
    def mlbinjuries(self, irc, msg, args, optteam):
        """<team>
        Returns injuries for given <team>.
        """
        
        # get team id for matching
        team, _, _ = self._parseInput(optteam)
        
        # url to get data
        url = 'http://mlb.mlb.com/fantasylookup/json/named.wsfb_news_injury.bam'
        
        # try to get the data
        try:
            data = requests.get(url).json()
        except:
            irc.reply('Something went wrong fetching the data.')
            return
        
        # pull out the relevant data
        injuries = data['wsfb_news_injury']['queryResults']['row']
        
        # build output
        output = []
        
        for injury in injuries:
            #print(team, int(injury['team_id']))
            if not team:
                if optteam.lower() in '{} {}'.format(injury['name_first'].lower(), injury['name_last'].lower()):
                    name = '\x02\x0312{} {}\x03\x02 ({})'.format(injury['name_first'],
                                                                 injury['name_last'],
                                                                 injury['position'])
                    inj = '{} on {} ({})'.format(injury['injury_status'],
                                                 injury['insert_ts'],
                                                 injury['injury_desc'])
                    upd = '\x02Latest:\x02 {}'.format(injury['injury_update'])
                    due = '\x02Returning:\x02 {}'.format(injury['due_back'])
                    output.append('{} :: {} | {} | {}'.format(name, inj, upd, due))
            else:
                if int(team) == int(injury['team_id']):
                    # our team query matches let's go
                    name = '\x02\x0312{} {}\x03\x02 ({})'.format(injury['name_first'],
                                               injury['name_last'],
                                               injury['position'])
                    inj = '{} on {}'.format(injury['injury_status'],
                                            injury['insert_ts'])
                    output.append('{} {}'.format(name, inj))
                
        if not output:
            irc.reply('ERROR: Team or player not found or no injuries found for provided team or player.')
            return
                
        if team:
            team_name = '\x02{}:\x02 '.format(self._TEAM_BY_ID['{}'.format(team)])
            irc.reply('{}{}'.format(team_name, ', '.join(i for i in output)))
        else:
            irc.reply(' || '.join(i for i in output))
            
    @wrap([optional('int'), 'somethingwithoutspaces', optional('somethingwithoutspaces')])
    def next(self, irc, msg, args, optdays, optteam, optteam2):
        """[<#>] <team> [<team>]
        Returns the next # of games for team (or team vs team), defaults to 1 if not given
        """
        
        tids = self._TEAM_BY_TRI
        
        if not optdays:
            optdays = 1
            
        if optdays == 0:
            optdays = 1
            
        if optdays < 0:
            optdays = optdays * -1
            
        if optdays > 10:
            irc.reply('ERROR: Too many games, has to be less than 10')
            return
            
        
        optteam = optteam.upper()
        
        if optteam not in tids:
            irc.reply('ERROR: Invalid team, must be team abbreviation (ex: BOS)')
            return
        
        if optteam2:
            optteam2 = optteam2.upper()
            if optteam == optteam2:
                irc.reply('ERROR: Both provided teams are the same')
                return
            if optteam2 not in tids:
                irc.reply('ERROR: Invalid team, must be team abbreviation (ex: BOS)')
                return
        
        today = self._getTodayDate()
        end = '2018-11-01'
        try:
            tid = tids[optteam]
        except:
            irc.reply('ERROR: Something went wrong parsing data')
            return
        #print(optdays, optteam)
        # TBD switch out season=YYYYYYYY automatically
        if optteam2:
            try:
                tid2 = tids[optteam2]
            except:
                irc.reply('ERROR: Something went wrong parsing data')
                return
            # url = ("https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}" +
            #       "&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all,schedule.ticket,schedule.game.content.media.epg" +
            #       "&leaderCategories=&site=en_nhl&teamId={}&teamId={}")
            url = ('https://statsapi.mlb.com/api/v1/schedule'
                                     '?sportId=1&startDate={}&endDate={}'
                                     '&hydrate=linescore,team,probablePitcher'
                                     '&teamId={}&teamId={}')

            # Fetch content
            content = requests.get(url.format(today, end, tid, tid2))
            content_json = content.json()
            #print(url.format(today, end, tid))
        else:
            url = ('https://statsapi.mlb.com/api/v1/schedule'
                                     '?sportId=1&startDate={}&endDate={}'
                                     '&hydrate=linescore,team,probablePitcher'
                                     '&teamId={}')

            # Fetch content
            content = requests.get(url.format(today, end, tid))
            content_json = content.json()
            #print(url.format(today, end, tid))
        
        games = []
        
        if optteam2:
            for idx, item in enumerate(content_json['dates']):
                for gidx, _ in enumerate(item['games']):
                    if optteam in item['games'][gidx]['teams']['away']['team']['abbreviation'] and optteam2 in item['games'][gidx]['teams']['home']['team']['abbreviation']:
                        string1 = '{}'.format(self._ISODateToEasternTimeNext(item['games'][gidx]['gameDate']))
                        string2 = '{} @ {}'.format(self._bold(item['games'][gidx]['teams']['away']['team']['abbreviation']), item['games'][gidx]['teams']['home']['team']['abbreviation'])
                        ppitchers = ''
                        if 'probablePitcher' in item['games'][gidx]['teams']['away'] and 'probablePitcher' in item['games'][gidx]['teams']['home']:
                            ppitchers = ' - {} vs {}'.format(item['games'][gidx]['teams']['away']['probablePitcher']['fullName'].split(',')[0], item['games'][gidx]['teams']['home']['probablePitcher']['fullName'].split(',')[0])
                        games.append(string1 + ' | ' + string2 + ppitchers)
                    elif optteam2 in item['games'][gidx]['teams']['away']['team']['abbreviation'] and optteam in item['games'][gidx]['teams']['home']['team']['abbreviation']:
                        string1 = '{}'.format(self._ISODateToEasternTimeNext(item['games'][gidx]['gameDate']))
                        string2 = '{} @ {}'.format(item['games'][gidx]['teams']['away']['team']['abbreviation'], self._bold(item['games'][gidx]['teams']['home']['team']['abbreviation']))
                        ppitchers = ''
                        if 'probablePitcher' in item['games'][gidx]['teams']['away'] and 'probablePitcher' in item['games'][gidx]['teams']['home']:
                            ppitchers = ' - {} vs {}'.format(item['games'][gidx]['teams']['away']['probablePitcher']['fullName'].split(',')[0], item['games'][gidx]['teams']['home']['probablePitcher']['fullName'].split(',')[0])
                        games.append(string1 + ' | ' + string2 + ppitchers)
                        
                    else:
                        pass
            
            if len(games) == 0:
                irc.reply('No future games found for {} vs {}'.format(optteam, optteam2))
                return
            #print(games)
            games = games[:optdays]
            
            if len(games) <= 4:
                for game in games:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
            else:
                #m = len(games)
                for game in games[:4]:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
                for game in games[4:]:
                    irc.reply(game)
        else:
            for idx, item in enumerate(content_json['dates'][:optdays]):
                for gidx, _ in enumerate(item['games']):
                    #print(item['games'][gidx]['teams']['away']['team']['id'])
                    string1 = '{}'.format(self._ISODateToEasternTimeNext(item['games'][gidx]['gameDate']))
                    necessary = ''
                    if item['games'][gidx]['ifNecessary'] == 'Y':
                        necessary = ' - If Necessary'
                    #string2 = '{}'.format('{} {}'.format('at', item['games'][gidx]['teams']['home']['team']['abbreviation']) if int(tid) == item['games'][gidx]['teams']['away']['team']['id'] else '{} {}'.format('vs', item['games'][gidx]['teams']['away']['team']['abbreviation']))
                    if optteam in item['games'][gidx]['teams']['away']['team']['abbreviation']:
                        string2 = '{} @ {}'.format(self._bold(item['games'][gidx]['teams']['away']['team']['abbreviation']), item['games'][gidx]['teams']['home']['team']['abbreviation'])
                    else:
                        string2 = '{} @ {}'.format(item['games'][gidx]['teams']['away']['team']['abbreviation'], self._bold(item['games'][gidx]['teams']['home']['team']['abbreviation']))
                    ppitchers = ''
                    if 'probablePitcher' in item['games'][gidx]['teams']['away'] and 'probablePitcher' in item['games'][gidx]['teams']['home']:
                        ppitchers = ' - {} vs {}'.format(item['games'][gidx]['teams']['away']['probablePitcher']['fullName'].split(',')[0], item['games'][gidx]['teams']['home']['probablePitcher']['fullName'].split(',')[0])
                    games.append(string1 + ' | ' + string2 + ppitchers + necessary)
            if len(games) <= 4:
                for game in games:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
            else:
                #m = len(games)
                for game in games[:4]:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
                for game in games[4:]:
                    irc.reply(game)


    @wrap([optional('int'), 'somethingwithoutspaces', optional('somethingwithoutspaces')])
    def last(self, irc, msg, args, optdays, optteam, optteam2):
        """[<#>] <team> [<team>]
        Returns the last # of games for team (or team vs team), defaults to 1 if not given
        """
        
        tids = self._TEAM_BY_TRI
        
        if not optdays:
            optdays = -1
            numdays = 1
        else:
            if optdays > 10:
                irc.reply('ERROR: Too many games, has to be less than 10')
                return
            if optdays == 0:
                optdays = 1
            if optdays < 0:
                optdays = optdays * -1
            if optdays > 10:
                irc.reply('ERROR: Too many games, has to be less than 10')
                return
            numdays = optdays
            optdays = optdays * -1
            
        optteam = optteam.upper()
        
        if optteam not in tids:
            irc.reply('ERROR: Invalid team, must be team abbreviation (ex: BOS)')
            return
        
        if optteam2:
            optteam2 = optteam2.upper()
            if optteam == optteam2:
                irc.reply('ERROR: Both provided teams are the same')
                return
            if optteam2 not in tids:
                irc.reply('ERROR: Invalid team, must be team abbreviation (ex: BOS)')
                return
        
        today = self._getTodayDate()
        dt_today = datetime.datetime.strptime(today, "%Y-%m-%d")
        dt_yesterday = dt_today - datetime.timedelta(1)
        yesterday = dt_yesterday.strftime('%Y-%m-%d')
        #last_date = datetime.datetime.today() - datetime.timedelta(days=optdays)
        #print(last_date)
        end = '2018-03-01'
        try:
            tid = tids[optteam]
        except:
            irc.reply('ERROR: Something went wrong parsing data')
            return
        #print(optdays, optteam)
        # TBD switch out season=YYYYYYYY automatically
        if optteam2:
            try:
                tid2 = tids[optteam2]
            except:
                irc.reply('ERROR: Something went wrong parsing data')
                return
            url = ('https://statsapi.mlb.com/api/v1/schedule'
                                     '?sportId=1&startDate={}&endDate={}'
                                     '&hydrate=linescore,team,decisions'
                                     '&teamId={}&teamId={}')

            # Fetch content
            content = requests.get(url.format(end, yesterday, tid, tid2))
            content_json = content.json()
            
            #print(url.format(today, end, tid, tid2))
        else:
            url = ('https://statsapi.mlb.com/api/v1/schedule'
                                     '?sportId=1&startDate={}&endDate={}'
                                     '&hydrate=linescore,team,decisions'
                                     '&teamId={}')

            # Fetch content
            content = requests.get(url.format(end, yesterday, tid))
            content_json = content.json()
            #print(url.format(end, yesterday, tid))

        games = []

        if optteam2: # team vs team
            for idx, item in enumerate(content_json['dates']):
                for gidx, _ in enumerate(item['games']):
                    if (optteam in item['games'][gidx]['teams']['away']['team']['abbreviation'] and optteam2 in item['games'][gidx]['teams']['home']['team']['abbreviation']) or (optteam2 in item['games'][gidx]['teams']['away']['team']['abbreviation'] and optteam in item['games'][gidx]['teams']['home']['team']['abbreviation']):
                        date = self._ISODateToEasternTimeNext(item['games'][gidx]['gameDate'])[:-3]

                        status_codes = ['DI', 'DC', 'DR', 'DS', 'PI']
                        #print(item['games'][gidx]['status']['statusCode'])
                        if item['games'][gidx]['status']['statusCode'] in status_codes:
                            #print('hi ppd')
                            home = item['games'][gidx]['teams']['home']['team']['abbreviation']
                            away = item['games'][gidx]['teams']['away']['team']['abbreviation']
                            #ppd = ' \x037P\x03'
                            ppd = '  '
                            reason = item['games'][gidx]['status']['reason']
                            str_reply = '{} @ {} \x034PPD\x03 ({})'.format(away, home, reason)
                            string1 = '{}'.format(date.split(',')[0])
                            games.append(string1 + ppd + ' | ' + str_reply)
                            continue

                        if int(item['games'][gidx]['linescore']['currentInning']) > 9:
                            ot_type = ' (' + item['games'][gidx]['linescore']['currentInningOrdinal'] + ')'
                        else:
                            ot_type = ''

                        string1 = '{}'.format(date.split(',')[0])

                        if int(item['games'][gidx]['teams']['away']['score']) > int(item['games'][gidx]['teams']['home']['score']):
                            away = self._bold(item['games'][gidx]['teams']['away']['team']['abbreviation'])
                            away_s = self._bold(item['games'][gidx]['teams']['away']['score'])
                            home = item['games'][gidx]['teams']['home']['team']['abbreviation']
                            home_s = item['games'][gidx]['teams']['home']['score']
                            if optteam in away:
                                result = self._green(' W')
                                try:
                                    pitcher = ' - {}'.format(item['games'][gidx]['decisions']['winner']['fullName'])
                                except:
                                    pitcher = ''
                            else:
                                result = self._red(' L')
                                try:
                                    pitcher = ' - {}'.format(item['games'][gidx]['decisions']['loser']['fullName'])
                                except:
                                    pitcher = ''
                        else:
                            home = self._bold(item['games'][gidx]['teams']['home']['team']['abbreviation'])
                            home_s = self._bold(item['games'][gidx]['teams']['home']['score'])
                            away = item['games'][gidx]['teams']['away']['team']['abbreviation']
                            away_s = item['games'][gidx]['teams']['away']['score']
                            if optteam in home:
                                result = self._green(' W')
                                try:
                                    pitcher = ' - {}'.format(item['games'][gidx]['decisions']['winner']['fullName'])
                                except:
                                    pitcher = ''
                            else:
                                result = self._red(' L')
                                try:
                                    pitcher = ' - {}'.format(item['games'][gidx]['decisions']['loser']['fullName'])
                                except:
                                    pitcher = ''

                        string3 = '{} {} @ {} {}{}{}'.format(away, away_s, home, home_s, ot_type, pitcher)

                        games.append(string1 + result + ' | ' + string3)
                    else:
                        pass

            #games = games[::-1]
            games_r = games[optdays:]
            games_r.reverse()
            
            if len(games) <= 4:
                for game in games_r:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
            else:
                for game in games_r[:4]:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
                for game in games_r[4:]:
                    irc.reply(game)
                
        else: # just team
            for idx, item in enumerate(content_json['dates'][optdays:]):
                for gidx, _ in enumerate(item['games']):
                    date = self._ISODateToEasternTimeNext(item['games'][gidx]['gameDate'])#[:-3]

                    status_codes = ['DI', 'DC', 'DR', 'DS']
                    #print(item['games'][gidx]['status']['statusCode'])
                    if item['games'][gidx]['status']['statusCode'] in status_codes:
                        #print('hi ppd')
                        home = item['games'][gidx]['teams']['home']['team']['abbreviation']
                        away = item['games'][gidx]['teams']['away']['team']['abbreviation']
                        #ppd = ' \x037P\x03'
                        ppd = '  '
                        reason = item['games'][gidx]['status']['reason']
                        str_reply = '{} @ {} \x034PPD\x03 ({})'.format(away, home, reason)
                        string1 = '{}'.format(date.split(',')[0])
                        games.append(string1 + ppd + ' | ' + str_reply)
                        continue

                    if int(item['games'][gidx]['linescore']['currentInning']) > 9:
                        ot_type = ' (F/' + item['games'][gidx]['linescore']['currentInningOrdinal'] + ')'
                    else:
                        ot_type = ''

                    string1 = '{}'.format(date.split(',')[0])

                    if int(item['games'][gidx]['teams']['away']['score']) > int(item['games'][gidx]['teams']['home']['score']):
                        away = self._bold(item['games'][gidx]['teams']['away']['team']['abbreviation'])
                        away_s = self._bold(item['games'][gidx]['teams']['away']['score'])
                        home = item['games'][gidx]['teams']['home']['team']['abbreviation']
                        home_s = item['games'][gidx]['teams']['home']['score']
                        if optteam in away:
                            result = self._green(' W')
                            try:
                                pitcher = ' - {}'.format(item['games'][gidx]['decisions']['winner']['fullName'])
                            except:
                                pitcher = ''
                        else:
                            result = self._red(' L')
                            try:
                                pitcher = ' - {}'.format(item['games'][gidx]['decisions']['loser']['fullName'])
                            except:
                                pitcher = ''
                    else:
                        home = self._bold(item['games'][gidx]['teams']['home']['team']['abbreviation'])
                        home_s = self._bold(item['games'][gidx]['teams']['home']['score'])
                        away = item['games'][gidx]['teams']['away']['team']['abbreviation']
                        away_s = item['games'][gidx]['teams']['away']['score']
                        if optteam in home:
                            result = self._green(' W')
                            try:
                                pitcher = ' - {}'.format(item['games'][gidx]['decisions']['winner']['fullName'])
                            except:
                                pitcher = ''
                        else:
                            result = self._red(' L')
                            try:
                                pitcher = ' - {}'.format(item['games'][gidx]['decisions']['loser']['fullName'])
                            except:
                                pitcher = ''

                    string3 = '{} {} @ {} {}{}{}'.format(away, away_s, home, home_s, ot_type, pitcher)

                    games.append(string1 + result + ' | ' + string3)
            
            games_r = games[::-1]
            
            if len(games) <= 4:
                for game in games_r:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
            else:
                for game in games_r[:4]:
                    irc.sendMsg(ircmsgs.privmsg(msg.args[0], game))
                for game in games_r[4:]:
                    irc.reply(game)
                    
#     @wrap(["text"])
#     def recap(self, irc, msg, args, optargs):
#         """<team> [<date>]
#         Returns a video recap from <team> optionally on <date>.
#         """
        
#         # hq = False
#         # if '--hq' in optargs or '--HQ' in optargs:
#         #     hq = True
#         #     optargs = optargs.strip('--hq')
#         #     optargs = optargs.strip('--HQ')
#         #     optargs = optargs.strip()
            
#         # print(optargs)
        
#         tids = self._TEAM_BY_TRI
        
# #         try:
# #             gamepk = self._findGamepk("summary", optargs)
# #         except:
# #             # try looking for yesterday's game
# #             #optargs += ' yesterday'
            
# #         try:
#         api_url = 'https://statsapi.mlb.com/api/v1/teams/{}/?expand=team.schedule.previous'.format(tids[optargs.upper()])
#         print(api_url)
#         data = requests.get(api_url)
#         data = data.json()
#         gamepk = str(data['teams'][0]['previousGameSchedule']['dates'][0]['games'][gidx]['gamePk'])
# #         except:
# #             irc.reply('Nothing found for given input')
# #             return

#         if not gamepk:
#             irc.reply('Nothing found, check your input')
#             return
#         url = ("http://statsapi.mlb.com/api/v1/schedule?expand=schedule.game.content.media.epg&leaderCategories=&site=en_nhl&gamePk=" + gamepk)
#         content = requests.get(url)
#         content_json = content.json()

#         print(url)
                
#         info = {}
#         #print(gamepk)
        
#         VIDEOurl = {}
#         try:
#             for item in content_json['dates'][0]['games'][gidx]['content']['media']['epg']:
#                 if item['title'] == 'Recap':
#                     info['title'] = item['items'][0]['title'].strip('Recap: ')
#                     info['blurb'] = item['items'][0]['blurb']
#                     info['description'] = item['items'][0]['description']
#                     info['duration'] = "{}m{}s".format(item['items'][0]['duration'].split(':')[0].lstrip('0'), item['items'][0]['duration'].split(':')[1])
#                     for video in item['items'][0]['playbacks']:
#                         if 'HTTP_CLOUD_WIRED_60' in video['name']:
#                             VIDEOurl['hls'] = self._shortenUrl(video['url'])
#                         if '1800K' in video['name']:
#                             VIDEOurl['mp4'] = self._shortenUrl(video['url'])
#             # if not VIDEOurl:
#             #     VIDEOurl = 'No video recap available'
#             # else:
#             #     VIDEOurl = self._shortenUrl(VIDEOurl)
#             # info['url'] = VIDEOurl
#         except:
#             VIDEOurl = 'No video recap available'
            
#         if not VIDEOurl:
#             VIDEOurl = 'No video recap available'
        
#         #test = {}
#         #test['url'] = 'hi this is a test'
        
#         #print(len(test))
        
#         if len(info) <= 1:
#             irc.reply('No video recap available.')
#             return
        
#         reply_string = ["\x02{}\x02 :: {}".format(info['title'],
#                                                   info['blurb']),
#                         "{}".format(info['description']),
#                         "\x02MP4:\x02 {} | \x02HLS:\x02 {} | {}".format(VIDEOurl['mp4'], VIDEOurl['hls'], info['duration'])]
        
#         for item in reply_string:
#             irc.sendMsg(ircmsgs.privmsg(msg.args[0], item))
                    
    def _red(self, string):
        """Returns a red string."""
        return ircutils.mircColor(string, 'red')

    def _yellow(self, string):
        """Returns a yellow string."""
        return ircutils.mircColor(string, 'yellow')

    def _green(self, string):
        """Returns a green string."""
        return ircutils.mircColor(string, 'green')

    def _blue(self, string):
        """Returns a blue string."""
        return ircutils.mircColor(string, 'blue')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))

############################
# Date-manipulation helpers
############################
    def _getTodayDate(self):
        """Get the current date formatted as "YYYYMMDD".
        Because the API separates games by day of start, we will consider and
        return the date in the Pacific timezone.
        The objective is to avoid reading future games anticipatedly when the
        day rolls over at midnight, which would cause us to ignore games
        in progress that may have started on the previous day.
        Taking the west coast time guarantees that the day will advance only
        when the whole continental US is already on that day."""
        today = self._pacificTimeNow().date()
        today_iso = today.isoformat()
        return today_iso #.replace('-', '')

    def _easternTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Eastern'))

    def _pacificTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Pacific'))
    
    def _ISODateToEasternTimeNext(self, iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern time formatted with am/pm. (The default human-readable format
        for the listing of games)."""
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_time = date_eastern.strftime('%a %m/%d, %I:%M %p %Z')
        return "{}".format(eastern_time) # Strip the seconds

    def _fetchPitchers(self, games, team, override):
        """fetch pitchers"""

        data = {}
        current_only = False
        ss_dh = False
        test_status = 'I'
        #print(games)
        for idx, game in enumerate(games):
            data['Game {}'.format(idx+1)] = []
            # if len(games) > 1:
            #     ss_dh = True
            #     data.append('\x02Game {}\x02'.format(idx+1))
            gpk = game['id']
            #print(game['status'])
            if 'I' in game['status']:
                current_only = True if not override else False
            if 'S' == game['status']:
                data['Game {}'.format(idx+1)] = False
                break
            url = 'https://statsapi.mlb.com/api/v1/game/{}/boxscore'.format(gpk)
            #print(url)
            temp = requests.get(url).json()
            for teams in temp['teams']:
                #print(temp['teams'][teams]['team']['id'])
                if int(team) == temp['teams'][teams]['team']['id']:
                    pitcher_ids = temp['teams'][teams]['pitchers']
                    for pitcher_id in pitcher_ids:
                        for player in temp['teams'][teams]['players']:
                            if int(pitcher_id) == temp['teams'][teams]['players'][player]['person']['id']:
                                if current_only:
                                    #if temp['teams'][teams]['players'][player]['gameStatus']['isCurrentPitcher']:
                                    data['Game {}'.format(idx+1)] = [temp['teams'][teams]['players'][player]]
                                else:
                                    data['Game {}'.format(idx+1)].append(temp['teams'][teams]['players'][player])
            #print(data)

        #print(data)
        #print(current_only, data)
        if current_only and not data:
            return ['No current pitcher for {} (use --all to see every pitcher)'.format(self._TEAM_BY_ID[team])]
        
        if not data:
            return None

        if len(data) > 1:
            for d in data:
                if not data[d]:
                    data[d] = ['No current pitcher for {} in {} (use --all to see every pitcher)'.format(self._TEAM_BY_ID[team], d)]
        else:
            for d in data:
                if not data[d]:
                    data[d] = ['No current pitcher for {} (use --all to see every pitcher)'.format(self._TEAM_BY_ID[team])]

        return data

    def _replyPitchersAsString(self, pitchers):
        """parses and returns pitchers"""

        resp = []
        width = 0

        def _iteratePitchers(pitchers):

            resp = []
            width = 0

            #print(pitchers)
            for idx, pitcher in enumerate(pitchers):
                #print(pitcher)
                if type(pitcher) == str:
                    continue
                name = pitcher['person']['fullName']
                name = ' '.join(name.split())
                suffixes = ['jr.']
                lname = -1
                for suffix in suffixes:
                    if name.split(' ')[lname].lower() in suffix:
                        lname = -2
                    else:
                        lname = -1
                if len(name.split(' ')[lname]) > width:
                    width = len(name.split(' ')[lname])

            for pitcher in pitchers:
                if type(pitcher) == str:
                    resp.append(pitcher)
                    continue
                name = pitcher['person']['fullName']
                name = ' '.join(name.split())
                stats = pitcher['stats']['pitching']
                try:
                    era = '{:.2f}'.format((stats['earnedRuns']/float(stats['inningsPitched']))*9)
                except:
                    if float(stats['inningsPitched']) == 0.0 and stats['earnedRuns'] > 0:
                        era = '∞'
                    else:
                        era = '0.00'
                try:
                    opBA = '{:.3f}'.format((stats['hits'])/(stats['battersFaced'] - stats['baseOnBalls']))
                except:
                    opBA = '.000'
                
                suffixes = ['jr.']
                lname = -1
                #print(name.split(' ')[lname].lower())
                for suffix in suffixes:
                    #print(suffix)
                    if name.split(' ')[lname].lower() in suffix:
                        #print('hi')
                        lname = -2
                    else:
                        lname = -1
                string = ('\x02\x0312{}. {:{width}}\x03 IP:\x02 {} '
                                        '\x02H:\x02 {} '
                                        '\x02R:\x02 {} '
                                        '\x02ER:\x02 {} '
                                        '\x02BB:\x02 {} '
                                        '\x02K:\x02 {} '
                                        '\x02HR:\x02 {} '
                                        '\x02BF:\x02 {:>2} '
                                        '\x02Pit:\x02 {:>3} '
                                        '\x02B-S:\x02 {:>2}-{:<2} '
                                        '\x02ERA:\x02 {:>6} '
                                        '\x02OpBA:\x02 {}').format(
                    name[0],
                    name.split(' ')[lname],
                    '0' if not stats.get('inningsPitched') else stats.get('inningsPitched'),
                    '0' if not stats.get('hits') else stats.get('hits'),
                    '0' if not stats.get('runs') else stats.get('runs'),
                    '0' if not stats.get('earnedRuns') else stats.get('earnedRuns'),
                    '0' if not stats.get('baseOnBalls') else stats.get('baseOnBalls'),
                    '0' if not stats.get('strikeOuts') else stats.get('strikeOuts'),
                    '0' if not stats.get('homeRuns') else stats.get('homeRuns'),
                    '0' if not stats.get('battersFaced') else stats.get('battersFaced'),
                    '0' if not stats.get('pitchesThrown') else stats.get('pitchesThrown'),
                    '0' if not stats.get('balls') else stats.get('balls'),
                    '0' if not stats.get('strikes') else stats.get('strikes'),
                    era,
                    opBA,
                    width=str(width))
                resp.append(string)
            return resp

        
        #print(len(pitchers))

        if len(pitchers) > 1:
            # double header
            #print('hi')
            resp = {}
            for game in pitchers:
                #print(pitchers[game])
                if "No current pitcher" not in pitchers[game][0]:
                    resp[game] = _iteratePitchers(pitchers[game])
        else:
            g1_pitchers = pitchers['Game 1']
            resp = _iteratePitchers(g1_pitchers)

        #print(resp)
        
        return resp

    def _sortGames(self, games):
        """sort based on status"""

        #sorted_games = sorted(games, key=lambda k: k['timestamp'])
        sorted_games = sorted(games, key=lambda k: k['ended'])
        
        return sorted_games

    def _replyAsString(self, team, games, tz='US/Eastern', tv=False):
        """parse games and return a string"""
        tmp_dt = '\x02{}\x02: '.format(games[0]['date'])
        
        def _parseStatus(state, inning):
            if not state:
                state = 'F'
            #print(state)
            if 'T' in state or 'B' in state:
                if 'T' in state:
                    resp = '\x033{}{}\x03'.format('↑', inning)
                else:
                    resp = '\x033{}{}\x03'.format('↓', inning)
            elif 'M' in state:
                resp = '\x037{}{}\x03'.format(state, inning)
            elif 'E' in state or 'F' in state:
                if inning == 9 and 'E' not in state:
                    resp = '\x034{}\x03'.format(state)
                elif 'E' in state:
                    resp = '\x037{}{}\x03'.format(state, inning)
                else:
                    resp = '\x034{}/{}\x03'.format(state, inning)
            else:
                resp = '{}{}'.format(state, inning)
            return resp

        def _parseTimezone(time, tz='US/Eastern'):
            if not tz:
                tz = 'US/Eastern'
                
            if 'Game 2' == time:
                return time

            def _checkTarget(target):
                """check input among common tz"""
                target2 = target.upper()
                common = {'CT':  'US/Central',
                        'CDT': 'US/Central',
                        'CST': 'US/Central',
                        'MT':  'US/Mountain',
                        'MDT': 'US/Mountain',
                        'MST': 'US/Mountain',
                        'PT':  'US/Pacific',
                        'PDT': 'US/Pacific',
                        'PST': 'US/Pacific',
                        'ET':  'US/Eastern',
                        'EDT': 'US/Eastern',
                        'EST': 'US/Eastern',
                        'CENTRAL': 'US/Central',
                        'EASTERN': 'US/Eastern',
                        'PACIFIC': 'US/Pacific',
                        'MOUNTAIN': 'US/Mountain'}
                if target2 in common:
                    target = common[target2]
                #print(target)
                return target
            tz = _checkTarget(tz)

            return pendulum.parse(time, strict=False).in_tz(tz).format('h:mm A zz')

        tmp = []
        if len(games) == 1:
            team = True
        for game in games:
            #print(game['homeTeam'], game['status'])
            if game['status'] == 'I':
                status = _parseStatus(game['state'], game['inning'])
                if '↓' in status and game['risp']:
                    if 'Corners' in game['runners'] or 'Loaded' in game['runners'] or '3rd' in game['runners']:
                        game['homeTeam'] = '\x034{}\x03'.format(game['homeTeam'])
                    elif '2nd' in game['runners']:
                        game['homeTeam'] = '\x037{}\x03'.format(game['homeTeam'])
                else:
                    if 'Corners' in game['runners'] or 'Loaded' in game['runners'] or '3rd' in game['runners']:
                        game['awayTeam'] = '\x034{}\x03'.format(game['awayTeam'])
                    elif '2nd' in game['runners']:
                        game['awayTeam'] = '\x037{}\x03'.format(game['awayTeam'])
                if game['homeScore'] > game['awayScore']:
                    tmp_st = '{} {} \x02{} {}\x02 {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                elif game['awayScore'] > game['homeScore']:
                    tmp_st = '\x02{} {}\x02 {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                else:
                    tmp_st = '{} {} {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                if game['broadcasts'] and tv:
                    if game['broadcasts']['tv'] and game['broadcasts']['radio']:
                        watch = ' [\x02TV:\x02 {} | \x02Radio:\x02 {}]'.format(
                            ', '.join(tv for tv in game['broadcasts']['tv']),
                            ', '.join(radio for radio in game['broadcasts']['radio']))
                    elif game['broadcasts']['tv'] and not game['broadcasts']['radio']:
                        watch = ' [\x02TV:\x02 {}]'.format(
                            ', '.join(tv for tv in game['broadcasts']['tv']))
                    elif not game['broadcasts']['tv'] and game['broadcasts']['radio']:
                        watch = ' [\x02Radio:\x02 {}]'.format(
                            ', '.join(radio for radio in game['broadcasts']['radio']))
                    else:
                        watch = ' [No TV or Radio broadcasts found]'
                    tmp_st += watch
                elif not game['broadcasts'] and tv:
                    tmp_st += ' [No TV or Radio broadcasts found]'
                if team and ('M' not in status and 'E' not in status) and not tv:
                    if game['pitcher'] and game['batter']:
                        pb = ' | \x02P:\x02 {}, \x02AB:\x02 {} '.format(game['pitcher'], game['batter'])
                    else:
                        pb = ''
                    if game['runners']:
                        ro = ' | \x037Runners\x03: {}'.format(game['runners'])
                    else:
                        ro = ''
                    tmp_st += ' | \x033B\x03:{} \x037S\x03:{} \x034O\x03:{}{}{}| {}'
                    tmp_st = tmp_st.format(game['balls'], game['strikes'], game['outs'], ro, pb, game['last'])
                elif team and ('M' in status or 'E' in status) and not tv:
                    tmp_st += ' | {}'
                    tmp_st = tmp_st.format(game['last'])
                #if team:
                    #print(game['id'])
                tmp.append(tmp_st)
            elif ('F' in game['status'] or 'O' in game['status']) and not team:
                status = _parseStatus(game['state'], game['inning'])
                if game['homeScore'] > game['awayScore']:
                    tmp_st = '{} {} \x02{} {}\x02 {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                elif game['awayScore'] > game['homeScore']:
                    tmp_st = '\x02{} {}\x02 {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                else:
                    tmp_st = '{} {} {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                
                tmp.append(tmp_st)
            elif (game['status'] == 'S' or game['status'] == 'P') and team and not tv:
                tmp_st = '{} {} @ {} {} {}'.format(game['awayTeam'], game['awayRecord'],
                                                   game['homeTeam'], game['homeRecord'],
                                                   game['dt'] if game['dh'] else _parseTimezone(game['dt'], tz))
                pitchers = ' | {} vs {}'.format(game['awayProb'], game['homeProb'])
                tmp_st += pitchers
                #print(game['broadcasts'])
                if game['broadcasts']:
                    if game['broadcasts']['tv'] and game['broadcasts']['radio']:
                        watch = ' | \x02TV:\x02 {} | \x02Radio:\x02 {}'.format(
                            ', '.join(tv for tv in game['broadcasts']['tv']),
                            ', '.join(radio for radio in game['broadcasts']['radio']))
                    elif game['broadcasts']['tv'] and not game['broadcasts']['radio']:
                        watch = ' | \x02TV:\x02 {}'.format(
                            ', '.join(tv for tv in game['broadcasts']['tv']))
                    elif not game['broadcasts']['tv'] and game['broadcasts']['radio']:
                        watch = ' | \x02Radio:\x02 {}'.format(
                            ', '.join(radio for radio in game['broadcasts']['radio']))
                    else:
                        watch = ''
                    tmp_st += watch
                if game['description']:
                    tmp_st += ' | {}'.format(game['description'])
                tmp.append(tmp_st)
            elif ('F' in game['status'] or 'O' in game['status']) and team:
                status = _parseStatus(game['state'], game['inning'])
                if game['homeScore'] > game['awayScore']:
                    tmp_st = '{} {} \x02{} {}\x02 {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                elif game['awayScore'] > game['homeScore']:
                    tmp_st = '\x02{} {}\x02 {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                else:
                    tmp_st = '{} {} {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                wls_line = ' | \x033W:\x03 {} \x034L:\x03 {}'.format(
                    game['decisions']['W'], game['decisions']['L'])
                if game['decisions'].get('S'):
                    wls_line += ' \x037S:\x03 {}'.format(game['decisions']['S'])
                tmp_st += wls_line
                if game['homers']:
                    hr_str = ' | \x02HR: {}\x02: {} \x02{}\x02: {}'.format(
                        game['awayTeam'],
                        ' '.join(item for item in game['homers'][game['awayTeam']]),
                        game['homeTeam'],
                        ' '.join(item for item in game['homers'][game['homeTeam']]))
                    tmp_st += hr_str
                tmp.append(tmp_st)
            elif game['status'] == 'DI' or game['status'] == 'DC' or game['status'] == 'DS' or game['status'] == 'DR' \
            or game['status'] == 'DV' or game['status'] == 'DG':
                tmp_st = '{} @ {} \x034PPD\x03'.format(game['awayTeam'], game['homeTeam'])
                if game['reason'] and team:
                    tmp_st += ' - {}'.format(game['reason'])
                tmp.append(tmp_st)
            # elif game['status'] == 'DI':
            #     tmp_st = '{} @ {} \x034PPD\x03'.format(game['awayTeam'], game['homeTeam'])
            #     if game['reason'] and team:
            #         tmp_st += ' - {}'.format(game['reason'])
            #     tmp.append(tmp_st)
            elif game['status'] == 'PW':
                tmp_st = '{} @ {} {} - Warmup'.format(game['awayTeam'], game['homeTeam'],
                                             _parseTimezone(game['dt'], tz))
                if team:
                    pitchers = ' | {} vs {}'.format(game['awayProb'], game['homeProb'])
                    tmp_st += pitchers
                    tv = True
                if tv:
                    if game['broadcasts']:
                        if game['broadcasts']['tv'] and game['broadcasts']['radio']:
                            watch = ' [\x02TV:\x02 {} | \x02Radio:\x02 {}]'.format(
                                ', '.join(tv for tv in game['broadcasts']['tv']),
                                ', '.join(radio for radio in game['broadcasts']['radio']))
                        elif game['broadcasts']['tv'] and not game['broadcasts']['radio']:
                            watch = ' [\x02TV:\x02 {}]'.format(
                                ', '.join(tv for tv in game['broadcasts']['tv']))
                        elif not game['broadcasts']['tv'] and game['broadcasts']['radio']:
                            watch = ' [\x02Radio:\x02 {}]'.format(
                                ', '.join(radio for radio in game['broadcasts']['radio']))
                        else:
                            watch = ' [No TV or Radio broadcasts found]'
                    else:
                        watch = ' [No TV or Radio broadcasts found]'
                    tmp_st += watch
                tmp.append(tmp_st)
            elif game['status'] == 'PC' or game['status'] == 'PS' or game['status'] == 'PR' or game['status'] == 'PI':
                status = _parseStatus(game['state'], game['inning'])
                if game['homeScore'] > game['awayScore']:
                    tmp_st = '{} {} \x02{} {}\x02 {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                elif game['awayScore'] > game['homeScore']:
                    tmp_st = '\x02{} {}\x02 {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                else:
                    tmp_st = '{} {} {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                status)
                tmp_st += ' \x037Delay\x03'
                if game['reason'] and team:
                    tmp_st += ' - {}'.format(game['reason'])
                tmp.append(tmp_st)
            elif game['status'] == 'IW' or game['status'] == 'IC' or game['status'] == 'IS' or game['status'] == 'IR':
                # status = _parseStatus(game['state'], game['inning'])
                if game['homeScore'] > game['awayScore']:
                    tmp_st = '{} {} \x02{} {}\x02'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                )
                elif game['awayScore'] > game['homeScore']:
                    tmp_st = '\x02{} {}\x02 {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                )
                else:
                    tmp_st = '{} {} {} {}'.format(game['awayTeam'],
                                                                game['awayScore'],
                                                                game['homeTeam'],
                                                                game['homeScore'],
                                                                )
                tmp_st += ' \x037Delay\x03'
                if game['reason'] and team:
                    tmp_st += ' - {}'.format(game['reason'])
                tmp.append(tmp_st)
            else:
                tmp_st = '{} @ {} {}'.format(game['awayTeam'], game['homeTeam'],
                                             game['dt'] if game['dh'] else _parseTimezone(game['dt'], tz))
                if game['status'] in self._STATUSES.keys() \
                and game['status'] not in ['S', 'P', 'D']:
                    tmp_st += ' - {}'.format(self._STATUSES[game['status']])
                if tv:
                    if game['broadcasts']:
                        if game['broadcasts']['tv'] and game['broadcasts']['radio']:
                            watch = ' [\x02TV:\x02 {} | \x02Radio:\x02 {}]'.format(
                                ', '.join(tv for tv in game['broadcasts']['tv']),
                                ', '.join(radio for radio in game['broadcasts']['radio']))
                        elif game['broadcasts']['tv'] and not game['broadcasts']['radio']:
                            watch = ' [\x02TV:\x02 {}]'.format(
                                ', '.join(tv for tv in game['broadcasts']['tv']))
                        elif not game['broadcasts']['tv'] and game['broadcasts']['radio']:
                            watch = ' [\x02Radio:\x02 {}]'.format(
                                ', '.join(radio for radio in game['broadcasts']['radio']))
                        else:
                            watch = ' [No TV or Radio broadcasts found]'
                    else:
                        watch = ' [No TV or Radio broadcasts found]'
                    tmp_st += watch
                tmp.append(tmp_st)

        if len(tmp) > 1 and team:
            tmp_dt = [tmp_dt + tmp[0]]
            for item in tmp[1:]:
                tmp_dt.append(item)
            return tmp_dt

        tmp_len = len(tmp)
        if tmp_len > 12:
            split_at_pre = ":{}".format(tmp_len // 2)
            split_at_post = "{}:".format(tmp_len // 2)
            split_at = tmp_len // 2
            #print(split_at)
            tmp_dt = (tmp_dt + ' | '.join(item for item in tmp[:split_at]), ' | '.join(item for item in tmp[split_at:]))
        else:
            tmp_dt +=  ' | '.join(item for item in tmp)

        return tmp_dt

    def _parseInput(self, args=None):
        """parse user input from mlb2"""
        # return team, date, timezone

        tz = 'US/Eastern'
        date = None
        team = None
        is_date = None

        if not args:
            return team, date, tz

        arg_array = []
        for arg in args.split(' '):
            arg_array.append(arg)
        
        for idx, arg in enumerate(arg_array):
            #print(arg)
            if '--tz' in arg:
                #print(arg_array[idx+1])
                try:
                    tz = arg_array[idx+1]
                except:
                    tz = 'US/Eastern'
            if arg.lower() in self._FUZZY_DAYS or arg[:3].lower() in self._FUZZY_DAYS:
                date = self._parseDate(arg)
                #print(date)
                #date = pendulum.parse(date).in_tz(tz)
            try:
                arg = arg.strip('-')
                arg = arg.strip('/')
                if arg[0].isdigit() and arg[1].isdigit() and arg[2].isalpha():
                    if arg[-1].isdigit():
                        yr = arg[-2:]
                        mnth = " ".join(re.findall("[a-zA-Z]+", arg))
                        #print(mnth,yr)
                        rebuild = '{}-{}-{}'.format(mnth, arg[:2], yr)
                    else:
                        rebuild = arg[2:] + arg[:2]
                    #print('both', rebuild)
                elif arg[0].isdigit() and arg[1].isalpha():
                    rebuild = arg[1:] + arg[0]
                    #print('one', rebuild)
                else:
                    rebuild = arg
                    
                #print(rebuild)
                is_date = pendulum.parse(rebuild, strict=False)
                #print(is_date)
            except:
                is_date = None
            if is_date:
                date = is_date.format('YYYY-MM-DD')
            if arg.upper() in self._TEAM_BY_TRI:
                team = str(self._TEAM_BY_TRI[arg.upper()])
            elif arg.lower() in self._TEAM_BY_NICK:
                abbr = str(self._TEAM_BY_NICK[arg.lower()])
                team = str(self._TEAM_BY_TRI[abbr])
            # else:
            #     return team, date, tz

        return team, date, tz

    def _parseDate(self, string):
        """parse date"""
        date = string[:3].lower()
        if date in self._FUZZY_DAYS or string.lower() in self._FUZZY_DAYS:
            if date == 'yes':
                date_string = pendulum.yesterday('US/Pacific').format('YYYY-MM-DD')
                #print(date_string)
                return date_string
            elif date == 'tod' or date == 'ton':
                date_string = pendulum.now('US/Pacific').format('YYYY-MM-DD')
                return date_string
            elif date == 'tom':
                date_string = pendulum.tomorrow('US/Pacific').format('YYYY-MM-DD')
                return date_string
            elif date == 'sun':
                date_string = pendulum.now('US/Pacific').next(pendulum.SUNDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'mon':
                date_string = pendulum.now('US/Pacific').next(pendulum.MONDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'tue':
                date_string = pendulum.now('US/Pacific').next(pendulum.TUESDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'wed':
                date_string = pendulum.now('US/Pacific').next(pendulum.WEDNESDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'thu':
                date_string = pendulum.now('US/Pacific').next(pendulum.THURSDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'fri':
                date_string = pendulum.now('US/Pacific').next(pendulum.FRIDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'sat':
                date_string = pendulum.now('US/Pacific').next(pendulum.SATURDAY).format('YYYY-MM-DD')
                return date_string

    def _fetchGames(self, team=None, date=None):
        """fetches games for mlb2"""

        team = 'all' if not team else team
        date = pendulum.now('US/Pacific').to_date_string() if not date else date

        url = self._SCOREBOARD_ENDPOINT.format(date)

        if 'all' not in team:
            url += '&teamId={}'.format(team)

        #print(url)

        try:
            data = requests.get(url).json()
        except:
            return None

        try:
            games = data['dates'][0]['games']
        except:
            return None

        return games

    def _parseGames(self, games, date, team=None):
        """parse games for mlb2"""
        #print('http://statsapi.mlb.com/api/v1/game/{}/linescore'.format(games[0]['gamePk']))
        
        if team:
            date = pendulum.now('US/Pacific').to_date_string() if not date else date
            games_url = self._SCOREBOARD_ENDPOINT.format(date)
            games_url += '&teamId={}'.format(team)
            games = requests.get(games_url).json()
            #print(games_url)
            try:
                games = games['dates'][0]['games']
            except:
                return None
        
        def _parseLastPlay():
            #print('len:', len(games))
            if len(games) == 1:
                url = 'http://statsapi.mlb.com/api/v1/game/{}/playByPlay'
                #print(url)
                url = url.format(games[0]['gamePk'])
                #print(url, 'http://statsapi.mlb.com/api/v1/game/{}/playByPlay'.format(games[0]['gamePk']))
                data = requests.get(url)
                data = data.json()
                plays = reversed(data['allPlays'])
                for play in plays:
                    if play['about']['isComplete'] == True:
                        last_play = play['result']['description']
                        break
            #print(last_play)
            return last_play
                    

        def _parsePitcher(pitcher):
            name = pitcher['lastInitName']
            pitches = pitcher['stats'][1]['stats']['pitchesThrown']
            tmp = '{} ({})'.format(name, pitches)
            return tmp
        
        def _parseBatter(batter):
            name = batter['lastInitName']
            line = '{}/{}'.format(batter['stats'][0]['stats']['hits'], batter['stats'][0]['stats']['atBats'])
            tmp = '{} ({})'.format(name, line)
            return tmp

        def _parseRunners(runners):
            first = True if runners.get('first') else False
            second = True if runners.get('second') else False
            third = True if runners.get('third') else False

            #print(first, second, third)

            if first and not second and not third:
                resp = '1st'
                shrt = '\x039⠠\x03'
                risp = False
            elif first and second and not third:
                resp = '1st and 2nd'
                shrt = '⠢'
                risp = True
            elif first and second and third:
                resp = 'Loaded'
                shrt = '∴'
                risp = True
            elif not first and second and not third:
                resp = '2nd'
                shrt = '⠁'
                risp = True
            elif not first and not second and third:
                resp = "3rd"
                shrt = '\x034⠄\x03'
                risp = True
            elif not first and not second and not third:
                resp = ''
                shrt = ''
                risp = False
            elif first and not second and third:
                resp = 'Corners'
                shrt = '⠤'
                risp = True
            elif not first and second and third:
                resp = '2nd and 3rd'
                shrt = '⠔'
                risp = True
            return resp, shrt, risp

        tmp = []
        for game in games:
            dh = False
            description = None
            gamePk = game['gamePk']
            dt = game['gameDate']
            #print(dt)
            timestamp = pendulum.parse(dt).in_tz('US/Eastern').int_timestamp
            #print(timestamp)
            date = pendulum.parse(game['gameDate']).in_tz('US/Eastern').format('MM/DD/YY')
            time = pendulum.parse(game['gameDate']).in_tz('US/Eastern').format('h:mm A zz')
            #print(date, time)
            status = game['status']['statusCode']
            reason = game['status'].get('reason')
            try:
                description = game['description']
            except:
                description = None
            if game['doubleHeader'] == 'Y' or game['doubleHeader'] == 'S':
                #print('doubleheader')
                if game['gameNumber'] > 1:
                    #print('game 2+')
                    timestamp = pendulum.parse(dt).in_tz('US/Eastern')
                    timestamp = timestamp.add(days=1)
                    timestamp = timestamp.int_timestamp
                    dt = 'Game {}'.format(game['gameNumber'])
                    dh = True
            #print(time)
            try:
                broadcasts = {}
                broadcasts['tv'] = []
                broadcasts['radio'] = []
                for channel in game['broadcasts']:
                    if 'TV' in channel['type']:
                        if 'MLB.com' not in channel['name'] and 'out-of-market' not in channel['name']:
                            broadcasts['tv'].append(channel['name'])
                    elif 'M' in channel['type']:
                        if 'MLB.com' not in channel['name'] and 'out-of-market' not in channel['name']:
                            broadcasts['radio'].append(channel['name'])
                broadcasts['tv'] = [*{*broadcasts['tv']}]
                broadcasts['radio'] = [*{*broadcasts['radio']}]
            except:
                broadcasts = None
            away_team = game['teams']['away']['team']['abbreviation']
            home_team = game['teams']['home']['team']['abbreviation']
            away_record = '({}-{})'.format(game['teams']['away']['leagueRecord']['wins'],
                                           game['teams']['away']['leagueRecord']['losses'])
            home_record = '({}-{})'.format(game['teams']['home']['leagueRecord']['wins'],
                                           game['teams']['home']['leagueRecord']['losses'])
            try:
                try:
                    away_era = game['teams']['away']['probablePitcher']['stats'][1]['stats']['era']
                    away_wins = game['teams']['away']['probablePitcher']['stats'][1]['stats']['wins']
                    away_loss = game['teams']['away']['probablePitcher']['stats'][1]['stats']['losses']
                    away_line = ' {}/{}-{}'. format(away_era, away_wins, away_loss)
                except:
                    away_line = ''
                try:
                    home_era = game['teams']['home']['probablePitcher']['stats'][1]['stats']['era']
                    home_wins = game['teams']['home']['probablePitcher']['stats'][1]['stats']['wins']
                    home_loss = game['teams']['home']['probablePitcher']['stats'][1]['stats']['losses']
                    home_line = ' {}/{}-{}'. format(home_era, home_wins, home_loss)
                except:
                    home_line = ''
                     
                try:
                    away_prob = '{} ({}HP{})'.format(
                        game['teams']['away']['probablePitcher']['lastInitName'],
                        game['teams']['away']['probablePitcher']['pitchHand']['code'],
                        away_line)
                except:
                    away_prob = 'TBD'
                try:
                    home_prob = '{} ({}HP{})'.format(
                        game['teams']['home']['probablePitcher']['lastInitName'],
                        game['teams']['home']['probablePitcher']['pitchHand']['code'],
                        home_line)
                except:
                    home_prob = 'TBD'
            except:
                away_prob = 'TBD'
                home_prob = 'TBD'
            away_score = game['teams']['away'].get('score')
            home_score = game['teams']['home'].get('score')
            #print('scores', away_score, home_score)
            if not away_score:
                away_score = 0
            if not home_score:
                home_score = 0
            try:
                inning = game['linescore'].get('currentInning')
            except:
                inning = 1
            try:
                state = game['linescore'].get('inningState')
            except:
                state = None
            #print(state)
            balls = '0'
            strikes = '0'
            outs = '0'
            pitcher = None
            batter = None
            runners = None
            short_runners = None
            risp = False
            if not state:
                if 'F' in status or 'O' in status:
                    state = 'F'
                    ended = True
                    last_play = ''
                elif status == 'DI' or status == 'DC' or status == 'DS' or status == 'DR' \
                or status == 'DV' or status == 'DG':
                    state = state
                    ended = True
                    last_play = ''
                else:
                    state = None
                    ended = False
                    last_play = ''
            else:
                if 'F' in status or 'O' in status:
                    state = 'F'
                    ended = True
                    last_play = ''
                elif status == 'DI' or status == 'DC' or status == 'DS' or status == 'DR' \
                or status == 'DV' or status == 'DG':
                    state = state
                    ended = True
                    last_play = ''
                else:
                    state = state[:1]
                    ended = False
                    if 'I' in status:
                        try:
                            pitcher = _parsePitcher(game['linescore']['defense']['pitcher'])
                        except:
                            pitcher = None
                        try:
                            batter = _parseBatter(game['linescore']['offense']['batter'])
                        except:
                            batter = None
                        try:
                            runners, short_runners, risp = _parseRunners(game['linescore']['offense'])
                        except:
                            runners = None
                            short_runners = None
                            risp = False
                        try:
                            try:
                                last_play = _parseLastPlay()
                                last_play = last_play.strip()
                                last_play = " ".join(last_play.split())
                            except:
                                last_play = game['previousPlay']['result'].get('description').strip()
                                last_play = " ".join(last_play.split())
                        except:
                            last_play = ''
                        try:
                            balls = str(game['linescore']['balls'])
                        except:
                            balls = balls
                        try:
                            strikes = str(game['linescore']['strikes'])
                        except:
                            strikes = strikes
                        try:
                            outs = str(game['linescore']['outs'])
                        except:
                            outs = outs
                    else:
                        last_play = ''
            if 'F' in status or 'O' in status:
                decisions = {}
                try:
                    decisions['W'] = '{} ({}/{}-{})'.format(
                        game['decisions']['winner']['lastInitName'],
                        game['decisions']['winner']['stats'][3]['stats']['era'],
                        game['decisions']['winner']['stats'][3]['stats']['wins'],
                        game['decisions']['winner']['stats'][3]['stats']['losses'])
                except:
                    decisions['W'] = 'TBD'
                try:
                    decisions['L'] = '{} ({}/{}-{})'.format(
                        game['decisions']['loser']['lastInitName'],
                        game['decisions']['loser']['stats'][3]['stats']['era'],
                        game['decisions']['loser']['stats'][3]['stats']['wins'],
                        game['decisions']['loser']['stats'][3]['stats']['losses'])
                except:
                    decisions['L'] = 'TBD'
                try:
                    save = game['decisions'].get('save')
                except:
                    save = None
                if save:
                    decisions['S'] = '{} ({}/{}-{}/{}-{})'.format(
                        save['lastInitName'],
                        save['stats'][3]['stats']['era'],
                        save['stats'][3]['stats']['wins'],
                        save['stats'][3]['stats']['losses'],
                        save['stats'][3]['stats']['saves'],
                        save['stats'][3]['stats']['blownSaves'])
                homers = {}
                homeRuns = game.get('homeRuns')
                if homeRuns:
                    homers[away_team] = []
                    homers[home_team] = []
                    for item in homeRuns:
                        #print(item)
                        try:
                            name = item['matchup']['batter']['lastInitName']
                        except:
                            name = item['matchup']['batter']['fullName']
                        num = item['matchup']['batter']['stats'][2]['stats']['homeRuns']
                        string = '{}({})'.format(name,num)
                        if 'top' in item['about']['halfInning']:
                            homers[away_team].append(string)
                        elif 'bot' in item['about']['halfInning']:
                            homers[home_team].append(string)
                    
                    if not homers[away_team]:
                        homers[away_team] = ['None']
                    if not homers[home_team]:
                        homers[home_team] = ['None']
                    
                    if homers[away_team]:
                        #print('hi')
                        homers[away_team] = [*{*homers[away_team]}]
                    if homers[home_team]:
                        #print('bye')
                        homers[home_team] = [*{*homers[home_team]}]

            else:
                homers = None
                decisions = None
            #print(time)
            tmp.append({'id': gamePk, 'date': date, 'time': time, 'dt': dt, 'dh': dh, 'timestamp': timestamp,
                        'awayTeam': away_team, 'awayScore': away_score,
                        'homeTeam': home_team, 'homeScore': home_score,
                        'inning': inning, 'state': state, 'last': last_play,
                        'status': status, 'reason': reason, 'broadcasts': broadcasts, 'ended': ended,
                        'balls': balls, 'strikes': strikes, 'outs': outs,
                        'pitcher': pitcher, 'batter': batter, 'runners': runners, 'sh_runs': short_runners, 'risp': risp,
                        'awayRecord': away_record, 'homeRecord': home_record,
                        'awayProb': away_prob, 'homeProb': home_prob,
                        'decisions': decisions, 'homers': homers, 'description': description})

        return(tmp)

Class = MLBScores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
