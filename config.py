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

# URL regex
conf.registerGlobalValue(SpiffyTitles, 'urlRegularExpression',
     registry.String(r"(https?:\/\/(?:www\.|(?!www))[^\s\.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})", _("""This regular expression will be used to match URLs""")))

# Bold
conf.registerGlobalValue(SpiffyTitles, 'useBold',
     registry.Boolean(False, _("""Use bold in titles""")))

# Title template
conf.registerGlobalValue(SpiffyTitles, 'defaultTitleTemplate',
     registry.String("^ $title", _("""Template used for default title responses""")))

# YouTube template
conf.registerGlobalValue(SpiffyTitles, 'youtubeTitleTemplate',
     registry.String("^ $title :: Duration: $duration :: Views: $view_count :: Rating: $rating", _("""Template used for YouTube title responses""")))

# User agents
conf.registerGlobalValue(SpiffyTitles, 'userAgents',
                        registry.CommaSeparatedListOfStrings(["Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.60 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0", "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"], _("""Reported user agent when fetching links""")))

# Mime Types
conf.registerGlobalValue(SpiffyTitles, 'mimeTypes',
                        registry.CommaSeparatedListOfStrings(["text/html"], _("""Acceptable mime types for displaying titles""")))

# Ignored domain pattern
conf.registerGlobalValue(SpiffyTitles, 'ignoredDomainPattern',
                        registry.Regexp(r"(i\.imgur\.com)", _("""Domains matching this patterns will be ignored""")))

# Channel whitelist
conf.registerGlobalValue(SpiffyTitles, 'channelWhitelist',
                        registry.CommaSeparatedListOfStrings([], _("""Only show titles on these channels, or all if empty""")))

# Channel blacklist
conf.registerGlobalValue(SpiffyTitles, 'channelBlacklist',
                        registry.CommaSeparatedListOfStrings([], _("""Never show titles on these channels""")))

# Cooldown
conf.registerGlobalValue(SpiffyTitles, 'cooldownInSeconds',
                        registry.Integer(5, _("""Only show titles from each url every X seconds""")))

# imgur API
conf.registerGlobalValue(SpiffyTitles, 'imgurClientID',
                        registry.String("", _("""imgur client ID""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurClientSecret',
                        registry.String("", _("""imgur client secret""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurTemplate',
                        registry.String("^ $title :: $type $widthx$height $file_size :: $view_count views :: $nsfw", _("""imgur template""")))
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
