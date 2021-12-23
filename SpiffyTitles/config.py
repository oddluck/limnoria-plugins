###
# Copyright (c) 2015, butterscotchstallion
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import supybot.conf as conf
import supybot.registry as registry

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("SpiffyTitles")
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

    conf.registerPlugin("SpiffyTitles", True)


SpiffyTitles = conf.registerPlugin("SpiffyTitles")

conf.registerGlobalValue(
    SpiffyTitles,
    "maxRetries",
    registry.Integer(3, _("""Maximum retries upon failure""")),
)

conf.registerGlobalValue(
    SpiffyTitles,
    "timeout",
    registry.Integer(10, _("""Maximum time in seconds to try and retrieve a link""")),
)

# URL regex
conf.registerChannelValue(
    SpiffyTitles,
    "urlRegexp",
    registry.String(
        r"", _("""If set, this regular expression will be used to match URLs"""),
    ),
)

# Bold
conf.registerChannelValue(
    SpiffyTitles, "useBold", registry.Boolean(False, _("""Use bold in titles"""))
)

# Bad link text
conf.registerChannelValue(
    SpiffyTitles,
    "badLinkText",
    registry.String(
        "Error retrieving title. Check the log for more details.",
        _("""Title to return for bad/unsnarfable links."""),
    ),
)

# Ignored domain pattern
conf.registerChannelValue(
    SpiffyTitles,
    "ignoredDomainPattern",
    registry.Regexp("", _("""Domains matching this patterns will be ignored""")),
)

# Whitelist domain pattern
conf.registerChannelValue(
    SpiffyTitles,
    "whitelistDomainPattern",
    registry.Regexp("", _("""Domains not matching this patterns will be ignored""")),
)

# Channel whitelist
conf.registerGlobalValue(
    SpiffyTitles,
    "channelWhitelist",
    registry.CommaSeparatedListOfStrings(
        [], _("""Only show titles on these channels, or all if empty""")
    ),
)

# Channel blacklist
conf.registerGlobalValue(
    SpiffyTitles,
    "channelBlacklist",
    registry.CommaSeparatedListOfStrings(
        [], _("""Never show titles on these channels""")
    ),
)

# Link cache lifetime
conf.registerGlobalValue(
    SpiffyTitles,
    "cacheLifetime",
    registry.Integer(600, _("""Link cache lifetime in seconds""")),
)

# Link cache lifetime
conf.registerGlobalValue(
    SpiffyTitles,
    "cacheGlobal",
    registry.Boolean(
        False,
        _(
            """
            Keep link cache globally. This will use global values for all link templates.
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles,
    "ignoredMessagePattern",
    registry.Regexp("", _("""Messages matching this pattern will be ignored.""")),
)

conf.registerChannelValue(
    SpiffyTitles,
    "ignoreActionLinks",
    registry.Boolean(True, _("""Ignore URLs that appear in an action such as /me.""")),
)

conf.registerChannelValue(
    SpiffyTitles,
    "ignoreAddressed",
    registry.Boolean(
        True,
        _(
            """
            Ignore URLs that appear in messages addressed to the bot.
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles, 
    "snarfMultipleUrls",
    registry.Boolean(
        True,
        _(
            """
            Determines whether SpiffyTitles will query all URLs in a message,
            or only the first one.
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles,
    "requireCapability",
    registry.String(
        "",
        _(
            """
            If defined, SpiffyTitles will only acknowledge links from users with this
            capability. Useful for hostile environments.
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles,
    "ignoredTitlePattern",
    registry.Regexp("", _("""Titles matching this pattern will be ignored.""")),
)

conf.registerChannelValue(
    SpiffyTitles, 
    "prefixNick",
    registry.Boolean(
        False,
        _(
            """
            Determines whether SpiffyTitles will prefix replies with the user's nick.
            """
        ),
    ),
)


# default configs
conf.registerGroup(SpiffyTitles, "default")

conf.registerChannelValue(
    SpiffyTitles.default,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about regular links.""")
    ),
)

conf.registerChannelValue(
    SpiffyTitles.default,
    "mimeTypes",
    registry.CommaSeparatedListOfStrings(
        ["text/html", "application/xhtml+xml"],
        _("""Acceptable mime types for parsing html titles."""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.default,
    "language",
    registry.String(
        "en-US, en;q=0.8",
        _(
            """
            Accept-Language header string.
            https://tools.ietf.org/html/rfc7231#section-5.3.5
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.default,
    "userAgents",
    registry.CommaSeparatedListOfStrings(
        [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101"
            " Firefox/75.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101"
            " Firefox/76.0",
            "Mozilla/5.0 (Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0",
            "Mozilla/5.0 (Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0",
        ],
        _("""Reported user agent when fetching links"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.default,
    "language",
    registry.String(
        "en-US, en;q=0.8",
        _(
            """
            Accept-Language header string.
            https://tools.ietf.org/html/rfc7231#section-5.3.5
            """
        ),
    ),
)

# default title template - show a warning if redirects to a different domain
conf.registerChannelValue(
    SpiffyTitles.default,
    "template",
    registry.String(
        "{% if redirect %}(REDIRECT) {% endif %}^ {{title}}",
        _("""Template used for default title responses"""),
    ),
)
# default file template - show a warning if redirects to a different domain
conf.registerChannelValue(
    SpiffyTitles.default,
    "fileTemplate",
    registry.String(
        "{% if type %}[{{type}}] {% endif %}{% if size %}({{size}}){% endif %}",
        _("""Template used for default title responses"""),
    ),
)

# Wikipedia configs
conf.registerGroup(SpiffyTitles, "wikipedia")

# wikipedia enabler
conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "enabled",
    registry.Boolean(True, _("""Whether to fetch extracts for Wikipedia articles.""")),
)

conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "apiParams",
    registry.SpaceSeparatedListOfStrings(
        [],
        _(
            """
            Add/override API parameters with a space-separated list of key=value pairs.
            """
        ),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "titleParam",
    registry.String(
        "titles",
        _("""The query parameter that will hold the page title from the URL."""),
    ),
)

# Ideally, links to specific article sections would produce the relevant output for
# that section. This is not currently implemented.
conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "ignoreSectionLinks",
    registry.Boolean(True, _("""Ignore links to specific article sections.""")),
)

conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "maxChars",
    registry.Integer(
        400, _("""Extract will be cut to this length (including '...').""")
    ),
)

# Remove parenthesized text from output.
conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "removeParentheses",
    registry.Boolean(True, _("""Remove parenthesized text from output.""")),
)

conf.registerChannelValue(
    SpiffyTitles.wikipedia,
    "extractTemplate",
    registry.String("^ {{extract}}", _("""Wikipedia template.""")),
)


# Reddit configs
conf.registerGroup(SpiffyTitles, "reddit")

# Reddit enabler
conf.registerChannelValue(
    SpiffyTitles.reddit,
    "enabled",
    registry.Boolean(True, _("""Whether to add additional info about Reddit links.""")),
)

# Reddit templates
conf.registerChannelValue(
    SpiffyTitles.reddit,
    "linkThreadTemplate",
    registry.String(
        "/r/{{subreddit}}{% if title %} :: {{title}}{% endif %} :: {{score}} points"
        " ({{percent}}) :: {{comments}} comments :: Posted {{age}} by {{author}}{% if"
        " url %} :: {{url}} ({{domain}}){% endif %}",
        _("""Template used for Reddit link thread title responses"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.reddit,
    "textThreadTemplate",
    registry.String(
        "/r/{{subreddit}}{% if title %} :: {{title}}{% endif %}{% if extract %} ::"
        " {{extract}}{% endif %} :: {{score}} points ({{percent}}) :: {{comments}}"
        " comments :: Posted {{age}} by {{author}}",
        _("""Template used for Reddit text thread title responses"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.reddit,
    "commentTemplate",
    registry.String(
        "/r/{{subreddit}}{% if extract %} :: {{extract}}{% endif %} :: {{score}} points"
        ' :: Posted {{age}} by {{author}} on "{{title}}"',
        _("""Template used for Reddit comment title responses"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.reddit,
    "userTemplate",
    registry.String(
        "/u/{{user}}{% if gold %} :: (GOLD{% if mod %}, MOD{% endif %}){% endif %} ::"
        " Joined: {{created}} :: Link karma: {{link_karma}} :: Comment karma:"
        " {{comment_karma}}",
        _("""Template used for Reddit user page title responses"""),
    ),
)

# Reddit max characters
conf.registerChannelValue(
    SpiffyTitles.reddit,
    "maxChars",
    registry.Integer(
        400, _("""Length of response (title/extract will be cut to fit).""")
    ),
)


# YouTube configs
conf.registerGroup(SpiffyTitles, "youtube")

# youtube enabler
conf.registerChannelValue(
    SpiffyTitles.youtube,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about YouTube videos""")
    ),
)

# Youtube API
conf.registerGlobalValue(
    SpiffyTitles.youtube,
    "developerKey",
    registry.String(
        "", _("""Youtube developer key - required for Youtube handler."""), private=True
    ),
)
# YouTube Logo
conf.registerChannelValue(
    SpiffyTitles.youtube,
    "logo",
    registry.String(
        "\x030,4 ► \x031,0YouTube", _("""Logo used with {{yt_logo}} in template""")
    ),
)
# YouTube template
conf.registerChannelValue(
    SpiffyTitles.youtube,
    "template",
    registry.String(
        "^ {{yt_logo}} :: {{title}} {%if timestamp%} @ {{timestamp}}{% endif %} ::"
        " Duration: {{duration}} :: Views: {{view_count}} :: Uploader:"
        " {{channel_title}} :: Uploaded: {{published}} :: {{like_count}} likes ::"
        " {{dislike_count}} dislikes :: {{favorite_count}} favorites ::"
        " {{comment_count}} comments",
        _("""Template used for YouTube title responses"""),
    ),
)


# imgur configs
conf.registerGroup(SpiffyTitles, "imgur")

# imgur enabler
conf.registerChannelValue(
    SpiffyTitles.imgur,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about imgur links""")
    ),
)

# imgur API
conf.registerGlobalValue(
    SpiffyTitles.imgur,
    "clientID",
    registry.String("", _("""imgur client ID"""), private=True),
)

conf.registerChannelValue(
    SpiffyTitles.imgur,
    "imageTemplate",
    registry.String(
        "^ {%if section %}[{{section}}] {% endif %}{% if title %}{{title}} :: {% endif"
        " %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if"
        " nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for"
        " work!{% else %}safe for work{% endif %}",
        _("""imgur image template"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.imgur,
    "albumTemplate",
    registry.String(
        "^ {%if section %}[{{section}}] {% endif %}{% if title %}{{title}} :: {% endif"
        " %}{%- if description -%}{{description}} :: {% endif %}{{image_count}} images"
        " :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{%"
        " elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}",
        _("""imgur album template"""),
    ),
)


# dailymotion configs
conf.registerGroup(SpiffyTitles, "dailymotion")

# dailymotion enabler
conf.registerChannelValue(
    SpiffyTitles.dailymotion,
    "enabled",
    registry.Boolean(
        True, _("""Enable additional information about dailymotion videos""")
    ),
)

# dailymotion template
conf.registerChannelValue(
    SpiffyTitles.dailymotion,
    "template",
    registry.String(
        "^ [{{ownerscreenname}}] {{title}} :: Duration: {{duration}} :: {{views_total}}"
        " views",
        _("""Template used for Vimeo title responses"""),
    ),
)


# Twitch configs
conf.registerGroup(SpiffyTitles, "twitch")

# twitch enabler
conf.registerChannelValue(
    SpiffyTitles.twitch,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about Twitch links""")
    ),
)

# Twitch API Keys
conf.registerGlobalValue(
    SpiffyTitles.twitch,
    "clientID",
    registry.String("", _("""Twitch API Client_ID"""), private=True),
)

conf.registerGlobalValue(
    SpiffyTitles.twitch,
    "accessToken",
    registry.String("", _("""Twitch API Access Token"""), private=True),
)

# Twitch Logo
conf.registerChannelValue(
    SpiffyTitles.twitch,
    "logo",
    registry.String(
        "\x030,6💬twitch", _("""Logo used with {{twitch_logo}} in template""")
    ),
)

conf.registerChannelValue(
    SpiffyTitles.twitch,
    "channelTemplate",
    registry.String(
        "^ {{twitch_logo}} :: {{display_name}} {%if description%}:: {{description}}"
        " {%endif%}:: Viewers: {{view_count}}",
        _("""twitch.tv channel template"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.twitch,
    "streamTemplate",
    registry.String(
        "^ {{twitch_logo}} :: {{display_name}} :: (LIVE) {%if"
        " game_name%}[{{game_name}}] {%endif%}{%if title%}:: {{title}} {%endif%}::"
        " Created: {{created_at}} :: Viewers: {{view_count}} {%if description%}::"
        " {{description}}{%endif%}",
        _("""twitch.tv stream template"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.twitch,
    "videoTemplate",
    registry.String(
        "^ {{twitch_logo}} :: {{display_name}} {%if title%}:: {{title}} {%endif%}}::"
        " Duration: {{duration}} :: Created: {{created_at}} {%if description%}::"
        " {{description}} {%endif%}:: Viewers: {{view_count}}",
        _("""twitch.tv video template"""),
    ),
)

conf.registerChannelValue(
    SpiffyTitles.twitch,
    "clipTemplate",
    registry.String(
        "^ {{twitch_logo}} :: {{display_name}} {%if game_name%}:: [{{game_name}}]"
        " {%endif%}{%if title%}:: {{title}} {%endif%}:: Created: {{created_at}} ::"
        " Viewers: {{view_count}} {%if description%}:: {{description}}{%endif%}",
        _("""twitch.tv clip template"""),
    ),
)


# vimeo configs
conf.registerGroup(SpiffyTitles, "vimeo")

# vimeo enabler
conf.registerChannelValue(
    SpiffyTitles.vimeo,
    "enabled",
    registry.Boolean(True, _("""Enable additional information about Vimeo videos""")),
)

# Vimeo template
conf.registerChannelValue(
    SpiffyTitles.vimeo,
    "template",
    registry.String(
        "^ {{title}} :: Duration: {{duration}} :: {{stats_number_of_plays}} plays ::"
        " {{stats_number_of_comments}} comments",
        _("""Template used for Vimeo title responses"""),
    ),
)


# IMDB configs
conf.registerGroup(SpiffyTitles, "imdb")

# imdb enabler
conf.registerChannelValue(
    SpiffyTitles.imdb,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about IMDB links""")
    ),
)

# OMDB API Key
conf.registerGlobalValue(
    SpiffyTitles.imdb,
    "omdbAPI",
    registry.String("", _("""OMDB API Key"""), private=True),
)

# IMDB Logo
conf.registerChannelValue(
    SpiffyTitles.imdb,
    "logo",
    registry.String("\x031,8 IMDb ", _("""Logo used with {{imdb_logo}} in template""")),
)

# IMDB template
conf.registerChannelValue(
    SpiffyTitles.imdb,
    "template",
    registry.String(
        "^ {{imdb_logo}} :: {{title}} ({{year}}, {{country}}, [{{rated}}], {{genre}},"
        " {{runtime}}) :: IMDb: {{imdb_rating}} | MC: {{metascore}} | RT:"
        " {{tomatoMeter}} :: {{plot}} :: Director: {{director}} :: Cast: {{actors}} ::"
        " Writer: {{writer}}",
        _("""IMDB title template"""),
    ),
)


# coub configs
conf.registerGroup(SpiffyTitles, "coub")

# coub enabler
conf.registerChannelValue(
    SpiffyTitles.coub,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about coub links""")
    ),
)

# coub template
conf.registerChannelValue(
    SpiffyTitles.coub,
    "template",
    registry.String(
        "^ {%if not_safe_for_work %}NSFW{% endif %} [{{channel.title}}] {{title}} ::"
        " {{views_count}} views :: {{likes_count}} likes :: {{recoubs_count}} recoubs",
        _("""Uses Coub API to get additional information about coub.com links"""),
    ),
)

# twitter configs
conf.registerGroup(SpiffyTitles, "twitter")

# twitter enabler
conf.registerChannelValue(
    SpiffyTitles.twitter,
    "enabled",
    registry.Boolean(
        True, _("""Whether to add additional information about Twitter links""")
    ),
)

# twitter template
conf.registerChannelValue(
    SpiffyTitles.twitter,
    "template",
    registry.String(
        "^ {{text}}",
        _("""Uses Twitter API to get additional information about twitter.com links"""),
    ),
)
