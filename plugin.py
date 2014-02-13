###
# Copyright (c) 2014, spline
# All rights reserved.
#
#
###

# my libs
import urllib
import urllib2
import json
import time
import pytz
import datetime
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WorldTime')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class WorldTime(callbacks.Plugin):
    """Add the help for "@plugin help WorldTime" here
    This should describe *how* to use this plugin."""
    threaded = True

    ##################
    # TIME FUNCTIONS #
    ##################
    
    def _utcnow(self):
        """Calculate Unix timestamp from GMT. Code from calendar.timegm()"""
    
        ttuple = datetime.datetime.utcnow().utctimetuple()
        _EPOCH_ORD = datetime.date(1970, 1, 1).toordinal()
        year, month, day, hour, minute, second = ttuple[:6]
        days = datetime.date(year, month, 1).toordinal() - _EPOCH_ORD + day - 1
        hours = days*24 + hour
        minutes = hours*60 + minute
        seconds = minutes*60 + second
        return seconds
    
    def _converttz(self, s, outputTZ):
        """Convert epoch seconds to a HH:MM readable string."""
    
        # now do some timezone math.
        try:
            dtobj = datetime.datetime.fromtimestamp(s, tz=pytz.timezone(outputTZ)) # convert epoch into aware dtobj.
            outstrf = '%a, %H:%M'  # Day, HH:MM
            local_dt = dtobj.astimezone(pytz.timezone(outputTZ))
            return local_dt.strftime(outstrf)
        except Exception, e:
            self.log.info("ERROR: _converttz: {0}".format(e))
            return None

    ##############
    # GAPI STUFF #
    ##############

    def _getlatlng(self, location):
        location = urllib.quote_plus(location)
        url = 'http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false' % location
        # wrap in a big try/except
        try:
            response = urllib2.urlopen(url).read()
            result = json.loads(response.decode('utf-8'))
            if result['status'] == 'OK':
               lat = str(result['results'][0]['geometry']['location']['lat'])
               lng = str(result['results'][0]['geometry']['location']['lng'])
               place = (result['results'][0]['formatted_address'])
               ll = '%s,%s' % (lat, lng)  # lat+long into a single string.
               return {'place':place, 'll':ll}
            else:
                self.log.info("ERROR: _getlatlng: status result NOT ok. Result: {0}".format(result))
                return None
        except Exception, e:
            self.log.info("ERROR: _getlatlng: {0}".format(e))
            return None
    
    def _gettime(self, latlng):
        latlng = urllib.quote_plus(latlng)
        url = 'https://maps.googleapis.com/maps/api/timezone/json?location=%s&sensor=false&timestamp=%s' % (latlng, time.time())
        # wrap in a big try/except
        try:
            response = urllib2.urlopen(url).read()
            result = json.loads(response.decode('utf-8'))
            if result['status'] == 'OK':
                # {u'status': u'OK', u'dstOffset': 0, u'rawOffset': -18000, u'timeZoneName': u'Eastern Standard Time', u'timeZoneId': u'America/New_York'}
                return result
            else:
                self.log.info("ERROR: _gettime: status result NOT ok. Result: {0}".format(result))
                return None
        except Exception, e:
            self.log.info("ERROR: _gettime: {0}".format(e))
            return None
    
    ###################
    # PUBLIC FUNCTION #
    ###################
    
    def worldtime(self, irc, msg, args, optinput):
        """<location>
        
        Query GAPIs for <location> and attempt to figure out local time.
        """
    
        # first, grab lat and long for user location    
        gc = self._getlatlng(optinput)
        if not gc:
            irc.reply("ERROR: I could not find lat/long for: {0}. Bad location? Spelled wrong?".format(optinput))
            return
        # next, lets grab the localtime for that location w/lat+long.
        ll = self._gettime(gc['ll'])
        if not ll:
            irc.reply("ERROR: I could not find local timezone for: {0}. Bad location? Spelled wrong?".format(optinput))
            return
        # if we're here, we have localtime zone.
        utcnow = self._utcnow()  # grab UTC now.
        # localtm = utcnow+ll['rawOffset']  # grab raw offset from 
        # now lets use pytz to convert into the localtime in the place.
        lt = self._converttz(utcnow, ll['timeZoneId'])
        if lt:  # make sure we get it back.
            irc.reply("{0} :: Current local time is: {1} ({2})".format(ircutils.bold(gc['place'].encode('utf-8')), lt, ll['timeZoneName'].encode('utf-8')))
        else:
            irc.reply("ERROR: Something went wrong during conversion to timezone. Check logs.")

    worldtime = wrap(worldtime, [('text')])

Class = WorldTime


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
