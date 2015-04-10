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
    
    def test_is_url(self):
        actual = self.is_url("http://google.com")
        
        self.assertTrue(actual)
    
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
