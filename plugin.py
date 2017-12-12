# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###
# my libs
from collections import defaultdict
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WolframAlpha')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class WolframAlpha(callbacks.Plugin):
    """Add the help for "@plugin help WolframAlpha" here
    This should describe *how* to use this plugin."""
    threaded = True

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _red(self, s):
        return ircutils.mircColor(s, 'red')

    def _bold(self, s):
        return ircutils.bold(s)

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    # API Documentation. http://products.wolframalpha.com/api/documentation.html
    def wolframalpha(self, irc, msg, args, optlist, optinput):
        """[--num #|--reinterpret|--usemetric|--shortest|--fulloutput] <query>

        Returns answer from Wolfram Alpha API.

        Use --num number to display a specific amount of lines.
        Use --reinterpret to have WA logic to interpret question if not understood.
        Use --usemetric to not display in imperial units.
        Use --shortest for the shortest output (ignores lines).
        Use --fulloutput to display everything from the API (can flood).
        """

        # check for API key before we can do anything.
        apiKey = self.registryValue('apiKey')
        if not apiKey or apiKey == "Not set":
            irc.reply("Wolfram Alpha API key not set. see 'config help supybot.plugins.WolframAlpha.apiKey'.")
            return
        # first, url arguments, some of which getopts and config variables can manipulate.
        urlArgs = { 'input':optinput,
                    'appid':apiKey,
                    'reinterpret':'false',
                    'format':'plaintext',
                    'units':'nonmetric' }
        # check for config variables to manipulate URL arguments.
        if not self.registryValue('useImperial'):
            urlArgs['units'] = 'metric'
        if self.registryValue('reinterpretInput'):
            urlArgs['reinterpret'] = 'true'
        # now handle input. default input arguments.
        args = { 'maxoutput': self.registryValue('maxOutput'),
                 'shortest':None,
                 'fulloutput':None }
        # handle getopts (optlist)
        if optlist:
            for (key, value) in optlist:
                if key == 'shortest':
                    args['shortest'] = True
                if key == 'fulloutput':
                    args['fulloutput'] = True
                if key == 'num':
                    args['maxoutput'] = value
                if key == 'usemetric':
                    urlArgs['units'] = 'metric'
                if key == 'reinterpret':
                    urlArgs['reinterpret'] = 'true'
        # build url and query.
        url = 'http://api.wolframalpha.com/v2/query?' + utils.web.urlencode(urlArgs)
        try:
            page = utils.web.getUrl(url)
        except Exception as e:
            self.log.error("ERROR opening {0} message: {1}".format(url, e))
            irc.reply("ERROR: Failed to open WolframAlpha API: {0}".format(url))
            return
        # now try to process XML.
        try:
            document = ElementTree.fromstring(page)
        except Exception as e:
            self.log.error("ERROR: Broke processing XML: {0}".format(e))
            irc.reply("ERROR: Something broke processing XML from WolframAlpha's API.")
            return
        #document = ElementTree.fromstring(page) #.decode('utf-8'))
        # check if we have an error. reports to irc but more detailed in the logs.
        if document.attrib['success'] == 'false' and document.attrib['error'] == 'true':
            errormsgs = []
            for error in document.findall('.//error'):
                errorcode = error.find('code').text.encode('utf-8')
                errormsg = error.find('msg').text.encode('utf-8')
                errormsgs.append("{0} - {1}".format(errorcode, errormsg))
            # log and report to irc if we have these.
            self.log.debug("ERROR processing request for: {0} message: {1}".format(optinput, errormsgs))
            irc.reply("ERROR: Something went wrong processing request for: {0} ERROR: {1}".format(optinput, errormsgs))
            return
        # check if we have no success but also no error. (Did you mean?)
        elif document.attrib['success'] == 'false' and document.attrib['error'] == 'false':
            errormsgs = []  # list to contain whatever is there.
            for error in document.findall('.//futuretopic'):
                errormsg = error.attrib['msg'].encode('utf-8')
                errormsgs.append("FUTURE TOPIC: {0}".format(errormsg))
            for error in document.findall('.//didyoumeans'):
                errormsg = error.find('didyoumean').text.encode('utf-8')
                errormsgs.append("Did you mean? {0}".format(errormsg))
            for error in document.findall('.//tips'):
                errormsg = error.find('tip').attrib['text'].text.encode('utf-8')
                errormsgs.append("TIPS: {0}".format(errormsg))
            # now output the messages to irc and log.
            self.log.debug("ERROR with input: {0} API returned: {1}".format(optinput, errormsgs))
            irc.reply("ERROR with input: {0} API returned: {1}".format(optinput, errormsgs))
            return
        else:  # this means we have success and no error messages.
            # each pod has a title, position and a number of subtexts. output contains the plaintext.
            # outputlist is used in sorting since defaultdict does not remember order/position.
            output = defaultdict(list)
            outputlist = {}
            # each answer has a different amount of pods.
            for pod in document.findall('.//pod'):
                title = pod.attrib['title'].encode('utf-8')  # title of it.
                position = int(pod.attrib['position'])  # store pods int when we sort.
                outputlist[position] = title  # pu
                for plaintext in pod.findall('.//plaintext'):
                    if plaintext.text:
                        output[title].append(plaintext.text.encode('utf-8').replace('\n',' '))
        # last sanity check...
        if len(output) == 0:
            irc.reply("ERROR: I received no output looking up: {0}".format(optinput))
            return
        # done processing the XML so lets work on the output.
        # the way we output is based on args above, controlled by getopts.
        if args['shortest']:  # just show the question and answer.
            # outputlist has pod titles, ordered by importance, not every input has a clear Input/Result (question/answer).
            outputlist = [outputlist[item] for item in sorted(outputlist.keys())]
            question = output.get(outputlist[0])  # get first (question).
            answer = output.get(outputlist[1])  # get second (answer).
            # output time. display with color or not?
            if self.registryValue('disableANSI'):
                irc.reply("{0} :: {1}".format("".join([i for i in question]), "".join([i for i in answer])))
            else:  # with ansi.
                irc.reply("{0} :: {1}".format(self._bold("".join([i for i in question])), "".join([i for i in answer])))
        elif args['fulloutput']: # show everything. no limits.
            # grab all values, sorted via the position number. output one per line.
            for (k, v) in sorted(outputlist.items()):
                itemout = output.get(v)  # items out will be a list of items.
                # now decide to output with ANSI or not.
                if self.registryValue('disableANSI'):
                    irc.reply("{0} :: {1}".format(v, "".join(itemout)))
                else:  # with ansi.
                    irc.reply("{0} :: {1}".format(self._red(v), "".join(itemout)))
        else:  # regular output, dictated by --lines or maxoutput.
            for q, k in enumerate(sorted(outputlist.keys())):
                if q < args['maxoutput']:  # if less than max.
                    itemout = output.get(outputlist[k])  # have the key, get the value, use for output.
                    if itemout:
                        if self.registryValue('disableANSI'):  # display w/o formatting.
                            irc.reply("{0} :: {1}".format(outputlist[k], "".join(itemout)))
                        else:  # display w/formatting.
                            irc.reply("{0} :: {1}".format(self._red(outputlist[k]), "".join(itemout)))

    wolframalpha = wrap(wolframalpha, [getopts({'num':('int'),
                                                'reinterpret':'',
                                                'usemetric':'',
                                                'shortest':'',
                                                'fulloutput':''}), ('text')])


Class = WolframAlpha


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
