###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cayenne')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Cayenne', True)

Cayenne = conf.registerPlugin('Cayenne')

conf.registerChannelValue(Cayenne, 'enable',
registry.Boolean(True, _("""Turns on and off Cayenne.""")))

conf.registerGlobalValue(Cayenne, 'factChance',
                        registry.Integer(10, _("""0-100 chance to trigger a cat fact""")))

conf.registerGlobalValue(Cayenne, 'linkChance',
                        registry.Integer(10, _("""0-100 chance to trigger a link to a cat gif""")))

conf.registerGlobalValue(Cayenne, 'linkURL',
                        registry.String("http://edgecats.net/random", _("""URL to get cat gif links from""")))

conf.registerGlobalValue(Cayenne, 'throttleInSeconds',
                        registry.Integer(60, _("""Will only trigger if it has been X seconds since the last trigger""")))

conf.registerGlobalValue(Cayenne, 'triggerWords',
                        registry.CommaSeparatedListOfStrings(["meow","cat","aww","kitten","feline"], _("""List of words that may trigger facts or links""")))
         
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
