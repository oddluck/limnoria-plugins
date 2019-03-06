# Copyright (c) 2013-2014, spline
###

from supybot.test import *
import os

class TweetyTestCase(PluginTestCase):
    plugins = ('Tweety',)

    def setUp(self):
        PluginTestCase.setUp(self)
        # get our variables via the secure environment.
        consumerKey = os.environ.get('consumerKey')
        consumerSecret = os.environ.get('consumerSecret')
        accessKey = os.environ.get('accessKey')
        accessSecret = os.environ.get('accessSecret')
        # now set them.
        conf.supybot.plugins.Tweety.consumerKey.setValue(consumerKey)
        conf.supybot.plugins.Tweety.consumerSecret.setValue(consumerSecret)
        conf.supybot.plugins.Tweety.accessKey.setValue(accessKey)
        conf.supybot.plugins.Tweety.accessSecret.setValue(accessSecret)

    def testTweety(self):
        self.assertSnarfResponse('reload Tweety', 'The operation succeeded.')
        self.assertRegexp('trends', 'Top 10 Twitter Trends')
        self.assertRegexp('twitter --info CNN', 'CNN')
        self.assertRegexp('twitter CNN', 'CNN')
        
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
