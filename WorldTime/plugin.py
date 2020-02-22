###
# Copyright (c) 2014, spline
# All rights reserved.
#
#
###

# my libs
import sys
import json
import time
import pickle
import pendulum

# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.conf as conf
import supybot.log as log
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WorldTime')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

filename = conf.supybot.directories.data.dirize('WorldTime.db')

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; WorldTime plugin)' % conf.version
}

class WorldTime(callbacks.Plugin):
    """Add the help for "@plugin help WorldTime" here
    This should describe *how* to use this plugin."""
    threaded = True

    ###############################
    # DATABASE HANDLING FUNCTIONS #
    ###############################

    def __init__(self, irc):
        self.__parent = super(WorldTime, self)
        self.__parent.__init__(irc)
        self.db = {}
        self._loadDb()
        world.flushers.append(self._flushDb)

    def _loadDb(self):
       """Loads the (flatfile) database mapping ident@hosts to timezones."""

       try:
           with open(filename, 'rb') as f:
               self.db = pickle.load(f)
       except Exception as e:
           self.log.debug('WorldTime: Unable to load pickled database: %s', e)

    def _flushDb(self):
       """Flushes the (flatfile) database mapping ident@hosts to timezones."""

       try:
           with open(filename, 'wb') as f:
               pickle.dump(self.db, f, 2)
       except Exception as e:
               self.log.warning('WorldTime: Unable to write pickled database: %s', e)

    def die(self):
       self._flushDb()
       world.flushers.remove(self._flushDb)
       self.__parent.die()

    ##################
    # TIME FUNCTIONS #
    ##################

    def _converttz(self, msg, outputTZ):
        """Convert epoch seconds to a HH:MM readable string."""

        # now do some timezone math.
        try:
            dt = pendulum.now(outputTZ)
            outstrf = self.registryValue("format", msg.args[0])
            return dt.strftime(outstrf)
        except Exception as e:
            self.log.info("WorldTime: ERROR: _converttz: {0}".format(e))

    ##############
    # GAPI STUFF #
    ##############

    def _getlatlng(self, location):
        api_key = self.registryValue('mapsAPIkey')
        location = utils.web.urlquote(location)
        url = 'https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&key=%s' % (location, api_key)

        # try and fetch url
        try:
            response = utils.web.getUrl(url, headers=HEADERS)
        except utils.web.Error as e:
            log.debug(str(e))

        # wrap in a big try/except
        try:
            result = json.loads(response.decode('utf-8'))
            if result['status'] == 'OK':
               lat = str(result['results'][0]['geometry']['location']['lat'])
               lng = str(result['results'][0]['geometry']['location']['lng'])
               place = (result['results'][0]['formatted_address'])
               ll = '%s,%s' % (lat, lng)  # lat+long into a single string.
               return {'place':place, 'll':ll}
            else:
                self.log.info("ERROR: _getlatlng: status result NOT ok. Result: {0}".format(result))
        except Exception as e:
            self.log.info("ERROR: _getlatlng: {0}".format(e))

    def _gettime(self, latlng):
        api_key = self.registryValue('mapsAPIkey')
        latlng = utils.web.urlquote(latlng)
        url = 'https://maps.googleapis.com/maps/api/timezone/json?location=%s&sensor=false&timestamp=%s&key=%s' % (latlng, time.time(), api_key)

        # try and fetch url
        try:
            response = utils.web.getUrl(url, headers=HEADERS)
        except utils.web.Error as e:
            log.debug(str(e))

        # wrap in a big try/except
        try:
            result = json.loads(response.decode('utf-8'))
            if result['status'] == 'OK':
                return result
            else:
                self.log.info("WorldTime: _gettime: status result NOT ok. Result: {0}".format(result))
        except Exception as e:
            self.log.info("WorldTime: _gettime: {0}".format(e))

    ###################
    # PUBLIC FUNCTION #
    ###################

    def worldtime(self, irc, msg, args, opts, location):
        """[--nick <nick] [<location>]

        Query GAPIs for <location> and attempt to figure out local time. [<location>]
        is only required if you have not yet set a location for yourself using the 'set'
        command. If --nick is given, try looking up the location for <nick>.
        """
        opts = dict(opts)
        if not location:
            try:
                if 'nick' in opts:
                    host = irc.state.nickToHostmask(opts['nick'])
                else:
                    host = msg.prefix
                ih = host.split('!')[1]
                location = self.db[ih]
            except KeyError:
                irc.error("No location for %s is set. Use the 'set' command "
                    "to set a location for your current hostmask, or call 'worldtime' "
                    "with <location> as an argument." % ircutils.bold('*!'+ih), Raise=True)
        # first, grab lat and long for user location
        gc = self._getlatlng(location)
        if not gc:
            irc.error("I could not find the location for: {0}. Bad location? Spelled wrong?".format(location), Raise=True)
        # next, lets grab the localtime for that location w/lat+long.
        ll = self._gettime(gc['ll'])
        if not ll:
            irc.error("I could not find the local timezone for: {0}. Bad location? Spelled wrong?".format(location), Raise=True)
        # if we're here, we have localtime zone.
        lt = self._converttz(msg, ll['timeZoneId'])
        if lt:  # make sure we get it back.
            if sys.version_info[0] <= 2:
                s = "{0} :: Current local time is: {1} ({2})".format(ircutils.bold(gc['place'].encode('utf-8')), lt, ll['timeZoneName'].encode('utf-8'))
            else:
                s ="{0} :: Current local time is: {1} ({2})".format(ircutils.bold(gc['place']), lt, ll['timeZoneName'])
            if self.registryValue('disableANSI', msg.args[0]):
                s = ircutils.stripFormatting(s)
            irc.reply(s)
        else:
            irc.error("Something went wrong during conversion to timezone. Check the logs.", Raise=True)

    worldtime = wrap(worldtime, [getopts({'nick': 'nick'}), additional('text')])

    def set(self, irc, msg, args, timezone):
        """<location>

        Sets the location for your current ident@host to <location>."""
        ih = msg.prefix.split('!')[1]
        self.db[ih] = timezone
        irc.replySuccess()
    set = wrap(set, ['text'])

    def unset(self, irc, msg, args):
        """takes no arguments.

        Unsets the location for your current ident@host."""
        ih = msg.prefix.split('!')[1]
        try:
            del self.db[ih]
            irc.replySuccess()
        except KeyError:
            irc.error("No entry for %s exists." % ircutils.bold('*!'+ih), Raise=True)

Class = WorldTime


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
