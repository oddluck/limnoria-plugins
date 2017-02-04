###
# Copyright (c) 2016, liriel
# All rights reserved.
#
#
###

from supybot.test import *
import os
#The plugin name will be based on the plugin's folder.
PluginName=os.path.dirname( __file__ ).split(os.sep)[-1]

class TestCase(PluginTestCase):
    plugins = (PluginName,)

TestCase.__name__=PluginName+'TestCase'

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
