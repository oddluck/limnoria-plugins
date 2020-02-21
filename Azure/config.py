###
# Copyright (c) 2020, oddluck
# All rights reserved.
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Azure')
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
    conf.registerPlugin('Azure', True)


Azure = conf.registerPlugin('Azure')

conf.registerGroup(Azure, 'translate')

conf.registerGlobalValue(Azure.translate, 'key',
    registry.String('', _("""The Azure API translation key
    (required)"""), private=True))

conf.registerChannelValue(Azure.translate, 'target',
    registry.String('en', _("""The default target language for the
    translate command."""), private=True))

conf.registerChannelValue(Azure.translate, 'source',
    registry.String('auto', _("""The default source language for the translate
    command. Default is 'auto' for automatic language detection."""), private=True))
