###
# Limnoria plugin to retrieve results from NBA.com using their (undocumented)
# JSON API.
# Copyright (c) 2016, Santiago Gil
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
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NBA')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

import datetime
import dateutil.parser
import json
import pytz
import urllib.request

class NBA(callbacks.Plugin):
    """Get scores from NBA.com."""
    def __init__(self, irc):
        self.__parent = super(NBA, self)
        self.__parent.__init__(irc)

        self._SCOREBOARD_ENDPOINT = ('https://data.nba.net/'
                                     + 'data/10s/prod/v1/{}/'
                                     + 'scoreboard.json')

        self._FUZZY_DAYS = frozenset(('yesterday', 'tonight',
                                      'today', 'tomorrow'))

        # These two variables store the latest data acquired from the
        # server and its modification time. It's a one-element cache.
        # They are used to employ HTTP's 'If-Modified-Since' header and
        # avoid unnecessary downloads for today's information (which
        # will be requested all the time to update the scores).
        self._today_scores_cached_url = None
        self._today_scores_last_modified_time = None
        self._today_scores_last_modified_data = None

        self._TEAM_TRICODES = frozenset(('CHA', 'ATL', 'IND', 'MEM', 'DET',
                                         'UTA', 'CHI', 'TOR', 'CLE', 'OKC',
                                         'DAL', 'MIN', 'BOS', 'SAS', 'MIA',
                                         'DEN', 'LAL', 'PHX', 'NOP', 'MIL',
                                         'HOU', 'NYK', 'ORL', 'SAC', 'PHI',
                                         'BKN', 'POR', 'GSW', 'LAC', 'WAS'))

    def nba(self, irc, msg, args, optional_team, optional_date):
        """[<TTT>] [<YYYY-MM-DD>]

        Get games for a given date. If none is specified, return
        games scheduled for today. Optionally add team abbreviation
        to filter for a specific team.
        """

        # Check to see if there's optional input and if there is check
        # if it's a date or a team, or both.
        try:
            team, date = self._parseOptionalArguments(optional_team,
                                                      optional_date)
        except ValueError as e:
            irc.error(str(e))
            return

        games = self._getTodayGames() if date is None \
                                      else self._getGamesForDate(date)

        games = self._filterGamesWithTeam(team, games)


        games_string = self._resultAsString(games)

        # When querying a specific game, if it has a text nugget and
        # it's not 'Watch live', print it:
        if len(games) == 1:
            broadcasters = games[0]['tv_broadcasters']
            broadcasters_string = self._broadcastersToString(broadcasters)
            games_string += ' [{}]'.format(broadcasters_string)

            nugget = games[0]['text_nugget']
            nugget_is_interesting = nugget and 'watch live' not in nugget.lower()
            if nugget_is_interesting:
                games_string += ' | {}'.format(nugget)

        irc.reply(games_string)

    nba = wrap(nba, [optional('somethingWithoutSpaces'),
                     optional('somethingWithoutSpaces')])

    def tv(self, irc, msg, args, team):
        """[<TTT>]

        Given a team, if there is a game scheduled for today,
        return where it is being broadcasted.
        """
        try:
            team = self._parseTeamInput(team)
        except ValueError as e:
            irc.error(str(e))
            return

        games = self._filterGamesWithTeam(team, self._getTodayGames())

        if len(games) == 0:
            irc.reply('{} is not playing today.'.format(team))
            return

        game = games[0]
        game_string = self._gameToString(game)
        broadcasters_string = self._broadcastersToString(game['tv_broadcasters'])
        irc.reply('{} on: {}'.format(game_string, broadcasters_string))

    tv = wrap(tv, ['somethingWithoutSpaces'])


    def _parseOptionalArguments(self, optional_team, optional_date):
        """Parse the optional arguments, which could be None, and return
        a (team, date) tuple. In case of finding an invalid argument, it
        throws a ValueError exception.
        """
        # No arguments:
        if optional_team is None:
            return (None, None)

        # Both arguments:
        if (optional_date is not None) and (optional_team is not None):
            team = self._parseTeamInput(optional_team)
            date = self._parseDateInput(optional_date)
            return (team, date)

        # Only one argument:
        if self._isPotentialDate(optional_team):
            # Should be a date.
            team = None
            date = self._parseDateInput(optional_team)
        else:
            # Should be a team.
            team = self._parseTeamInput(optional_team)
            date = None

        return (team, date)

    def _getTodayGames(self):
        return self._getGames(self._getTodayDate())

    def _getGamesForDate(self, date):
        return self._getGames(date)

    def _filterGamesWithTeam(self, team, games):
        """Given a list of games, return those that involve a given
        team. If team is None, return the list with no modifications.
        """
        if team is None:
            return games

        return [g for g in games if team == g['home_team']
                                    or team == g['away_team']]

############################
# Content-getting helpers
############################
    def _getGames(self, date):
        """Given a date, populate the url with it and try to download
        its content. If successful, parse the JSON data and extract the
        relevant fields for each game. Returns a list of games.
        """
        url = self._getEndpointURL(date)

        # (If asking for today's results, enable the 'If-Mod.-Since' flag)
        use_cache = (date == self._getTodayDate())
        response = self._getURL(url, use_cache)

        json = self._extractJSON(response)

        return self._parseGames(json)

    def _getEndpointURL(self, date):
        return self._SCOREBOARD_ENDPOINT.format(date)

    def _getURL(self, url, use_cache=False):
        """Use urllib to download the URL's content.
        The use_cache flag enables the use of the one-element cache,
        which will be reserved for today's games URL.
        (In the future we could implement a real cache with TTLs).
        """
        user_agent = 'Mozilla/5.0 \
                      (X11; Ubuntu; Linux x86_64; rv:45.0) \
                      Gecko/20100101 Firefox/45.0'
        header = {'User-Agent': user_agent}

        # ('If-Modified-Since' to avoid unnecessary downloads.)
        if use_cache and self._hasCachedData(url):
            header['If-Modified-Since'] = self._today_scores_last_modified_time

        request = urllib.request.Request(url, headers=header)

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

        if not use_cache:
            return response.read()

        # Updating the cached data:
        self._updateCache(url, response)
        return self._cachedData()

    def _extractJSON(self, body):
        return json.loads(body.decode('utf-8'))

    def _parseGames(self, json):
        """Extract all relevant fields from NBA.com's scoreboard.json
        and return a list of games.
        """
        games = []
        for g in json['games']:
            # Starting times are in UTC. By default, we will show
            # Eastern times.
            # (In the future we could add a user option to select
            # timezones.)
            try:
                starting_time = self._ISODateToEasternTime(g['startTimeUTC'])
            except:
                starting_time = 'TBD' if g['isStartTimeTBD'] else ''
            game_info = {'home_team': g['hTeam']['triCode'],
                         'away_team': g['vTeam']['triCode'],
                         'home_score': g['hTeam']['score'],
                         'away_score': g['vTeam']['score'],
                         'starting_time': starting_time,
                         'starting_time_TBD': g['isStartTimeTBD'],
                         'clock': g['clock'],
                         'period': g['period'],
                         'buzzer_beater': g['isBuzzerBeater'],
                         'ended': (g['statusNum'] == 3),
                         'text_nugget': g['nugget']['text'].strip(),
                         'tv_broadcasters': self._extractGameBroadcasters(g)
                        }

            games.append(game_info)

        return games

    def _extractGameBroadcasters(self, game_json):
        """Extract the list of broadcasters from the API.
        Return a dictionary of broadcasts:
        (['vTeam', 'hTeam', 'national', 'canadian']) to
        the short name of the broadcaster.
        """
        json = game_json['watch']['broadcast']['broadcasters']
        game_broadcasters = dict()

        for category in json:
            broadcasters_list = json[category]
            if broadcasters_list and 'shortName' in broadcasters_list[0]:
               game_broadcasters[category] = broadcasters_list[0]['shortName']
        return game_broadcasters

############################
# Today's games cache
############################
    def _cachedData(self):
        return self._today_scores_last_modified_data

    def _hasCachedData(self, url):
        return (self._today_scores_cached_url == url
                and self._today_scores_last_modified_time is not None)

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

        # sort games list and put F(inal) games at end
        sorted_games = sorted(games, key=lambda k: k['ended'])
        return ' | '.join([self._gameToString(g) for g in sorted_games])

    def _gameToString(self, game):
        """ Given a game, format the information into a string
        according to the context.

        For example:
        * "MEM @ CLE 07:00 PM ET" (a game that has not started yet),
        * "HOU 132 GSW 127 F OT2" (a game that ended and went to 2
        overtimes),
        * "POR 36 LAC 42 8:01 Q2" (a game in progress).
        """
        away_team = game['away_team']
        home_team = game['home_team']

        if game['period']['current'] == 0: # The game hasn't started yet
            starting_time = game['starting_time'] \
                            if not game['starting_time_TBD'] \
                            else "TBD"
            return "{} @ {} {}".format(away_team, home_team, starting_time)

        # The game started => It has points:
        away_score = game['away_score']
        home_score = game['home_score']

        away_string = "{} {}".format(away_team, away_score)
        home_string = "{} {}".format(home_team, home_score)

        # Bold for the winning team:
        if int(away_score) > int(home_score):
            away_string = ircutils.bold(away_string)
        elif int(home_score) > int(away_score):
            home_string = ircutils.bold(home_string)

        game_string = "{} {} {}".format(away_string, home_string,
                                        self._clockBoardToString(game['clock'],
                                                                 game['period'],
                                                                 game['ended']))
        # Highlighting 'buzzer-beaters':
        if game['buzzer_beater'] and not game['ended']:
            game_string = ircutils.mircColor(game_string, fg='yellow',
                                                          bg='black')

        return game_string

    def _clockBoardToString(self, clock, period, game_ended):
        """Get a string with current period and, if the game is still
        in progress, the remaining time in it.
        """
        period_number = period['current']
        # Game hasn't started => There is no clock yet.
        if period_number == 0:
            return ""

        # Halftime
        if period['isHalftime']:
            return ircutils.mircColor('Halftime', 'orange')

        period_string = self._periodToString(period_number)

        # Game finished:
        if game_ended:
            if period_number == 4:
                return ircutils.mircColor('F', 'red')
            else:
                return ircutils.mircColor("F {}".format(period_string), 'red')

        # Game in progress:
        if period['isEndOfPeriod']:
            return ircutils.mircColor("E{}".format(period_string), 'blue')
        else:
            # Period in progress, show clock:
            return "{} {}".format(clock, ircutils.mircColor(period_string,
                                                            'green'))

    def _periodToString(self, period):
        """Get a string describing the current period in the game.

        Period is an integer counting periods from 1 (so 5 would be
        OT1).
        The output format is as follows: {Q1...Q4} (regulation);
        {OT, OT2, OT3...} (overtimes).
        """
        if period <= 4:
            return "Q{}".format(period)

        ot_number = period - 4
        if ot_number == 1:
            return "OT"
        return "OT{}".format(ot_number)

    def _broadcastersToString(self, broadcasters):
        """Given a broadcasters dictionary (category->name), where
        category is in ['vTeam', 'hTeam', 'national', 'canadian'],
        return a printable string representation of that list.
        """
        items = []
        for category in ['vTeam', 'hTeam', 'national', 'canadian']:
            if category in broadcasters:
                items.append(broadcasters[category])
        return ', '.join(items)

############################
# Date-manipulation helpers
############################
    def _getTodayDate(self):
        """Get the current date formatted as "YYYYMMDD".
        Because the API separates games by day of start, we will
        consider and return the date in the Pacific timezone.
        The objective is to avoid reading future games anticipatedly
        when the day rolls over at midnight, which would cause us to
        ignore games in progress that may have started on the previous
        day.
        Taking the west coast time guarantees that the day will advance
        only when the whole continental US is already on that day.
        """
        today = self._pacificTimeNow().date()
        today_iso = today.isoformat()
        return today_iso.replace('-', '')

    def _easternTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Eastern'))

    def _pacificTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Pacific'))

    def _ISODateToEasternTime(self, iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern time formatted with am/pm.
        (The default human-readable format for the listing of games).
        """
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_time = date_eastern.strftime('%-I:%M %p')
        return "{} ET".format(eastern_time) # Strip the seconds

    def _stripDateSeparators(self, date_string):
        return date_string.replace('-', '')

    def _EnglishDateToDate(self, date):
        """Convert a human-readable like 'yesterday' to a datetime
        object and return a 'YYYYMMDD' string.
        """
        if date == "yesterday":
            day_delta = -1
        elif date == "today" or date =="tonight":
            day_delta = 0
        elif date == "tomorrow":
            day_delta = 1
        # Calculate the day difference and return a string
        date_string = (self._pacificTimeNow() +
                      datetime.timedelta(days=day_delta)).strftime('%Y%m%d')
        return date_string

    def _isValidTricode(self, team):
        return (team in self._TEAM_TRICODES)

############################
# Input-parsing helpers
############################
    def _isPotentialDate(self, string):
        """Given a user-provided string, check whether it could be a
        date.
        """
        return (string in self._FUZZY_DAYS or
                string.replace('-', '').isdigit())

    def _parseTeamInput(self, team):
        """Given a user-provided string, try to extract an upper-case
        team tricode from it. If not valid, throws a ValueError
        exception.
        """
        t = team.upper()
        if not self._isValidTricode(t):
            raise ValueError('{} is not a valid team'.format(team))
        return t

    def _parseDateInput(self, date):
        """Verify that the given string is a valid date formatted as
        YYYY-MM-DD. Also, the API seems to go back until 2014-10-04,
        so we will check that the input is not a date earlier than that.
        In case of failure, throws a ValueError exception.
        """
        if date in self._FUZZY_DAYS:
            date = self._EnglishDateToDate(date)
        elif date.replace('-','').isdigit():
            try:
                parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')

            # The current API goes back until 2014-10-04. Is it in range?
            if parsed_date.date() <  datetime.date(2014, 10, 4):
                raise ValueError('I can only go back until 2014-10-04')
        else:
            raise ValueError('Date is not valid')

        return self._stripDateSeparators(date)

Class = NBA

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
