###
# Copyright (c) 2015, PrgmrBill
# All rights reserved.
#
#
###

from supybot.test import *


class SpiffyTitlesTestCase(ChannelPluginTestCase):
    plugins = ('SpiffyTitles',)

    def setUp(self):
        ChannelPluginTestCase.setUp(self)
        
        self.assertNotError('reload SpiffyTitles')

    
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
