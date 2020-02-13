###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

import os
from supybot.test import *


class WolframAlphaTestCase(PluginTestCase):
    plugins = ('WolframAlpha',)
    
    def testWolframAlpha(self):
        apiKey = os.environ.get('apiKey')
        conf.supybot.plugins.WolframAlpha.apiKey.setValue(apiKey)
        conf.supybot.plugins.WolframAlpha.disableANSI.setValue('True')
        self.assertResponse('wolframalpha --shortest 2+2', '2+2 :: 4')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
