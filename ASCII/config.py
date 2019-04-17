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
    _ = PluginInternationalization('ASCII')
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
    conf.registerPlugin('ASCII', True)

ASCII = conf.registerPlugin('ASCII')

conf.registerGlobalValue(ASCII, 'pasteAPI',
registry.String('', _("""Paste.ee API Key""")))

conf.registerChannelValue(ASCII, 'pasteEnable',
registry.Boolean(False, _("""Turns on and off paste.ee support""")))

conf.registerChannelValue(ASCII, 'delay',
registry.Float(1.0, _("""Set the time delay betwen lines""")))

conf.registerChannelValue(ASCII, 'waitMessage',
registry.String("Please be patient while I render the image into ASCII characters and colorize the output.", _("""Set the wait message text""")))
