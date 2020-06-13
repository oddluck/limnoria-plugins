###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
#
###

from supybot import conf, registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('AzuraCast')
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
    conf.registerPlugin('AzuraCast', True)


AzuraCast = conf.registerPlugin('AzuraCast')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(AzuraCast, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
conf.registerGlobalValue(AzuraCast, 'AzuraAPI',
    registry.String('', _("""AzuraCast local API URL""")))
conf.registerGlobalValue(AzuraCast, 'PublicURL',
    registry.String('', _("""Public URL for your radio""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
