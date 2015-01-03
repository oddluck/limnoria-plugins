###
# Copyright (c) 2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class WorldTimeTestCase(PluginTestCase):
    plugins = ('WorldTime',)
    config = {'supybot.plugins.WorldTime.disableANSI': True}

    def setUp(self):
        PluginTestCase.setUp(self)
        self.prefix = 'foo!bar@baz'

    def testWorldTime(self):
        # New York, NY, USA :: Current local time is: Thu, 12:02 (Eastern Daylight Time)
        self.assertRegexp('worldtime New York, NY', 'New York\, NY\, USA')
        self.assertRegexp('worldtime Chicago', 'Current local time is')

    def testWorldTimeDb(self):
        self.assertError('worldtime') # Fail if location not set & none is given
        self.assertNotError('set Vancouver, BC')
        self.assertRegexp('worldtime', 'Vancouver') # Should work if location is set
        self.assertNotError('unset') # Unsetting location should work,
        self.assertError('unset') # But only once.

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
