###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
# SEE LICENSE.txt
#
###

import pendulum
import requests
import collections

from supybot import utils, plugins, ircutils, callbacks, conf, schedule
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CBBScores')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

SCOREBOARD = ('http://site.api.espn.com/apis/site/v2/sports/basketball/'
              'mens-college-basketball/scoreboard?lang=en&region=us'
              '&calendartype=blacklist&limit=300&dates={date}')

class CBBScores(callbacks.Plugin):
    """Fetches College Basketball scores"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(CBBScores, self)
        self.__parent.__init__(irc)
        #self.filename = conf.supybot.directories.data.dirize('CBBScores.db')
        def checkcbbscores():
            self._checkscores()
        self.SCORES = self._checkscores()
        # try:  # check scores.
        #     schedule.addPeriodicEvent(checkcbbscores, 30, 
        #         now=False, name='checkcbbscores')
        # except AssertionError:
        #     try:
        #         schedule.removeEvent('checkcbbscores')
        #     except KeyError:
        #         pass
        #     schedule.addPeriodicEvent(checkcbbscores, 30, 
        #         now=False, name='checkcbbscores')

    # def die(self):
    #     try:
    #         schedule.removeEvent('checkcbbscores')
    #     except KeyError:
    #         pass
    #     self.__parent.die()

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    @wrap([getopts({'date': 'somethingWithoutSpaces'}),
           optional('text')])
    def cbb(self, irc, msg, args, options, team=None):
        """(--date YYYYMMDD) (team)
        Fetches college basketball scores for given date and/or team.
        Defaults to today and all teams if no input given.
        Ex: --date 20181117 MICH
        """
        options = dict(options)
        date = options.get('date') or pendulum.now().format('YYYYMMDD')        

        if date not in self.SCORES:
            # fetch another day
            print('date not in scores db')
            pass
        else:
            if team:
                # single team
                for key,value in self.SCORES[date].items():
                    if team.lower() in key.lower():
                        irc.reply(value['long'])
                        return
                pass
            else:
                # all teams
                irc.reply(' | '.join(value['short'] for item,value in self.SCORES[date].items()))
                return

        return

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _checkscores(self):
        today = pendulum.now().format('YYYYMMDD')
        yesterday = pendulum.yesterday().format('YYYYMMDD')
        tomorrow = pendulum.tomorrow().format('YYYYMMDD')

        dates = [yesterday, today, tomorrow]
        data = collections.OrderedDict()
        for date in dates:
            tmp = requests.get(SCOREBOARD.format(date=date)).json()
            tmp_date = pendulum.parse(tmp['eventsDate']['date'], 
                strict=False).in_tz('US/Eastern').format('YYYYMMDD')
            data[tmp_date] = tmp['events']

        #print(data)
        """
        'day': {'game1': {'short', 'long'},
                'game2': {'short', 'long'}}
        """
        games = collections.OrderedDict()
        for day, d in data.items():
            #print(day, d)
            if d:
                games[day] = collections.OrderedDict()
                for event in d:
                    key = '{} | {}'.format(event['name'], event['shortName'])
                    comp = event['competitions'][0]
                    time = pendulum.parse(comp['date'], strict=False).in_tz('US/Eastern')
                    short_time = time.format('h:mm A zz')
                    long_time = time.format('dddd, MMM Do, h:mm A zz')
                    status = comp['status']['type']['state']
                    is_ended = comp['status']['type']['completed']
                    home_short = comp['competitors'][0]['team']['abbreviation']
                    home_long = comp['competitors'][0]['team']['displayName']
                    away_short = comp['competitors'][1]['team']['abbreviation']
                    away_long = comp['competitors'][1]['team']['displayName']
                    home_score = int(comp['competitors'][0]['score'])
                    away_score = int(comp['competitors'][1]['score'])
                    #print(home_short, away_short, ' || ', is_ended, status)
                    if is_ended:
                        # strings for final games
                        short = 'tbd'
                        long = 'tbd'
                    else:
                        # strings for pre/in games
                        if status == 'pre':
                            # pre
                            short = '{} @ {} {}'.format(away_short, home_short, short_time)
                            long = '{} @ {} | {}'.format(away_long, home_long, long_time)
                        else:
                            # inp
                            clock = ircutils.mircColor(comp['status']['displayClock'], 'green')
                            if away_score > home_score:
                                away_short_str = ircutils.bold('{} {}'.format(away_short, away_score))
                                away_long_str = ircutils.bold('{} {}'.format(away_long, away_score))
                                home_short_str = '{} {}'.format(home_short, home_score)
                                home_long_str = '{} {}'.format(home_long, home_score)
                            elif home_score > away_score:
                                away_short_str = '{} {}'.format(away_short, away_score)
                                away_long_str = '{} {}'.format(away_long, away_score)
                                home_short_str = ircutils.bold('{} {}'.format(home_short, home_score))
                                home_long_str = ircutils.bold('{} {}'.format(home_long, home_score))
                            else:
                                away_short_str = '{} {}'.format(away_short, away_score)
                                away_long_str = '{} {}'.format(away_long, away_score)
                                home_short_str = '{} {}'.format(home_short, home_score)
                                home_long_str = '{} {}'.format(home_long, home_score)
                            short = '{} {} {}'.format(away_short_str, home_short_str, clock)
                            long = '{} @ {} - {}'.format(away_long_str, home_long_str, clock)
                    games[day][key] = {'short': short, 'long': long}

        return games


Class = CBBScores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
