# TVMaze v0.0.1
###
# Copyright (c) 2019, cottongin
# All rights reserved.
#
# See LICENSE.txt
###

import requests
import pendulum
import urllib.parse

from . import accountsdb

from supybot import utils, plugins, ircutils, callbacks, world
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('TVMaze')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class TVMaze(callbacks.Plugin):
    """Limnoria plugin to fetch TV show information and schedules from tvmaze.com API"""
    threaded = True
    
    def __init__(self, irc):
        super().__init__(irc)
        self.db = accountsdb.AccountsDB("TVMaze", 'TVMaze.db', self.registryValue(accountsdb.CONFIG_OPTION_NAME))
        world.flushers.append(self.db.flush)
        
    def die(self):
        world.flushers.remove(self.db.flush)
        self.db.flush()
        super().die()
        
    #--------------------#
    # Formatting helpers #
    #--------------------#
    
    def _bold(self, string):
        return ircutils.bold(string)
    
    def _ul(self, string):
        return ircutils.underline(string)
    
    def _color(self, string, color):
        return ircutils.mircColor(string, color)
    
    #--------------------#
    # Internal functions #
    #--------------------#
    
    def _get(self, mode, country='US', date=None, query=None, id_=None):
        """wrapper for requests tailored to TVMaze API"""
        
        base_url = 'http://api.tvmaze.com'
        
        if mode == 'search':
            if not query:
                return
            query = urllib.parse.quote_plus(query)
            base_url += '/search/shows?q={}'.format(query)
            try:
                data = requests.get(base_url).json()
            except:
                data = None
        elif mode == 'schedule':
            if not date:
                date = pendulum.now().format('YYYY-MM-DD')
            base_url += '/schedule?country={}&date={}'.format(country, date)
            try:
                data = requests.get(base_url).json()
            except:
                data = None
        elif mode == 'shows':
            if not id_:
                return
            base_url += '/shows/{}?embed[]=previousepisode&embed[]=nextepisode'.format(id_)
            try:
                data = requests.get(base_url).json()
            except:
                data = None
        else:
            data = None
        
        return data
        
    #------------------#
    # Public functions #
    #------------------#
    
    @wrap([getopts({'country': 'somethingWithoutSpaces',
                    'detail': '',
                    'd': ''}), 'text'])
    def tvshow(self, irc, msg, args, options, query):
        """[--country <country> | --detail|--d] <TV Show Title>
        Fetches information about provided TV Show from TVMaze.com.
        Optionally include --country to find shows with the same name from another country.
        Optionally include --detail (or --d) to show additional details.
        Ex: tvshow --country GB the office
        """
        # prefer manually passed options, then saved user options
        # this merges the two possible dictionaries, prefering manually passed
        # options if they already exist
        options = {**self.db.get(msg.prefix), **dict(options)}
        
        # filter out any manually passed options
        country = options.get('country')
        show_detail = options.get('d') or options.get('detail')
        
        # search for the queried TV show
        show_search = self._get('search', query=query)
        if not show_search:
            irc.reply('Nothing found for your query: {}'.format(query))
            return
        
        # if we have a country, look for that first instead of the first result
        if country:
            for show in show_search:
                if show['show'].get('network'):
                    if show['show']['network']['country']['code'].upper() == country.upper():
                        show_id = show['show']['id']
                        break
            # if we can't find it, default to the first result anyway
            if not show_id:
                show_id = show_search[0]['show']['id']
        else:
            show_id = show_search[0]['show']['id']
        
        # fetch the show information
        show_info = self._get('shows', id_=show_id)
        
        # grab the included URLs and generate an imdb one
        urls = []
        urls.append(show_info['url'])
        urls.append('https://imdb.com/title/{}/'.format(show_info['externals']['imdb']))
        urls.append(show_info['officialSite'])
        
        # grab the genres
        genres = '{}: {}'.format(
            self._bold('Genre(s)'),
            '/'.join(show_info['genres'])
        )
        
        # show name
        name = self._bold(show_info['name'])
        
        # show language
        lang = "{}: {}".format(
            self._bold('Language'),
            show_info['language']
        )
        
        # show status
        status = show_info['status']
        if status == 'Ended':
            status = self._color(status, 'red')
        elif status == 'Running':
            status = self._color(status, 'green')
            
        # show duration
        runtime = "{}: {}m".format(
            self._bold('Duration'),
            show_info['runtime']
        )
        
        # show premiere date, stripped to year and added to name
        if show_info.get('premiered'):
            premiered = show_info['premiered'][:4]
        else:
            premiered = "TBD"
        name = "{} ({})".format(name, premiered)
        
        # is the show on television or web (netflix, amazon, etc)
        if show_info.get('network'):
            # we use this if --detail/--d is asked for
            network = show_info['network']['name']
            schedule = "{}: {} at {} on {}".format(
                self._bold('Schedule'),
                ', '.join(show_info['schedule']['days']),
                show_info['schedule']['time'],
                network
            )
        elif show_info.get('webChannel'):
            # we use this if --detail/--d is asked for
            network = show_info['webChannel']['name']
            schedule = "Watch on {}".format(
                network
            )
            
        # try to get previous and/or next episode details
        if show_info['_embedded']:
            # previous episode
            if show_info['_embedded'].get('previousepisode'):
                try:
                    ep = "S{:02d}E{:02d}".format(
                        show_info['_embedded']['previousepisode']['season'],
                        show_info['_embedded']['previousepisode']['number']
                    )
                except:
                    ep = "?"
                ep = self._color(ep, 'orange')
                previous = " | {}: {ep_name} [{ep}] ({ep_date})".format(
                    self._bold('Prev'),
                    ep_name=show_info['_embedded']['previousepisode']['name'],
                    ep=ep,
                    ep_date=show_info['_embedded']['previousepisode']['airdate']
                )
            else:
                previous = ""
            # next episode
            if show_info['_embedded'].get('nextepisode'):
                try:
                    ep = "S{:02d}E{:02d}".format(
                        show_info['_embedded']['nextepisode']['season'],
                        show_info['_embedded']['nextepisode']['number']
                    )
                except:
                    ep = "?"
                ep = self._color(ep, 'orange')
                next_ = " | {}: {ep_name} [{ep}] ({ep_date} {when})".format(
                    self._bold('Next'),
                    ep_name=show_info['_embedded']['nextepisode']['name'],
                    ep=ep,
                    ep_date=show_info['_embedded']['nextepisode']['airdate'],
                    when=pendulum.parse(show_info['_embedded']['nextepisode']['airstamp']).diff_for_humans()
                )
            else:
                next_ = ""
        
        # now finally put it all together and reply
        reply = "{0} ({3}){1}{2} | {4}".format(
            name,
            next_,
            previous,
            status,
            ' | '.join(urls)
        )
        irc.reply(reply)
        
        # add a second line for details if requested
        if show_detail:
            reply = "{} | {} | {} | {}".format(
                schedule,
                runtime,
                lang,
                genres
            )
            irc.reply(reply)
        
    
    @wrap([getopts({'all': '', 
                    'tz': 'somethingWithoutSpaces',
                    'network': 'somethingWithoutSpaces',
                    'country': 'somethingWithoutSpaces',
                    'showEpisodeTitle': ''})])
    def schedule(self, irc, msg, args, options):
        """[--all | --tz <IANA timezone> | --network <network> | --country <country>]
        Fetches upcoming TV schedule from TVMaze.com.
        """
        # prefer manually passed options, then saved user options
        # this merges the two possible dictionaries, prefering manually passed
        # options if they already exist
        options = {**self.db.get(msg.prefix), **dict(options)}
        
        # parse manually passed options, if any
        tz = options.get('tz') or 'US/Eastern'
        country = options.get('country')
        # TO-DO: add a --filter option(s)
        if country:
            country = country.upper()
            # if user isn't asking for a specific timezone,
            # default to some sane ones given the country
            if not options.get('tz'):
                if country == 'GB':
                    tz = 'GMT'
                elif country == 'AU':
                    tz = 'Australia/Sydney'
                else:
                    tz = 'US/Eastern'
        else:
            country = 'US'
            # we don't need to default tz here because it's already set
        
        # fetch the schedule
        schedule_data = self._get('schedule', country=country)
        
        if not schedule_data:
            irc.reply('Something went wrong fetching TVMaze schedule data.')
            return
        
        # parse schedule
        shows = []
        for show in schedule_data:
            tmp = "{show_name} [{ep}] ({show_time})"
            # by default we show the episode title, there is a channel config option to disable this
            # and users can override with --showEpisodeTitle flag
            show_title = options.get('showEpisodeTitle') or self.registryValue('showEpisodeTitle', msg.args[0])
            if show_title:
                name = "{1}: {0}".format(show['name'], show['show']['name'])
            else:
                name = "{0}".format(show['show']['name'])
            # try to build some season/episode information
            try:
                ep_id = "S{:02d}E{:02d}".format(show['season'], show['number'])
            except:
                ep_id = '?'
            time = pendulum.parse(show['airstamp']).in_tz(tz)
            # put it all together
            tmp = tmp.format(show_name=self._bold(name), 
                             ep=self._color(ep_id, 'orange'), 
                             show_time=time.format('h:mm A zz'))
            # depending on any options, append to list
            if options.get('all'):
                shows.append(tmp)
            elif options.get('network'):
                if show['show'].get('network'):
                    if show['show']['network']['name'].lower() == options.get('network').lower():
                        shows.append(tmp)
            else:
                # for now, defaults to only upcoming 'Scripted' shows
                if show['show']['type'] == 'Scripted' and pendulum.now(tz) <= time:
                    shows.append(tmp)
         
        # finally reply
        reply = "{}: {}".format(self._ul("Today's Shows"), ", ".join(shows))
        irc.reply(reply)
        
    @wrap([getopts({'country': 'somethingWithoutSpaces',
                    'tz': 'somethingWithoutSpaces',
                    'showEpisodeTitle': 'boolean',
                    'clear': ''})])
    def settvmazeoptions(self, irc, msg, args, options):
        """--country <country> | --tz <IANA timezone> | --showEpisodeTitle (True|False)
        Allows user to set options for easier use of TVMaze commands.
        Use --clear to reset all options.
        """
        if not options:
            irc.reply('You must give me some options!')
            return
        
        # prefer manually passed options, then saved user options
        # this merges the two possible dictionaries, prefering manually passed
        # options if they already exist
        options = {**self.db.get(msg.prefix), **dict(options)}
        
        if options.get('clear'):
            self.db.set(msg.prefix, {})
            irc.replySuccess()
            return
        
        self.db.set(msg.prefix, options)
        irc.replySuccess()
        
        
        

Class = TVMaze


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
