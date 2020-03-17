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

import json
import requests
import csv
import datetime
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
    "BS": "BAHAMAS, THE",
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
    "CV": "CAPE VERDE",
    "KY": "CAYMAN ISLANDS",
    "CF": "CENTRAL AFRICAN REPUBLIC",
    "TD": "CHAD",
    "CL": "CHILE",
    "CN": "CHINA",
    "CX": "CHRISTMAS ISLAND",
    "CC": "COCOS ISLANDS",
    "CO": "COLOMBIA",
    "KM": "COMOROS",
    "CG": "CONGO (BRAZZAVILLE)",
    "CD": "CONGO (KINSHASA)",
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
    "GF": "GUIANA",
    "PF": "POLYNESIA",
    "TF": "FRENCH SOUTHERN TERRITORIES",
    "GA": "GABON",
    "GM": "GAMBIA, THE",
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
    "GW": "GUINEA-BISSAU",
    "GY": "GUYANA",
    "HT": "HAITI",
    "HM": "HEARD ISLAND AND MCDONALD ISLANDS",
    "VA": "HOLY SEE",
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
    "KP": "KOREA, NORTH",
    "KR": "KOREA, SOUTH",
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
    "PS": "PALESTINE, STATE OF",
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
    "BL": "SAINT BARTHÉLEMY",
    "SH": "SAINT HELENA",
    "KN": "SAINT KITTS AND NEVIS",
    "LC": "SAINT LUCIA",
    "MF": "SAINT MARTIN",
    "PM": "SAINT PIERRE AND MIQUELON",
    "VC": "SAINT VINCENT AND THE GRENADINES",
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
    "SS": "SOUTH SUDAN",
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
    "TC": "TURKS AND CAICOS ISLANDS",
    "TV": "TUVALU",
    "UG": "UGANDA",
    "UA": "UKRAINE",
    "AE": "UNITED ARAB EMIRATES",
    "GB": "UNITED KINGDOM",
    "UK": "UNITED KINGDOM",
    "US": "US",
    "UM": "UNITED STATES MINOR OUTLYING ISLANDS",
    "UY": "URUGUAY",
    "UZ": "UZBEKISTAN",
    "VU": "VANUATU",
    "VE": "VENEZUELA",
    "VN": "VIETNAM",
    "VG": "VIRGIN ISLANDS",
    "VI": "VIRGIN ISLANDS",
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
        self.cache = {}

    def getCSV(self):
        data = None
        try:
            day = datetime.date.today().strftime('%m-%d-%Y')
            url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{0}.csv".format(day)
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            log.debug('Corona: error retrieving data for today: {0}'.format(e))
            try:
                day = datetime.date.today() - datetime.timedelta(days=1)
                day = day.strftime('%m-%d-%Y')
                url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{0}.csv".format(day)
                r = requests.get(url, timeout=10)
                r.raise_for_status()
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                log.debug('Corona: error retrieving data for yesterday: {0}'.format(e))
            else:
                data = csv.DictReader(r.iter_lines(decode_unicode = True))
        else:
            data = csv.DictReader(r.iter_lines(decode_unicode = True))
        return data

    def getAPI(self):
        data = None
        url = "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/ncov_cases/FeatureServer/1/query?f=json&where=Confirmed>0&outFields=*"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            log.debug('Corona: error retrieving data from API: {0}'.format(e))
        else:
            try:
                r = json.loads(r.content.decode())
                data = r.get('features')
            except:
                data = None
            if not data:
                log.debug("Corona: Error retrieving features data from API.")
        return data

    def timeCreated(self, time):
        time = datetime.datetime.fromtimestamp(time/1000.0)
        d = datetime.datetime.now() - time
        if d.days:
            rel_time = "{:1d} days ago".format(abs(d.days))
        elif d.seconds > 3600:
            rel_time = "{:.1f} hours ago".format(round((abs(d.seconds) / 3600),1))
        elif 60 <= d.seconds < 3600:
            rel_time = "{:.1f} minutes ago".format(round((abs(d.seconds) / 60),1))
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
        git = api = False
        data = None
        if len(self.cache) > 0:
            cacheLifetime = self.registryValue("cacheLifetime")
            now = datetime.datetime.now()
            seconds = (now - self.cache['timestamp']).total_seconds()
            if seconds < cacheLifetime:
                data = self.cache['data']
                api = True
                log.debug("Corona: returning cached API data")
            else:
                data = self.getAPI()
                if data:
                    api = True
                    self.cache['timestamp'] = datetime.datetime.now()
                    self.cache['data'] = data
                    log.debug("Corona: caching API data")
                else:
                    now = datetime.datetime.now()
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    seconds = (now - midnight).seconds
                    if seconds > (now - self.cache['timestamp']).total_seconds():
                        data = self.cache['data']
                        api = True
                        log.debug("Corona: error accessing API, returning cached API data")
                    else:
                        data = self.getCSV()
                        if data:
                            git = True
        else:
            data = self.getAPI()
            if data:
                api = True
                self.cache['timestamp'] = datetime.datetime.now()
                self.cache['data'] = data
                log.debug("Corona: caching API data")
            else:
                data = self.getCSV()
                if data:
                    git = True
        if not data:
            irc.reply("Error. Unable to access database.")
            return
        total_confirmed = total_deaths = total_recovered = last_update = 0
        confirmed = deaths = recovered = updated = 0
        location = 'Global'
        for region in data:
            if api:
                r = region.get('attributes')
            else:
                r = region
            if search:
                if api:
                    region = r.get('Country_Region')
                    state = r.get('Province_State')
                else:
                    region = r.get('Country/Region')
                    state = r.get('Province/State')
                if len(search) == 2:
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
                if search.lower() == 'usa' or 'united states' in search.lower():
                    search = 'us'
                if 'korea' in search.lower():
                    search = 'korea, south'
                if region and search.lower() == region.lower():
                    location = region
                    confirmed += int(r.get('Confirmed'))
                    deaths += int(r.get('Deaths'))
                    recovered += int(r.get('Recovered'))
                    if api:
                        time = int(r.get('Last_Update'))
                    if git:
                        time = datetime.datetime.strptime(r.get('Last Update'), "%Y-%m-%dT%H:%M:%S")
                        time = int(time.timestamp()*1000)
                    if time > updated:
                        updated = time
                    local_ratio_dead = "{0:.1%}".format(deaths/confirmed)
                elif state and search.lower() == state.lower():
                    location = state
                    confirmed += int(r.get('Confirmed'))
                    deaths += int(r.get('Deaths'))
                    recovered += int(r.get('Recovered'))
                    if api:
                        time = int(r.get('Last_Update'))
                    if git:
                        time = datetime.datetime.strptime(r.get('Last Update'), "%Y-%m-%dT%H:%M:%S")
                        time = int(time.timestamp()*1000)
                    if time > updated:
                        updated = time
                    local_ratio_dead = "{0:.1%}".format(deaths/confirmed)
            total_confirmed += int(r.get('Confirmed'))
            total_deaths += int(r.get('Deaths'))
            total_recovered += int(r.get('Recovered'))
            if api:
                time = int(r.get('Last_Update'))
            if git:
                time = datetime.datetime.strptime(r.get('Last Update'), "%Y-%m-%dT%H:%M:%S")
                time = int(time.timestamp()*1000)
            if time > last_update:
                last_update = time
        ratio_dead = "{0:.1%}".format(total_deaths/total_confirmed)
        template = self.registryValue("template", msg.channel)
        if location == 'Global':
            last_update = self.timeCreated(last_update)
            template = template.replace("$location", location)
            template = template.replace("$confirmed", str(total_confirmed))
            template = template.replace("$dead", str(total_deaths))
            template = template.replace("$recovered", str(total_recovered))
            template = template.replace("$ratio", ratio_dead)
            template = template.replace("$updated", last_update)
        else:
            updated = self.timeCreated(updated)
            template = template.replace("$location", location)
            template = template.replace("$confirmed", str(confirmed))
            template = template.replace("$dead", str(deaths))
            template = template.replace("$recovered", str(recovered))
            template = template.replace("$ratio", local_ratio_dead)
            template = template.replace("$updated", updated)
        irc.reply(template)

Class = Corona
