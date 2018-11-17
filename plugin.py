###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
# SEE LICENSE.txt
#
###

import pendulum
import requests
import dataset

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
        self.filename = conf.supybot.directories.data.dirize('CBBScores.db')
        self.SCORES = dataset.connect('sqlite:///{}'.format(self.filename))
        def checkcbbscores():
            self._checkscores()
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

        self._checkscores()
        
        if date not in self.SCORES:
            # fetch another day
            pass
        else:
            if team:
                # single team
                pass
            else:
                # all teams
                pass

        return

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _checkscores(self):
        today = pendulum.now().format('YYYYMMDD')
        yesterday = pendulum.yesterday().format('YYYYMMDD')
        tomorrow = pendulum.tomorrow().format('YYYYMMDD')

        dates = [yesterday, today, tomorrow]
        data = {}
        for date in dates:
            tmp = requests.get(SCOREBOARD.format(date=date)).json()
            tmp_date = pendulum.parse(tmp['eventsDate']['date'], 
                strict=False).in_tz('US/Eastern').format('YYYYMMDD')
            data[tmp_date] = tmp['events']

        print(data)

        return data


Class = CBBScores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
