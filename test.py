# Copyright (c) 2013-2014, spline
###

from supybot.test import *
import os

class TweetyTestCase(PluginTestCase):
    plugins = ('Tweety',)

    def testTweety(self):
        t = os.environ.get('test')
        print t

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
