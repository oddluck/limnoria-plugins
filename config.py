###
# Copyright (c) 2015, butterscotchstallion
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

# alternative template:
#                     ^ {{Title}} ({{Year}} - {{Director}}) :: [i:{{imdbRating}} r:{{tomatoMeter}} m:{{Metascore}}] {{Plot}}

conf.registerGlobalValue(SpiffyTitles, 'coubTemplate',
     registry.String("^ {%if not_safe_for_work %}NSFW{% endif %} [{{channel.title}}] {{title}} :: {{views_count}} views :: {{likes_count}} likes :: {{recoubs_count}} recoubs", _("""Uses Coub API to get additional information about coub.com links""")))

# enable/disable toggles
conf.registerChannelValue(SpiffyTitles, 'coubHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about coub links""")))

conf.registerChannelValue(SpiffyTitles, 'defaultHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about regular links""")))

conf.registerChannelValue(SpiffyTitles, 'youtubeHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about YouTube videos""")))

conf.registerChannelValue(SpiffyTitles, 'imgurHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about imgur links""")))

conf.registerChannelValue(SpiffyTitles, 'imdbHandlerEnabled',
     registry.Boolean(True, _("""Whether to add additional information about IMDB links""")))

# URL regex
conf.registerGlobalValue(SpiffyTitles, 'urlRegularExpression',
     registry.String(r"(https?:\/\/(?:www\.|(?!www))[^\s\.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})", _("""This regular expression will be used to match URLs""")))

# Bold
conf.registerChannelValue(SpiffyTitles, 'useBold',
     registry.Boolean(False, _("""Use bold in titles""")))

# Title template
conf.registerChannelValue(SpiffyTitles, 'defaultTitleTemplate',
     registry.String("^ {{title}}", _("""Template used for default title responses""")))

# YouTube template
conf.registerChannelValue(SpiffyTitles, 'youtubeTitleTemplate',
     registry.String("^ {{yt_logo}} :: {{title}} {%if timestamp%} @ {{timestamp}}{% endif %} :: Duration: {{duration}} :: Views: {{view_count}} uploaded by {{channel_title}} :: {{like_count}} likes :: {{dislike_count}} dislikes :: {{favorite_count}} favorites", _("""Template used for YouTube title responses""")))

# Vimeo template
conf.registerChannelValue(SpiffyTitles, 'vimeoTitleTemplate',
     registry.String("^ {{title}} :: Duration: {{duration}} :: {{stats_number_of_plays}} plays :: {{stats_number_of_comments}} comments", _("""Template used for Vimeo title responses""")))

conf.registerChannelValue(SpiffyTitles, 'vimeoHandlerEnabled',
     registry.Boolean(True, _("""Enable additional information about Vimeo videos""")))

# dailymotion template
conf.registerChannelValue(SpiffyTitles, 'dailymotionVideoTitleTemplate',
     registry.String("^ [{{ownerscreenname}}] {{title}} :: Duration: {{duration}} :: {{views_total}} views", _("""Template used for Vimeo title responses""")))

conf.registerChannelValue(SpiffyTitles, 'dailymotionHandlerEnabled',
     registry.Boolean(True, _("""Enable additional information about dailymotion videos""")))

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
                        registry.String("", _("""imgur client ID"""), private=True))

conf.registerGlobalValue(SpiffyTitles, 'imgurClientSecret',
                        registry.String("", _("""imgur client secret"""), private=True))

conf.registerChannelValue(SpiffyTitles, 'imgurTemplate',
                        registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))

conf.registerChannelValue(SpiffyTitles, 'imgurAlbumTemplate',
                        registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{image_count}} images :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))

# Youtube API
conf.registerGlobalValue(SpiffyTitles, 'youtubeDeveloperKey',
                        registry.String("", _("""Youtube developer key - required for Youtube handler."""), private=True))

# Link cache lifetime
conf.registerGlobalValue(SpiffyTitles, 'linkCacheLifetimeInSeconds',
                        registry.Integer(60, _("""Link cache lifetime in seconds""")))

conf.registerChannelValue(SpiffyTitles, 'onDemandTitleError',
                        registry.String("Error retrieving title.", _("""This error message is used when there is a problem getting an on-demand title""")))
                        
conf.registerGlobalValue(SpiffyTitles, 'linkMessageIgnorePattern',
                        registry.Regexp("", _("""Messages matching this pattern will be ignored.""")))
                        
conf.registerChannelValue(SpiffyTitles, 'ignoreActionLinks',
     registry.Boolean(True, _("""Ignores URLs that appear in an action such as /me""")))

conf.registerChannelValue(SpiffyTitles, 'requireCapability',
     registry.String("", _("""If defined, SpiffyTitles will only acknowledge links from users with this capability. Useful for hostile environments.""")))

conf.registerChannelValue(SpiffyTitles, 'ignoredTitlePattern',
                        registry.Regexp("", _("""Titles matching this pattern will be ignored.""")))


conf.registerGroup(SpiffyTitles, 'wikipedia')

conf.registerChannelValue(SpiffyTitles.wikipedia, 'enabled',
                        registry.Boolean(True, _("""Whether to fetch extracts for Wikipedia articles.""")))

conf.registerChannelValue(SpiffyTitles.wikipedia, 'apiParams',
                        registry.SpaceSeparatedListOfStrings([], _("""Add or override API query parameters with a space-separated list of key=value pairs.""")))

conf.registerChannelValue(SpiffyTitles.wikipedia, 'titleParam',
                        registry.String("titles", _("""The query parameter that will hold the page title from the URL.""")))

# Ideally, links to specific article sections would produce the relevant output for that section. This is not currently implemented.
conf.registerChannelValue(SpiffyTitles.wikipedia, 'ignoreSectionLinks',
                        registry.Boolean(True, _("""Ignore links to specific article sections.""")))

conf.registerChannelValue(SpiffyTitles.wikipedia, 'maxChars',
                        registry.Integer(240, _("""Extract will be cut to this length (including '...').""")))

# Remove parenthesized text from output.
conf.registerChannelValue(SpiffyTitles.wikipedia, 'removeParentheses',
                        registry.Boolean(True, _("""Remove parenthesized text from output.""")))

conf.registerChannelValue(SpiffyTitles.wikipedia, 'extractTemplate',
                        registry.String("^ {{extract}}", _("""Wikipedia template.""")))
