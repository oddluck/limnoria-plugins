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

conf.registerGlobalValue(SpiffyTitles, 'maxRetries',
     registry.Integer(3, _("""Maximum retries upon failure""")))

conf.registerGlobalValue(SpiffyTitles, 'wallClockTimeoutInSeconds',
     registry.Integer(8, _("""Timeout for getting a title. If you set this too high, the bot will time out.""")))

# Language
conf.registerGlobalValue(SpiffyTitles, 'language',
     registry.String("en-US", _("""Language code""")))

# imdb template
conf.registerGlobalValue(SpiffyTitles, 'imdbTemplate',
     registry.String("^ {{Title}} ({{Year}}, {{Country}}) - Rating: {{imdbRating}} ::  {{Plot}}", _("""Uses http://www.omdbapi.com to provide additional information about IMDB links""")))

# enable/disable toggles
conf.registerGlobalValue(SpiffyTitles, 'defaultHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about regular links""")))

conf.registerGlobalValue(SpiffyTitles, 'youtubeHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about YouTube videos""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about imgur links""")))

conf.registerGlobalValue(SpiffyTitles, 'imdbHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about IMDB links""")))

# URL regex
conf.registerGlobalValue(SpiffyTitles, 'urlRegularExpression',
     registry.String(r"(https?:\/\/(?:www\.|(?!www))[^\s\.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})", _("""This regular expression will be used to match URLs""")))

# Bold
conf.registerGlobalValue(SpiffyTitles, 'useBold',
     registry.Boolean(False, _("""Use bold in titles""")))

# Title template
conf.registerGlobalValue(SpiffyTitles, 'defaultTitleTemplate',
     registry.String("^ {{title}}", _("""Template used for default title responses""")))

# YouTube template
conf.registerGlobalValue(SpiffyTitles, 'youtubeTitleTemplate',
     registry.String("^ {{title}} :: Duration: {{duration}} :: Views: {{view_count}} uploaded by {{channel_title}} :: {{like_count}} likes :: {{dislike_count}} dislikes :: {{favorite_count}} favorites", _("""Template used for YouTube title responses""")))

# User agents
conf.registerGlobalValue(SpiffyTitles, 'userAgents',
                         registry.CommaSeparatedListOfStrings(["Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.60 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0", "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"], _("""Reported user agent when fetching links""")))

# Mime Types
conf.registerGlobalValue(SpiffyTitles, 'mimeTypes',
                         registry.CommaSeparatedListOfStrings(["text/html"], _("""Acceptable mime types for displaying titles""")))

# Ignored domain pattern
conf.registerGlobalValue(SpiffyTitles, 'ignoredDomainPattern',
                         registry.Regexp("", _("""Domains matching this patterns will be ignored""")))

# Whitelist domain pattern
conf.registerGlobalValue(SpiffyTitles, 'whitelistDomainPattern',
                         registry.Regexp("", _("""Domains not matching this patterns will be ignored""")))

# Channel whitelist
conf.registerGlobalValue(SpiffyTitles, 'channelWhitelist',
                         registry.CommaSeparatedListOfStrings([], _("""Only show titles on these channels, or all if empty""")))

# Channel blacklist
conf.registerGlobalValue(SpiffyTitles, 'channelBlacklist',
                        registry.CommaSeparatedListOfStrings([], _("""Never show titles on these channels""")))

# imgur API
conf.registerGlobalValue(SpiffyTitles, 'imgurClientID',
                        registry.String("", _("""imgur client ID""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurClientSecret',
                        registry.String("", _("""imgur client secret""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurTemplate',
                        registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))

conf.registerGlobalValue(SpiffyTitles, 'imgurAlbumTemplate',
                        registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{image_count}} images :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))

# Youtube API
conf.registerGlobalValue(SpiffyTitles, 'youtubeDeveloperKey',
                        registry.String("", _("""Youtube developer key - required for Youtube handler.""")))

# Link cache lifetime
conf.registerGlobalValue(SpiffyTitles, 'linkCacheLifetimeInSeconds',
                        registry.Integer(60, _("""Link cache lifetime in seconds""")))                    
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
