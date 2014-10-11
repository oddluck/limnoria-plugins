###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class UrbanDictionaryTestCase(PluginTestCase):
    plugins = ('UrbanDictionary',)

    def testUrbanDictionary(self):
        conf.supybot.plugins.UrbanDictionary.disableANSI.setValue('True')
        self.assertRegexp('urbandictionary hello', 'hello :: what you say when your talking casually with friends and your mom walks in the room')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
