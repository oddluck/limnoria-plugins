# -*- coding: utf-8 -*-
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

# my libs
import json
import urllib2
import urllib
import string
import unicodedata

# supybot libs
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
    
    # helper methods.
    def _remove_accents(self, data):
        nkfd_form = unicodedata.normalize('NFKD', unicode(data))
        return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

    def _red(self, string):
        """return a red string."""
        return ircutils.mircColor(string, 'red')

    def _bu(self, string):
        """bold and underline string."""
        return ircutils.bold(ircutils.underline(string))

    # main urbandict function.
    def urbandictionary(self, irc, msg, args, optlist, optterm):
        """<term>
        Fetches definition for term on UrbanDictionary.com
        """
        
        # default args for output.
        args = {'showExamples': True, 'numberOfDefinitions':'10', 'showVotes': False }
               
        # optlist to change args.
        if optlist:
            for (key, value) in optlist:
                if key == 'disableexamples':
                    args['showExamples'] = False
                if key == 'showvotes':
                    args['showVotes'] = True
                if key == 'num': # number of definitions. max 10 default but also is enforced 
                    if value > self.registryValue('maxNumberOfDefinitions') or value <= 0:
                        args['numberOfDefinitions'] = '10'
                    else:
                        args['numberOfDefinitions'] = value
        
        # url                 
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % (urllib.quote(optterm))

        # try fetching url.
        try:
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
        except Exception, e:
            irc.reply("{0} fetching {1}".format(self._red("Error"), url))
            self.log.debug("Error fetching: {0} :: {1}".format(url, e))
            return

        # try parsing json. 
        try:
            jsondata = response.read().decode('utf-8')
            jsondata = json.loads(jsondata.replace(r'\r','').replace(r'\n','')) # odds chars in UD.
        except:
            irc.reply("Failed to parse json data. Check logs for error")
            return
        
        # handle output based on what comes back. 2 different results, fallback on else.
        # asshole - "has_related_words": true, "result_type": "exact"
        # assmole - "has_related_words": true, "result_type": "exact", total: 1
        # asswole - "has_related_words": false, "result_type": "no_results" - list->term
        definitions = jsondata.get('list', None) 
        result_type = jsondata.get('result_type', None)
        total = jsondata.get('total', None)
        
        if result_type == "exact" and len(jsondata['list']) > 0: # exact, means we found, and we have definitions.
            output = [] # container to put all def/ex in.
            for item in jsondata['list'][0:int(args['numberOfDefinitions'])]: 
                outputstring = "{0}".format(item['definition'].encode('utf-8').strip()) # start outputstring.
                if args['showExamples']: # if we're showing examples
                    if self.registryValue('disableANSI'):
                        outputstring += " {0} {1} {2}".format("[ex:]", item['example'].encode('utf-8').strip(), "[/ex]")
                    else:
                        outputstring += " {0} {1} {2}".format(self._bu("[ex:]"), item['example'].encode('utf-8').strip(), self._bu("[/ex]"))
                if args['showVotes']: # if we're showing votes
                        outputstring += " (+{0}/-{1})".format(item['thumbs_up'], item['thumbs_down'])
                
                output.append(outputstring) # finally add to output
            
            #output.
            if self.registryValue('disableANSI'):
                irc.reply("{0} ({1}): {2}".format(optterm, total, string.join([item for item in output], " | ")))
            else:
                irc.reply("{0} ({1}): {2}".format(self._red(optterm), total, string.join([item for item in output], " | ")))

        elif result_type == "no_results" and len(jsondata['list']) > 0:
            outrelated = string.join([item['term'].encode('utf-8') for item in jsondata['list']], " | ")
            
            if self.registryValue('disableANSI'):
                irc.reply("{0}: {1} not found. {2}: {3}".format("ERROR", optterm, "Related terms", outrelated))
            else:
                irc.reply("{0}: {1} not found. {2}: {3}".format(self._red("ERROR"), optterm, self._bu("Related terms"), outrelated))

        else:
            if self.registryValue('disableANSI'):
                irc.reply("{0} nothing found in output looking up: {1}".format("ERROR", optterm))
            else:
                irc.reply("{0} nothing found in output looking up: {1}".format(self._red("ERROR"), optterm))

    urbandictionary = wrap(urbandictionary, [getopts({'showvotes':'', 'num':('int'), 'disableexamples':''}), ('text')])

Class = UrbanDictionary


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
