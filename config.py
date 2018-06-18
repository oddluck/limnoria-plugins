###
# Copyright (c) 2014, SpiderDave
# Copyright (c) 2016-2017 Ormanya
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
import os
try:
    from supybot.i18n import PluginInternationalization, internationalizeDocstring
except:
    PluginInternationalization, internationalizeDocstring = lambda x:x, lambda x:x

#The plugin name will be based on the plugin's folder.
PluginName=os.path.dirname( __file__ ).split(os.sep)[-1]

_ = PluginInternationalization(PluginName)

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin(PluginName, True)

Trackers = conf.registerPlugin('Trackers')

conf.registerGroup(Trackers, 'announce')
conf.registerChannelValue(Trackers.announce, 'seconds',
    registry.PositiveInteger(10, _("""Determines the amount of time in seconds the bot should
        announce tracker statuses.""")))

_events = {'ab':False, 'ahd':False, 'ar':False, 'btn':False, 'emp':False, 'ggn':False, 'mtv':False, 'nbl':False, 'nwcd':False, '32p':False, 'ptp':False, 'red':False}
for ev in _events:
    conf.registerChannelValue(Trackers.announce, 'relay%s' % ev,
        registry.Boolean(_events[ev], """Determines whether the bot should announce status for %s.""" % ev))


P = conf.registerPlugin(PluginName)
P.__name__ = PluginName

# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(PluginName, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
