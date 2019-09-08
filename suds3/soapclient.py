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

import logging
import queue

from libottdadmin2.trackingclient import TrackingAdminClient
from libottdadmin2.event import Event
from libottdadmin2.enums import UpdateType, UpdateFrequency

from .enums import RconStatus, ConnectionState

class SoapEvents(object):
    def __init__(self):
        self.connected      = Event()
        self.disconnected   = Event()

        self.shutdown       = Event()
        self.new_game       = Event()

        self.new_map        = Event()
        # self.protocol       = Event()

        # self.datechanged    = Event()

        # self.clientinfo     = Event()
        self.clientjoin     = Event()
        self.clientupdate   = Event()
        self.clientquit     = Event()

        # self.companyinfo    = Event()
        # self.companynew     = Event()
        # self.companyupdate  = Event()
        # self.companyremove  = Event()
        # self.companystats   = Event()
        # self.companyeconomy = Event()

        self.chat           = Event()
        self.rcon           = Event()
        self.rconend        = Event()
        self.console        = Event()
        self.cmdlogging     = Event()

        self.pong           = Event()

class SoapClient(TrackingAdminClient):



    # Initialization & miscellanious functions

    def __init__(self, channel, serverid, events = None):
        super(SoapClient, self).__init__(events)
        self.channel = channel
        self.ID = serverid
        self.soapEvents = SoapEvents()
        self._attachEvents()
        self.logger = logging.getLogger('Soap-%s' % self.ID)
        self.logger.setLevel(logging.INFO)

        self.rconCommands = queue.Queue()
        self.rconNick = None
        self.rconResults = {}
        self.rconState = RconStatus.IDLE

        self.connectionstate = ConnectionState.DISCONNECTED
        self.registered = False
        self.filenumber = None

        self.clientPassword = None

    def _attachEvents(self):
        self.events.connected       += self._rcvConnected
        self.events.disconnected    += self._rcvDisconnected

        self.events.shutdown        += self._rcvShutdown
        self.events.new_game        += self._rcvNewGame

        self.events.new_map         += self._rcvNewMap

        self.events.clientjoin      += self._rcvClientJoin
        self.events.clientupdate    += self._rcvClientUpdate
        self.events.clientquit      += self._rcvClientQuit

        self.events.chat            += self._rcvChat
        self.events.rcon            += self._rcvRcon
        self.events.rconend         += self._rcvRconEnd
        self.events.console         += self._rcvConsole
        self.events.cmdlogging      += self._rcvCmdLogging

        self.events.pong            += self._rcvPong

    def copy(self):
        obj = SoapClient(self._channel, self._ID, self.events)
        for prop in self._settable_args:
            setattr(obj, prop, getattr(self, prop, None))
        return obj



    # Insert connection info into parameters

    def _rcvConnected(self):
        self.registered = True
        self.soapEvents.connected(self.channel)

    def _rcvDisconnected(self, canRetry):
        self.registered = False
        self.soapEvents.disconnected(self.channel, canRetry)

    def _rcvShutdown(self):
        self.soapEvents.shutdown(self.channel)

    def _rcvNewGame(self):
        self.soapEvents.new_game(self.channel)

    def _rcvNewMap(self, mapinfo, serverinfo):
        self.soapEvents.new_map(self.channel, mapinfo, serverinfo)

    def _rcvClientJoin(self, client):
        self.soapEvents.clientjoin(self.channel, client)

    def _rcvClientUpdate(self, old, client, changed):
        self.soapEvents.clientupdate(self.channel, old, client, changed)

    def _rcvClientQuit(self, client, errorcode):
        self.soapEvents.clientquit(self.channel, client, errorcode)

    def _rcvChat(self, **kwargs):
        data = dict(list(kwargs.items()))
        data['connChan'] = self.channel
        self.soapEvents.chat(**data)

    def _rcvRcon(self, result, colour):
        self.soapEvents.rcon(self.channel, result, colour)

    def _rcvRconEnd(self, command):
        self.soapEvents.rconend(self.channel, command)

    def _rcvConsole(self, message, origin):
        self.soapEvents.console(self.channel, origin, message)

    def _rcvCmdLogging(self, **kwargs):
        data = dict(list(kwargs.items()))
        data['connChan'] = self.channel
        self.soapEvents.cmdlogging(**data)

    def _rcvPong(self, start, end, delta):
        self.soapEvents.pong(self.channel, start, end, delta)



    # Store some extra info

    _settable_args = TrackingAdminClient._settable_args + ['irc', 'ID', 'channel', 'debugLog']
    _irc = None
    _ID = 'Default'
    _channel = None
    _debugLog = False

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value.lower()

    @property
    def irc(self):
        return self._irc

    @irc.setter
    def irc(self, value):
        self._irc = value

    @property
    def ID(self):
        return self._ID

    @ID.setter
    def ID(self, value):
        self._ID = value.lower()

    @property
    def debugLog(self):
        return self._debugLog

    @debugLog.setter
    def debugLog(self, value):
        self._debugLog = value
        if self._debugLog:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    update_types = [
        (UpdateType.CLIENT_INFO,        UpdateFrequency.AUTOMATIC),
        (UpdateType.COMPANY_INFO,       UpdateFrequency.AUTOMATIC),
        (UpdateType.COMPANY_ECONOMY,    UpdateFrequency.WEEKLY),
        (UpdateType.COMPANY_STATS,      UpdateFrequency.WEEKLY),
        (UpdateType.CHAT,               UpdateFrequency.AUTOMATIC),
        (UpdateType.CONSOLE,            UpdateFrequency.AUTOMATIC),
        (UpdateType.LOGGING,            UpdateFrequency.AUTOMATIC),
        (UpdateType.DATE,               UpdateFrequency.DAILY),
    ]
