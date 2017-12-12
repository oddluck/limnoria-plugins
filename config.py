###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WolframAlpha')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('WolframAlpha', True)


WolframAlpha = conf.registerPlugin('WolframAlpha')
conf.registerGlobalValue(WolframAlpha, 'apiKey', registry.String('', ("""Your Wolfram Alpha API key."""), private=True))
conf.registerGlobalValue(WolframAlpha, 'maxOutput', registry.Integer(4, ("""How many lines by default to output.""")))
conf.registerGlobalValue(WolframAlpha, 'useImperial', registry.Boolean(True, ("""Use imperial units? Defaults to yes.""")))
conf.registerGlobalValue(WolframAlpha, 'reinterpretInput', registry.Boolean(False, ("""Reinterpret input string if WA API cannot understand. Best to leave false.""")))
conf.registerChannelValue(WolframAlpha, 'disableANSI', registry.Boolean(False, """Do not display any ANSI (color/bold) for channel."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=250:
