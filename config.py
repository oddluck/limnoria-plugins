###
# Copyright (c) 2014, spline
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WorldTime')
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
    conf.registerPlugin('WorldTime', True)


WorldTime = conf.registerPlugin('WorldTime')
# This is where your configuration variables (if any) should go.  For example:
conf.registerChannelValue(WorldTime, 'disableANSI', registry.Boolean(False, _("""Disable color/bolding for WorldTime output in channel.""")))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
