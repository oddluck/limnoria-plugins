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

from supybot import utils, plugins, ircutils, callbacks, conf, schedule, ircmsgs
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CBB')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

SCOREBOARD = ('http://site.api.espn.com/apis/site/v2/sports/basketball/'
              'mens-college-basketball/scoreboard?lang=en&region=us'
              '&calendartype=blacklist&limit=300&groups=50&dates={date}')

class CBB(callbacks.Plugin):
    """Fetches College Basketball scores"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(CBB, self)
        self.__parent.__init__(irc)

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    @wrap([getopts({'date': 'somethingWithoutSpaces', 'all':''}),
           optional('text')])
    def cbb(self, irc, msg, args, options, team=None):
        """[--date] [--all] [team]
        Fetches college basketball scores/schedule for given date and/or team.
        Defaults to today and top 25 teams (if playing, otherwise shows all games).
        Use --all to show results for all teams.
        """
        channel = msg.args[0]
        if channel == irc.nick:
            channel = msg.nick
        options = dict(options)
        date = options.get('date')
        if 'all' in options:
            all = True
        else:
            all = False
        if date:
            if date.lower() in ['yesterday', 'tomorrow', 'today']:
                if date.lower() in 'yesterday':
                    date = pendulum.yesterday().format('YYYYMMDD')
                elif date.lower() in 'tomorrow':
                    date = pendulum.tomorrow().format('YYYYMMDD')
                else:
                    date = pendulum.now().format('YYYYMMDD')
            else:
                try:
                    date = pendulum.parse(date, strict=False).format('YYYYMMDD')
                except:
                    irc.reply('Invalid date format')
                    return
            SCORES = self._checkscores(date)
            if date not in SCORES:
                niceDate = pendulum.parse(date)
                niceDate = "{0}/{1}/{2}".format(niceDate.month, niceDate.day, niceDate.year)
                irc.reply('No games found for {}.'.format(date))
        else:
            today = pendulum.now().format('YYYYMMDD')
            yesterday = pendulum.yesterday().format('YYYYMMDD')
            tomorrow = date = pendulum.tomorrow().format('YYYYMMDD')
            SCORES = self._checkscores()
            if today in SCORES:
                date = today
            elif yesterday in SCORES:
                date = yesterday
            elif tomorrow in SCORES:
                date = tomorrow
            else:
                irc.reply('No games found.')
                return

        if team:
            if len(team) > 2:
                reply = []
                # single team
                for key,value in SCORES[date].items():
                    if team.lower() in value['lookup']['abbr'].lower():
                        #print(team.lower(), '\t', value['lookup']['abbr'].lower())
                        reply.append(value['long'])
                        #break
                if not reply:
                    for key,value in SCORES[date].items():
                        if team.lower() in value['lookup']['full'].lower():
                            reply.append(value['long'])
                            #break
                if not reply:
                    irc.reply('ERROR: no match found for your input: {}'.format(team))
                    return
                else:
                    if len(reply) <= 4:
                        for item in reply:
                            irc.sendMsg(ircmsgs.privmsg(channel, item))
                    else:
                        for item in reply:
                            irc.reply(item)
                return
            else:
                irc.reply('ERROR: search string too short')
                return
        else:
            niceDate = pendulum.parse(date)
            niceDate = "{0}/{1}/{2}".format(niceDate.month, niceDate.day, niceDate.year)
            reply = ' | '.join(value['short'] for item,value in SCORES[date].items() if value['top25'])
            if reply and not all:
                irc.reply("Showing teams in the top 25 for {0}. Use --all to see more games.".format(niceDate), prefixNick = False)
                irc.reply(reply, prefixNick = False)
            else:
                reply = ' | '.join(value['short'] for item,value in SCORES[date].items())
                irc.reply("Showing all games for {0}.".format(niceDate), prefixNick = False)
                irc.reply(reply, prefixNick = False)
            return

        return

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _checkscores(self, cdate=None):
        if cdate:
            #today = pendulum.parse(cdate, strict=False).format('YYYYMMDD')
            #yesterday = pendulum.parse(cdate, strict=False).subtract(days=1).format('YYYYMMDD')
            #tomorrow = pendulum.parse(cdate, strict=False).add(days=1).format('YYYYMMDD')
            dates = [cdate]
        else:
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
                    key = event['id']
                    lookup = {'abbr': '{}'.format(event['shortName']),
                              'full': '{}'.format(event['name'])}
                    comp = event['competitions'][0]
                    time = pendulum.parse(comp['date'], strict=False).in_tz('US/Eastern')
                    short_time = time.format('h:mm A zz')
                    long_time = time.format('dddd, MMM Do, h:mm A zz')
                    status = comp['status']['type']['state']
                    is_ended = comp['status']['type']['completed']
                    top25 = True if (0 < comp['competitors'][0]['curatedRank']['current'] <= 25 
                                  or 0 < comp['competitors'][1]['curatedRank']['current'] <= 25) else False
                    home_rank = '(#{})'.format(comp['competitors'][0]['curatedRank']['current']) \
                        if 0 < comp['competitors'][0]['curatedRank']['current'] <= 25 else ''
                    away_rank = '(#{})'.format(comp['competitors'][1]['curatedRank']['current']) \
                        if 0 < comp['competitors'][1]['curatedRank']['current'] <= 25 else ''
                    home_short = comp['competitors'][0]['team']['abbreviation']
                    home_long = comp['competitors'][0]['team']['displayName']
                    away_short = comp['competitors'][1]['team']['abbreviation']
                    away_long = comp['competitors'][1]['team']['displayName']
                    home_score = int(comp['competitors'][0]['score'])
                    away_score = int(comp['competitors'][1]['score'])
                    broadcasts = []
                    try:
                        for thing in comp['broadcasts']:
                            for station in thing['names']:
                                broadcasts.append(station)
                    except:
                        pass
                    #print(home_short, away_short, '\t||\t', top25, status, comp['competitors'][0]['curatedRank']['current'],
                    #                                                       comp['competitors'][1]['curatedRank']['current'])
                    if status == 'pre':
                        # pre
                        short = '{} @ {} {}'.format(away_short, home_short, short_time)
                        long = '{}{} @ {}{} | {}{}'.format(away_long, away_rank, home_long, home_rank, long_time,
                            " [TV: {}]".format(", ".join(broadcasts) if broadcasts else "")
                        )
                    else:
                        # inp
                        if is_ended:
                            clock_short = ircutils.mircColor('F', 'red')
                            clock_long = ircutils.mircColor('Final', 'red')
                        else:
                            if 'Halftime' in comp['status']['type']['detail']:
                                clock_short = ircutils.mircColor('HT', 'orange')
                                clock_long = ircutils.mircColor('Halftime', 'orange')
                            else:
                                clock_short = ircutils.mircColor(comp['status']['type']['shortDetail'].replace(' - ', ' '), 'green')
                                clock_long = ircutils.mircColor(comp['status']['type']['detail'], 'green')
                        try:
                            last_play = ' | \x02Last Play:\x02 {}'.format(comp['situation']['lastPlay']['text']) \
                                if 'situation' in comp else ''
                        except:
                            last_play = ''
                        if away_score > home_score:
                            away_short_str = ircutils.bold('{} {}'.format(away_short, away_score))
                            away_long_str = ircutils.bold('{}{} {}'.format(away_long, away_rank, away_score))
                            home_short_str = '{} {}'.format(home_short, home_score)
                            home_long_str = '{}{} {}'.format(home_long, home_rank, home_score)
                        elif home_score > away_score:
                            away_short_str = '{} {}'.format(away_short, away_score)
                            away_long_str = '{}{} {}'.format(away_long, away_rank, away_score)
                            home_short_str = ircutils.bold('{} {}'.format(home_short, home_score))
                            home_long_str = ircutils.bold('{}{} {}'.format(home_long, home_rank, home_score))
                        else:
                            away_short_str = '{} {}'.format(away_short, away_score)
                            away_long_str = '{}{} {}'.format(away_long, away_rank, away_score)
                            home_short_str = '{} {}'.format(home_short, home_score)
                            home_long_str = '{}{} {}'.format(home_long, home_rank, home_score)
                        short = '{} {} {}'.format(away_short_str, home_short_str, clock_short)
                        long = '{} @ {} - {}{}'.format(away_long_str, home_long_str, clock_long, last_play)
                    games[day][key] = {'short': short, 'long': long, 'ended': is_ended, 'top25': top25, 'lookup': lookup}

                # sort events
                games[day] = collections.OrderedDict(sorted(games[day].items(), key=lambda k: k[1]['ended']))

        return games


Class = CBB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
