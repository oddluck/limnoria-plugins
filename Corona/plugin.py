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

    url = "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/ncov_cases/FeatureServer/1/query?f=json&where=Confirmed>0&outFields=*"

    @wrap([optional('text')])
    def corona(self, irc, msg, args, search):
        """<area>
        Displays Coronavirus stats
        """

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
        confirmed = deaths = recovered = 0
        location = 'Global'

        for region in features:
            r = region.get('attributes')

            if search:
                region = r.get('Country_Region')
                state = r.get('Province_State')
                if 'china' in search.lower():
                    search = 'mainland china'
                if region and search.lower() == region.lower():
                    location = region
                    confirmed += r.get('Confirmed')
                    deaths += r.get('Deaths')
                    recovered += r.get('Recovered')
                    local_ratio_dead = "{0:.00%}".format(deaths/confirmed)
                elif state:
                    if search.lower() == state.lower():
                        location = state
                        confirmed += r.get('Confirmed')
                        deaths += r.get('Deaths')
                        recovered += r.get('Recovered')
                        local_ratio_dead = "{0:.00%}".format(deaths/confirmed)
                    else:
                        state = state.split(',', 1)
                        if search.lower() == state[0].lower().strip():
                            location = r.get('Province_State')
                            confirmed += r.get('Confirmed')
                            deaths += r.get('Deaths')
                            recovered += r.get('Recovered')
                            local_ratio_dead = "{0:.00%}".format(deaths/confirmed)
                        elif len(state) > 1 and search.lower() == state[1].lower().strip():
                            location = state[1].strip()
                            confirmed += r.get('Confirmed')
                            deaths += r.get('Deaths')
                            recovered += r.get('Recovered')
                            local_ratio_dead = "{0:.00%}".format(deaths/confirmed)
                        elif search.lower().replace('county', '').strip() == state[0].lower().replace('county', '').strip():
                            location = r.get('Province_State')
                            confirmed += r.get('Confirmed')
                            deaths += r.get('Deaths')
                            recovered += r.get('Recovered')
                            local_ratio_dead = "{0:.00%}".format(deaths/confirmed)

            total_confirmed += r.get('Confirmed')
            total_deaths += r.get('Deaths')
            total_recovered += r.get('Recovered')

        ratio_dead = "{0:.00%}".format(total_deaths/total_confirmed)

        template = self.registryValue("template", msg.channel)
        if location == 'Global':
            template = template.replace("$location", location)
            template = template.replace("$confirmed", str(total_confirmed))
            template = template.replace("$dead", str(total_deaths))
            template = template.replace("$recovered", str(total_recovered))
            template = template.replace("$ratio", ratio_dead)
        else:
            template = template.replace("$location", location)
            template = template.replace("$confirmed", str(confirmed))
            template = template.replace("$dead", str(deaths))
            template = template.replace("$recovered", str(recovered))
            template = template.replace("$ratio", local_ratio_dead)

        irc.reply(template)

Class = Corona
