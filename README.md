# SpiffyTitles #

Displays link titles when posted in a channel.

## Available Options ##

`defaultTitleTemplate` - This is the template used when showing the title of a link. 

Default:

    ^ Google.com

`youtubeTitleTemplate` - This is the template used when showing the title of a YouTube video

Default:

    ^ Example Video Title :: Views: 3,1337 :: Rating: 5.0

`useBold` - Whether to bold the title. Defaults to `False`

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
