import supybot.conf as conf
import supybot.registry as registry

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Geo')
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
    conf.registerPlugin('Geo', True)


Geo = conf.registerPlugin('Geo')
conf.registerGlobalValue(Geo, 'datalastupdated',
    registry.PositiveInteger(1, """An integer representing the time since epoch the .dat file was last updated."""))

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
