# SpiffyTitles #

Displays link titles when posted in a channel. This plugin has the following goals:

- Extreme reliability and in the case of failure, robust error reporting to ease debugging. Errors
are logged.

- The ability to customize features that could conceivably need to change (within reason)

## Using SpiffyTitles ##
- You should `unload` the Web plugin and any other plugins that show link titles for best results

To unload the Web plugin:

    !unload Web

Load SpiffyTitles:
    
    !load SpiffyTitles

## Available Options ##

`defaultTitleTemplate` - This is the template used when showing the title of a link. 

Default value: `^ $title`

Example output:

    ^ Google.com

`youtubeTitleTemplate` - This is the template used when showing the title of a YouTube video

Default value: `^ $title :: Duration: $duration :: Views: $view_count :: Rating: $rating`

Example output:

    ^ Snoop Dogg - Pump Pump feat. Lil Malik :: Duration: 00:04:41 :: Views: 189,120 :: Rating: 4.82

`useBold` - Whether to bold the title. Default value: `False`

`channelWhitelist` - a comma separated list of channels in which titles should be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

`channelBlacklist` - a comma separated list of channels in which titles should never be displayed. If `""`,
titles will be shown in all channels. Default value: `""`

### About white/black lists ###

- If `channelWhitelist` and `channelBlacklist` are empty, then titles will be displayed in every channel
- If `channelBlacklist` has #foo, then titles will be displayed in every channel except #foo
- If `channelWhitelist` has #foo then `channelBlacklist` will be ignored

### Examples ###


### Show titles in every channel except #foo ###
    
    !config supybot.plugins.SpiffyTitles.channelBlacklist #foo
    
### Only show titles in #bar ###
    
    !config supybot.plugins.SpiffyTitles.channelWhitelist #bar

### Remove channel whitelist ###
    
    !config supybot.plugins.SpiffyTitles.channelWhitelist ""

`ignoredDomainPattern` - ignore domains matching this pattern. Default value: `(i\.imgur\.com)`

### Tip ###

You can ignore domains that you know aren't websites, like `i.imgur.com`. This prevents a request
from being made at all.

### Examples ###

Ignore all links with the domain `i.imgur.com` (default behavior)

    !config supybot.plugins.SpiffyTitles.ignoredDomainPattern (i\.imgur\.com)

Ignore `*.tk` and `i.imgur.com`

    !config supybot.plugins.SpiffyTitles.ignoredDomainPattern (\.tk|i\.imgur\.com)

`userAgents` - A comma separated list of strings of user agents randomly chosen when requesting. 

`urlRegularExpression` - A regular expression used to match URLs. You shouldn't need to change this.

### FAQ ###

Q: Why not use the [Web](https://github.com/ProgVal/Limnoria/tree/master/plugins/Web) plugin?

A: My experience was that it didn't work very well and lacked the ability to customize the options
I wanted to change.

Q: What about [Supybot-Titler](https://github.com/reticulatingspline/Supybot-Titler) ?

A: I couldn't get this to work on my system and it has a lot of features I didn't want

Q: It doesn't work for me. What can I do?

A: [Open an issue](https://github.com/prgmrbill/limnoria-plugins/issues/new) and include at minimum the following:

- Brief description of the problem
- Any errors that were logged (Look for the ones prefixed "SpiffyTitles")
- How to reproduce the effect
- Any other information you think would be helpful
