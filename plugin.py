# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
#
#
###
# my libs
import json
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

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def urbandictionary(self, irc, msg, args, optlist, optterm):
        """[--disableexamples | --showvotes | --num #] <term>

        Fetches definition for <term> on UrbanDictionary.com

        Use --disableexamples to not display examples.
        Use --showvotes to show votes [default: off]
        Use --num # to limit the number of definitions. [default:10]
        """

        # default args for output. can manip via --getopts.
        args = {'showExamples': True,
                'numberOfDefinitions':self.registryValue('maxNumberOfDefinitions'),
                'showVotes': False
               }
        # optlist to change args.
        if optlist:
            for (key, value) in optlist:
                if key == 'disableexamples':
                    args['showExamples'] = False
                if key == 'showvotes':
                    args['showVotes'] = True
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
        try:
            jsondata = html.decode('utf-8')  # decode utf-8. fix \r\n that ud puts in below.
            jsondata = json.loads(jsondata.replace(r'\r','').replace(r'\n',''))  # odds chars in UD.
        except:
            irc.reply("ERROR: Failed to parse json data. Check logs for error")
            return
        # process json.
        results = jsondata.get('result_type')  # exact, no_results, fulltext .
        definitions = jsondata.get('list')
        # prep output now depending on results.
        if results == "exact":  # we did not find anything.
            outdefs = []
            for i in definitions[0:args['numberOfDefinitions']]:  # iterate through each def.
                outputstring = "{0}".format(i['definition'].encode('utf-8').strip())  # default string.
                if args['showExamples']:  # show examples?
                    outputstring += " {0} {1} {2}".format(self._bu("[ex:]"), i['example'].encode('utf-8').strip(), self._bu("[/ex]"))
                if args['showVotes']:  # show votes?
                    outputstring += " (+{0}/-{1})".format(i['thumbs_up'], i['thumbs_down'])
                outdefs.append(outputstring)  # add to our list.
            output = " | ".join([item for item in outdefs])  # create string with everything.
        elif results == "fulltext":  # not direct. yields related terms.
            output = " | ".join(sorted(set([item['word'].encode('utf-8') for item in definitions])))  # sorted, unique words.
        # output time.
        if results == "no_results" or len(definitions) == 0:  # NOTHING FOUND.
            irc.reply("ERROR: '{0}' not defined on UrbanDictionary.".format(optterm))
            return
        else:  # we have definitions.
            if self.registryValue('disableANSI'):  # disable formatting.
                irc.reply("{0} :: {1}".format(optterm, ircutils.stripFormatting(output)))
            else:  # colors.
                irc.reply("{0} :: {1}".format(self._red(optterm), output))

    urbandictionary = wrap(urbandictionary, [getopts({'showvotes':'', 'num':('int'), 'disableexamples':''}), ('text')])

Class = UrbanDictionary


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
