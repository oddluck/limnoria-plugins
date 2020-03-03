###
# Copyright (c) 2020, Hoaas
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
import urllib

from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Corona')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Corona(callbacks.Plugin):
    """Displays current stats of the Coronavirus outbreak"""
    threaded = True

    url = 'https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/ncov_cases/FeatureServer/1/query?f=json&where=Confirmed>0&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Confirmed%20desc%2CCountry_Region%20asc%2CProvince_State%20asc&outSR=102100&resultOffset=0&resultRecordCount=250&cacheHint=true'

    @wrap([optional('text')])
    def corona(self, irc, msg, args, search):
        """<area>
        Displays Coronavirus stats"""

        try:
            data = utils.web.getUrl(self.url).decode()
            data = json.loads(data)
        except utils.web.Error as e:
            log.debug('Corona: error retrieving data from {0}: {1}'.format(self.url, e))
            return

        features = data.get('features')
        if not features:
            log.debug("Corona: Error retrieving features data.")
            return

        total_confirmed = total_deaths = total_recovered = 0

        extra_output = None
        for region in features:
            r = region.get('attributes')

            confirmed = r.get('Confirmed')
            deaths = r.get('Deaths')
            recovered = r.get('Recovered')

            if search:
                name = r.get('Country_Region')
                if search.lower() in name.lower():
                    local_ratio_dead = deaths/confirmed
                    extra_output = ' {0} infected, {1} dead ({4:.00%}), {2} recovered in {3}.'\
                        .format(confirmed, deaths, recovered, name, local_ratio_dead)

            total_confirmed += r.get('Confirmed')
            total_deaths += r.get('Deaths')
            total_recovered += r.get('Recovered')

        ratio_dead = total_deaths/total_confirmed

        output = '{0} infected, {1} dead ({3:.00%}), {2} recovered globally.'\
            .format(total_confirmed, total_deaths, total_recovered, ratio_dead)

        if extra_output:
            output += extra_output

        irc.reply(output)

Class = Corona
