###
# Copyright (c) 2018, cottongin
# All rights reserved.
# see LICENSE.txt
#
###

import requests

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("AzuraCast")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class AzuraCast(callbacks.Plugin):
    """Plugin for the AzuraCast API"""

    threaded = True

    def __init__(self, irc):
        self.__parent = super(AzuraCast, self)
        self.__parent.__init__(irc)

        self.BASE_API = self.registryValue("AzuraAPI")
        self.PUB_URL = self.registryValue("PublicURL") + "#{name}"

    def _fetchURL(self, url, headers=None):
        return requests.get(url, headers=headers).json()

    def _parseData(self, data):
        stations = {}
        for station in data:
            tmp_dict = {}
            code = station["station"]["shortcode"]
            tmp_dict["id"] = station["station"]["id"]
            tmp_dict["name"] = station["station"]["name"]
            tmp_dict["description"] = station["station"]["description"]
            tmp_dict["player_url"] = (
                station["station"]["listen_url"].split("?")[0]
                if station["station"]["is_public"]
                else ""
            )
            tmp_dict["public_url"] = (
                self.PUB_URL.format(name=code)
                if station["station"]["is_public"]
                else ""
            )
            tmp_dict["listeners"] = station["listeners"]
            tmp_dict["nowplaying"] = station["now_playing"]
            stations[code] = tmp_dict
        return stations

    @wrap([getopts({"station": "somethingWithoutSpaces"})])
    def nowplaying(self, irc, msg, args, options):
        """
        Fetches what is now playing
        """
        options = dict(options)
        station = options.get("station")
        url = self.BASE_API + "nowplaying"

        data = self._fetchURL(url)

        if not data:
            irc.reply("ERROR: Something went wrong fetching data @ {}".format(url))
            return

        data = self._parseData(data)

        output = []
        if station:
            # one station only
            d = data.get(station.lower())
            prefix = ircutils.bold("Now Playing on {}:".format(d["name"]))
            album = (
                " [{}]".format(d["nowplaying"]["song"]["album"])
                if d["nowplaying"]["song"]["album"]
                else ""
            )
            url = " | {}".format(d["public_url"]) if d["public_url"] else ""
            np = "{}".format(d["nowplaying"]["song"]["text"])
            listeners = " | Listeners: {}".format(d["listeners"]["current"])
            listen = " | Audio player link: {}/public/{}/playlist/pls".format(
                self.BASE_API.replace("/api/", ""), d["id"]
            )
            string = "{} {}{}{}{}{}".format(prefix, np, album, listeners, url, listen)
            output.append(string)
        else:
            # all stations?
            for s, d in data.items():
                prefix = ircutils.bold("Now Playing on {}:".format(d["name"]))
                album = (
                    " [{}]".format(d["nowplaying"]["song"]["album"])
                    if d["nowplaying"]["song"]["album"]
                    else ""
                )
                url = " | {}".format(d["public_url"]) if d["public_url"] else ""
                np = "{}".format(d["nowplaying"]["song"]["text"])
                listeners = " | Listeners: {}".format(d["listeners"]["current"])
                listen = " | Audio player link: {}/public/{}/playlist/pls".format(
                    self.BASE_API.replace("/api/", ""), d["id"]
                )
                string = "{} {}{}{}{}{}".format(
                    prefix, np, album, listeners, url, listen
                )
                output.append(string)

        for string in output:
            irc.reply(string)

        return

    @wrap([getopts({"station": "somethingWithoutSpaces"})])
    def listeners(self, irc, msg, args, options):
        """
        Fetches listeners
        """
        options = dict(options)
        station = options.get("station")
        url = self.BASE_API + "nowplaying"

        data = self._fetchURL(url)

        if not data:
            irc.reply("ERROR: Something went wrong fetching data @ {}".format(url))
            return

        data = self._parseData(data)

        output = []
        if station:
            # one station only
            d = data.get(station.lower())
            count = d["listeners"]["current"]
            if count > 1 and count != 0:
                cur = "are currently"
                plr = " {} listeners ".format(ircutils.bold(count))
            elif count == 1:
                cur = "is currently"
                plr = " {} listener ".format(ircutils.bold(count))
            else:
                cur = "are no listeners"
                plr = " "
            string = "There {}{}on {}".format(cur, plr, ircutils.bold(d["name"]))
            output.append(string)
        else:
            # all stations?
            for s, d in data.items():
                count = d["listeners"]["current"]
                if count > 1 and count != 0:
                    cur = "are currently"
                    plr = " {} listeners ".format(ircutils.bold(count))
                elif count == 1:
                    cur = "is currently"
                    plr = " {} listener ".format(ircutils.bold(count))
                else:
                    cur = "are no listeners"
                    plr = " "
                string = "There {}{}on {}".format(cur, plr, ircutils.bold(d["name"]))
                output.append(string)

        for string in output:
            irc.reply(string)

        return


Class = AzuraCast


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
