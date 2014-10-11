###
# Copyright (c) 2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class WorldTimeTestCase(PluginTestCase):
    plugins = ('WorldTime',)
    
    def testWorldTime(self):
        # New York, NY, USA :: Current local time is: Thu, 12:02 (Eastern Daylight Time)
        conf.supybot.plugins.WorldTime.disableANSI.setValue('True')
        self.assertRegexp('worldtime New York, NY', 'New York\, NY\, USA')
        self.assertRegexp('worldtime Chicago', 'Current local time is')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
