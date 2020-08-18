###
# Copyright (c) 2020, Hoaas
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import requests
import datetime
import re
from bs4 import BeautifulSoup
from .codes import states, countries
from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("Corona")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Corona(callbacks.Plugin):
    """Displays current stats of the Coronavirus outbreak"""

    threaded = True

    def __init__(self, irc):
        self.__parent = super(Corona, self)
        self.__parent.__init__(irc)
        self.countries = requests.structures.CaseInsensitiveDict()
        self.states = requests.structures.CaseInsensitiveDict()
        self.updated = None
        self.top = {}
        self.top["countries"] = []
        self.top["states"] = []

    def time_created(self, time):
        """
        Return relative time delta between now and s (dt string).
        """
        d = datetime.datetime.utcnow() - time
        if d.days:
            rel_time = "{:1d}d ago".format(abs(d.days))
        elif d.seconds > 3600:
            rel_time = "{:.1f}h ago".format(round((abs(d.seconds) / 3600), 1))
        elif 60 <= d.seconds < 3600:
            rel_time = "{:.1f}m ago".format(round((abs(d.seconds) / 60), 1))
        else:
            rel_time = "%ss ago" % (abs(d.seconds))
        return rel_time

    def get_data(self):
        headers = {}
        headers["countries"] = []
        headers["states"] = []
        OK = False
        try:
            r = requests.get("https://www.worldometers.info/coronavirus/", timeout=10)
            r.raise_for_status()
            OK = True
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("Corona: error retrieving World data from API: {0}".format(e))
            OK = False
            return
        soup = BeautifulSoup(r.content)
        update = soup.find("div", text=re.compile("Last updated:"))
        update = update.text.split(":", 1)[1].replace("GMT", "UTC").strip()
        updated = datetime.datetime.strptime(update, "%B %d, %Y, %H:%M %Z")
        if OK and not self.updated or OK and updated > self.updated:
            self.updated = updated
            table = soup.find("table", {"id": "main_table_countries_today"})
            headers["countries"] = [header.text for header in table.find_all("th")]
            results = [
                {
                    headers["countries"][i]: cell.text.strip()
                    for i, cell in enumerate(row.find_all("td"))
                }
                for row in table.find_all("tr", {"style": ""})
            ]
            results = sorted(
                results,
                key=lambda k_v: int(re.sub(r"[^\d]", "", k_v["TotalCases"]))
                if len(k_v) == len(headers["countries"])
                else 0,
                reverse=True,
            )
            top = []
            for item in results:
                if len(item) == len(headers["countries"]):
                    i = 0
                    while i < len(headers["countries"]):
                        if i < 8 and not item[headers["countries"][i]]:
                            item[headers["countries"][i]] = "0"
                        elif not item[headers["countries"][i]]:
                            item[headers["countries"][i]] = "N/A"
                        if re.sub(
                            r"[^\w. ]", "", item[headers["countries"][i]]
                        ).isdigit():
                            item[headers["countries"][i]] = int(
                                re.sub(r"[^\d]", "", item[headers["countries"][i]])
                            )
                        i += 1
                    self.countries[item["Country,Other"]] = item
                    rank = results.index(item) - 1
                    self.countries[item["Country,Other"]]["rank"] = rank
                    if rank > 0 and rank <= 10:
                        top.append(
                            "#{0}: \x1F{1}\x1F (\x0307{2}\x03/\x0304{3}\x03)".format(
                                rank,
                                item["Country,Other"],
                                "{:,}".format(item["TotalCases"]),
                                "{:,}".format(item["TotalDeaths"]),
                            )
                        )
            self.top["countries"] = top
            for item in self.countries:
                try:
                    self.countries[item]["ratio_new_cases"] = "{0:.1%}".format(
                        self.countries[item]["NewCases"]
                        / (
                            self.countries[item]["TotalCases"]
                            - self.countries[item]["NewCases"]
                        )
                    )
                except:
                    self.countries[item]["ratio_new_cases"] = "0%"
                try:
                    self.countries[item]["ratio_new_dead"] = "{0:.1%}".format(
                        self.countries[item]["NewDeaths"]
                        / (
                            self.countries[item]["TotalDeaths"]
                            - self.countries[item]["NewDeaths"]
                        )
                    )
                except:
                    self.countries[item]["ratio_new_dead"] = "0%"
                try:
                    self.countries[item]["ratio_dead"] = "{0:.1%}".format(
                        self.countries[item]["TotalDeaths"]
                        / self.countries[item]["TotalCases"]
                    )
                except:
                    self.countries[item]["ratio_dead"] = "N/A"
                try:
                    self.countries[item]["ratio_recovered"] = "{0:.1%}".format(
                        self.countries[item]["TotalRecovered"]
                        / self.countries[item]["TotalCases"]
                    )
                except:
                    self.countries[item]["ratio_recovered"] = "N/A"
                try:
                    self.countries[item]["mild"] = (
                        self.countries[item]["ActiveCases"]
                        - self.countries[item]["Serious,Critical"]
                    )
                except:
                    self.countries[item]["mild"] = "N/A"
                try:
                    self.countries[item]["ratio_mild"] = "{0:.1%}".format(
                        self.countries[item]["mild"]
                        / self.countries[item]["ActiveCases"]
                    )
                except:
                    self.countries[item]["ratio_mild"] = "N/A"
                try:
                    self.countries[item]["ratio_serious"] = "{0:.1%}".format(
                        self.countries[item]["Serious,Critical"]
                        / self.countries[item]["ActiveCases"]
                    )
                except:
                    self.countries[item]["ratio_serious"] = "N/A"
                for value in self.countries[item]:
                    if isinstance(self.countries[item][value], int):
                        self.countries[item][value] = "{:,}".format(
                            self.countries[item][value]
                        )
            try:
                r = requests.get(
                    "https://www.worldometers.info/coronavirus/country/us/", timeout=10
                )
                r.raise_for_status()
                OK = True
            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
            ) as e:
                log.error("Corona: error retrieving USA data from API: {0}".format(e))
                OK = False
                return
            if OK:
                soup = BeautifulSoup(r.content)
                table = soup.find("table", {"id": "usa_table_countries_today"})
                headers["states"] = [header.text for header in table.find_all("th")]
                results = [
                    {
                        headers["states"][i]: cell.text.strip()
                        for i, cell in enumerate(row.find_all("td"))
                    }
                    for row in table.find_all("tr")
                ]
                results = sorted(
                    results,
                    key=lambda k_v: int(re.sub(r"[^\d]", "", k_v["TotalCases"]))
                    if len(k_v) == len(headers["states"])
                    else 0,
                    reverse=True,
                )
                top = []
                for item in results:
                    if len(item) == len(headers["states"]):
                        i = 0
                        while i < len(headers["states"]):
                            if not item[headers["states"][i]]:
                                item[headers["states"][i]] = "0"
                            if re.sub(
                                r"[^\w. ]", "", item[headers["states"][i]]
                            ).isdigit():
                                item[headers["states"][i]] = int(
                                    re.sub(r"[^\d]", "", item[headers["states"][i]])
                                )
                            i += 1
                        self.states[item["USAState"]] = item
                        rank = results.index(item)
                        self.states[item["USAState"]]["rank"] = rank
                        if rank > 0 and rank <= 10:
                            top.append(
                                "#{0}: \x1F{1}\x1F (\x0307{2}\x03/\x0304{3}\x03)"
                                .format(
                                    rank,
                                    item["USAState"],
                                    "{:,}".format(item["TotalCases"]),
                                    "{:,}".format(item["TotalDeaths"]),
                                )
                            )
                self.top["states"] = top
                for item in self.states:
                    try:
                        self.states[item]["ratio_new_cases"] = "{0:.1%}".format(
                            self.states[item]["NewCases"]
                            / (
                                self.states[item]["TotalCases"]
                                - self.states[item]["NewCases"]
                            )
                        )
                    except:
                        self.states[item]["ratio_new_cases"] = "0%"
                    try:
                        self.states[item]["ratio_new_dead"] = "{0:.1%}".format(
                            self.states[item]["NewDeaths"]
                            / (
                                self.states[item]["TotalDeaths"]
                                - self.states[item]["NewDeaths"]
                            )
                        )
                    except:
                        self.states[item]["ratio_new_dead"] = "0%"
                    try:
                        self.states[item]["ratio_dead"] = "{0:.1%}".format(
                            self.states[item]["TotalDeaths"]
                            / self.states[item]["TotalCases"]
                        )
                    except:
                        self.states[item]["ratio_dead"] = "N/A"
                    for value in self.states[item]:
                        if isinstance(self.states[item][value], int):
                            self.states[item][value] = "{:,}".format(
                                self.states[item][value]
                            )
                return True
            else:
                log.error("Corona: unable to retrieve latest USA data")
                return
        elif len(self.countries) > 0 and len(self.states) > 0:
            log.info("Corona: data not yet updated, using cache")
            return True
        else:
            log.error("Corona: Error. Unable to retrieve data.")
            return

    @wrap([getopts({"top10": ""}), optional("text")])
    def corona(self, irc, msg, args, optlist, search):
        """[region]
        Return Coronavirus statistics from https://www.worldometers.info/coronavirus/.
        Search accepts full country/state names or ISO 3166-1 alpha-2 (two character)
        country abbreviations and US Postal (two character) state abbreviations.
        Invalid region names or search terms without data return global results.
        """
        optlist = dict(optlist)
        if "top10" in optlist:
            self.top10(irc, msg, args, None)
            return
        if search:
            search = search.strip()
        if not self.get_data():
            irc.reply(
                "Error retrieving data from https://www.worldometers.info/coronavirus/"
            )
            return
        if search and len(search) == 2:
            if self.registryValue("countryFirst", msg.channel):
                try:
                    search = countries[search.upper()]
                except KeyError:
                    try:
                        search = states[search.upper()]
                    except KeyError:
                        pass
            else:
                try:
                    search = states[search.upper()]
                except KeyError:
                    try:
                        search = countries[search.upper()]
                    except KeyError:
                        pass

        def reply_country():
            irc.reply(
                "\x02\x1F{0}\x1F: World Rank: #{1} | Cases: \x0307{2}\x03 "
                "(\x0307+{3}\x03) (\x0307+{4}\x03) | Deaths: \x0304{5}\x03 "
                "(\x0304{6}\x03) (\x0304+{7}\x03) (\x0304+{8}\x03) | Recovered: "
                "\x0309{9}\x03 (\x0309{10}\x03) | Active: \x0307{11}\x03 "
                "(\x0310{12}\x03 Mild) (\x0313{13}\x03 Serious) (\x0310{14}\x03/"
                "\x0313{15}\x03) | Cases/1M: \x0307{16}\x03 | Deaths/1M: \x0304{17}"
                "\x03 | Updated: {18}".format(
                    self.countries[search]["Country,Other"],
                    self.countries[search]["rank"],
                    self.countries[search]["TotalCases"],
                    self.countries[search]["NewCases"],
                    self.countries[search]["ratio_new_cases"],
                    self.countries[search]["TotalDeaths"],
                    self.countries[search]["ratio_dead"],
                    self.countries[search]["NewDeaths"],
                    self.countries[search]["ratio_new_dead"],
                    self.countries[search]["TotalRecovered"],
                    self.countries[search]["ratio_recovered"],
                    self.countries[search]["ActiveCases"],
                    self.countries[search]["mild"],
                    self.countries[search]["Serious,Critical"],
                    self.countries[search]["ratio_mild"],
                    self.countries[search]["ratio_serious"],
                    self.countries[search]["Tot\xa0Cases/1M pop"],
                    self.countries[search]["Deaths/1M pop"],
                    self.time_created(self.updated),
                )
            )

        def reply_state():
            irc.reply(
                "\x02\x1F{0}\x1F: USA Rank: #{1} | Cases: \x0307{2}\x03 "
                "(\x0307+{3}\x03) (\x0307+{4}\x03) | Deaths: \x0304{5}\x03 "
                "(\x0304{6}\x03) (\x0304+{7}\x03) (\x0304+{8}\x03) | Active: "
                "\x0307{9}\x03 | Cases/1M: \x0307{10}\x03 | Deaths/1M: "
                "\x0304{11}\x03 | Updated: {12}".format(
                    self.states[search]["USAState"],
                    self.states[search]["rank"],
                    self.states[search]["TotalCases"],
                    self.states[search]["NewCases"],
                    self.states[search]["ratio_new_cases"],
                    self.states[search]["TotalDeaths"],
                    self.states[search]["ratio_dead"],
                    self.states[search]["NewDeaths"],
                    self.states[search]["ratio_new_dead"],
                    self.states[search]["ActiveCases"],
                    self.states[search]["Tot\xa0Cases/1M pop"],
                    self.states[search]["Deaths/1M pop"],
                    self.time_created(self.updated),
                )
            )

        def reply_global():
            irc.reply(
                "\x02\x1F{0}\x1F: Cases: \x0307{1}\x03 (\x0307+{2}\x03) "
                "(\x0307+{3}\x03) | Deaths: \x0304{4}\x03 (\x0304{5}\x03) "
                "(\x0304+{6}\x03) (\x0304+{7}\x03) | Recovered: \x0309{8}\x03 "
                "(\x0309{9}\x03) | Active: \x0307{10}\x03 (\x0310{11}\x03 Mild) "
                "(\x0313{12}\x03 Serious) (\x0310{13}\x03/\x0313{14}\x03) | "
                "Cases/1M: \x0307{15}\x03 | Deaths/1M: \x0304{16}\x03 | "
                "Updated: {17}".format(
                    "Global",
                    self.countries[list(self.countries)[0]]["TotalCases"],
                    self.countries[list(self.countries)[0]]["NewCases"],
                    self.countries[list(self.countries)[0]]["ratio_new_cases"],
                    self.countries[list(self.countries)[0]]["TotalDeaths"],
                    self.countries[list(self.countries)[0]]["ratio_dead"],
                    self.countries[list(self.countries)[0]]["NewDeaths"],
                    self.countries[list(self.countries)[0]]["ratio_new_dead"],
                    self.countries[list(self.countries)[0]]["TotalRecovered"],
                    self.countries[list(self.countries)[0]]["ratio_recovered"],
                    self.countries[list(self.countries)[0]]["ActiveCases"],
                    self.countries[list(self.countries)[0]]["mild"],
                    self.countries[list(self.countries)[0]]["Serious,Critical"],
                    self.countries[list(self.countries)[0]]["ratio_mild"],
                    self.countries[list(self.countries)[0]]["ratio_serious"],
                    self.countries[list(self.countries)[0]]["Tot\xa0Cases/1M pop"],
                    self.countries[list(self.countries)[0]]["Deaths/1M pop"],
                    self.time_created(self.updated),
                )
            )

        if self.registryValue("countryFirst", msg.channel):
            if search and self.countries.get(search):
                reply_country()
            elif search and self.states.get(search):
                reply_state()
            else:
                reply_global()
        else:
            if search and self.states.get(search):
                reply_state()
            elif search and self.countries.get(search):
                reply_country()
            else:
                reply_global()

    @wrap([optional("text")])
    def top10(self, irc, msg, args, search):
        """[usa|global]
        Return the countries with the most confirmed cases. Valid options are USA or
        global. Returns global list if no option given.
        """
        if not self.get_data():
            irc.reply(
                "Error retrieving data from https://www.worldometers.info/coronavirus/"
            )
            return
        if search:
            search = search.strip().lower()
        else:
            search = "global"
        if not search.startswith("us"):
            irc.reply(
                "{0} | Updated: {1}".format(
                    ", ".join(self.top["countries"]), self.time_created(self.updated)
                )
            )
        else:
            irc.reply(
                "{0} | Updated: {1}".format(
                    ", ".join(self.top["states"]), self.time_created(self.updated)
                )
            )


Class = Corona
