# SpiffyTitles #

The ONLY gluten-free plugin for displaying link titles.

## Notable features

- Configurable template so you can decide how titles are displayed and what they say
- Additional information about [Youtube](https://youtube.com) videos
- Additional information about [imgur](https://imgur.com) links
- Article extracts from [Wikipedia](https://en.wikipedia.org) links
- Rate limiting to mitigate abuse
- Configurable white/black list to control where titles are disabled
- Configurable list of user agents
- Ability to ignore domains using a regular expression

Check out the [available options](#available-options)!

## Install SpiffyTitles
- `git clone https://github.com/butterscotchstallion/limnoria-plugins.git`
- `cd limnoria-plugins`
- `cp -r SpiffyTitles ~/your_bot_directory/plugins`
- `cd ~/your_bot_directory/plugins/SpiffyTitles`
- `pip install -r requirements.txt --user --upgrade`
- If you need to install `certifi` you may have to restart the bot afterwards

You should `!unload Web` and any other plugins that show link titles for best results

Load SpiffyTitles:
    
    !load SpiffyTitles

Pro Tip: Observe the logs when loading the plugin and afterwards to see if there are any errors.

You can increase the verbosity of the logging in SpiffyTitles by issuing the following command:


`!config supybot.log.level DEBUG`


## On-Demand Titles
You can retrieve titles on demand using the `t` command. If something goes wrong, `onDemandTitleError`
will be sent instead of the link title.

## Available Options

### Note
Almost all of the below options can be customized per-channel.

Example:

`!config channel ##example-channel-one supybot.plugins.SpiffyTitles.defaultTitleTemplate "^ {{title}}"`

`!config channel ##example-channel-two supybot.plugins.SpiffyTitles.defaultTitleTemplate ":: {{title}}"`

This means that you can change whether a handler is enabled, or what the template looks like for any channel.

### Default handler

`defaultHandlerEnabled` - Whether to show additional information about links that aren't handled elsewhere. You'd really only want to disable this if all of the other handlers were enabled. In this scenario, the bot would only show information for websites with custom handlers, like Youtube, IMDB, and imgur.

`defaultTitleTemplate` - This is the template used when showing the title of a link.

Default value: `^ {{title}}`

Example output:

    ^ Google.com

### Youtube handler

Note: as of April 20 2015 version 2 of the Youtube API was deprecated. As a result, this feature now
requires a [developer key](https://code.google.com/apis/youtube/dashboard/gwt/index.html#settings).

- Obtain a [developer key](https://code.google.com/apis/youtube/dashboard/gwt/index.html#settings)
- Click the link on the left to go to the `Credentials` area under `APIs and auth`
- Click `Create new Key` under `Public API access`
- Choose `Server key`
- Click `Create` as shown in the screenshot below

![Google Developer Console Screenshot](https://i.imgur.com/IUfk3VB.jpg "Google Developer Console Screenshot")

- You may specify allowed IPs but be aware that this setting seems to cache. It is easier to test using the URL listed in the console to verify requests from that machine are working.
- Make sure the YouTube API is enabled in [the developer console](https://developers.google.com/console/help/#activatingapis).
- Set the key: `!config supybot.plugins.SpiffyTitles.youtubeDeveloperKey your_developer_key_here`
- Observe the logs to check for errors

### Youtube handler options

`youtubeHandlerEnabled` - Whether to show additional information about Youtube links

`youtubeTitleTemplate` - This is the template used when showing the title of a YouTube video

Default value: `^ {{yt_logo}} :: {{title}} {%if timestamp%} @ {{timestamp}}{% endif %} :: Duration: {{duration}} :: Views: {{view_count}} uploaded by {{channel_title}} :: {{like_count}} likes :: {{dislike_count}} dislikes :: {{favorite_count}} favorites`

Example output:

    ^ Snoop Dogg - Pump Pump feat. Lil Malik uploaded by GeorgeRDR3218 @ 00:45:: Duration: 04:41 :: 203,218 views :: 933 likes :: 40 dislikes :: 0 favorites :: 112 comments

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
timestamp      | If specified, the start time of the video

Tip: You can use irc colors colors in your templates, but be sure to quote the value

### imdb handler
Queries the [OMDB API](http://www.omdbapi.com) to get additional information about [IMDB](http://imdb.com) links

`imdbHandlerEnabled` - Whether to show additional information about [IMDB](http://imdb.com) links

`imdbTemplate` - This is the template used for [IMDB](http://imdb.com) links

Default value: `^ {{Title}} ({{Year}}, {{Country}}) - Rating: {{imdbRating}} ::  {{Plot}}`

### imgur handler

`imgurTemplate` - This is the template used when showing information about an [imgur](https://imgur.com) link.

Default value

    ^ {%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{type}} {{width}}x{{height}} {{file_size}} :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}

Example output:

    ^ [pics] He really knows nothing... :: image/jpeg 700x1575 178.8KiB :: 809 views :: safe for work

`imgurAlbumTemplate` - This is the template used when showing information about an imgur album link.

Default value

    ^ {%if section %} [{{section}}] {% endif -%}{%- if title -%} {{title}} :: {% endif %}{{image_count}} images :: {{view_count}} views :: {%if nsfw == None %}not sure if safe for work{% elif nsfw == True %}not safe for work!{% else %}safe for work{% endif %}

Example output:
    
    ^ [compsci] Regex Fractals :: 33 images :: 21,453 views :: safe for work

### Using the imgur handler

- You'll need to [register an application with imgur](https://api.imgur.com/oauth2/addclient)
- Select "OAuth 2 authorization without a callback URL"
- Once registered, set your client id and client secret

    `!config supybot.plugins.SpiffyTitles.imgurClientID`
    
    `!config supybot.plugins.SpiffyTitles.imgurClientSecret`

### Notes on the imgur handler

- If there is a problem reaching the API the default handler will be used as a fallback. See logs for details.
- The API seems to report information on the originally uploaded image and not other formats
- If you see something from [the imgur api](https://api.imgur.com/models/image) that you want and is not available
in the above example, [please open an issue!](https://github.com/butterscotchstallion/limnoria-plugins/issues/new)

### coub handler

`coubTemplate` - Template for [coub](http://coub.com) links.

Default value: `^ {%if not_safe_for_work %}NSFW{% endif %} [{{channel.title}}] {{title}} :: {{views_count}} views :: {{likes_count}} likes :: {{recoubs_count}} recoubs`

`coubHandlerEnabled` - Whether to enable additional information about coub videos.

### vimeo handler

`vimeoTitleTemplate` - Template for [vimeo](https://vimeo.com) links.

Default value: `^ {{title}} :: Duration: {{duration}} :: {{stats_number_of_plays}} plays :: {{stats_number_of_comments}} comments`

`vimeoHandlerEnabled` - Whether to enable additional information about vimeo videos.

### dailymotion handler

`dailymotionVideoTitleTemplate` - Template for [dailymotion](https://www.dailymotion.com) links.

Default value: `^ [{{ownerscreenname}}] {{title}} :: Duration: {{duration}} :: {{views_total}} views`

`dailymotionHandlerEnabled` - Whether to enable additional information about dailymotion videos.

### wikipedia handler

`wikipedia.enabled` - Whether to fetch extracts for Wikipedia articles.

`wikipedia.extractTemplate` - Wikipedia template.

Default value: "^ {{extract}}"

`wikipedia.maxChars` - Extract will be cut to this length (including '...').

Default value: 240

`wikipedia.removeParentheses` - Whether to remove parenthesized text from output.

`wikipedia.ignoreSectionLinks` - Whether to ignore links to specific article sections.

`wikipedia.apiParams` - Add or override API query parameters with a space-separated list of key=value pairs.

`wikipedia.titleParam` - The query parameter that will hold the page title from the URL.


## Other options

`useBold` - Whether to bold the title. Default value: `False`

`linkCacheLifetimeInSeconds` - Caches the title of links. This is useful for reducing API usage and 
improving performance. Default value: `60`

`wallClockTimeoutInSeconds` - Timeout for total elapsed time when retrieving a title. If you set this value too 
high, the bot may time out. Default value: `8` (seconds). You must `!reload SpiffyTitles` for this setting to take effect.

`channelWhitelist` - a comma separated list of channels in which titles should be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

`channelBlacklist` - a comma separated list of channels in which titles should never be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

### About white/black lists
- Channel names must be in lowercase
- If `channelWhitelist` and `channelBlacklist` are empty, then titles will be displayed in every channel
- If `channelBlacklist` has #foo, then titles will be displayed in every channel except #foo
- If `channelWhitelist` has #foo then `channelBlacklist` will be ignored

### Examples

### Show titles in every channel except #foo

    !config supybot.plugins.SpiffyTitles.channelBlacklist #foo

### Only show titles in #bar

    !config supybot.plugins.SpiffyTitles.channelWhitelist #bar

### Only show titles in #baz and #bar

    !config supybot.plugins.SpiffyTitles.channelWhitelist #baz,#bar

### Remove channel whitelist

    !config supybot.plugins.SpiffyTitles.channelWhitelist ""

`ignoredDomainPattern` - ignore domains matching this pattern. Default value: `""`

`whitelistDomainPattern` - ignore any link without a domain matching this pattern. Default value: `""`

### Pro Tip

You can ignore domains that you know aren't websites. This prevents a request from being made at all.

### Examples

Ignore all links with the domain `buzzfeed.com`

    !config supybot.plugins.SpiffyTitles.ignoredDomainPattern (buzzfeed\.com)

Ignore `*.tk` and `buzzfeed.com`

    !config supybot.plugins.SpiffyTitles.ignoredDomainPattern (\.tk|buzzfeed\.com)

Ignore all links except youtube, imgur, and reddit

    !config supybot.plugins.SpiffyTitles.whitelistDomainPattern /(reddit\.com|youtube\.com|youtu\.be|imgur\.com)/

`userAgents` - A comma separated list of strings of user agents randomly chosen when requesting. 

`urlRegularExpression` - A regular expression used to match URLs. You shouldn't need to change this.

`linkMessageIgnorePattern` - If a message matches this pattern, it will be ignored. This differs from `ignoredDomainPattern` in that it compares against the entire message rather than just the domain.

Example: `!config supybot.plugins.SpiffyTitles.linkMessageIgnorePattern "/\[tw\]/"`

This would ignore any message that contains "[tw]".

`ignoreActionLinks` (Boolean) - By default SpiffyTitles will ignore links that appear in an action, like `/me`.

`requireCapability` (String) - If defined, SpiffyTitles will only acknowledge links from users with this capability. Useful for hostile environments. [Refer to Limnoria's documentation on capabilities for more information](http://doc.supybot.aperio.fr/en/latest/use/capabilities.html)

`ignoredTitlePattern` (Regexp) - If the parsed title matches this regular expression, it will be ignored.

Example: `!config channel #example supybot.plugins.SpiffyTitles.ignoredTitlePattern m/^\^ Google$|- Google Search$|^\^ Google Maps$|^\^ Imgur: The most awesome images on the Internet$|^\^ Pastebin \| IRCCloud|^\^ Instagram|^\^ Urban Dictionary:|– Wikipedia$|- Wikipedia, the free encyclopedia$|- Wiktionary$| - RationalWiki$|^\^ Meet Google Drive|- Wikia$|^\^ Imgur$|^\^ Google Trends|^\^ reactiongifs/`

This line would ignore any link which results in a title matching the above pattern.

### FAQ

Q: I have a question. Where can I get help?

A: Join #limnoria on chat.freenode.net

Q: I'm getting the error `Error: That configuration variable is not a channel-specific configuration variable.`
when I try to change a configuration value.

A: Some configuration values were previously global. Simply restart your bot to fix this error.

Q: How can I only show information about certain links?

A: You can use the settings `defaultHandlerEnabled`, `youtubeHandlerEnabled`, `imgurHandlerEnabled`, and `imdbHandlerEnabled` to choose which links you want to show information about.

Q: Why not use the [Web](https://github.com/ProgVal/Limnoria/tree/master/plugins/Web) plugin?

A: My experience was that it didn't work very well and lacked the ability to customize the options
I wanted to change.

Q: What about [Supybot-Titler](https://github.com/reticulatingspline/Supybot-Titler) ?

A: I couldn't get this to work on my system and it has a lot of features I didn't want

Q: It doesn't work for me. What can I do?

A: [Open an issue](https://github.com/butterscotchstallion/limnoria-plugins/issues/new) and include at minimum the following:

- Brief description of the problem
- Any errors that were logged (Look for the ones prefixed "SpiffyTitles")
- How to reproduce the effect
- Any other information you think would be helpful
