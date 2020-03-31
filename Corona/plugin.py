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
from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("Corona")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

countries = {
    "AF": "AFGHANISTAN",
    "AX": "ÅLAND ISLANDS",
    "AL": "ALBANIA",
    "DZ": "ALGERIA",
    "AS": "AMERICAN SAMOA",
    "AD": "ANDORRA",
    "AO": "ANGOLA",
    "AI": "ANGUILLA",
    "AQ": "ANTARCTICA",
    "AG": "ANTIGUA AND BARBUDA",
    "AR": "ARGENTINA",
    "AM": "ARMENIA",
    "AW": "ARUBA",
    "AU": "AUSTRALIA",
    "AT": "AUSTRIA",
    "AZ": "AZERBAIJAN",
    "BS": "BAHAMAS",
    "BH": "BAHRAIN",
    "BD": "BANGLADESH",
    "BB": "BARBADOS",
    "BY": "BELARUS",
    "BE": "BELGIUM",
    "BZ": "BELIZE",
    "BJ": "BENIN",
    "BM": "BERMUDA",
    "BT": "BHUTAN",
    "BO": "BOLIVIA",
    "BQ": "BONAIRE",
    "BA": "BOSNIA AND HERZEGOVINA",
    "BW": "BOTSWANA",
    "BV": "BOUVET ISLAND",
    "BR": "BRAZIL",
    "IO": "BRITISH INDIAN OCEAN TERRITORY",
    "BN": "BRUNEI",
    "BG": "BULGARIA",
    "BF": "BURKINA FASO",
    "BI": "BURUNDI",
    "KH": "CAMBODIA",
    "CM": "CAMEROON",
    "CA": "CANADA",
    "CV": "CABO VERDE",
    "KY": "CAYMAN ISLANDS",
    "CF": "CAR",
    "TD": "CHAD",
    "CL": "CHILE",
    "CN": "CHINA",
    "CX": "CHRISTMAS ISLAND",
    "CC": "COCOS ISLANDS",
    "CO": "COLOMBIA",
    "KM": "COMOROS",
    "CG": "CONGO",
    "CD": "CONGO",
    "CK": "COOK ISLANDS",
    "CR": "COSTA RICA",
    "CI": "CÔTE D'IVOIRE",
    "HR": "CROATIA",
    "CU": "CUBA",
    "CW": "CURAÇAO",
    "CY": "CYPRUS",
    "CZ": "CZECHIA",
    "DK": "DENMARK",
    "DJ": "DJIBOUTI",
    "DM": "DOMINICA",
    "DO": "DOMINICAN REPUBLIC",
    "EC": "ECUADOR",
    "EG": "EGYPT",
    "SV": "EL SALVADOR",
    "GQ": "EQUATORIAL GUINEA",
    "ER": "ERITREA",
    "EE": "ESTONIA",
    "ET": "ETHIOPIA",
    "FK": "FALKLAND ISLANDS",
    "FO": "FAROE ISLANDS",
    "FJ": "FIJI",
    "FI": "FINLAND",
    "FR": "FRANCE",
    "GF": "FRENCH GUIANA",
    "PF": "FRENCH POLYNESIA",
    "TF": "FRENCH SOUTHERN TERRITORIES",
    "GA": "GABON",
    "GM": "GAMBIA",
    "GE": "GEORGIA",
    "DE": "GERMANY",
    "GH": "GHANA",
    "GI": "GIBRALTAR",
    "GR": "GREECE",
    "GL": "GREENLAND",
    "GD": "GRENADA",
    "GP": "GUADELOUPE",
    "GU": "GUAM",
    "GT": "GUATEMALA",
    "GG": "GUERNSEY",
    "GN": "GUINEA",
    "GW": "GUINEA",
    "GY": "GUYANA",
    "HT": "HAITI",
    "HM": "HEARD ISLAND AND MCDONALD ISLANDS",
    "VA": "VATICAN CITY",
    "HN": "HONDURAS",
    "HK": "HONG KONG",
    "HU": "HUNGARY",
    "IS": "ICELAND",
    "IN": "INDIA",
    "ID": "INDONESIA",
    "IR": "IRAN",
    "IQ": "IRAQ",
    "IE": "IRELAND",
    "IM": "ISLE OF MAN",
    "IL": "ISRAEL",
    "IT": "ITALY",
    "JM": "JAMAICA",
    "JP": "JAPAN",
    "JE": "JERSEY",
    "JO": "JORDAN",
    "KZ": "KAZAKHSTAN",
    "KE": "KENYA",
    "KI": "KIRIBATI",
    "KP": "N. KOREA",
    "KR": "S. KOREA",
    "KW": "KUWAIT",
    "KG": "KYRGYZSTAN",
    "LA": "LAOS",
    "LV": "LATVIA",
    "LB": "LEBANON",
    "LS": "LESOTHO",
    "LR": "LIBERIA",
    "LY": "LIBYA",
    "LI": "LIECHTENSTEIN",
    "LT": "LITHUANIA",
    "LU": "LUXEMBOURG",
    "MO": "MACAO",
    "MK": "NORTH MACEDONIA",
    "MG": "MADAGASCAR",
    "MW": "MALAWI",
    "MY": "MALAYSIA",
    "MV": "MALDIVES",
    "ML": "MALI",
    "MT": "MALTA",
    "MH": "MARSHALL ISLANDS",
    "MQ": "MARTINIQUE",
    "MR": "MAURITANIA",
    "MU": "MAURITIUS",
    "YT": "MAYOTTE",
    "MX": "MEXICO",
    "FM": "MICRONESIA",
    "MD": "MOLDOVA",
    "MC": "MONACO",
    "MN": "MONGOLIA",
    "ME": "MONTENEGRO",
    "MS": "MONTSERRAT",
    "MA": "MOROCCO",
    "MZ": "MOZAMBIQUE",
    "MM": "MYANMAR",
    "NA": "NAMIBIA",
    "NR": "NAURU",
    "NP": "NEPAL",
    "NL": "NETHERLANDS",
    "NC": "NEW CALEDONIA",
    "NZ": "NEW ZEALAND",
    "NI": "NICARAGUA",
    "NE": "NIGER",
    "NG": "NIGERIA",
    "NU": "NIUE",
    "NF": "NORFOLK ISLAND",
    "MP": "NORTHERN MARIANA ISLANDS",
    "NO": "NORWAY",
    "OM": "OMAN",
    "PK": "PAKISTAN",
    "PW": "PALAU",
    "PS": "PALESTINE",
    "PA": "PANAMA",
    "PG": "PAPUA NEW GUINEA",
    "PY": "PARAGUAY",
    "PE": "PERU",
    "PH": "PHILIPPINES",
    "PN": "PITCAIRN",
    "PL": "POLAND",
    "PT": "PORTUGAL",
    "PR": "PUERTO RICO",
    "QA": "QATAR",
    "RE": "RÉUNION",
    "RO": "ROMANIA",
    "RU": "RUSSIA",
    "RW": "RWANDA",
    "BL": "ST. BARTH",
    "SH": "SAINT HELENA",
    "KN": "SAINT KITTS AND NEVIS",
    "LC": "SAINT LUCIA",
    "MF": "SAINT MARTIN",
    "PM": "SAINT PIERRE AND MIQUELON",
    "VC": "ST. VINCENT GRENADINES",
    "WS": "SAMOA",
    "SM": "SAN MARINO",
    "ST": "SAO TOME AND PRINCIPE",
    "SA": "SAUDI ARABIA",
    "SN": "SENEGAL",
    "RS": "SERBIA",
    "SC": "SEYCHELLES",
    "SL": "SIERRA LEONE",
    "SG": "SINGAPORE",
    "SX": "SINT MAARTEN",
    "SK": "SLOVAKIA",
    "SI": "SLOVENIA",
    "SB": "SOLOMON ISLANDS",
    "SO": "SOMALIA",
    "ZA": "SOUTH AFRICA",
    "GS": "GEORGIA",
    "SS": "SUDAN",
    "ES": "SPAIN",
    "LK": "SRI LANKA",
    "SD": "SUDAN",
    "SR": "SURINAME",
    "SJ": "SVALBARD AND JAN MAYEN",
    "SZ": "SWAZILAND",
    "SE": "SWEDEN",
    "CH": "SWITZERLAND",
    "SY": "SYRIA",
    "TW": "TAIWAN",
    "TJ": "TAJIKISTAN",
    "TZ": "TANZANIA",
    "TH": "THAILAND",
    "TL": "TIMOR-LESTE",
    "TG": "TOGO",
    "TK": "TOKELAU",
    "TO": "TONGA",
    "TT": "TRINIDAD AND TOBAGO",
    "TN": "TUNISIA",
    "TR": "TURKEY",
    "TM": "TURKMENISTAN",
    "TC": "TURKS AND CAICOS",
    "TV": "TUVALU",
    "UG": "UGANDA",
    "UA": "UKRAINE",
    "AE": "UNITED ARAB EMIRATES",
    "GB": "UK",
    "UK": "UK",
    "US": "USA",
    "UM": "UNITED STATES MINOR OUTLYING ISLANDS",
    "UY": "URUGUAY",
    "UZ": "UZBEKISTAN",
    "VU": "VANUATU",
    "VE": "VENEZUELA",
    "VN": "VIETNAM",
    "VG": "U.S. VIRGIN ISLANDS",
    "VI": "U.S. VIRGIN ISLANDS",
    "WF": "WALLIS AND FUTUNA",
    "EH": "WESTERN SAHARA",
    "YE": "YEMEN",
    "ZM": "ZAMBIA",
    "ZW": "ZIMBABWE",
}

states = {
    "AK": "ALASKA",
    "AL": "ALABAMA",
    "AR": "ARKANSAS",
    "AS": "AMERICAN SAMOA",
    "AZ": "ARIZONA",
    "CA": "CALIFORNIA",
    "CO": "COLORADO",
    "CT": "CONNECTICUT",
    "DC": "DISTRICT OF COLUMBIA",
    "DE": "DELAWARE",
    "FL": "FLORIDA",
    "GA": "GEORGIA",
    "GU": "GUAM",
    "HI": "HAWAII",
    "IA": "IOWA",
    "ID": "IDAHO",
    "IL": "ILLINOIS",
    "IN": "INDIANA",
    "KS": "KANSAS",
    "KY": "KENTUCKY",
    "LA": "LOUISIANA",
    "MA": "MASSACHUSETTS",
    "MD": "MARYLAND",
    "ME": "MAINE",
    "MI": "MICHIGAN",
    "MN": "MINNESOTA",
    "MO": "MISSOURI",
    "MP": "NORTHERN MARIANA ISLANDS",
    "MS": "MISSISSIPPI",
    "MT": "MONTANA",
    "NA": "NATIONAL",
    "NC": "NORTH CAROLINA",
    "ND": "NORTH DAKOTA",
    "NE": "NEBRASKA",
    "NH": "NEW HAMPSHIRE",
    "NJ": "NEW JERSEY",
    "NM": "NEW MEXICO",
    "NV": "NEVADA",
    "NY": "NEW YORK",
    "OH": "OHIO",
    "OK": "OKLAHOMA",
    "OR": "OREGON",
    "PA": "PENNSYLVANIA",
    "PR": "PUERTO RICO",
    "RI": "RHODE ISLAND",
    "SC": "SOUTH CAROLINA",
    "SD": "SOUTH DAKOTA",
    "TN": "TENNESSEE",
    "TX": "TEXAS",
    "UT": "UTAH",
    "VA": "VIRGINIA",
    "VI": "VIRGIN ISLANDS",
    "VT": "VERMONT",
    "WA": "WASHINGTON",
    "WI": "WISCONSIN",
    "WV": "WEST VIRGINIA",
    "WY": "WYOMING",
}


class Corona(callbacks.Plugin):
    """Displays current stats of the Coronavirus outbreak"""

    threaded = True

    def __init__(self, irc):
        self.__parent = super(Corona, self)
        self.__parent.__init__(irc)
        self.countries = requests.structures.CaseInsensitiveDict()
        self.states = requests.structures.CaseInsensitiveDict()
        today = datetime.datetime.utcnow()
        self.updated = today - datetime.timedelta(days=1)
        self.headers = {}
        self.top = {}
        self.headers["countries"] = []
        self.headers["states"] = []
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
        updated = soup.find("div", text=re.compile("Last updated:"))
        updated = updated.text.split(":", 1)[1].replace("GMT", "").strip()
        updated = datetime.datetime.strptime(updated, "%B %d, %Y, %H:%M")
        if OK and updated > self.updated:
            self.updated = updated
            table = soup.find("table", {"id": "main_table_countries_today"})
            self.headers["countries"] = [header.text for header in table.find_all("th")]
            results = [
                {
                    self.headers["countries"][i]: cell.text.strip()
                    for i, cell in enumerate(row.find_all("td"))
                }
                for row in table.find_all("tr")
            ]
            results = sorted(
                results,
                key=lambda k_v: int(
                    re.sub("[^\d]", "", k_v[self.headers["countries"][1]])
                )
                if len(k_v) == len(self.headers["countries"])
                else 0,
                reverse=True,
            )
            top = []
            for item in results:
                if len(item) == len(self.headers["countries"]):
                    i = 0
                    while i < len(self.headers["countries"]):
                        if i < 7 and not item[self.headers["countries"][i]]:
                            item[self.headers["countries"][i]] = "0"
                        elif not item[self.headers["countries"][i]]:
                            item[self.headers["countries"][i]] = "N/A"
                        if re.sub(
                            "[^\w ]", "", item[self.headers["countries"][i]]
                        ).isdigit():
                            item[self.headers["countries"][i]] = int(
                                re.sub("[^\d]", "", item[self.headers["countries"][i]])
                            )
                        i += 1
                    self.countries[item[self.headers["countries"][0]]] = item
                    rank = results.index(item)
                    self.countries[item[self.headers["countries"][0]]]["rank"] = rank
                    if rank > 0 and rank <= 10:
                        top.append(
                            "#{0}: \x1F{1}\x1F (\x0307{2}\x03/\x0304{3}\x03)".format(
                                rank,
                                item[self.headers["countries"][0]],
                                "{:,}".format(item[self.headers["countries"][1]]),
                                "{:,}".format(item[self.headers["countries"][2]]),
                            )
                        )
            self.top["countries"] = top
            for item in self.countries:
                try:
                    self.countries[item]["ratio_new_cases"] = "{0:.1%}".format(
                        self.countries[item][self.headers["countries"][2]]
                        / (
                            self.countries[item][self.headers["countries"][1]]
                            - self.countries[item][self.headers["countries"][2]]
                        )
                    )
                except:
                    self.countries[item]["ratio_new_cases"] = "0%"
                try:
                    self.countries[item]["ratio_new_dead"] = "{0:.1%}".format(
                        self.countries[item][self.headers["countries"][4]]
                        / (
                            self.countries[item][self.headers["countries"][3]]
                            - self.countries[item][self.headers["countries"][4]]
                        )
                    )
                except:
                    self.countries[item]["ratio_new_dead"] = "0%"
                try:
                    self.countries[item]["ratio_dead"] = "{0:.1%}".format(
                        self.countries[item][self.headers["countries"][3]]
                        / self.countries[item][self.headers["countries"][1]]
                    )
                except:
                    self.countries[item]["ratio_dead"] = "N/A"
                try:
                    self.countries[item]["ratio_recovered"] = "{0:.1%}".format(
                        self.countries[item][self.headers["countries"][5]]
                        / self.countries[item][self.headers["countries"][1]]
                    )
                except:
                    self.countries[item]["ratio_recovered"] = "N/A"
                try:
                    self.countries[item]["mild"] = (
                        self.countries[item][self.headers["countries"][6]]
                        - self.countries[item][self.headers["countries"][7]]
                    )
                except:
                    self.countries[item]["mild"] = "N/A"
                try:
                    self.countries[item]["ratio_mild"] = "{0:.1%}".format(
                        self.countries[item]["mild"]
                        / self.countries[item][self.headers["countries"][6]]
                    )
                except:
                    self.countries[item]["ratio_mild"] = "N/A"
                try:
                    self.countries[item]["ratio_serious"] = "{0:.1%}".format(
                        self.countries[item][self.headers["countries"][7]]
                        / self.countries[item][self.headers["countries"][6]]
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
                self.headers["states"] = [
                    header.text for header in table.find_all("th")
                ]
                results = [
                    {
                        self.headers["states"][i]: cell.text.strip()
                        for i, cell in enumerate(row.find_all("td"))
                    }
                    for row in table.find_all("tr")
                ]
                results = sorted(
                    results,
                    key=lambda k_v: int(
                        re.sub("[^\d]", "", k_v[self.headers["states"][1]])
                    )
                    if len(k_v) == len(self.headers["states"])
                    else 0,
                    reverse=True,
                )
                top = []
                for item in results:
                    if len(item) == len(self.headers["states"]):
                        i = 0
                        while i < len(self.headers["states"]):
                            if not item[self.headers["states"][i]]:
                                item[self.headers["states"][i]] = "0"
                            if re.sub(
                                "[^\w ]", "", item[self.headers["states"][i]]
                            ).isdigit():
                                item[self.headers["states"][i]] = int(
                                    re.sub("[^\d]", "", item[self.headers["states"][i]])
                                )
                            i += 1
                        self.states[item[self.headers["states"][0]]] = item
                        rank = results.index(item)
                        self.states[item[self.headers["states"][0]]]["rank"] = rank
                        if rank > 0 and rank <= 10:
                            top.append(
                                "#{0}: \x1F{1}\x1F (\x0307{2}\x03/\x0304{3}\x03)".format(
                                    rank,
                                    item[self.headers["states"][0]],
                                    "{:,}".format(item[self.headers["states"][1]]),
                                    "{:,}".format(item[self.headers["states"][2]]),
                                )
                            )
                self.top["states"] = top
                for item in self.states:
                    try:
                        self.states[item]["ratio_new_cases"] = "{0:.1%}".format(
                            self.states[item][self.headers["states"][2]]
                            / (
                                self.states[item][self.headers["states"][1]]
                                - self.states[item][self.headers["states"][2]]
                            )
                        )
                    except:
                        self.states[item]["ratio_new_cases"] = "0%"
                    try:
                        self.states[item]["ratio_new_dead"] = "{0:.1%}".format(
                            self.states[item][self.headers["states"][4]]
                            / (
                                self.states[item][self.headers["states"][3]]
                                - self.states[item][self.headers["states"][4]]
                            )
                        )
                    except:
                        self.states[item]["ratio_new_dead"] = "0%"
                    try:
                        self.states[item]["ratio_dead"] = "{0:.1%}".format(
                            self.states[item][self.headers["states"][3]]
                            / self.states[item][self.headers["states"][1]]
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
        if search and self.countries.get(search):
            irc.reply(
                "\x02\x1F{0}\x1F: World Rank: #{1} | Cases: \x0307{2}\x03 "
                "(\x0307+{3}\x03) (\x0307+{4}\x03) | Deaths: \x0304{5}\x03 "
                "(\x0304+{6}\x03) (\x0304+{7}\x03) (\x0304{8}\x03) | Recovered: "
                "\x0309{9}\x03 (\x0309{10}\x03) | Active: \x0307{11}\x03 "
                "(\x0310{12}\x03 Mild) (\x0313{13}\x03 Serious) (\x0310{14}\x03/"
                "\x0313{15}\x03) | Cases/1M: \x0307{16}\x03 | Deaths/1M: \x0304{17}"
                "\x03 | 1st Case: {18} | Updated: {19}".format(
                    self.countries[search][self.headers["countries"][0]],
                    self.countries[search]["rank"],
                    self.countries[search][self.headers["countries"][1]],
                    self.countries[search][self.headers["countries"][2]],
                    self.countries[search]["ratio_new_cases"],
                    self.countries[search][self.headers["countries"][3]],
                    self.countries[search][self.headers["countries"][4]],
                    self.countries[search]["ratio_new_dead"],
                    self.countries[search]["ratio_dead"],
                    self.countries[search][self.headers["countries"][5]],
                    self.countries[search]["ratio_recovered"],
                    self.countries[search][self.headers["countries"][6]],
                    self.countries[search]["mild"],
                    self.countries[search][self.headers["countries"][7]],
                    self.countries[search]["ratio_mild"],
                    self.countries[search]["ratio_serious"],
                    self.countries[search][self.headers["countries"][8]],
                    self.countries[search][self.headers["countries"][9]],
                    self.countries[search][self.headers["countries"][10]],
                    self.time_created(self.updated),
                )
            )
        elif search and self.states.get(search):
            irc.reply(
                "\x02\x1F{0}\x1F: USA Rank: #{1} | Cases: \x0307{2}\x03 "
                "(\x0307+{3}\x03) (\x0307+{4}\x03) | Deaths: \x0304{5}\x03 "
                "(\x0304+{6}\x03) (\x0304+{7}\x03) (\x0304{8}\x03) | Active: "
                "\x0307{9}\x03 | Updated: {10}".format(
                    self.states[search][self.headers["states"][0]],
                    self.states[search]["rank"],
                    self.states[search][self.headers["states"][1]],
                    self.states[search][self.headers["states"][2]],
                    self.states[search]["ratio_new_cases"],
                    self.states[search][self.headers["states"][3]],
                    self.states[search][self.headers["states"][4]],
                    self.states[search]["ratio_new_dead"],
                    self.states[search]["ratio_dead"],
                    self.states[search][self.headers["states"][5]],
                    self.time_created(self.updated),
                )
            )
        else:
            irc.reply(
                "\x02\x1F{0}\x1F: Cases: \x0307{1}\x03 (\x0307+{2}\x03) "
                "(\x0307+{3}\x03) | Deaths: \x0304{4}\x03 (\x0304+{5}\x03) "
                "(\x0304+{6}\x03) (\x0304{7}\x03) | Recovered: \x0309{8}\x03 "
                "(\x0309{9}\x03) | Active: \x0307{10}\x03 (\x0310{11}\x03 Mild) "
                "(\x0313{12}\x03 Serious) (\x0310{13}\x03/\x0313{14}\x03) | "
                "Cases/1M: \x0307{15}\x03 | Deaths/1M: \x0304{16}\x03 | 1st Case: "
                "{17} | Updated: {18}".format(
                    "Global",
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][1]
                    ],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][2]
                    ],
                    self.countries[list(self.countries)[0]]["ratio_new_cases"],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][3]
                    ],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][4]
                    ],
                    self.countries[list(self.countries)[0]]["ratio_new_dead"],
                    self.countries[list(self.countries)[0]]["ratio_dead"],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][5]
                    ],
                    self.countries[list(self.countries)[0]]["ratio_recovered"],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][6]
                    ],
                    self.countries[list(self.countries)[0]]["mild"],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][7]
                    ],
                    self.countries[list(self.countries)[0]]["ratio_mild"],
                    self.countries[list(self.countries)[0]]["ratio_serious"],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][8]
                    ],
                    self.countries[list(self.countries)[0]][
                        self.headers["countries"][9]
                    ],
                    self.countries["China"][self.headers["countries"][10]],
                    self.time_created(self.updated),
                )
            )

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
        reply = ""
        n = 1
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
