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

from supybot import utils, plugins, ircutils, callbacks
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
        
    def die(self):
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
    
    @wrap([getopts({'country': 'somethingWithoutSpaces'}), 'text'])
    def tvshow(self, irc, msg, args, options, query):
        """[--country <country>] <TV Show Title>
        Fetches information about provided TV Show from TVMaze.com.
        Optionally include --country to find shows with the same name from another country
        Ex: tvshow --country GB the office
        """
        options = dict(options)
        country = options.get('country')
        
        show_search = self._get('search', query=query)
        if not show_search:
            irc.reply('Nothing found for your query: {}'.format(query))
            return
        
        if country:
            for show in show_search:
                if show['show'].get('network'):
                    if show['show']['network']['country']['code'].upper() == country.upper():
                        show_id = show['show']['id']
                        break
        else:
            show_id = show_search[0]['show']['id']
        
        show_info = self._get('shows', id_=show_id)
        
        urls = []
        urls.append(show_info['url'])
        urls.append('https://imdb.com/title/{}/'.format(show_info['externals']['imdb']))
        urls.append(show_info['officialSite'])
        
        genres = '/'.join(g for g in show_info['genres'])
        
        name = self._bold(show_info['name'])
        lang = show_info['language']
        status = show_info['status']
        if status == 'Ended':
            status = self._color(status, 'red')
        elif status == 'Running':
            status = self._color(status, 'green')
        runtime = "{}m".format(show_info['runtime'])
        if show_info.get('premiered'):
            premiered = show_info['premiered'][:4]
        else:
            premiered = "TBD"
        name = "{} ({})".format(name, premiered)
        network = show_info.get('network')
        network = network['name'] if network else ""
        
        if show_info['_embedded']:
            if show_info['_embedded'].get('previousepisode'):
                try:
                    ep = "S{:02d}E{:02d}".format(
                        show_info['_embedded']['previousepisode']['season'],
                        show_info['_embedded']['previousepisode']['number']
                    )
                except:
                    ep = "?"
                ep = self._color(ep, 'orange')
                previous = " | {}: {ep_name} [{ep}] ({ep_date}) | ".format(
                    self._bold('Prev'),
                    ep_name=show_info['_embedded']['previousepisode']['name'],
                    ep=ep,
                    ep_date=show_info['_embedded']['previousepisode']['airdate']
                )
            else:
                previous = ""
                
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
                
        reply = "{}{}{}{} | {} | {} | {} | {} | {}".format(
            name,
            next_,
            previous,
            status,
            lang,
            runtime,
            network,
            genres,
            ' | '.join(u for u in urls)
        )
        irc.reply(reply)
        
    
    @wrap([getopts({'all': '', 
                    'tz': 'somethingWithoutSpaces',
                    'network': 'somethingWithoutSpaces',
                    'country': 'somethingWithoutSpaces'})])
    def schedule(self, irc, msg, args, options):
        """[--all | --tz <IANA timezone> | --network <network> | --country <country>]
        Fetches upcoming TV schedule from TVMaze.com.
        """
        options = dict(options)
        tz = options.get('tz') or 'US/Eastern'
        country = options.get('country')
        if country:
            country = country.upper()
            if not options.get('tz'):
                if country == 'GB':
                    tz = 'GMT'
                elif country == 'AU':
                    tz = 'Australia/Sydney'
                else:
                    tz = 'US/Eastern'
        else:
            country = 'US'
        
        schedule_data = self._get('schedule', country=country)
        
        if not schedule_data:
            irc.reply('Something went wrong fetching TVMaze schedule data.')
            return
        
        shows = []
        for show in schedule_data:
            # TO-DO: implement custom --filter
            tmp = "{show_name} [{ep}] ({show_time})"
            name = "{1}: {0}".format(show['name'], show['show']['name'])
            try:
                ep_id = "S{:02d}E{:02d}".format(show['season'], show['number'])
            except:
                ep_id = '?'
            time = pendulum.parse(show['airstamp']).in_tz(tz).format('h:mm A zz')
            tmp = tmp.format(show_name=self._bold(name), 
                             ep=self._color(ep_id, 'orange'), 
                             show_time=time)
            if options.get('all'):
                shows.append(tmp)
            elif options.get('network'):
                if show['show'].get('network'):
                    if show['show']['network']['name'].lower() == options.get('network').lower():
                        shows.append(tmp)
            else:
                if show['show']['type'] == 'Scripted':
                    shows.append(tmp)
                
        reply = "{}: {}".format(self._ul("Today's Shows"), ", ".join(s for s in shows))
        irc.reply(reply)
        
        

Class = TVMaze


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
