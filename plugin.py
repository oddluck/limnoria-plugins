###
# Geo/plugin.py
# by SpiderDave
###

import time
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import os, errno
import supybot.registry as registry
import supybot.ircdb as ircdb
import gzip
from urlparse import urlparse

import pygeoip

class Geo(callbacks.Plugin):
    threaded=True
    """
    Geolocation using GeoLiteCity
    """
    
    def make_sure_path_exists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
    
    # **********************************************************************
    def geo( self, irc, msgs, args, stuff):
        """[<ip> | <hostname>]
        
        Geolocation of an ip or host.
        """
        if stuff.lower()=='update':
            irc.reply('Updating data file...')
            self.update()
            irc.reply('Update finished.')
            
            return
        
        try:
            gic = pygeoip.GeoIP('%s%spygeoip%sGeoLiteCity.dat' % (conf.supybot.directories.data(), os.sep, os.sep))
        except:
            irc.reply("Error:  GeoLiteCity database not found, attempting to update...")
            try:
                self.update()
                irc.reply('Update finished.')
            except:
                irc.reply("Update failed.")
            
            return


        if not utils.net.isIP(stuff):
            try:
                x_hostname=urlparse(stuff).hostname # get hostname from url
                if not x_hostname: x_hostname= stuff # already hostname?
                info=gic.record_by_name(x_hostname)
                if 'city' in info.keys():
                    x_city=info['city'] + ', '
                else:
                    x_city=''
                if 'region_name' in info.keys():
                    x_region_name=info['region_name'] + ', '
                else:
                    x_region_name=''
                if 'country_name' in info.keys():
                    x_country_name=info['country_name']
                else:
                    x_country_name=''
                irc.reply('%s%s%s' % (x_city,x_region_name,x_country_name))
            except:
                irc.reply('Not a valid ip or name.')
                return
        else:
            info=gic.record_by_addr(stuff)
            
            if 'city' in info.keys():
                x_city=info['city'] + ', '
            else:
                x_city=''
            if 'region_name' in info.keys():
                x_region_name=info['region_name'] + ', '
            else:
                x_region_name=''
            if 'country_name' in info.keys():
                x_country_name=info['country_name']
            else:
                x_country_name=''
            irc.reply('%s%s%s' % (x_city,x_region_name,x_country_name))
    geo = wrap(geo, ['text'])

    def update(self):
        """update the geo files"""
        now=int(time.time())
        try:
            lastupdate=self.registryValue('datalastupdated')
            self.log.info('Last update: %s seconds ago.' % lastupdate)
        except registry.NonExistentRegistryEntry:
            self.log.info('supybot.plugins.%s.datalastupdate not set. Creating...' % self.name)
            conf.registerGlobalValue(conf.supybot.plugins.get(self.name), 'datalastupdated', registry.PositiveInteger(1, """An integer representing the time since epoch the .dat file was last updated."""))
            self.log.info('...success!')
            lastupdate=1
            self.log.info('Last update: Unknown/Never')

        #if (now-lastupdate)>604800: # updated weekly
        if 1==1:
            self.setRegistryValue('datalastupdated', now)
            self.log.info("Starting update of Geo data files...")
            self.getfile()
        return
        
    def getfile(self):
        """grabs the data file"""
        u=r'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
        f= r'%s%sGeoLiteCity.dat.gz' % (conf.supybot.directories.data.tmp(),os.sep)
        f2 = r'%s%spygeoip%sGeoLiteCity.dat' % (conf.supybot.directories.data(),os.sep, os.sep)
        self.make_sure_path_exists(r'%s%spygeoip' % (conf.supybot.directories.data(),os.sep))
        
        self.log.info('Starting download: %s' % f)
        
        h = utils.web.getUrl(u)
        if h:
            tempfile=open(f, 'w+b')
            if tempfile:
                tempfile.write(h)
                tempfile.close()
                self.log.info('Completed: %s' % f)
                self.log.info('Unzipping: %s' % f)
                f_in = gzip.open(f, 'rb')
                f_out=open(f2, 'wb')
                f_out.writelines(f_in)
                f_out.close()
                f_in.close()
                self.log.info('Finished Unzipping: %s' % f)
        else:
            self.log.info('Could not download: %s' % f)
        return

Class = Geo

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
