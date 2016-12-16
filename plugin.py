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

        self._SCOREBOARD_ENDPOINT = ("http://data.nba.net/" +
                                    "data/10s/prod/v1/{}/" +
                                    "scoreboard.json")

        self._FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow']

        # These two variables store the latest data acquired from the server
        # and its modification time. It's a one-element cache.
        # They are used to employ HTTP's 'If-Modified-Since' header and
        # avoid unnecessary downloads for today's information (which will be
        # requested all the time to update the scores).
        self._today_scores_cached_url = None
        self._today_scores_last_modified_time = None
        self._today_scores_last_modified_data = None

    def nba(self, irc, msg, args, optional_team, optional_date):
        """[<team>] [<date>]
        Get games for a given date (YYYY-MM-DD). If none is specified, return games
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
            irc.reply(self._getTodayGames(team))
        else:
            irc.reply(self._getGamesForDate(team, date))                                                                                                        
    nba = wrap(nba, [optional('somethingWithoutSpaces'), optional('somethingWithoutSpaces')])

    def _getTodayGames(self, team):
        games = self._getGames(team, self._getTodayDate())
        return self._resultAsString(games)

    def _getGamesForDate(self, team, date):
        games = self._getGames(team, date)
        return self._resultAsString(games)

############################
# Content-getting helpers
############################
    def _getGames(self, team, date):
        """Given a date, populate the url with it and try to download its
        content. If successful, parse the JSON data and extract the relevant
        fields for each game. Returns a list of games."""
        url = self._getEndpointURL(date)

        # (If asking for today's results, enable the 'If-Mod.-Since' flag)
        use_cache = (date == self._getTodayDate())
        response = self._getURL(url, use_cache)

        json = self._extractJSON(response)
        games = self._parseGames(json, team)
        return games

    def _getEndpointURL(self, date):
        return self._SCOREBOARD_ENDPOINT.format(date)

    def _getURL(self, url, use_cache=False):
        """Use urllib to download the URL's content. The use_cache flag enables
        the use of the one-element cache, which will be reserved for today's
        games URL. (In the future we could implement a real cache with TTLs)."""
        user_agent = 'Mozilla/5.0 \
                      (X11; Ubuntu; Linux x86_64; rv:45.0) \
                      Gecko/20100101 Firefox/45.0'
        header = {'User-Agent': user_agent}

        # ('If-Modified-Since' to avoid unnecessary downloads.)
        if use_cache and self._haveCachedData(url):
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

def _parseGames(self, json, team):
        """Extract all relevant fields from NBA.com's scoreboard.json
        and return a list of games."""
        games = []
        for g in json['games']:
            # Starting times are in UTC. By default, we will show Eastern times.
            # (In the future we could add a user option to select timezones.)
            starting_time = self._ISODateToEasternTime(g['startTimeUTC'])
            game_info = {'home_team': g['hTeam']['triCode'],
                         'away_team': g['vTeam']['triCode'],
                         'home_score': g['hTeam']['score'],
                         'away_score': g['vTeam']['score'],  
                          'starting_time': starting_time,
                          'starting_time_TBD': g['isStartTimeTBD'],
                          'clock': g['clock'],
                          'period': g['period'],
                          'buzzer_beater': g['isBuzzerBeater'],
                          'ended': (g['statusNum'] == 3)
                        }
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
            sorted_games = sorted(games, key=lambda k: k['ended']) # sort games list and put F(inal) games at end
            b = []
            for g in sorted_games:
                b.append(self._gameToString(g))
            return ' | '.join(b)

    def _gameToString(self, game):
        """ Given a game, format the information into a string according to the
        context. For example:
        "MEM @ CLE 07:00 PM ET" (a game that has not started yet),
        "HOU 132 GSW 127 F OT2" (a game that ended and went to 2 overtimes),
        "POR 36 LAC 42 8:01 Q2" (a game in progress)."""
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
            game_string = ircutils.mircColor(game_string, 'yellow')

        return game_string

    def _clockBoardToString(self, clock, period, game_ended):
        """Get a string with current period and, if the game is still
        in progress, the remaining time in it."""
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
            return ircutils.mircColor("E{}".format(period_string), 'yellow')
        else:
            # Period in progress, show clock:
            return "{} {}".format(clock, ircutils.mircColor(period_string, 'green'))

    def _periodToString(self, period):
        """Get a string describing the current period in the game.
        period is an integer counting periods from 1 (so 5 would be OT1).
        The output format is as follows: {Q1...Q4} (regulation);
        {OT, OT2, OT3...} (overtimes)."""
        if period <= 4:
            return "Q{}".format(period)

        ot_number = period - 4
        if ot_number == 1:
            return "OT"
        return "OT{}".format(ot_number)

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
        return today_iso.replace('-', '')

    def _easternTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Eastern'))

    def _pacificTimeNow(self):
        return datetime.datetime.now(pytz.timezone('US/Pacific'))

    def _ISODateToEasternTime(self, iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern time formatted with am/pm. (The default human-readable format
        for the listing of games)."""
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_time = date_eastern.strftime('%-I:%M %p')
        return "{} ET".format(eastern_time) # Strip the seconds

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
        # Calculate the day difference and return a string
        date_string = (self._pacificTimeNow() +
                      datetime.timedelta(days=day_delta)).strftime('%Y%m%d')
        return date_string

    def _checkDateInput(self, date):
        """Verify that the given string is a valid date formatted as
        YYYY-MM-DD. Also, the API seems to go back until 2014-10-04, so we
        will check that the input is not a date earlier than that."""
        if date is None:
            return None

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
            return None

        return self._stripDateSeparators(date)

Class = NBA

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
