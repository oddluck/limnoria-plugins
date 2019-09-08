# -*- coding: utf-8 -*-
###
# This file is part of Soap.
#
# Soap is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# Soap is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should have received
# a copy of the GNU General Public License along with Soap. If not, see
# <http://www.gnu.org/licenses/>.
###

import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils

import logging
import logging.handlers
import os.path
import re
import urllib2
import requests
import sys
import json
from datetime import datetime, timedelta

from enums import *
from libottdadmin2.enums import Colour, Action, DestType, ClientID
from libottdadmin2.packets.admin import AdminRcon, AdminChat
from libottdadmin2.trackingclient import MappingObject

class RconResults(MappingObject):
    _mapping = [
        ('irc', 'irc'),
        ('command', 'command'),
        ('succestext', 'succestext'),
        ('results', 'results'),
    ]

def checkPermission(irc, msg, channel, allowOps):
    capable = ircdb.checkCapability(msg.prefix, 'trusted')
    if capable:
        return True
    else:
        opped = msg.nick in irc.state.channels[channel].ops
        if opped and allowOps:
            return True
        else:
            return False

def disconnect(conn, forced):
    if forced:
        conn.force_disconnect()
    else:
        conn.disconnect()

def generateDownloadUrl(irc, version, osType = None):
    stable = '\d\.\d\.\d'
    testing = '\d\.\d\.\d-rc\d'
    trunk = 'r\d{5}'

    if not osType:
        url = 'http://www.openttd.org/en/'
        if re.match(stable, version) or re.match(testing, version):
            url += 'download-stable/%s' % version
        elif re.match(trunk, version):
            url += 'download-trunk/%s' % version
        else:
            url = None
    else:
        url = 'http://binaries.openttd.org/'
        if re.match(stable, version):
            url += 'releases/%s/openttd-%s-' % (version, version)
        elif re.match(trunk, version):
            url += 'nightlies/trunk/%s/openttd-trunk-%s-' % (version, version)
        else:
            url = None
        if url:
            if osType.startswith('lin'):
                url += 'linux-generic-'
                if osType == 'lin':
                    url += 'i686.tar.xz'
                elif osType == 'lin64':
                    url += 'amd64.tar.xz'
                else:
                    url = None
            elif osType == 'osx':
                url += 'macosx-universal.zip'
            elif osType == 'source':
                url += 'source.tar.xz'
            elif osType.startswith('win'):
                url += 'windows-%s.zip' % osType
            else:
                url = None
    return url

def getColourNameFromNumber(number):
    colours = {
        Colour.COLOUR_DARK_BLUE    : 'Dark Blue',
        Colour.COLOUR_PALE_GREEN   : 'Pale Green',
        Colour.COLOUR_PINK         : 'Pink',
        Colour.COLOUR_YELLOW       : 'Yellow',
        Colour.COLOUR_RED          : 'Red',
        Colour.COLOUR_LIGHT_BLUE   : 'Light Blue',
        Colour.COLOUR_GREEN        : 'Green',
        Colour.COLOUR_DARK_GREEN   : 'Dark Green',
        Colour.COLOUR_BLUE         : 'Blue',
        Colour.COLOUR_CREAM        : 'Cream',
        Colour.COLOUR_MAUVE        : 'Mauve',
        Colour.COLOUR_PURPLE       : 'Purple',
        Colour.COLOUR_ORANGE       : 'Orange',
        Colour.COLOUR_BROWN        : 'Brown',
        Colour.COLOUR_GREY         : 'Grey',
        Colour.COLOUR_WHITE        : 'White',
    }
    colourName = colours.get(number, number)
    return colourName

def getQuitReasonFromNumber(number):
    reasons = {
        0x00 :'general error',
        0x01 :'desync error',
        0x02 :'could not load map',
        0x03 :'connection lost',
        0x04 :'protocol error',
        0x05 :'NewGRF mismatch',
        0x06 :'not authorized',
        0x07 :'received invalid or unexpected packet',
        0x08 :'wrong revision',
        0x09 :'name already in use',
        0x0A :'wrong password',
        0x0B :'wrong company in DoCommand',
        0x0C :'kicked by server',
        0x0D :'was trying to use a cheat',
        0x0E :'server full',
        0x0F :'was sending too many commands',
        0x10 :'received no password in time',
        0x11 :'general timeout',
        0x12 :'downloading map took too long',
        0x13 :'processing map took too long',
    }
    reasonText = reasons.get(number, number)
    return reasonText

def getConnection(connections, channels, source, serverID = None):
    conn = None

    if not serverID:
        if ircutils.isChannel(source) and source.lower() in channels:
            conn = connections.get(source)
    else:
        if ircutils.isChannel(serverID):
            conn = connections.get(serverID)        

    serverID = serverID and serverID.lower() or 'default'
    
    if not conn:
        for c in connections.itervalues():
            if c.ID == serverID:
                conn = c

    return conn

def getConnectionID(conn):
    if conn.ID == 'default':
        return conn.channel
    else:
        return conn.ID

def initLogger(conn, logdir, history):
    if os.path.isdir(logdir):
        if not len(conn.logger.handlers):
            logfile = os.path.join(logdir, '%s.log' % conn.ID)
            logformat = logging.Formatter('%(asctime)s %(message)s')
            handler = logging.handlers.RotatingFileHandler(logfile, backupCount = history)
            handler.setFormatter(logformat)
            conn.logger.addHandler(handler)

def logEvent(logger, message):
    try:
        logger.info(message)
    except AttributeError:
        pass

def msgChannel(irc, channel, msg):
    if channel in irc.state.channels or irc.isNick(channel):
        irc.queueMsg(ircmsgs.privmsg(channel, msg))

def checkIP(irc, conn, client, whitelist, checkedDict):

    if client.hostname in whitelist:
        text = '*** {name} is a whitelisted player, and will not be checked.'.format(name=client.name)
        conn.send_packet(AdminChat,
                         action=Action.CHAT,
                         destType=DestType.BROADCAST,
                         clientID=ClientID.SERVER,
                         message=text)
        msgChannel(irc, conn.channel, text)
        return
    result = None

    # First let's garbage collect
    # learner's note: you can't just do iteritems() into a del because you'll get a RuntimeError exception when
    # the dictionary changes size during the loop
    cutoff = datetime.utcnow() - timedelta(days=1)
    checkedDict = { k:v for k,v in checkedDict.iteritems() if v.get('timestamp') < cutoff }

    if client.hostname not in checkedDict \
    or not checkedDict.get(client.hostname, {}).get('message', False):
        try:
            result = requests.get("http://check.getipintel.net/check.php?ip=" + client.hostname + "&format=json&oflags=bc&contact=" + "ttd-abuse@duck.me.uk",timeout=5.00)
            if (result.status_code != 200):
                msgChannel(irc, conn.channel, str("*** *[ADM]* Couldn\'t contact validator to check %s. Status error?" % client.name))
                return
            result = json.loads(result.text)
        except requests.exceptions.RequestException as e:
            msgChannel(irc, conn.channel, str("*** *[ADM]* Couldn\'t contact validator to check {name}. Timeout?".format(name=client.name)))
            return

        if (result == None):
            msgChannel(irc, conn.channel,"*** *[ADM]* Received NONE during checkIP (this should never happen!)")
            return
        conn.logger.debug('>>--DEBUG--<< CheckIP result: %s' % str(result))
        if result['result'] < 0:

            checkedDict[client.hostname] = {'result': result['result'], 'BadIP': result.get('BadIP', 0), 'Country': result['Country'], 'timestamp': datetime.utcnow()}
        else:
            checkedDict[client.hostname] = {'result': result['result'], 'message': result.get('message', 'Unknown failure'), 'timestamp': datetime.utcnow()}
    else:
        conn.logger.debug('>>--DEBUG--<< Using cached result for IP: %s' % client.hostname)
        result = checkedDict[client.hostname]

    if float(result['result']) < 0:
        msgChannel(irc, conn.channel, "*** There was a problem validating {name}. The error was: {error}".format(name=client.name, error=result['message']))
    elif float(result['result']) == 1:
        conn.send_packet(AdminChat,
                         action=Action.CHAT_CLIENT,
                         destType=DestType.CLIENT,
                         clientID=client.id,
                         message='Sorry, connecting from a VPN or proxy is not allowed! Please disable any such software and try again. If you think this is an error, please contact us.')
        text = '*** {name} was trying to connect from a VPN or proxy in {location}, which is not allowed.'.format(name=client.name, location=result['Country'])
        command = 'ban %s' % client.id
        conn.rcon = conn.channel
        conn.send_packet(AdminChat,
                         action=Action.CHAT,
                         destType=DestType.BROADCAST,
                         clientID=ClientID.SERVER,
                         message=text)
        msgChannel(irc, conn.channel, text)
        conn.send_packet(AdminRcon, command=command)
    elif float(result['result']) > 0.95 or result.get('BadIP', 0) == 1:
        text = str('*** {name} MIGHT BE CONNECTING VIA A PROXY IN {location}. {certainty:.2f} certainty.' + (" Warning: Potential ISP blacklisted address!" if bool(result.get('BadIP', False)) else "")).format(name=client.name, location=result['Country'], certainty=float(result['result'])*100)
        conn.send_packet(AdminChat,
                         action=Action.CHAT,
                         destType=DestType.BROADCAST,
                         clientID=ClientID.SERVER,
                         message=text)
        msgChannel(irc, conn.channel, text)
    else:
        text = '*** {name} is a valid player from {location}.'.format(name=client.name, location=result.get('Country', 'an unknown country'))
        conn.send_packet(AdminChat,
                         action=Action.CHAT,
                         destType=DestType.BROADCAST,
                         clientID=ClientID.SERVER,
                         message=text)
        msgChannel(irc, conn.channel, text)
    return

def moveToSpectators(irc, conn, client, kickCount, kickDict):
    if client.id in kickDict:
        kickDict[client.id] += 1
    else:
        kickDict[client.id] = 1

    text = '%s: Change your name before joining/starting a company. Use \'!name <new name>\' to do so. (%s OF %s BEFORE KICK)' % (client.name, kickDict[client.id], kickCount)
    command = 'move %s 255' % client.id
    conn.rcon = conn.channel
    conn.send_packet(AdminRcon, command = command)
    conn.send_packet(AdminChat,
        action = Action.CHAT,
        destType = DestType.BROADCAST,
        clientID = ClientID.SERVER,
        message = text)
    conn.send_packet(AdminRcon, command = command)

    if kickDict is not None and kickDict[client.id] >= kickCount:
        text = 'Kicking %s for reaching name change warning count' % client.name
        command = 'kick %s' % client.id
        conn.rcon = conn.channel
        conn.send_packet(AdminChat,
            action = Action.CHAT,
            destType = DestType.BROADCAST,
            clientID = ClientID.SERVER,
            message = text)
        msgChannel(irc, conn.channel, text)
        conn.send_packet(AdminRcon, command = command)

def playercount(conn):
    clients = len(conn.clients)
    if conn.serverinfo.dedicated:
        clients -= 1 # deduct server-client for dedicated servers
    players = 0
    for client in conn.clients.values():
        if not client.play_as == 255:
            players += 1
    spectators = clients - players
    if clients:
        text = 'There are currently %d players and %d spectators, '\
            'making a total of %d clients connected' % (
            (players, spectators, clients))
    else:
        text = 'The server is empty, noone is connected. '\
                    'Feel free to remedy this situation'
    return text

def ofsGetsaveExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Invalid directory in ofs-getsave.py. Please configure it accordingly',
        0x02 :'Couldn\'t save game to disk',
        0x03 :'URL did not lead to a valid savegame. Please check the url in your browser',
    }
    text = texts.get(number, number)
    return text

def ofsStartExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'OpenTTD appears to be running already. Try !apconnect instead',
        0x02 :'OpenTTD was started succesfully, but openttd.pid could not be updated',
        0x03 :'Could not start OpenTTD. Check the configuration of ofs-start.py',
        0x04 :'Started OpenTTD, but couldn\'t read a valid pid from the output. Likely something went wrong',
    }
    text = texts.get(number, number)
    return text

def ofsSvnToBinExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Copying the new executable to the server directory did not succeed',
    }
    text = texts.get(number, number)
    return text

def ofsSvnUpdateExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Source directory does not seem to exist. Please check ofs-svnupdate.py configuration',
        0x02 :'Invalid branch selected in ofs-svnupdate.py\'s configuration. Please use nightlies/trunk, stable or testing',
        0x03 :'Something went wrong executing make or svn. Please run ofs-svnupdate.py manually and see what goes wrong',
    }
    text = texts.get(number, number)
    return text

def ofsTransferSaveExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'File already exists, not transferring savegame',
        0x02 :'Missing either game ID or savegame, or possibly both',
        0x03 :'SSH configuration invalid. Please review ofs-transfersave.py\'s configuration',
        0x04 :'Couldn\'t find file, please specify a valid savegame',
        0x05 :'Failed to trasfer the savegame. Please run ofs-transfersave manually to see what causes this',
    }
    text = texts.get(number, number)
    return text

def refreshConnection(connections, registeredConnections, conn):
    try:
        del registeredConnections[conn.filenumber]
    except KeyError:
        pass
    newconn = conn.copy()
    connections[conn.channel] = newconn
    return newconn

def vehicleCount(companies):
    rail = road = water = air = 0
    for company in companies.values():
        if not company.id == 255:
                rail += company.vehicles.train
                road += (company.vehicles.lorry + company.vehicles.bus)
                water += company.vehicles.ship
                air += company.vehicles.plane
    return (rail, road, water, air)

def companyValue(companies):
    value = loan = income = cargo = 0
    for company in companies.values():
        if not company.id == 255:
            try:
                value += company.economy.history[0].value
            except:
                value = 0
            try:
                loan += company.economy.currentLoan
            except:
                loan = 0
            try:
                income += company.economy.income
            except:
                income = 0
            try:
                cargo += company.economy.deliveredCargo
            except:
                cargo = 0
    return (value, loan, income, cargo)
