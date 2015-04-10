###
# Copyright (c) 2015, PrgmrBill
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('SpiffyTitles')
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
    conf.registerPlugin('SpiffyTitles', True)


SpiffyTitles = conf.registerPlugin('SpiffyTitles')
# This is where your configuration variables (if any) should go.  For example:
conf.registerGlobalValue(SpiffyTitles, 'urlRegularExpression',
     registry.String(r"(https?:\/\/(?:www\.|(?!www))[^\s\.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})", _("""This regular expression will be used to match URLs""")))

conf.registerGlobalValue(SpiffyTitles, 'useBold',
     registry.Boolean(False, _("""Use bold in titles""")))

conf.registerGlobalValue(SpiffyTitles, 'defaultTitleTemplate',
     registry.String("^ %s", _("""Template used for default title responses""")))

conf.registerGlobalValue(SpiffyTitles, 'youtubeTitleTemplate',
     registry.String("^ %s :: Views: %s :: Rating: %s", _("""Template used for YouTube title responses""")))
     
conf.registerGlobalValue(SpiffyTitles, 'userAgents',
                        registry.CommaSeparatedListOfStrings(["Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.60 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0", "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"], _("""Reported user agent when fetching links""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
