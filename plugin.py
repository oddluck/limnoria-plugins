###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import json
import urllib2
import urllib
import string

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('UrbanDictionary')

@internationalizeDocstring
class UrbanDictionary(callbacks.Plugin):
    """Add the help for "@plugin help UrbanDictionary" here
    This should describe *how* to use this plugin."""
    threaded = True

    def _bu(self, string):
        """bold and underline string."""
        try:
            string = ircutils.bold(ircutils.underline(string))
        except:
            string = string

        return string

    # main urbandict function.
    def urbandictionary(self, irc, msg, args, term):
        """<term>
        Fetches definition for term on UrbanDictionary.com
        """

        # build url based on sport with key.
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % (urllib.quote(term))

        #self.log.info(url)

        # attempt to fetch data
        try:
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
        except URLError, e:
            irc.reply(ircutils.mircColor("ERROR:", 'red') + " fetching bettingexpress.com URL: %s" % (e.reason))
            return
        except HTTPError, e:
            irc.reply(ircutils.mircColor("ERROR:", 'red') + " fetching bettingexpress.com URL: %s" % (e.code))
            return

        try:
            response_data = response.read()
            jsondata = json.loads(response_data.replace(r'\r', '').replace(r'\n', ''))
            #jsondata = json.loads(response_data)
        except:
            irc.reply(ircutils.mircColor("ERROR:", 'red') + " Failed to read and parse JSON response data.")
            return

        definitions = jsondata.get('list', None) 
        result_type = jsondata.get('result_type', None) # exact, no_results
        has_related_words = jsondata.get('has_related_words', None) # false, true
        total = jsondata.get('total', None)

        # data['list'] = data['list'][:1]  # only print 2 results 

        if result_type != None and result_type == "exact" and len(jsondata['list']) > 0: 
            output = ircutils.mircColor(term, 'red') + ": "
            outdef = string.join([item['definition'] + " " + self._bu("[ex:]") + " " + item['example'] + " " + self._bu("[/ex]") + " " for item in jsondata['list']], " | ")
            output += outdef.encode('utf8')
            irc.reply(output)

        elif result_type == "no_results":
            output = ircutils.mircColor(term, 'red') + ": not found. "
            output += ircutils.bold("Related words:") + " " 
            outrelated = string.join([item['term'].encode('utf-8') + " " for item in jsondata['list']], " | ")
            output += outrelated
            irc.reply(output)

        else:
            irc.reply("Nothing found in the output for: %s" % term)

    urbandictionary = wrap(urbandictionary, [('text')])

Class = UrbanDictionary


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
