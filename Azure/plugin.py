###
# Copyright (c) 2020, oddluck
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


import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.conf as conf
import requests


class Azure(callbacks.Plugin):


    def translate(self, irc, msg, args, optlist, text):
        """[--from <source>] [--to <target>] <text>
        Translate text using Microsoft Azure. Uses automatic language detection if source not
        set. No target uses the plugin default.
        https://docs.microsoft.com/en-us/azure/cognitive-services/translator/language-support
        """
        optlist = dict(optlist)
        if 'from' in optlist:
            source = optlist.get('from')
        else:
            source = self.registryValue('translate.source')
        if 'to' in optlist:
            target = optlist.get('to')
        else:
            target = self.registryValue('translate.target')
        if source != 'auto':
            url = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={0}&from={1}'.format(target, source)
        else:
            url = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={0}'.format(target)
        key = self.registryValue('translate.key')
        headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-type': 'application/json'
        }
        body = [{
        'text' : text
        }]
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        if result[0]['detectedLanguage']:
            reply = "{0} [{1}~>{2}]".format(result[0]['translations'][0]['text'], result[0]['detectedLanguage']['language'], target)
        else:
            reply = "{0} [{1}~>{2}]".format(source, target)
        irc.reply(reply)
    translate = wrap(translate, [getopts({'from':'text', 'to':'text'}), 'text'])


Class = Azure
