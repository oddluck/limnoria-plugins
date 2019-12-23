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

# URL regex
conf.registerGlobalValue(SpiffyTitles, 'urlRegularExpression',
     registry.String(r"(https?:\/\/(?:www\.|(?!www))[^\s\.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})", _("""This regular expression will be used to match URLs""")))

# Bold
conf.registerChannelValue(SpiffyTitles, 'useBold',
     registry.Boolean(False, _("""Use bold in titles""")))

# User agents
conf.registerGlobalValue(SpiffyTitles, 'userAgents',
     registry.CommaSeparatedListOfStrings(["Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.60 Safari/537.36", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0", "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"], _("""Reported user agent when fetching links""")))

# Mime Types
conf.registerGlobalValue(SpiffyTitles, 'mimeTypes',
     registry.CommaSeparatedListOfStrings(["text/html"], _("""Acceptable mime types for displaying titles""")))

# Ignored domain pattern
conf.registerChannelValue(SpiffyTitles, 'ignoredDomainPattern',
     registry.Regexp("", _("""Domains matching this patterns will be ignored""")))

# Whitelist domain pattern
conf.registerChannelValue(SpiffyTitles, 'whitelistDomainPattern',
     registry.Regexp("", _("""Domains not matching this patterns will be ignored""")))

# Channel whitelist
conf.registerGlobalValue(SpiffyTitles, 'channelWhitelist',
     registry.CommaSeparatedListOfStrings([], _("""Only show titles on these channels, or all if empty""")))

# Channel blacklist
conf.registerGlobalValue(SpiffyTitles, 'channelBlacklist',
    registry.CommaSeparatedListOfStrings([], _("""Never show titles on these channels""")))

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



#default configs
conf.registerGroup(SpiffyTitles, 'default')

conf.registerChannelValue(SpiffyTitles.default, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about regular links""")))

# default title template - show a warning if redirects to a different domain
conf.registerChannelValue(SpiffyTitles.default, 'template',
     registry.String("{% if redirect %}(REDIRECT) {% endif %}^ {{title}}", _("""Template used for default title responses""")))



#Wikipedia configs
conf.registerGroup(SpiffyTitles, 'wikipedia')

#wikipedia enabler
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



#Reddit configs
conf.registerGroup(SpiffyTitles, 'reddit')

#Reddit enabler
conf.registerChannelValue(SpiffyTitles.reddit, 'enabled',
    registry.Boolean(True, _("""Whether to add additional info about Reddit links.""")))

#Reddit templates
conf.registerChannelValue(SpiffyTitles.reddit, 'linkThreadTemplate',
     registry.String(u"/r/{{subreddit}}{% if title %} :: {{title}}{% endif %} :: {{score}} points ({{percent}}) :: {{comments}} comments :: Posted {{age}} by {{author}}{% if url %} :: {{url}} ({{domain}}){% endif %}", _("""Template used for Reddit link thread title responses""")))

conf.registerChannelValue(SpiffyTitles.reddit, 'textThreadTemplate',
     registry.String(u"/r/{{subreddit}}{% if title %} :: {{title}}{% endif %}{% if extract %} :: {{extract}}{% endif %} :: {{score}} points ({{percent}}) :: {{comments}} comments :: Posted {{age}} by {{author}}", _("""Template used for Reddit text thread title responses""")))

conf.registerChannelValue(SpiffyTitles.reddit, 'commentTemplate',
     registry.String(u"/r/{{subreddit}}{% if extract %} :: {{extract}}{% endif %} :: {{score}} points :: Posted {{age}} by {{author}} on \"{{title}}\"", _("""Template used for Reddit comment title responses""")))

conf.registerChannelValue(SpiffyTitles.reddit, 'userTemplate',
     registry.String(u"/u/{{user}}{% if gold %} :: (GOLD{% if mod %}, MOD{% endif %}){% endif %} :: Joined: {{created}} :: Link karma: {{link_karma}} :: Comment karma: {{comment_karma}}", _("""Template used for Reddit user page title responses""")))

#Reddit max characters
conf.registerChannelValue(SpiffyTitles.reddit, 'maxChars',
    registry.Integer(400, _("""Length of response (title/extract will be cut to fit).""")))



#YouTube configs
conf.registerGroup(SpiffyTitles, 'youtube')

#youtube enabler
conf.registerChannelValue(SpiffyTitles.youtube, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about YouTube videos""")))

# Youtube API
conf.registerGlobalValue(SpiffyTitles.youtube, 'developerKey',
    registry.String("", _("""Youtube developer key - required for Youtube handler."""), private=True))
# YouTube Logo
conf.registerChannelValue(SpiffyTitles.youtube, 'logo',
    registry.String("\x030,4 ► \x031,0YouTube", _("""Logo used with {{yt_logo}} in template""")))
# YouTube template
conf.registerChannelValue(SpiffyTitles.youtube, 'template',
     registry.String("^ {{yt_logo}} :: {{title}} {%if timestamp%} @ {{timestamp}}{% endif %} :: Duration: {{duration}} :: Views: {{view_count}} uploaded by {{channel_title}} :: {{like_count}} likes :: {{dislike_count}} dislikes :: {{favorite_count}} favorites", _("""Template used for YouTube title responses""")))



#imgur configs
conf.registerGroup(SpiffyTitles, 'imgur')

#imgur enabler
conf.registerChannelValue(SpiffyTitles.imgur, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about imgur links""")))

# imgur API
conf.registerGlobalValue(SpiffyTitles.imgur, 'clientID',
    registry.String("", _("""imgur client ID"""), private=True))

conf.registerGlobalValue(SpiffyTitles.imgur, 'clientSecret',
    registry.String("", _("""imgur client secret"""), private=True))

conf.registerChannelValue(SpiffyTitles.imgur, 'template',
    registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))

conf.registerChannelValue(SpiffyTitles.imgur, 'albumTemplate',
    registry.String("^{%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{image_count}} images :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}", _("""imgur template""")))



#dailymotion configs
conf.registerGroup(SpiffyTitles, 'dailymotion')

#dailymotion enabler
conf.registerChannelValue(SpiffyTitles.dailymotion, 'enabled',
     registry.Boolean(True, _("""Enable additional information about dailymotion videos""")))

# dailymotion template
conf.registerChannelValue(SpiffyTitles.dailymotion, 'template',
     registry.String("^ [{{ownerscreenname}}] {{title}} :: Duration: {{duration}} :: {{views_total}} views", _("""Template used for Vimeo title responses""")))



#Twitch configs
conf.registerGroup(SpiffyTitles, 'twitch')

#twitch enabler
conf.registerChannelValue(SpiffyTitles.twitch, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about Twitch links""")))

#Twitch API Key
conf.registerGlobalValue(SpiffyTitles.twitch, 'clientID',
     registry.String('', _("""Twitch API Client_ID""")))

# Twitch Logo
conf.registerChannelValue(SpiffyTitles.twitch, 'logo',
     registry.String("\x030,6💬twitch", _("""Logo used with {{twitch_logo}} in template""")))

conf.registerChannelValue(SpiffyTitles.twitch, 'channelTemplate',
     registry.String("^ {{twitch_logo}} :: {{display_name}} {%if description%}:: {{description}} {%endif%}:: Viewers: {{view_count}}", _("""twitch.tv channel template""")))

conf.registerChannelValue(SpiffyTitles.twitch, 'streamTemplate',
     registry.String("^ {{twitch_logo}} :: {{display_name}} :: (LIVE) {%if game_name%}[{{game_name}}] {%endif%}{%if title%}:: {{title}} {%endif%}:: Created: {{created_at}} :: Viewers: {{view_count}} {%if description%}:: {{description}}{%endif%}", _("""twitch.tv stream template""")))

conf.registerChannelValue(SpiffyTitles.twitch, 'videoTemplate',
     registry.String("^ {{twitch_logo}} :: {{display_name}} {%if title%}:: {{title}} {%endif%}}:: Duration: {{duration}} :: Created: {{created_at}} {%if description%}:: {{description}} {%endif%}:: Viewers: {{view_count}}", _("""twitch.tv video template""")))

conf.registerChannelValue(SpiffyTitles.twitch, 'clipTemplate',
     registry.String("^ {{twitch_logo}} :: {{display_name}} {%if game_name%}:: [{{game_name}}] {%endif%}{%if title%}:: {{title}} {%endif%}:: Created: {{created_at}} :: Viewers: {{view_count}} {%if description%}:: {{description}}{%endif%}", _("""twitch.tv clip template""")))



#vimeo configs
conf.registerGroup(SpiffyTitles, 'vimeo')

#vimeo enabler
conf.registerChannelValue(SpiffyTitles.vimeo, 'enabled',
     registry.Boolean(True, _("""Enable additional information about Vimeo videos""")))

# Vimeo template
conf.registerChannelValue(SpiffyTitles.vimeo, 'template',
     registry.String("^ {{title}} :: Duration: {{duration}} :: {{stats_number_of_plays}} plays :: {{stats_number_of_comments}} comments", _("""Template used for Vimeo title responses""")))



#IMDB configs
conf.registerGroup(SpiffyTitles, 'imdb')

#imdb enabler
conf.registerChannelValue(SpiffyTitles.imdb, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about IMDB links""")))

#OMDB API Key
conf.registerGlobalValue(SpiffyTitles.imdb, 'omdbAPI',
     registry.String('', _("""OMDB API Key""")))

# IMDB Logo
conf.registerChannelValue(SpiffyTitles.imdb, 'logo',
     registry.String("\x031,8IMDb", _("""Logo used with {{imdb_logo}} in template""")))

# IMDB template
conf.registerChannelValue(SpiffyTitles.imdb, 'template',
     registry.String("^ {{imdb_logo}} :: {{title}} ({{year}}, {{country}} [{{rated}}], {{genre}}, {{runtime}}) ::  IMDB: {{imdb_rating}} MC: {{metascore}} :: {{plot}}", _("""IMDB title template""")))



#coub configs
conf.registerGroup(SpiffyTitles, 'coub')

#coub enabler
conf.registerChannelValue(SpiffyTitles.coub, 'enabled',
     registry.Boolean(True, _("""Whether to add additional information about coub links""")))

# coub template
conf.registerChannelValue(SpiffyTitles.coub, 'template',
     registry.String("^ {%if not_safe_for_work %}NSFW{% endif %} [{{channel.title}}] {{title}} :: {{views_count}} views :: {{likes_count}} likes :: {{recoubs_count}} recoubs", _("""Uses Coub API to get additional information about coub.com links""")))
