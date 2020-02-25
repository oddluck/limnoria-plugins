###
# Copyright (c) 2016, Santiago Gil
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import json
import urllib.request
import pendulum
import requests

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NHL')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class NHL(callbacks.Plugin):
    """Get scores from NHL.com."""
    def __init__(self, irc):
        self.__parent = super(NHL, self)
        self.__parent.__init__(irc)

        self._SCOREBOARD_ENDPOINT = ("https://statsapi.web.nhl.com/api/v1/schedule?startDate={}&endDate={}" +
                                     "&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all,schedule.ticket,schedule.game.content.media.epg" +
                                     "&leaderCategories=&site=en_nhl&teamId=")
        # https://statsapi.web.nhl.com/api/v1/schedule?startDate=2016-12-15&endDate=2016-12-15
        # &expand=schedule.teams,schedule.linescore,schedule.broadcasts,schedule.ticket,schedule.game.content.media.epg
        # &leaderCategories=&site=en_nhl&teamId=

        self._FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow',
                            'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

        # These two variables store the latest data acquired from the server
        # and its modification time. It's a one-element cache.
        # They are used to employ HTTP's 'If-Modified-Since' header and
        # avoid unnecessary downloads for today's information (which will be
        # requested all the time to update the scores).
        self._today_scores_cached_url = None
        self._today_scores_last_modified_time = None
        self._today_scores_last_modified_data = None
        
        self._TEAMS_BY_TRI = self._getTeams()

        #pendulum.set_formatter('alternative')

    def nhl(self, irc, msg, args, optional_team, optional_date):
        """[<team>] [<date>]
        Get games for a given date (YYYY-MM-DD). If none is specified, return games
        scheduled for today. Optionally add team abbreviation to filter
        for a specific team."""

        # Check to see if there's optional input and if there is check if it's
        # a date or a team, or both.
        tz = None
        if optional_team is None:
            team = "all"
            if optional_date:
                if '--tz' in optional_date:
                    tz = optional_date.split()[2]
                    optional_date = optional_date.split()[0]
            try:
                date = self._checkDateInput(optional_date)
                #print("1")
            except ValueError as e:
                irc.reply('ERROR: {0!s}'.format(e))
                return
        else:
            if optional_team == '--tz':
                tz = optional_date
                team = 'all'
                date = None
            else:
                date = self._checkDateInput(optional_team)
                #print("2")
                if date: # and len(date) != 3:
                    team = "all"
#                 elif date and len(date) == 3:
#                     team = date
#                     date = None
                else:
                    team = optional_team.upper()
                    try:
                        date = self._checkDateInput(optional_date)
                        #print("3")
                    except ValueError as e:
                        irc.reply('ERROR: {0!s}'.format(e))
                        return

        if date is None:
            if not tz:
                tz = 'US/Eastern'
            games = self._getTodayGames(team, tz)
            games_string = self._resultAsString(games)
            if not games_string:
                irc.reply("No games found for {}".format(team))
                return
            try:
                tdate = pendulum.from_format(games[0], 'YYYY-MM-DD').strftime('%m/%d/%y')
                games_string_date = ircutils.bold(tdate + ': ')
            except:
                games_string_date = ''
            #print(games[1]['clock'], games[1]['ended'])
            if len(games) == 2:
                if not games[1]['ended']:
                    broadcasts = games[1]['broadcasts']
                    games_string += ' [{}]'.format(broadcasts)
            #print(games)
            irc.reply(games_string_date + games_string)
        else:
            games = self._getGamesForDate(team, date)
            games_string = self._resultAsString(games)
            #print(games_string)
            if games_string == '':
                irc.reply("No games found for {}".format(team))
                return
            try:
                tdate = pendulum.from_format(games[0], 'YYYY-MM-DD').strftime('%m/%d/%y')
                games_string_date = ircutils.bold(tdate + ': ')
            except:
                games_string_date = ''
            if len(games) == 1:
                if not games[1]['ended']:
                    try:
                        broadcasts = games[1]['broadcasts']
                        games_string += ' [{}]'.format(broadcasts)
                    except:
                        pass
            #irc.reply(games_string)
            irc.reply(games_string_date + games_string)

    nhl = wrap(nhl, [optional('somethingWithoutSpaces'), optional('somethingWithoutSpaces')])
    
    def _getTeams(self):
        
        url = 'https://statsapi.web.nhl.com/api/v1/teams'
        try:
            data = requests.get(url).json()
            data = data['teams']
        except:
            return None
        
        teams = []
        for team in data:
            teams.append(team['abbreviation'])
        return teams

    def nhltv(self, irc, msg, args, optional_team, optional_date):
        """[<team>] [<date>]
        Get television broadcasts for a given date (YYYY-MM-DD). If none is specified, return broadcasts
        scheduled for today. Optionally add team abbreviation to filter
        for a specific team."""

        # Check to see if there's optional input and if there is check if it's
        # a date or a team, or both.
        if optional_team is None:
            team = "all"
            try:
                date = self._checkDateInput(optional_date)
            except ValueError as e:
                irc.reply('ERROR: {0!s}'.format(e))
                return
        else:
            date = self._checkDateInput(optional_team)
            if date:
                team = "all"
            else:
                team = optional_team.upper()
                try:
                    date = self._checkDateInput(optional_date)
                except ValueError as e:
                    irc.reply('ERROR: {0!s}'.format(e))
                    return

        if date is None:
            games = self._getTodayTV(team)
            games_string = self._resultTVAsString(games)
            try:
                tdate = pendulum.from_format(games[0], 'YYYY-MM-DD').strftime('%m/%d/%y')
                games_string_date = ircutils.bold(tdate + ': ')
            except:
                games_string_date = ''
            #print(games[0]['clock'], games[0]['ended'])
            if len(games) == 1:
                if not games[1]['ended']:
                    broadcasts = games[1]['broadcasts']
                    games_string += ' [{}]'.format(broadcasts)
            irc.reply(games_string_date + games_string)
        else:
            games = self._getTVForDate(team, date)
            if isinstance(games, str):
                irc.reply(games)
                return
            games_string = self._resultTVAsString(games)
            try:
                tdate = pendulum.from_format(games[0], 'YYYY-MM-DD').strftime('%m/%d/%y')
                games_string_date = ircutils.bold(tdate + ': ')
            except:
                games_string_date = ''
            if len(games) == 1:
                if not games[1]['ended']:
                    try:
                        broadcasts = games[1]['broadcasts']
                        games_string += ' [{}]'.format(broadcasts)
                    except:
                        pass
            #irc.reply(games_string)
            irc.reply(games_string_date + games_string)
        
        #if date is None:
        #    irc.reply(self._getTodayTV(team))
        #else:
        #    irc.reply(self._getTVForDate(team, date))

    nhltv = wrap(nhltv, [optional('somethingWithoutSpaces'), optional('somethingWithoutSpaces')])

    def _getTodayGames(self, team, tz='US/Eastern'):
        games = self._getGames(team, self._getTodayDate(), tz)
        return games

    def _getGamesForDate(self, team, date):
        #print(date)
        games = self._getGames(team, date)
        return games

    def _getTodayTV(self, team):
        games = self._getGames(team, self._getTodayDate())
        return games

    def _getTVForDate(self, team, date):
        #print(date)
        games = self._getGames(team, date)
        return games

############################
# Content-getting helpers
############################
    def _getGames(self, team, date, tz='US/Eastern'):
        """Given a date, populate the url with it and try to download its
        content. If successful, parse the JSON data and extract the relevant
        fields for each game. Returns a list of games."""
        url = self._getEndpointURL(date)

        # (If asking for today's results, enable the 'If-Mod.-Since' flag)
        use_cache = (date == self._getTodayDate())
        #use_cache = False
        response = self._getURL(url, use_cache)
        if isinstance(response, str):
            return "ERROR: Something went wrong, check input"

        json = self._extractJSON(response)
        games = self._parseGames(json, team, tz)
        return games

    def _getEndpointURL(self, date):
        return self._SCOREBOARD_ENDPOINT.format(date, date)

    def _getURL(self, url, use_cache=False):
        """Use urllib to download the URL's content. The use_cache flag enables
        the use of the one-element cache, which will be reserved for today's
        games URL. (In the future we could implement a real cache with TTLs)."""
        user_agent = 'Mozilla/5.0 \
                      (X11; Ubuntu; Linux x86_64; rv:45.0) \
                      Gecko/20100101 Firefox/45.0'
        header = {'User-Agent': user_agent}
        response = None

        # ('If-Modified-Since' to avoid unnecessary downloads.)
        if use_cache and self._haveCachedData(url):
            header['If-Modified-Since'] = self._today_scores_last_modified_time

        request = urllib.request.Request(url, headers=header)
        #print(url)

        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            if use_cache and error.code == 304: # Cache hit
                self.log.info("{} - 304"
                              "(Last-Modified: "
                              "{})".format(url, self._cachedDataLastModified()))
                return self._cachedData()
            else:
                self.log.error("HTTP Error ({}): {}".format(url, error.code))
                pass

        self.log.info("{} - 200".format(url))
        
        if not response:
            return "ERROR: Something went wrong, check input"

        if not use_cache:
            return response.read()

        # Updating the cached data:
        self._updateCache(url, response)
        return self._cachedData()

    def _extractJSON(self, body):
        return json.loads(body.decode('utf-8'))

    def _parseGames(self, json, team, tz='US/Eastern'):
        """Extract all relevant fields from NHL.com's json
        and return a list of games."""
        games = []
        if json['totalGames'] == 0:
            return games
        games.append(json['dates'][0]['date'])
        for g in json['dates'][0]['games']:
            #print(g)
            # Starting times are in UTC. By default, we will show Eastern times.
            # (In the future we could add a user option to select timezones.)
            tbd_check = self._ISODateToEasternTime(g['gameDate'])
            #print(tbd_check)
            if '3:00 AM' in tbd_check:
                starting_time = 'TBD'
                #starting_time_TBD = True
            else:
                if 'US/Eastern' not in tz:
                    starting_time = self._convertISODateToTime(g['gameDate'], tz)
                else:
                    starting_time = self._ISODateToEasternTime(g['gameDate'])
            broadcasts = []
            try:
                for item in g['broadcasts']:
                    broadcasts.append(item['name'])
            except:
                pass
            #print(broadcasts)
            game_info = {'home_team': g['teams']['home']['team']['abbreviation'],
                         'away_team': g['teams']['away']['team']['abbreviation'],
                         'home_score': g['teams']['home']['score'],
                         'away_score': g['teams']['away']['score'],
                         'broadcasts': '{}'.format(', '.join(item for item in broadcasts)),
                         'starting_time': starting_time,
                         'starting_time_TBD': g['status']['startTimeTBD'],
                         'pregame': (True if 'Pre-Game' in g['status']['detailedState'] else False),
                         'period': g['linescore']['currentPeriod'],
                         'clock': g['linescore'].get('currentPeriodTimeRemaining'),
                         'powerplay_h': g['linescore']['teams']['home']['powerPlay'],
                         'powerplay_a': g['linescore']['teams']['away']['powerPlay'],
                         'goaliePulled_h': g['linescore']['teams']['home']['goaliePulled'],
                         'goaliePulled_a': g['linescore']['teams']['away']['goaliePulled'],
                         'ended': (g['status']['statusCode'] == '7' or g['status']['statusCode'] == '9'),
                         'ppd': (g['status']['statusCode'] == '9'),
                         'type': g['gameType']
                        }
            #print(game_info)
            if team == "all":
                games.append(game_info)
            else:
                if team in game_info['home_team'] or team in game_info['away_team']:
                    games.append(game_info)
                else:
                    pass
        return games

############################
# Today's games cache
############################
    def _cachedData(self):
        return self._today_scores_last_modified_data

    def _haveCachedData(self, url):
        return (self._today_scores_cached_url == url) and \
                (self._today_scores_last_modified_time is not None)

    def _cachedDataLastModified(self):
        return self._today_scores_last_modified_time

    def _updateCache(self, url, response):
        self._today_scores_cached_url = url
        self._today_scores_last_modified_time = response.headers['last-modified']
        self._today_scores_last_modified_data = response.read()

############################
# Formatting helpers
############################
    def _resultAsString(self, games):
        if len(games) == 0:
            return "No games found"
        else:
            s = sorted(games[1:], key=lambda k: k['ended']) #, reverse=True)
            #s = [self._gameToString(g) for g in games]
            b = []
            for g in s:
                b.append(self._gameToString(g))
            #print(b)
            #print(' | '.join(b))
            #games_strings = [self._gameToString(g) for g in games]
            return ' | '.join(b)

    def _resultTVAsString(self, games):
        if len(games) == 0:
            return "No games found"
        else:
            s = sorted(games[1:], key=lambda k: k['ended']) #, reverse=True)
            #s = [self._gameToString(g) for g in games]
            b = []
            for g in s:
                b.append(self._TVToString(g))
            #print(b)
            #print(' | '.join(b))
            #games_strings = [self._gameToString(g) for g in games]
            return ' | '.join(b)

    def _TVToString(self, game):
        """ Given a game, format the information into a string according to the
        context. For example:
        "MEM @ CLE 07:00 PM ET" (a game that has not started yet),
        "HOU 132 GSW 127 F OT2" (a game that ended and went to 2 overtimes),
        "POR 36 LAC 42 8:01 Q2" (a game in progress)."""
        away_team = game['away_team']
        home_team = game['home_team']
        if game['period'] == 0: # The game hasn't started yet
            starting_time = game['starting_time'] \
                            if not game['starting_time_TBD'] \
                            else "TBD"
            starting_time = ircutils.mircColor('PPD', 'red') if game['ppd'] else starting_time
            return "{} @ {} {} [{}]".format(away_team, home_team, starting_time, ircutils.bold(game['broadcasts']))

        # The game started => It has points:
        away_score = game['away_score']
        home_score = game['home_score']

        away_string = "{} {}".format(away_team, away_score)
        home_string = "{} {}".format(home_team, home_score)

        # Highlighting 'powerPlay':
        if game['powerplay_h'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and not game['goaliePulled_h']:
            home_string = ircutils.mircColor(home_string, 'orange') # 'black', 'yellow')
        if game['powerplay_a'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and not game['goaliePulled_a']:
            away_string = ircutils.mircColor(away_string, 'orange') # 'black', 'yellow')

        # Highlighting an empty net (goalie pulled):
        if game['goaliePulled_h'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and game['clock'] != "00:00":
            home_string = ircutils.mircColor(home_string, 'red')
        if game['goaliePulled_a'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and game['clock'] != "00:00":
            away_string = ircutils.mircColor(away_string, 'red')

        # Bold for the winning team:
        if int(away_score) > int(home_score):
            away_string = ircutils.bold(away_string)
        elif int(home_score) > int(away_score):
            home_string = ircutils.bold(home_string)

        #print('got here ', game['broadcasts'])

        base_str = ''
        if not game['ended']:
            base_str = ' [{}]'.format(game['broadcasts'])

        game_string = "{} {} {}{}".format(away_string, home_string,
                                        self._clockBoardToString(game['clock'],
                                                                game['period'],
                                                                game['ended'],
                                                                game['pregame'],
                                                                game['type']),
                                                                base_str)

        return game_string

    def _gameToString(self, game):
        """ Given a game, format the information into a string according to the
        context. For example:
        "MEM @ CLE 07:00 PM ET" (a game that has not started yet),
        "HOU 132 GSW 127 F OT2" (a game that ended and went to 2 overtimes),
        "POR 36 LAC 42 8:01 Q2" (a game in progress)."""
        away_team = game['away_team']
        home_team = game['home_team']
        if game['period'] == 0: # The game hasn't started yet
            starting_time = game['starting_time'] \
                            if not game['starting_time_TBD'] \
                            else "TBD"
            starting_time = ircutils.mircColor('PPD', 'red') if game['ppd'] else starting_time
            return "{} @ {} {}".format(away_team, home_team, starting_time)

        # The game started => It has points:
        away_score = game['away_score']
        home_score = game['home_score']

        away_string = "{} {}".format(away_team, away_score)
        home_string = "{} {}".format(home_team, home_score)

        # Highlighting 'powerPlay':
        if game['powerplay_h'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and not game['goaliePulled_h']:
            home_string = ircutils.mircColor(home_string, 'orange') # 'black', 'yellow')
        if game['powerplay_a'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and not game['goaliePulled_a']:
            away_string = ircutils.mircColor(away_string, 'orange') # 'black', 'yellow')

        # Highlighting an empty net (goalie pulled):
        if game['goaliePulled_h'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and game['clock'] != "00:00":
            home_string = ircutils.mircColor(home_string, 'red')
        if game['goaliePulled_a'] and game['clock'].upper() != "END" and game['clock'].upper() != "FINAL" and game['clock'] != "00:00":
            away_string = ircutils.mircColor(away_string, 'red')

        # Bold for the winning team:
        if int(away_score) > int(home_score):
            away_string = ircutils.bold(away_string)
        elif int(home_score) > int(away_score):
            home_string = ircutils.bold(home_string)

        game_string = "{} {} {}".format(away_string, home_string,
                                        self._clockBoardToString(game['clock'],
                                                                game['period'],
                                                                game['ended'],
                                                                game['pregame'],
                                                                game['type']))

        return game_string

    def _clockBoardToString(self, clock, period, game_ended, pregame=None, gType=None):
        """Get a string with current period and, if the game is still
        in progress, the remaining time in it."""
        period_number = period
        # Game hasn't started => There is no clock yet.
        if period_number == 0:
            return ""

        # Halftime
        #if period:
        #    return ircutils.mircColor('Halftime', 'orange')

        period_string = self._periodToString(period_number, gType)

        # Game finished:
        if game_ended or clock.upper() == "FINAL":
            if period_number == 3:
                return ircutils.mircColor('F', 'red')
            else:
                return ircutils.mircColor("F/{}".format(period_string), 'red')

        # Game in progress:
        if clock.upper() == "END":
            return ircutils.mircColor("End {}".format(period_string), 'light blue')
        else:
            # Period in progress, show clock:
            if pregame:
                return "{}".format(ircutils.mircColor('Pre-Game', 'green'))
            return "{}{}".format(clock + ' ' if clock != '00:00' else "", ircutils.mircColor(period_string, 'green'))

    def _periodToString(self, period, gType):
        """Get a string describing the current period in the game.
        period is an integer counting periods from 1 (so 5 would be OT1).
        The output format is as follows: {Q1...Q4} (regulation);
        {OT, OT2, OT3...} (overtimes)."""
        if period <= 3:
            return "P{}".format(period)

        ot_number = period - 3
        if ot_number == 1:
            return "OT"
        # if regular/pre season game, we have shootouts
        if gType == 'R' or gType == 'PR':
            if ot_number > 1:
                return "SO"
        return "{}OT".format(ot_number)

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
        return pendulum.now('US/Eastern')

    def _pacificTimeNow(self):
        return pendulum.now('US/Pacific')

    def _convertISODateToTime(self, iso, target='US/Eastern'):
        """Convert the ISO date in UTC time that the API outputs into a
        time (target timezone) formatted with am/pm. Defaults to US/Eastern."""
        try:
            date = pendulum.parse(iso).in_tz('{}'.format(target))
        except:
            try:
                target = self._checkTarget(target)
                date = pendulum.parse(iso).in_tz('{}'.format(target))
            except:
                date = pendulum.parse(iso).in_tz('{}'.format('US/Eastern'))
        time = date.format('h:mm A zz')
        return "{}".format(time)

    def _checkTarget(self, target):
        """check input among common tz"""
        target = target.upper()
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
        if target in common:
            target = common[target]

        return target

    def _ISODateToEasternTime(self, iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern time formatted with am/pm. (The default human-readable format
        for the listing of games)."""
        date = pendulum.parse(iso).in_tz('{}'.format('US/Eastern'))
        time = date.format('h:mm A zz')
        return "{}".format(time) # Strip the seconds

    def _stripDateSeparators(self, date_string):
        return date_string.replace('-', '')

    def _EnglishDateToDate(self, date):
        """Convert a human-readable like 'yesterday' to a datetime object
        and return a 'YYYYMMDD' string."""
        if date == "lastweek":
            day_delta = -7
        elif date == "yesterday":
            day_delta = -1
        elif date == "today" or date =="tonight":
            day_delta = 0
        elif date == "tomorrow":
            day_delta = 1
        elif date == "nextweek":
            day_delta = 7
        elif date[:3] == 'sun':
            date_string = pendulum.now('US/Pacific').next(pendulum.SUNDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'mon':
            date_string = pendulum.now('US/Pacific').next(pendulum.MONDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'tue':
            date_string = pendulum.now('US/Pacific').next(pendulum.TUESDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'wed':
            date_string = pendulum.now('US/Pacific').next(pendulum.WEDNESDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'thu':
            date_string = pendulum.now('US/Pacific').next(pendulum.THURSDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'fri':
            date_string = pendulum.now('US/Pacific').next(pendulum.FRIDAY).format('YYYY-MM-DD')
            return date_string
        elif date[:3] == 'sat':
            date_string = pendulum.now('US/Pacific').next(pendulum.SATURDAY).format('YYYY-MM-DD')
            return date_string
        # Calculate the day difference and return a string
        date_string = self._pacificTimeNow().add(days=day_delta).strftime('%Y-%m-%d')
        return date_string

    def _checkDateInput(self, date):
        """Verify that the given string is a valid date formatted as
        YYYY-MM-DD. Also, the API seems to go back until 2014-10-04, so we
        will check that the input is not a date earlier than that."""

        error_string = 'Incorrect date format, should be YYYY-MM-DD'

        if date is None:
            return None

        if date in self._FUZZY_DAYS:
            date = self._EnglishDateToDate(date)
        elif date[:3].lower() in self._FUZZY_DAYS:
            date = self._EnglishDateToDate(date.lower())

        if date.isdigit():
            try:
                date = pendulum.from_format(date, 'YYYYMMDD').strftime('%Y-%m-%d')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')
        elif date.replace('-','').isdigit():
            try:
                parsed_date = pendulum.from_format(date, 'YYYY-MM-DD')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')
        elif date.replace('/','').isdigit():
            if len(date.split('/')) == 2:
                year = '/' + str(pendulum.datetime.now().year)
                date += year
            elif len(date.split('/')) == 3:
                if len(date.split('/')[2]) == 2:
                    date = '{}/{}/{}'.format(date.split('/')[0], date.split('/')[1], '20{}'.format(date.split('/')[2]))
            else:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')
            try:
                date = pendulum.from_format(date, 'MM/DD/YYYY').strftime('%Y-%m-%d')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')
        elif '-' not in date and date.isdigit() == False and len(date) > 3:
            if date.title() in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                return "Incorrect date format, should be YYYY-MM-DD"
            try:
                date = date.title()
                year = str(pendulum.datetime.now().year)
                date += year
                try:
                    date = pendulum.from_format(date, 'DDMMMYYYY').strftime('%Y-%m-%d')
                except:
                    date = pendulum.from_format(date, 'MMMDDYYYY').strftime('%Y-%m-%d')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')
                #return "Incorrect date format, should be YYYY-MM-DD"
        else:
            return None

        return date

Class = NHL

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
