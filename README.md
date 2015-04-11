# SpiffyTitles #

Displays link titles when posted in a channel. This plugin has the following goals:

- Extreme reliability and in the case of failure, robust error reporting to ease debugging. Errors
are logged.

- The ability to customize features that could conceivably need to change (within reason)

## Using SpiffyTitles ##
- You should disable the Web plugin and any other plugins that show link titles for best results

## Available Options ##

`defaultTitleTemplate` - This is the template used when showing the title of a link. 

Default:

    ^ Google.com

`youtubeTitleTemplate` - This is the template used when showing the title of a YouTube video

Default:

    ^ Example Video Title :: Views: 3,1337 :: Rating: 5.0

`useBold` - Whether to bold the title. Defaults to `False`

`channelWhitelist` - a comma separated list of channels in which titles should be displayed. If empty,
titles will be shown in all channels.

`ignoredDomainPatterns` - a comma separated list of strings that are regular expressions to match
against URLs posted in channels.

    Examples

    Ignore all domains matching *.tk

        (.*)\.tk

    Ignore all domains matching *.net

        (.*)\.net

`userAgents` - A comma separated list of strings of user agents randomly chosen when requesting. 

`urlRegularExpression` - A regular expression used to match URLs. You shouldn't need to change this.

### FAQ ###

Q: Why not use the [Web](https://github.com/ProgVal/Limnoria/tree/master/plugins/Web) plugin?

A: My experience was that it didn't work very well and lacked the ability to customize its options

Q: What about [Supybot-Titler](https://github.com/reticulatingspline/Supybot-Titler) ?

A: I couldn't get this to work on my system and it has a lot of features I didn't want

Q: It doesn't work for me. What can I do?

A: [Open an issue](https://github.com/prgmrbill/limnoria-plugins/issues/new) and include at minimum the following:

- Brief description of the problem
- Any errors that were logged (Look for the ones prefixed "SpiffyTitles")
- How to reproduce the effect
- Any other information you think would be helpful
