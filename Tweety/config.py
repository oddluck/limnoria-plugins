# -*- coding: utf-8 -*-
# Copyright (c) 2013, spline
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Tweety', True)


Tweety = conf.registerPlugin('Tweety')
conf.registerGlobalValue(Tweety,'consumerKey',registry.String('', """The consumer key of the application."""))
conf.registerGlobalValue(Tweety,'consumerSecret',registry.String('', """The consumer secret of the application.""", private=True))
conf.registerGlobalValue(Tweety,'accessKey',registry.String('', """The Twitter Access Token key for the bot's account"""))
conf.registerGlobalValue(Tweety,'accessSecret',registry.String('', """The Twitter Access Token secret for the bot's account""", private=True))
conf.registerChannelValue(Tweety,'hideRealName',registry.Boolean(False, """Do not show real name when displaying tweets."""))
conf.registerChannelValue(Tweety,'addShortUrl',registry.Boolean(False, """Whether or not to add a short URL to the tweets."""))
conf.registerChannelValue(Tweety,'woeid',registry.Integer(1, """Where On Earth ID. World Wide is 1. USA is 23424977."""))
conf.registerChannelValue(Tweety,'defaultSearchResults',registry.Integer(3, """Default number of results to return on searches."""))
conf.registerChannelValue(Tweety,'maxSearchResults',registry.Integer(10, """Maximum number of results to return on searches"""))
conf.registerChannelValue(Tweety,'defaultResults',registry.Integer(1, """Default number of results to return on timelines."""))
conf.registerChannelValue(Tweety,'maxResults',registry.Integer(10, """Maximum number of results to return on timelines."""))
conf.registerChannelValue(Tweety,'outputColorTweets',registry.Boolean(False, """When outputting Tweets, display them with some color."""))
conf.registerChannelValue(Tweety,'hideHashtagsTrends',registry.Boolean(False, """When displaying trends, should we display #hashtags? Default is no."""))
conf.registerChannelValue(Tweety,'requireVoiceOrAbove',registry.Boolean(False, """Only allows a user with voice or above on a channel to use commands."""))
conf.registerChannelValue(Tweety,'colorTweetURLs',registry.Boolean(False, """Try and color URLs (red) in Tweets?"""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=250:
