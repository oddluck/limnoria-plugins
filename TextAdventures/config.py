###
# Copyright (c) 2019, oddluck
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('TextAdventures')
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
    conf.registerPlugin('TextAdventures', True)

TextAdventures = conf.registerPlugin('TextAdventures')

conf.registerGlobalValue(TextAdventures, 'dfrotzPath',
        registry.String('/usr/local/bin/dfrotz', _("""The path to the dfrotz executable.""")))

conf.registerGlobalValue(TextAdventures, 'allowPrivate',
        registry.Boolean('True', _("""Allow games to be played over private message.""")))

conf.registerChannelValue(TextAdventures, 'requireCommand',
        registry.Boolean('False', _("""Require game input to be sent via command. Disables 
        monitoring of chanel messages for game input.""")))

TextAdventures = conf.registerPlugin('TextAdventures')
