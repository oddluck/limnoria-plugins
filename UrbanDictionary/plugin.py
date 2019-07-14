# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
#
#
###
from __future__ import unicode_literals
# my libs
import json
import re
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

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _red(self, string):
        """return a red string."""
        return ircutils.mircColor(string, 'red')

    def _bu(self, string):
        """bold and underline string."""
        return ircutils.bold(ircutils.underline(string))

    def cleanjson(self, s):
        """clean up json and return."""

        s = s.replace('\n', '')
        s = s.replace('\r', '')
        s = s.replace('\t', '')
        s = s.strip()
        # return
        return s

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def urbandictionary(self, irc, msg, args, optlist, optterm):
        """[--disableexamples | --showvotes | --num # | --showtags] <term>

        Fetches definition for <term> on UrbanDictionary.com

        Use --disableexamples to not display examples.
        Use --showvotes to show votes [default: off]
        Use --num # to limit the number of definitions. [default:10]
        Use --showtags to display tags (if available)
        """

        # default args for output. can manip via --getopts.
        args = {'showExamples': True,
                'numberOfDefinitions':self.registryValue('maxNumberOfDefinitions'),
                'showVotes': False,
                'showTags':False
               }
        # optlist to change args.
        if optlist:
            for (key, value) in optlist:
                if key == 'disableexamples':
                    args['showExamples'] = False
                if key == 'showvotes':
                    args['showVotes'] = True
                if key == 'showtags':
                    args['showTags'] = True
                if key == 'num':  # if number is >, default to config var.
                    if 0 <= value <= self.registryValue('maxNumberOfDefinitions'):
                        args['numberOfDefinitions'] = value
        # build and fetch url.
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % utils.web.urlquote(optterm)
        try:
            html = utils.web.getUrl(url)
        except utils.web.Error as e:
            self.log.error("ERROR opening {0} message: {1}".format(url, e))
            irc.reply("ERROR: could not open {0} message: {1}".format(url, e))
            return
        # try parsing json.
        #irc.reply("{0}".format(self._repairjson(html.decode('utf-8'))))
        try:
            #jsondata = self._repairjson(html.decode('utf-8'))  # decode utf-8. fix \r\n that ud puts in below.
            jsondata = html.decode('utf-8')
            jsondata = json.loads(jsondata)  # odds chars in UD.
        except Exception as e:
            self.log.error("Error parsing JSON from UD: {0}".format(e))
            irc.reply("ERROR: Failed to parse json data. Check logs for error")
            return
        # process json.
        results = jsondata.get('result_type')  # exact, no_results, fulltext .
        if not results:
            # assume exact i guess... 
            results = 'exact'
        definitions = jsondata.get('list')
        # prep output now depending on results.
        if results == "exact":  # we did not find anything.
            outdefs = []
            for i in definitions[0:args['numberOfDefinitions']]:  # iterate through each def.
                # clean these up.
                definition = self.cleanjson(''.join(i['definition'])) #.encode('utf-8')
                example = self.cleanjson(''.join(i['example']))
                # now add
                outputstring = "{0}".format(definition)  # default string.
                if args['showExamples']:  # show examples?
                    outputstring += " {0} {1} {2}".format(self._bu("[ex:]"), example, self._bu("[/ex]"))
                if args['showVotes']:  # show votes?
                    outputstring += " (+{0}/-{1})".format(i['thumbs_up'], i['thumbs_down'])
                outdefs.append(outputstring)  # add to our list.
            output = " | ".join([item for item in outdefs])  # create string with everything.
        elif results == "fulltext":  # not direct. yields related terms.
            output = " | ".join(sorted(set([item['word'] for item in definitions])))  # sorted, unique words.
        # output time.
        if results == "no_results" or len(definitions) == 0:  # NOTHING FOUND.
            irc.reply("ERROR: '{0}' not defined on UrbanDictionary.".format(optterm))
            return
        else:  # we have definitions, so we're gonna output.
            # check if we should add tags.
            if args['showTags']:  # display tags.
                tags = jsondata.get('tags')
                if tags:  # we have tags. add it to optterm.
                    tags = " | ".join([i for i in tags])
                else:
                    tags = False
            else:
                tags = False
            # now lets output.
            if self.registryValue('disableANSI'):  # disable formatting.
                if tags:
                    irc.reply("{0} :: {1} :: {2}".format(optterm, tags, ircutils.stripFormatting(output)))
                else:
                    irc.reply("{0} :: {1}".format(optterm, ircutils.stripFormatting(output)))
            else:  # colors.
                if tags:
                    irc.reply("{0} :: {1} :: {2}".format(self._red(optterm), tags, output))
                else:
                    irc.reply("{0} :: {1}".format(self._red(optterm), output))

    urbandictionary = wrap(urbandictionary, [getopts({'showtags':'',
                                                      'showvotes':'',
                                                      'num':('int'),
                                                      'disableexamples':''}), ('text')])

Class = UrbanDictionary


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
