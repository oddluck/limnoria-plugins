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
    _ = PluginInternationalization('Corona')
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
    "ZW": "ZIMBABWE"
}

states = {
    'AK': 'ALASKA',
    'AL': 'ALABAMA',
    'AR': 'ARKANSAS',
    'AS': 'AMERICAN SAMOA',
    'AZ': 'ARIZONA',
    'CA': 'CALIFORNIA',
    'CO': 'COLORADO',
    'CT': 'CONNECTICUT',
    'DC': 'DISTRICT OF COLUMBIA',
    'DE': 'DELAWARE',
    'FL': 'FLORIDA',
    'GA': 'GEORGIA',
    'GU': 'GUAM',
    'HI': 'HAWAII',
    'IA': 'IOWA',
    'ID': 'IDAHO',
    'IL': 'ILLINOIS',
    'IN': 'INDIANA',
    'KS': 'KANSAS',
    'KY': 'KENTUCKY',
    'LA': 'LOUISIANA',
    'MA': 'MASSACHUSETTS',
    'MD': 'MARYLAND',
    'ME': 'MAINE',
    'MI': 'MICHIGAN',
    'MN': 'MINNESOTA',
    'MO': 'MISSOURI',
    'MP': 'NORTHERN MARIANA ISLANDS',
    'MS': 'MISSISSIPPI',
    'MT': 'MONTANA',
    'NA': 'NATIONAL',
    'NC': 'NORTH CAROLINA',
    'ND': 'NORTH DAKOTA',
    'NE': 'NEBRASKA',
    'NH': 'NEW HAMPSHIRE',
    'NJ': 'NEW JERSEY',
    'NM': 'NEW MEXICO',
    'NV': 'NEVADA',
    'NY': 'NEW YORK',
    'OH': 'OHIO',
    'OK': 'OKLAHOMA',
    'OR': 'OREGON',
    'PA': 'PENNSYLVANIA',
    'PR': 'PUERTO RICO',
    'RI': 'RHODE ISLAND',
    'SC': 'SOUTH CAROLINA',
    'SD': 'SOUTH DAKOTA',
    'TN': 'TENNESSEE',
    'TX': 'TEXAS',
    'UT': 'UTAH',
    'VA': 'VIRGINIA',
    'VI': 'VIRGIN ISLANDS',
    'VT': 'VERMONT',
    'WA': 'WASHINGTON',
    'WI': 'WISCONSIN',
    'WV': 'WEST VIRGINIA',
    'WY': 'WYOMING'
}

class Corona(callbacks.Plugin):
    """Displays current stats of the Coronavirus outbreak"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Corona, self)
        self.__parent.__init__(irc)
        self.data = requests.structures.CaseInsensitiveDict()
        today = datetime.datetime.utcnow()
        self.updated = today - datetime.timedelta(days=1)

    def time_created(self, time):
        """
        Return relative time delta between now and s (dt string).
        """
        d = datetime.datetime.utcnow() - time
        if d.days:
            rel_time = "{:1d}d ago".format(abs(d.days))
        elif d.seconds > 3600:
            rel_time = "{:.1f}h ago".format(round((abs(d.seconds) / 3600),1))
        elif 60 <= d.seconds < 3600:
            rel_time = "{:.1f}m ago".format(round((abs(d.seconds) / 60),1))
        else:
            rel_time = "%ss ago" % (abs(d.seconds))
        return rel_time

    @wrap([optional('text')])
    def corona(self, irc, msg, args, search):
        """[region]
        Displays Coronavirus statistics. Add a region name to search for country/state
        specific results. Accepts full country/state names or ISO 3166-1 alpha-2 (two
        character) country abbreviations and US Postal (two character) state abbreviations.
        Invalid region names or search terms without data return global results.
        """
        OK = False
        try:
            r = requests.get('https://www.worldometers.info/coronavirus/', timeout=10)
            r.raise_for_status()
            OK = True
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            log.debug('Corona: error retrieving World data from API: {0}'.format(e))
            OK = False
        soup = BeautifulSoup(r.content)
        updated = soup.find("div", text = re.compile('Last updated:'))
        updated = updated.text.split(':', 1)[1].replace('GMT', '').strip()
        updated = datetime.datetime.strptime(updated, "%B %d, %Y, %H:%M")
        if OK and updated > self.updated:
            self.updated = updated
            table = soup.find("table", { "id" : "main_table_countries_today" })
            n = 0
            for row in table.findAll("tr"):
                cells = row.findAll("td")
                if len(cells) >= 9:
                    n += 1
                    country = cells[0].text.strip()
                    self.data[country] = {}
                    self.data[country]['name'] = country
                    self.data[country]['country'] = True
                    if cells[1].text.strip():
                        self.data[country]['total_cases'] = cells[1].text.strip()
                    else:
                        self.data[country]['total_cases'] = '0'
                    if cells[2].text.strip():
                        self.data[country]['new_cases'] = cells[2].text.strip()
                    else:
                        self.data[country]['new_cases'] = '+0'
                    if cells[3].text.strip():
                        self.data[country]['total_deaths'] = cells[3].text.strip()
                    else:
                        self.data[country]['total_deaths'] = '0'
                    if cells[4].text.strip():
                        self.data[country]['new_deaths'] = cells[4].text.strip()
                    else:
                        self.data[country]['new_deaths'] = '+0'
                    if cells[5].text.strip():
                        self.data[country]['total_recovered'] = cells[5].text.strip()
                    else:
                        self.data[country]['total_recovered'] = '0'
                    if cells[6].text.strip():
                        self.data[country]['active'] = cells[6].text.strip()
                    else:
                        self.data[country]['active'] = 'N/A'
                    if cells[7].text.strip():
                        self.data[country]['serious'] = cells[7].text.strip()
                    else:
                        self.data[country]['serious'] = 'N/A'
                    if cells[8].text.strip():
                        self.data[country]['cases_million'] = cells[8].text.strip()
                    else:
                        self.data[country]['cases_million'] = 'N/A'
                    if cells[9].text.strip():
                        self.data[country]['deaths_million'] = cells[9].text.strip()
                    else:
                        self.data[country]['deaths_million'] = 'N/A'
                    self.data[country]['rank'] = "#{}".format(n)
            try:
                r = requests.get('https://www.worldometers.info/coronavirus/country/us/', timeout=10)
                r.raise_for_status()
                OK = True
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                log.debug('Corona: error retrieving USA data from API: {0}'.format(e))
                OK = False
            if OK:
                soup = BeautifulSoup(r.content)
                table = soup.find("table", { "id" : "usa_table_countries_today" })
                n = 0
                for row in table.findAll("tr")[:-1]:
                    cells = row.findAll("td")
                    if len(cells) >= 7:
                        n += 1
                        state = cells[0].text.strip()
                        self.data[state] = {}
                        self.data[state]['country'] = False
                        self.data[state]['name'] = state
                        if cells[1].text.strip():
                            self.data[state]['total_cases'] = cells[1].text.strip()
                        else:
                            self.data[state]['total_cases'] = '0'
                        if cells[2].text.strip():
                            self.data[state]['new_cases'] = cells[2].text.strip()
                        else:
                            self.data[state]['new_cases'] = '+0'
                        if cells[3].text.strip():
                            self.data[state]['total_deaths'] = cells[3].text.strip()
                        else:
                            self.data[state]['total_deaths'] = '0'
                        if cells[4].text.strip():
                            self.data[state]['new_deaths'] = cells[4].text.strip()
                        else:
                            self.data[state]['new_deaths'] = '+0'
                        if cells[5].text.strip():
                            self.data[state]['active'] = cells[5].text.strip()
                        else:
                            self.data[state]['active'] = 'N/A'
                        self.data[state]['rank'] = "#{}".format(n)
            else:
                log.debug("Corona: unable to retrieve latest USA data")
        elif len(self.data) > 0:
            log.debug("Corona: data not yet updated, using cache")
        else:
            log.debug("Corona: Error. Unable to retrieve data.")
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
        if search and self.data.get(search):
            if self.data[search]['country']:
                ratio_dead = "{0:.1%}".format(int(self.data[search]['total_deaths'].replace(',', ''))/int(self.data[search]['total_cases'].replace(',', '')))
                ratio_recovered = "{0:.1%}".format(int(self.data[search]['total_recovered'].replace(',', ''))/int(self.data[search]['total_cases'].replace(',', '')))
                if self.data[search]['serious'].replace(',', '').isdigit():
                    mild = '{:,}'.format(int(self.data[search]['active'].replace(',', '')) - int(self.data[search]['serious'].replace(',', '')))
                else:
                    mild = 'N/A'
                irc.reply("\x02\x1F{0}\x1F: World Rank: {1} | Cases: \x0307{2}\x03 (\x0307{3}\x03) | Deaths: \x0304{4}\x03 (\x0304{5}\x03) (\x0304{6}\x03) | Recovered: \x0309{7}\x03 (\x0309{8}\x03) | Active: \x0307{9}\x03 (\x0310{10}\x03 Mild) (\x0313{11}\x03 Serious) | Cases/1M: \x0307{12}\x03 | Deaths/1M: \x0304{13}\x03 | Updated: {14}".format(
                    self.data[search]['name'],
                    self.data[search]['rank'],
                    self.data[search]['total_cases'],
                    self.data[search]['new_cases'],
                    self.data[search]['total_deaths'],
                    self.data[search]['new_deaths'],
                    ratio_dead,
                    self.data[search]['total_recovered'],
                    ratio_recovered,
                    self.data[search]['active'],
                    mild,
                    self.data[search]['serious'],
                    self.data[search]['cases_million'],
                    self.data[search]['deaths_million'],
                    self.time_created(updated)))
            else:
                ratio_dead = "{0:.1%}".format(int(self.data[search]['total_deaths'].replace(',', ''))/int(self.data[search]['total_cases'].replace(',', '')))
                irc.reply("\x02\x1F{0}\x1F: USA Rank: {1} | Cases: \x0307{2}\x03 (\x0307{3}\x03) | Deaths: \x0304{4}\x03 (\x0304{5}\x03) (\x0304{6}\x03) | Active: \x0307{7}\x03 | Updated: {8}".format(
                    self.data[search]['name'],
                    self.data[search]['rank'],
                    self.data[search]['total_cases'],
                    self.data[search]['new_cases'],
                    self.data[search]['total_deaths'],
                    self.data[search]['new_deaths'],
                    ratio_dead,
                    self.data[search]['active'],
                    self.time_created(updated)))
        else:
            if self.data['total:']['serious'].replace(',', '').isdigit():
                mild = '{:,}'.format(int(self.data['total:']['active'].replace(',', '')) - int(self.data['total:']['serious'].replace(',', '')))
            else:
                mild = 'N/A'
            ratio_dead = "{0:.1%}".format(int(self.data['total:']['total_deaths'].replace(',', ''))/int(self.data['total:']['total_cases'].replace(',', '')))
            ratio_recovered = "{0:.1%}".format(int(self.data['total:']['total_recovered'].replace(',', ''))/int(self.data['total:']['total_cases'].replace(',', '')))
            irc.reply("\x02\x1F{0}\x1F: Cases: \x0307{1}\x03 (\x0307+{2}\x03) | Deaths: \x0304{3}\x03 (\x0304+{4}\x03) (\x0304{5}\x03) | Recovered: \x0309{6}\x03 (\x0309{7}\x03) | Active: \x0307{8}\x03 (\x0310{9}\x03 Mild) (\x0313{10}\x03 Serious) | Cases/1M: \x0307{11}\x03 | Deaths/1M: \x0304{12}\x03 | Updated: {13}".format(
                'Global',
                self.data['total:']['total_cases'],
                self.data['total:']['new_cases'],
                self.data['total:']['total_deaths'],
                self.data['total:']['new_deaths'],
                ratio_dead,
                self.data['total:']['total_recovered'],
                ratio_recovered,
                self.data['total:']['active'],
                mild,
                self.data['total:']['serious'],
                self.data['total:']['cases_million'],
                self.data['total:']['deaths_million'],
                self.time_created(updated)))

Class = Corona
