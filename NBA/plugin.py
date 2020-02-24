###
# Copyright (c) 2018, Santiago Gil
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

#import supybot.utils as utils
#from supybot.commands import *
from supybot.commands import optional, wrap

#import supybot.plugins as plugins
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
import httplib2
import json
import pytz
from xml.etree import ElementTree

class NBA(callbacks.Plugin):
    """Get scores from NBA.com."""

    _ENDPOINT_BASE_URL = 'https://data.nba.net'

    _SCOREBOARD_ENDPOINT = (_ENDPOINT_BASE_URL
                            + '/10s/prod/v2/{}/'
                            + 'scoreboard.json')

    _TODAY_ENDPOINT = (_ENDPOINT_BASE_URL
                       + '/prod/v3/today.json')

    _FUZZY_DAYS = frozenset(('yesterday', 'tonight',
                             'today', 'tomorrow'))

    _TEAM_TRICODES = frozenset(('CHA', 'ATL', 'IND', 'MEM', 'DET',
                                'UTA', 'CHI', 'TOR', 'CLE', 'OKC',
                                'DAL', 'MIN', 'BOS', 'SAS', 'MIA',
                                'DEN', 'LAL', 'PHX', 'NOP', 'MIL',
                                'HOU', 'NYK', 'ORL', 'SAC', 'PHI',
                                'BKN', 'POR', 'GSW', 'LAC', 'WAS'))

    def __init__(self, irc):
        self.__parent = super(NBA, self)
        self.__parent.__init__(irc)

        self._http = httplib2.Http('.cache')

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
        except ValueError as error:
            irc.error(str(error))
            return

        try:
            games = self._getTodayGames() if date is None \
                    else self._getGamesForDate(date)
        except ConnectionError as error:
            irc.error('Could not connect to nba.com')
            return
        except:
            irc.error('Something went wrong')
            return

        games = self._filterGamesWithTeam(team, games)

        games_string = self._resultAsString(games)

        # Single game query? We can show some extra info.
        if len(games) == 1:
            game = games[0]

            # If the game has ended, we fetch the recap info from NBA.com:
            if game['ended']:
                try:
                    recap = self._getRecapInfo(game)
                    games_string += ' | {} {}'.format(ircutils.bold('Recap:'),
                                                      recap)
                except:
                    pass

            else:
                # Otherwise, when querying a specific game in progress,
                # we show the broadcaster list.
                # Also, if it has a text nugget, and it's not
                # 'Watch live', we show it:
                broadcasters = game['tv_broadcasters']
                broadcasters_string = self._broadcastersToString(broadcasters)
                games_string += ' [{}]'.format(broadcasters_string)

                nugget = game['text_nugget']
                nugget_is_interesting = nugget and 'Watch live' not in nugget
                if nugget_is_interesting:
                    games_string += ' | {}'.format(nugget)

        irc.reply(games_string)

    nba = wrap(nba, [optional('somethingWithoutSpaces'),
                     optional('somethingWithoutSpaces')])

    def nbatv(self, irc, msg, args, team):
        """[<TTT>]

        Given a team, if there is a game scheduled for today,
        return where it is being broadcasted.
        """
        try:
            team = self._parseTeamInput(team)
        except ValueError as error:
            irc.error(str(error))
            return

        games = self._filterGamesWithTeam(team, self._getTodayGames())

        if not games:
            irc.reply('{} is not playing today.'.format(team))
            return

        game = games[0]
        game_string = self._gameToString(game)
        broadcasters_string = self._broadcastersToString(game['tv_broadcasters'])
        irc.reply('{} on: {}'.format(game_string, broadcasters_string))

    nbatv = wrap(nbatv, ['somethingWithoutSpaces'])

    def nbanext(self, irc, msg, args, n, team, team2):
        """[<n>] <TTT> [<TTT>]

        Get the next <n> games (1 by default; max. 10) for a given team
        or, if two teams are provided, matchups between them.

        """
        MAX_GAMES_IN_RESULT = 10

        try:
            if team == team2:
                irc.error('Both teams should be different.')
                return

            team = self._parseTeamInput(team)
            if team2 is not None:
                team2 = self._parseTeamInput(team2)

            team_schedule = self._getTeamSchedule(team)
        except ValueError as error:
            irc.error(str(error))
            return

        last_played = team_schedule['lastStandardGamePlayedIndex']

        # Keeping only the games that haven't been played:
        future_games = team_schedule['standard'][last_played+1:]

        if n is None:
            n = 1
        end = min(MAX_GAMES_IN_RESULT, n, len(future_games)-1)

        if team2 is None:
            games = future_games
        else:
            # Filtering matchups between team and team2:
            team2_id = self._tricodeToTeamId(team2)
            games = [g for g in future_games \
                     if team2_id in [g['vTeam']['teamId'],
                                     g['hTeam']['teamId']]]

        if not games:
            irc.error('I could not find future games.')
            return

        for game in games[:end]:
            irc.reply(self._upcomingGameToString(game))


    nbanext = wrap(nbanext, [optional('positiveInt'),
                       'somethingWithoutSpaces',
                       optional('somethingWithoutSpaces')])

    def nbalast(self, irc, msg, args, n, team, team2):
        """[<n>] <TTT> [<TTT>]

        Get the last <n> games (1 by default; max. 10) for a given team
        or, if two teams are provided, matchups between them.

        """
        MAX_GAMES_IN_RESULT = 10

        try:
            if team == team2:
                irc.error('Both teams should be different.')
                return

            team = self._parseTeamInput(team)
            if team2 is not None:
                team2 = self._parseTeamInput(team2)

            team_schedule = self._getTeamSchedule(team)
        except ValueError as error:
            irc.error(str(error))
            return

        last_played = team_schedule['lastStandardGamePlayedIndex']

        # Keeping only the games that have been played:
        team_past_games = team_schedule['standard'][:last_played+1]

        # Making sure the number of games we will show is a valid one:
        if n is None:
            n = 1
        n = min(MAX_GAMES_IN_RESULT, n)

        if team2 is None:
            games = team_past_games
        else:
            # Filtering matchups between team and team2:
            team2_id = self._tricodeToTeamId(team2)
            games = [g for g in team_past_games \
                     if team2_id in [g['vTeam']['teamId'],
                                     g['hTeam']['teamId']]]

        if not games:
            irc.error('I could not find past games.')
            return

        for game in reversed(games[-n:]): # Most-recent game first.
            irc.reply(self._pastGameToString(game))


    nbalast = wrap(nbalast, [optional('positiveInt'),
                       'somethingWithoutSpaces',
                       optional('somethingWithoutSpaces')])

    @classmethod
    def _parseOptionalArguments(cls, optional_team, optional_date):
        """Parse the optional arguments, which could be None, and return
        a (team, date) tuple. In case of finding an invalid argument, it
        throws a ValueError exception.
        """
        # No arguments:
        if optional_team is None:
            return (None, None)

        # Both arguments:
        if (optional_date is not None) and (optional_team is not None):
            team = cls._parseTeamInput(optional_team)
            date = cls._parseDateInput(optional_date)
            return (team, date)

        # Only one argument:
        if cls._isPotentialDate(optional_team):
            # Should be a date.
            team = None
            date = cls._parseDateInput(optional_team)
        else:
            # Should be a team.
            team = cls._parseTeamInput(optional_team)
            date = None

        return (team, date)

    def _getTodayGames(self):
        return self._getGames(self._getTodayDate())

    def _getGamesForDate(self, date):
        return self._getGames(date)

    @staticmethod
    def _filterGamesWithTeam(team, games):
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
    def _getTodayJSON(self):
        today_url = self._ENDPOINT_BASE_URL + '/10s/prod/v3/today.json'
        return self._getJSON(today_url)

    def _getGames(self, date):
        """Given a date, populate the url with it and try to download
        its content. If successful, parse the JSON data and extract the
        relevant fields for each game. Returns a list of games.
        """
        url = self._getEndpointURL(date)

        # If asking for today's results, revalidate the cached data.
        # ('If-Mod.-Since' flag.). This allows to get real-time scores.
        revalidate_cache = (date == self._getTodayDate())
        response = self._getURL(url, revalidate_cache)

        json_data = self._extractJSON(response)

        return self._parseGames(json_data)

    @classmethod
    def _getEndpointURL(cls, date):
        return cls._SCOREBOARD_ENDPOINT.format(date)

    def _getTeamSchedule(self, tricode):
        """Fetch the json with the given team's schedule"""

        # First we fetch `today.json` to extract the path to teams'
        # schedules and `seasonScheduleYear`:
        today_json = self._getTodayJSON()
        schedule_path = today_json['links']['teamScheduleYear2']
        season_year = today_json['seasonScheduleYear']

        # We also need to convert the `tricode` to a `team_id`:
        team_id = self._tricodeToTeamId(tricode)

        # (The path looks like this:
        # '/prod/v1/{{seasonScheduleYear}}/teams/{{teamId}}/schedule.json')

        # Now we can fill-in the url:
        schedule_path = schedule_path.replace('{{teamId}}', team_id)
        schedule_path = schedule_path.replace('{{seasonScheduleYear}}',
                                              str(season_year))

        return self._getJSON(self._ENDPOINT_BASE_URL + schedule_path)['league']

    def _tricodeToTeamId(self, tricode):
        """Given a valid team tricode, get the `teamId` used in NBA.com"""

        teams_path = self._getJSON(self._TODAY_ENDPOINT)['links']['teams']
        teams_json = self._getJSON(self._ENDPOINT_BASE_URL + teams_path)

        for team in teams_json['league']['standard']:
            if team['tricode'] == tricode:
                return team['teamId']

        raise ValueError('{} is not a valid tricode'.format(tricode))

    def _teamIdToTricode(self, team_id):
        """Given a valid teamId, get the team's tricode"""

        teams_path = self._getJSON(self._TODAY_ENDPOINT)['links']['teams']
        teams_json = self._getJSON(self._ENDPOINT_BASE_URL + teams_path)

        for team in teams_json['league']['standard']:
            if team['teamId'] == team_id:
                return team['tricode']

        raise ValueError('{} is not a valid teamId'.format(team_id))

    def _getURL(self, url, force_revalidation=False):
        """Use httplib2 to download the URL's content.

        The `force_revalidation` parameter forces the data to be
        validated before being returned from the cache.
        In the worst case the data has not changed in the server,
        and we get a '304 - Not Modified' response.
        """
        user_agent = 'Mozilla/5.0 \
                      (X11; Ubuntu; Linux x86_64; rv:45.0) \
                      Gecko/20100101 Firefox/45.0'
        header = {'User-Agent': user_agent}

        if force_revalidation:
            header['Cache-Control'] = 'max-age=0'

        response, content = self._http.request(url, 'GET', headers=header)

        if response.fromcache:
            self.log.debug('%s - 304/Cache Hit', url)

        if response.status == 200:
            return content

        self.log.error('HTTP Error (%s): %s', url, error.code)
        raise ConnectionError('Could not access URL')

    @staticmethod
    def _extractJSON(body):
        return json.loads(body)

    def _getJSON(self, url):
        """Fetch `url` and return its contents decoded as json."""
        return self._extractJSON(self._getURL(url))

    @classmethod
    def _parseGames(cls, json_data):
        """Extract all relevant fields from NBA.com's scoreboard.json
        and return a list of games.
        """
        games = []
        for g in json_data['games']:
            # Starting times are in UTC. By default, we will show
            # Eastern times.
            # (In the future we could add a user option to select
            # timezones.)
            try:
                starting_time = cls._ISODateToEasternTime(g['startTimeUTC'])
            except:
                starting_time = 'TBD' if g['isStartTimeTBD'] else ''

            game_info = {'game_id': g['gameId'],
                         'home_team': g['hTeam']['triCode'],
                         'away_team': g['vTeam']['triCode'],
                         'home_score': g['hTeam']['score'],
                         'away_score': g['vTeam']['score'],
                         'starting_year': g['startDateEastern'][0:4],
                         'starting_month': g['startDateEastern'][4:6],
                         'starting_day': g['startDateEastern'][6:8],
                         'starting_time': starting_time,
                         'starting_time_TBD': g['isStartTimeTBD'],
                         'clock': g['clock'],
                         'period': g['period'],
                         'buzzer_beater': g['isBuzzerBeater'],
                         'ended': (g['statusNum'] == 3),
                         'text_nugget': g['nugget']['text'].strip(),
                         'tv_broadcasters': cls._extractGameBroadcasters(g)
                        }

            games.append(game_info)

        return games

    @staticmethod
    def _extractGameBroadcasters(game_json):
        """Extract the list of broadcasters from the API.
        Return a dictionary of broadcasts:
        (['vTeam', 'hTeam', 'national', 'canadian']) to
        the short name of the broadcaster.
        """
        json_data = game_json['watch']['broadcast']['broadcasters']
        game_broadcasters = dict()

        for category in json_data:
            broadcasters_list = json_data[category]
            if broadcasters_list and 'shortName' in broadcasters_list[0]:
                game_broadcasters[category] = broadcasters_list[0]['shortName']
        return game_broadcasters

############################
# Formatting helpers
############################
    @classmethod
    def _resultAsString(cls, games):
        if not games:
            return "No games found"

        # sort games list and put F(inal) games at end
        sorted_games = sorted(games, key=lambda k: k['ended'])
        return ' | '.join([cls._gameToString(g) for g in sorted_games])

    @classmethod
    def _gameToString(cls, game):
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
                                        cls._clockBoardToString(game['clock'],
                                                                game['period'],
                                                                game['ended']))
        # Highlighting 'buzzer-beaters':
        if game['buzzer_beater'] and not game['ended']:
            game_string = ircutils.mircColor(game_string, fg='yellow',
                                             bg='black')

        return game_string

    @classmethod
    def _clockBoardToString(cls, clock, period, game_ended):
        """Get a string with current period and, if the game is still
        in progress, the remaining time in it.
        """
        period_number = period['current']
        # Game hasn't started => There is no clock yet.
        if period_number == 0:
            return ''

        # Halftime
        if period['isHalftime']:
            return ircutils.mircColor('Halftime', 'orange')

        period_string = cls._periodToString(period_number)

        # Game finished:
        if game_ended:
            if period_number == 4:
                return ircutils.mircColor('F', 'red')

            return ircutils.mircColor("F {}".format(period_string), 'red')

        # Game in progress:
        if period['isEndOfPeriod']:
            return ircutils.mircColor("E{}".format(period_string), 'blue')

        # Period in progress, show clock:
        return "{} {}".format(clock, ircutils.mircColor(period_string,
                                                        'green'))

    @staticmethod
    def _periodToString(period):
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

    @staticmethod
    def _broadcastersToString(broadcasters):
        """Given a broadcasters dictionary (category->name), where
        category is in ['vTeam', 'hTeam', 'national', 'canadian'],
        return a printable string representation of that list.
        """
        items = []
        for category in ['vTeam', 'hTeam', 'national', 'canadian']:
            if category in broadcasters:
                items.append(broadcasters[category])
        return ', '.join(items)

    def _upcomingGameToString(self, game):
        """Given a team's upcoming game, return a string with
        the opponent's tricode and the date of the game.
        """

        date = self._ISODateToEasternDatetime(game['startTimeUTC'])

        home_tricode = self._teamIdToTricode(game['hTeam']['teamId'])
        away_tricode = self._teamIdToTricode(game['vTeam']['teamId'])

        if game['isHomeTeam']:
            home_tricode = ircutils.bold(home_tricode)
        else:
            away_tricode = ircutils.bold(away_tricode)

        return '{} | {} @ {}'.format(date, away_tricode, home_tricode)

    def _pastGameToString(self, game):
        """Given a team's upcoming game, return a string with
        the opponent's tricode and the result.
        """
        date = self._ISODateToEasternDate(game['startTimeUTC'])

        home_tricode = self._teamIdToTricode(game['hTeam']['teamId'])
        away_tricode = self._teamIdToTricode(game['vTeam']['teamId'])

        home_score = int(game['hTeam']['score'])
        away_score = int(game['vTeam']['score'])

        if game['isHomeTeam']:
            was_victory = (home_score > away_score)
        else:
            was_victory = (away_score > home_score)

        if home_score > away_score:
            home_tricode = ircutils.bold(home_tricode)
            home_score = ircutils.bold(home_score)
        else:
            away_tricode = ircutils.bold(away_tricode)
            away_score = ircutils.bold(away_score)

        result = ircutils.mircColor('W', 'green') if was_victory \
                 else ircutils.mircColor('L', 'red')

        points = '{} {} {} {}'.format(away_tricode, away_score,
                                      home_tricode, home_score)

        if game['seasonStageId'] == 1:
            points += ' (Preseason)'

        return '{} {} | {}'.format(date, result, points)

############################
# Date-manipulation helpers
############################
    @classmethod
    def _getTodayDate(cls):
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
        today = cls._pacificTimeNow().date()
        today_iso = today.isoformat()
        return today_iso.replace('-', '')

    @staticmethod
    def _easternTimeNow():
        return datetime.datetime.now(pytz.timezone('US/Eastern'))

    @staticmethod
    def _pacificTimeNow():
        return datetime.datetime.now(pytz.timezone('US/Pacific'))

    @staticmethod
    def _ISODateToEasternDate(iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern-time date.
        (The default human-readable format for the listing of games).
        """
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_date = date_eastern.strftime('%a %m/%d')
        return "{}".format(eastern_date)

    @staticmethod
    def _ISODateToEasternTime(iso):
        """Convert the ISO date in UTC time that the API outputs into an
        Eastern time formatted with am/pm.
        (The default human-readable format for the listing of games).
        """
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_time = date_eastern.strftime('%-I:%M %p')
        return "{} ET".format(eastern_time)

    @staticmethod
    def _ISODateToEasternDatetime(iso):
        """Convert the ISO date in UTC time that the API outputs into a
        string with a date and Eastern time formatted with am/pm.
        """
        date = dateutil.parser.parse(iso)
        date_eastern = date.astimezone(pytz.timezone('US/Eastern'))
        eastern_datetime = date_eastern.strftime('%a %m/%d, %I:%M %p')
        return "{} ET".format(eastern_datetime)

    @staticmethod
    def _stripDateSeparators(date_string):
        return date_string.replace('-', '')

    @classmethod
    def _EnglishDateToDate(cls, date):
        """Convert a human-readable like 'yesterday' to a datetime
        object and return a 'YYYYMMDD' string.
        """
        if date == 'yesterday':
            day_delta = -1
        elif date == 'today' or date == 'tonight':
            day_delta = 0
        elif date == 'tomorrow':
            day_delta = 1
        # Calculate the day difference and return a string
        date_string = (cls._pacificTimeNow() +
                       datetime.timedelta(days=day_delta)).strftime('%Y%m%d')
        return date_string

    @classmethod
    def _isValidTricode(cls, team):
        return team in cls._TEAM_TRICODES

############################
# Input-parsing helpers
############################
    @classmethod
    def _isPotentialDate(cls, string):
        """Given a user-provided string, check whether it could be a
        date.
        """
        return (string.lower() in cls._FUZZY_DAYS or
                string.replace('-', '').isdigit())

    @classmethod
    def _parseTeamInput(cls, team):
        """Given a user-provided string, try to extract an upper-case
        team tricode from it. If not valid, throws a ValueError
        exception.
        """
        t = team.upper()
        if not cls._isValidTricode(t):
            raise ValueError('{} is not a valid team'.format(team))
        return t

    @classmethod
    def _parseDateInput(cls, date):
        """Verify that the given string is a valid date formatted as
        YYYY-MM-DD. Also, the API seems to go back until 2014-10-04,
        so we will check that the input is not a date earlier than that.
        In case of failure, throws a ValueError exception.
        """
        date = date.lower()

        if date in cls._FUZZY_DAYS:
            date = cls._EnglishDateToDate(date)

        elif date.replace('-', '').isdigit():
            try:
                parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            except:
                raise ValueError('Incorrect date format, should be YYYY-MM-DD')

            # The current API goes back until 2014-10-04. Is it in range?
            if parsed_date.date() < datetime.date(2014, 10, 4):
                raise ValueError('I can only go back until 2014-10-04')
        else:
            raise ValueError('Date is not valid')

        return cls._stripDateSeparators(date)


    def _getRecapInfo(self, game):
        """Given a finished game, fetch its recap summary and a link
        to its video recap. It returns a string with the format
        '{summary} (link to video)'.

        The link is shortened by calling _shortenURL(str) -> str.
        """

        recap_base_url = 'https://www.nba.com/video/'\
                         '{year}/{month}/{day}/'\
                         '{game_id}-{away_team}-{home_team}-recap.xml'

        url = recap_base_url.format(year=game['starting_year'],
                                    month=game['starting_month'],
                                    day=game['starting_day'],
                                    game_id=game['game_id'],
                                    away_team=game['away_team'].lower(),
                                    home_team=game['home_team'].lower())

        xml = self._getURL(url)
        tree = ElementTree.fromstring(xml)

        res = []

        summary = tree.find('description')
        if summary is not None:
            res.append(summary.text)

        video_recap = tree.find("*file[@bitrate='1920x1080_5904']")
        if video_recap is not None:
            url = self._shortenURL(video_recap.text)
            res.append('({})'.format(url))

        return ' '.join(res)

    @staticmethod
    def _shortenURL(url):
        """ Run a link through an URL shortener and return the new url."""

        # Complete with the code that uses your desired
        # shortener service.
        return url


Class = NBA

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
