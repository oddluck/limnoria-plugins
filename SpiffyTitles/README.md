Highly customizable and fully-featured link title snarfer with many URL handlers.

Forked from https://github.com/butterscotchstallion/limnoria-plugins/tree/master/SpiffyTitles

If you're coming from another fork of SpiffyTitles, please note that some config variables have changed in this version. Everything is now grouped by url handler; spiffytitles.default, spiffytitles.youtube, spiffytitles.imdb, etc.

# SpiffyTitles #

The ONLY gluten-free plugin for displaying link titles.

## Notable features

- Configurable template so you can decide how titles are displayed and what they say
- Additional information about [Youtube](https://youtube.com) videos
- Additional information about [Twitter](https://twitter.com) links
- Additional information about [imgur](https://imgur.com) links
- Additional information about [IMDB](https://imdb.com) links
- Additional information about [Reddit](https://reddit.com/) links
- Additional information about [Twitch](https://twitch.tv) links
- Additional information about [vimeo](https://vimeo.com) links
- Additional information about [DailyMotion](https://dailymotion.com) links
- Additional information about [Coub](https://coub.com) links
- Article extracts from [Wikipedia](https://en.wikipedia.org) links
- Rate limiting to mitigate abuse
- Configurable white/black list to control where titles are disabled
- MIME type and size info for file links
- Configurable list of user agents
- Ability to ignore domains using a regular expression

Check out the [available options](#available-options)!

## Install SpiffyTitles
- install pip if you don't have it already (eg. `apt install python3-pip`)
- `pip3 install --user --upgrade git+https://github.com/oddluck/limnoria-plugins.git#subdirectory=SpiffyTitles`

You should `!unload Web` and any other plugins that show link titles for best results

Load SpiffyTitles:
    
`!load SpiffyTitles`

Pro Tip: Observe the logs when loading the plugin and afterwards to see if there are any errors.

You can increase the verbosity of the logging in SpiffyTitles by issuing the following command:


`!config supybot.log.level DEBUG`


## On-Demand Titles
You can retrieve titles on demand using the `t` command. If something goes wrong, `badLinkText`
will be sent instead of the link title.

## Available Options

### Note
Almost all of the below options can be customized per-channel.

Example:

`!config channel ##example-channel-one supybot.plugins.SpiffyTitles.default.template "^ {{title}}"`

`!config channel ##example-channel-two supybot.plugins.SpiffyTitles.default.template ":: {{title}}"`

This means that you can change whether a handler is enabled, or what the template looks like for any channel.

### Default handler

`default.enabled` - Whether to show additional information about links that aren't handled elsewhere. You'd really only want to disable this if all of the other handlers were enabled. In this scenario, the bot would only show information for websites with custom handlers, like Youtube, IMDB, and imgur.

`default.userAgents` - A comma separated list of strings of user agents randomly chosen when requesting.

`default.language` - Accept-Language header string. https://tools.ietf.org/html/rfc7231#section-5.3.5

`default.mimeTypes` - Comma separated list of strings of mime types to parse for html title. Default value: `text/html`. You shouldn't need to change this.

`default.template` - This is the template used when showing the title of a link.

Default value: `^ {{title}}`

Example output:

`^ Google.com`

`default.fileTemplate` - Template shown for direct file links

Default value: `{% if type %}[{{type}}] {% endif %}{% if size %}({{size}}){% endif %}`

### Twitter/X handler

`twitter.enabled` - Whether to show additional information about Twitter/X links

`twitter.template` - This is the template used when showing the title of a Twitter/X link

Default value: `^ {{text}}`

### Available variables for the Twitter template ###

Variable       | Description
---------------|------------
text           | Full tweet text, all inclusive of available variables
name           | User name
nick           | User nick (aka @)
content        | Tweet content
date           | Date of tweet

### Youtube handler

Note: as of April 20 2015 version 2 of the Youtube API was deprecated. As a result, this feature now
requires a [developer key](https://code.google.com/apis/youtube/dashboard/gwt/index.html#settings).

- Obtain an [API key](https://console.cloud.google.com/apis/credentials)
- Make sure the [YouTube Data API](https://console.developers.google.com/apis/library/youtube.googleapis.com) is enabled.
- Set the key: `!config supybot.plugins.SpiffyTitles.youtube.developerKey your_developer_key_here`
- Observe the logs to check for errors

### Youtube handler options

`youtube.enabled` - Whether to show additional information about Youtube links

`youtube.logo` - This is the colored text used for {{yt_logo}} in title template strings.

Default value: `\x030,4 ► \x031,0YouTube`

`youtube.template` - This is the template used when showing the title of a YouTube video

Default value: `^ {{yt_logo}} :: {{title}} {%if timestamp%} @ {{timestamp}}{% endif %} :: Duration: {{duration}} :: Views: {{view_count}} :: Uploader: {{channel_title}} :: Uploaded: {{published}} :: {{like_count}} likes :: {{dislike_count}} dislikes :: {{favorite_count}} favorites :: {{comment_count}} comments`

Example output:

`^ Snoop Dogg - Pump Pump feat. Lil Malik uploaded by GeorgeRDR3218 @ 00:45:: Duration: 04:41 :: 203,218 views :: 933 likes :: 40 dislikes :: 0 favorites :: 112 comments`

### Available variables for the Youtube template ###

Variable       | Description
---------------|------------
yt_logo        | Colored YouTube logo
title          | Video title
channel_title  | Channel title
duration       | Duration
view_count     | Number of views
like_count     | Number of likes
dislike_count  | Number of dislikes
favorite_count | Number of favorites
comment_count  | Number of comments
published      | Date uploaded
timestamp      | If specified, the start time of the video

Tip: You can use irc colors colors in your templates, but be sure to quote the value

### imdb handler
Queries the [OMDB API](http://www.omdbapi.com) to get additional information about [IMDB](http://imdb.com) links

`imdb.omdbAPI` - Set your OMDB API key here (free) https://www.omdbapi.com/apikey.aspx

`imdb.enabled` - Whether to show additional information about [IMDB](http://imdb.com) links

`imdb.template` - This is the template used for [IMDB](http://imdb.com) links

Default value: `^ {{imdb_logo}} :: {{title}} ({{year}}, {{country}}, [{{rated}}], {{genre}}, {{runtime}}) ::  IMDB: {{imdb_rating}} | MC: {{metascore}} | RT: {{tomatoMeter}} :: {{plot}}`

`imdb.logo` - This is the logo text used for imdb_logo in the template

Default value: `\x031,8IMDb`

### Available variables for IMDB template ###

Variable       | Description
---------------|------------
imdb_logo      | Colored IMDB logo
title          | Movie title
year           | Release year
country        | Country
director       | Director
plot           | Plot
imdb_id        | IMDB tile ID#
imdb_rating    | IMDB rating
metascore      | Metacritic score
released       | Release date
genre          | Genre
awards         | Awards won
actors         | Actors
rated          | Rating
runtime        | Runtime
writer         | Writer
votes          | Votes
website        | Website URL
language       | Language
box_office     | Box Office
production     | Production company
poster         | Poster URL

### Twitch handler
Queries the [Twitch API](https://dev.twitch.tv/) to get additional information about [Twitch](http://twitch.tv) links

Visit https://twitchtokengenerator.com/ and scroll down until you see the 'Generate Token' button. Click the button and authorize the app on Twitch. Set the Client ID and Access Token using the values generated by Twitch Token Generator.

`twitch.clientID` - Set your Twitch Client_ID here.

`twitch.accessToken` - Set your Twitch Access Token here.

`twitch.enabled` - Whether to show additional information about [Twitch](http://twitch.tv) links

`twitch.logo` - This is the colored text used for {{twitch_logo}} in title template strings.

`twitch.channelTemplate'` - Template for channel links

Default value: `^ {{twitch_logo}} :: {{display_name}} {%if description%}:: {{description}} {%endif%}:: Viewers: {{view_count}}`

`twitch.streamTemplate` - Template for live stream links

Default value: `^ {{twitch_logo}} :: {{display_name}} :: (LIVE) {%if game_name%}[{{game_name}}] {%endif%}{%if title%}:: {{title}} {%endif%}:: Created: {{created_at}} :: Viewers: {{view_count}} {%if description%}:: {{description}} {%endif%}`

`twitch.videoTemplate` - Template for video links

Default value: `^ {{twitch_logo}} :: {{display_name}} {%if title%}:: {{title}} {%endif%}}:: Duration: {{duration}} :: Created: {{created_at}} {%if description%}:: {{description}} {%endif%}:: Viewers: {{view_count}}`
   
`twitch.clipTemplate` - Template for clip links

Default value: `^ {{twitch_logo}} :: {{display_name}} {%if game_name%}:: [{{game_name}}] {%endif%}{%if title%}:: {{title}} {%endif%}:: Created: {{created_at}} :: Viewers: {{view_count}} {%if description%}:: {{description}} {%endif%}"`


### imgur handler

`imgur.imagetemplate` - This is the template used when showing information about an [imgur](https://imgur.com) link.

Default value

`^ {%if section %}[{{section}}] {% endif -%}{%- if title -%}{{title}} :: {% endif %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}`

Example output:

`^ [pics] He really knows nothing... :: image/jpeg 700x1575 178.8KiB :: 809 views :: safe for work`

`imgur.albumTemplate` - This is the template used when showing information about an imgur album link.

Default value

`^ {%if section %}[{{section}}] {% endif -%}{%- if title -%}{{title}} :: {% endif %}{%- if description -%}{{description}} :: {% endif %}{{image_count}} images :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}`

Example output:
    
`^ [compsci] Regex Fractals :: 33 images :: 21,453 views :: safe for work`

### Using the imgur handler

- You'll need to [register an application with imgur](https://api.imgur.com/oauth2/addclient)
- Select "OAuth 2 authorization without a callback URL"
- Once registered, set your client id

`!config supybot.plugins.SpiffyTitles.imgur.clientID`

### Notes on the imgur handler

- If there is a problem reaching the API the default handler will be used as a fallback. See logs for details.
- The API seems to report information on the originally uploaded image and not other formats
- If you see something from [the imgur api](https://api.imgur.com/models/image) that you want and is not available
in the above example, [please open an issue!](https://github.com/oddluck/limnoria-plugins/issues/new)

### coub handler

`coub.template` - Template for [coub](http://coub.com) links.

Default value: `^ {%if not_safe_for_work %}NSFW{% endif %} [{{channel.title}}] {{title}} :: {{views_count}} views :: {{likes_count}} likes :: {{recoubs_count}} recoubs`

`coub.enabled` - Whether to enable additional information about coub videos.

### vimeo handler

`vimeo.template` - Template for [vimeo](https://vimeo.com) links.

Default value: `^ {{title}} :: Duration: {{duration}} :: {{stats_number_of_plays}} plays :: {{stats_number_of_comments}} comments`

`vimeo.enabled` - Whether to enable additional information about vimeo videos.

### dailymotion handler

`dailymotion.template` - Template for [dailymotion](https://www.dailymotion.com) links.

Default value: `^ [{{ownerscreenname}}] {{title}} :: Duration: {{duration}} :: {{views_total}} views`

`dailymotion.enabled` - Whether to enable additional information about dailymotion videos.

### wikipedia handler

`wikipedia.enabled` - Whether to fetch extracts for Wikipedia articles.

`wikipedia.extractTemplate` - Wikipedia template.

Default value: "^ {{extract}}"

`wikipedia.maxChars` - Extract will be cut to this length (including '...').

Default value: 400

`wikipedia.removeParentheses` - Whether to remove parenthesized text from output.

`wikipedia.ignoreSectionLinks` - Whether to ignore links to specific article sections.

`wikipedia.apiParams` - Add or override API query parameters with a space-separated list of key=value pairs.

`wikipedia.titleParam` - The query parameter that will hold the page title from the URL.


## Other options

`useBold` - Whether to bold the title. Default value: `False`

`cacheLifetime` - Caches the title of links. This is useful for reducing API usage and 
improving performance. Default value: `600`

`cacheGlobal` - Caches link titles globally. Setting this will use global templates for all titles, per-channel templates will be ignored.

`timeout` - Timeout for total elapsed time when requestging a title. If you set this value too 
high, the bot may time out. Default value: `10` (seconds). You must `!reload SpiffyTitles` for this setting to take effect.

`maxRetries` - Maximum number of times to retry retrieving a link. Default value: `3`

`channelWhitelist` - A comma separated list of channels in which titles should be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

`channelBlacklist` - A comma separated list of channels in which titles should never be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

`badLinkText` - The text to return when unable to retrieve a title from a URL. Default value: `Error retrieving title. Check the log for more details.`

`urlRegexp` - A regular expression override used to match URLs. You shouldn't need to change this.

`ignoreActionLinks` (Boolean) - By default SpiffyTitles will ignore links that appear in an action, like /me.

`ignoreAddressed` (Boolean) - By default SpiffyTitles will ignore links that appear in messages addressed to the bot.

`requireCapability` (String) - If defined, SpiffyTitles will only acknowledge links from users with this capability. Useful for hostile environments. Refer to [Limnoria's documentation on capabilities](http://doc.supybot.aperio.fr/en/latest/use/capabilities.html) for more information

`ignoredTitlePattern` (Regexp) - If the parsed title matches this regular expression, it will be ignored.

`ignoredDomainPattern` - Ignore domains matching this pattern.

`ignoredMessagePattern` - If a message matches this pattern, it will be ignored. This differs from ignoredDomainPattern in that it compares against the entire message rather than just the domain.

`whitelistDomainPattern` - ignore any link without a domain matching this pattern. Default value: `""`

### About white/black lists
- Channel names must be in lowercase
- If `channelWhitelist` and `channelBlacklist` are empty, then titles will be displayed in every channel
- If `channelBlacklist` has #foo, then titles will be displayed in every channel except #foo
- If `channelWhitelist` has #foo then `channelBlacklist` will be ignored

### Examples

### Show titles in every channel except #foo

`!config supybot.plugins.SpiffyTitles.channelBlacklist #foo`

### Only show titles in #bar

`!config supybot.plugins.SpiffyTitles.channelWhitelist #bar`

### Only show titles in #baz and #bar

`!config supybot.plugins.SpiffyTitles.channelWhitelist #baz,#bar`

### Remove channel whitelist

`!config supybot.plugins.SpiffyTitles.channelWhitelist ""`

### Pro Tip

You can ignore domains that you know aren't websites. This prevents a request from being made at all.

### Examples

Ignore all links with the domain `buzzfeed.com`

`!config supybot.plugins.SpiffyTitles.ignoredDomainPattern (buzzfeed\.com)`

Ignore `*.tk` and `buzzfeed.com`

`!config supybot.plugins.SpiffyTitles.ignoredDomainPattern (\.tk|buzzfeed\.com)`

Ignore all links except youtube, imgur, and reddit

`!config supybot.plugins.SpiffyTitles.whitelistDomainPattern /(reddit\.com|youtube\.com|youtu\.be|imgur\.com)/`

Ignore any message that contains "[tw]".

`!config supybot.plugins.SpiffyTitles.linkMessageIgnorePattern "/\[tw\]/"`

Ignore any link which results in a title matching a pattern.

`!config channel #example supybot.plugins.SpiffyTitles.ignoredTitlePattern m/^\^ Google$|- Google Search$|^\^ Google Maps$|^\^ Imgur: The most awesome images on the Internet$|^\^ Pastebin \| IRCCloud|^\^ Instagram|^\^ Urban Dictionary:|– Wikipedia$|- Wikipedia, the free encyclopedia$|- Wiktionary$| - RationalWiki$|^\^ Meet Google Drive|- Wikia$|^\^ Imgur$|^\^ Google Trends|^\^ reactiongifs/`

### FAQ

Q: I have a question. Where can I get help?

A: Join #limnoria on chat.freenode.net

Q: I'm getting the error `Error: That configuration variable is not a channel-specific configuration variable.`
when I try to change a configuration value.

A: Some configuration values were previously global. Simply restart your bot to fix this error.

Q: How can I only show information about certain links?

A: You can use the settings `default.enabled`, `youtube.enabled`, `imgur.enabled`, `twitch.enabled`, `dailymotion.enabled`, `wikipedia.enabled`, `coub.enabled`, `vimeo.enabled`, and `imdb.enabled` to choose which links you want to show information about.

Q: Why not use the [Web](https://github.com/ProgVal/Limnoria/tree/master/plugins/Web) plugin?

A: My experience was that it didn't work very well and lacked the ability to customize the options
I wanted to change.

Q: What about [Supybot-Titler](https://github.com/reticulatingspline/Supybot-Titler) ?

A: I couldn't get this to work on my system and it has a lot of features I didn't want

Q: It doesn't work for me. What can I do?

A: [Open an issue](https://github.com/oddluck/limnoria-plugins/issues/new) and include at minimum the following:

- Brief description of the problem
- Any errors that were logged (Look for the ones prefixed "SpiffyTitles")
- How to reproduce the effect
- Any other information you think would be helpful
