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
import tarfile
import gzip
import socket

try:
    import geoip2.database
except:
    raise ImportError("The Geo plugin requires geoip2 be installed.  Load aborted.")

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

    def geo(self, irc, msg, args, stuff):
        """[<ip> | <host> | <nick>]
        Geolocation of an ip, hostname, or nick. Nick must be in channel.
        """
        channel = msg.args[0]
        try:
            reader = geoip2.database.Reader('%s%sgeo%sGeoLite2-City.mmdb' % (conf.supybot.directories.data(), os.sep, os.sep))
        except:
            irc.reply("Error:  GeoLite2-City database not found, attempting to update...")
            try:
                self.do_update()
                irc.reply('Update finished.')
            except:
                irc.reply("Update failed.")
            return
        if stuff.lower() in (nick.lower() for nick in list(irc.state.channels[channel].users)):
            try:
                stuff = irc.state.nickToHostmask(stuff).split('@')[1]
                ip = socket.gethostbyname(stuff)
            except:
                irc.reply("Invalid hostname {0}".format(stuff))
                return
        elif not utils.net.isIP(stuff):
            try:
                ip = socket.gethostbyname(stuff)
            except:
                irc.reply("Invalid nick/hostname {0}".format(stuff))
                return
        elif utils.net.isIP(stuff):
            ip = stuff
        else:
            irc.reply("invalid nick or hostname/ip {0}".format(stuff))
        try:
            res = reader.city(ip)
            if res:
                irc.reply('%s, %s, %s' % (res.city.name, res.subdivisions.most_specific.name, res.country.name ))
            else:
                irc.reply("No results found")
        except:
            irc.reply("No results found")
    geo = wrap(geo, ['text'])

    def update(self, irc, msg, args):
        """
        Update geoip database
        """
        try:
            irc.reply('Updating data file...')
            self.do_update()
            irc.reply('Update finished.')
        except:
            irc.reply("Update failed.")
            return
    update = wrap(update)

    def do_update(self):
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
        u='https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz'
        f = '%s%sgeo%sGeoLite2-City.tar.gz' % (conf.supybot.directories.data(), os.sep, os.sep)
        f2 = '%s%sgeo%sGeoLite2-City.tar' % (conf.supybot.directories.data(), os.sep, os.sep)
        self.make_sure_path_exists(r'%s%sgeo' % (conf.supybot.directories.data(),os.sep))
        path = '%s%sgeo' % (conf.supybot.directories.data(),os.sep)
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
                self.log.info('Untarring: %s' % f2)
                tar = tarfile.open(f2)
                tar.getmembers()
                for member in tar.getmembers():
                    if "GeoLite2-City.mmdb" in member.name:
                        member.name = "GeoLite2-City.mmdb"
                        self.log.info(member.name)
                        tar.extract(member, path=path)
                self.log.info('Finished Untarring: %s' % f2)
                tar.close()
                os.remove(f)
                os.remove(f2)
        else:
            self.log.info('Could not download: %s' % f)
        return

Class = Geo
