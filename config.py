# coding=utf8
###
# Copyright (c) 2011, Terje Hoås
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

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Tweety', True)


Tweety = conf.registerPlugin('Tweety')
conf.registerGlobalValue(Tweety, 'consumerKey', registry.String('', """The consumer key of the application."""))
conf.registerGlobalValue(Tweety, 'consumerSecret', registry.String('', """The consumer secret of the application.""", private=True))
conf.registerGlobalValue(Tweety, 'accessKey', registry.String('', """The Twitter Access Token key for the bot's account"""))
conf.registerGlobalValue(Tweety, 'accessSecret', registry.String('', """The Twitter Access Token secret for the bot's account""", private=True))
conf.registerChannelValue(Tweety, 'hideRealName', registry.Boolean(False, """Do not show real name when displaying tweets."""))
conf.registerChannelValue(Tweety, 'addShortUrl', registry.Boolean(False, """Whether or not to add a short URL to the tweets."""))
conf.registerChannelValue(Tweety, 'woeid', registry.Integer(1, """Where On Earth ID. World Wide is 1. USA is 23424977."""))
conf.registerChannelValue(Tweety, 'defaultSearchResults', registry.Integer(3, """Default number of results to return on searches."""))
conf.registerChannelValue(Tweety, 'maxSearchResults', registry.Integer(10, """Maximum number of results to return on searches"""))
conf.registerChannelValue(Tweety, 'defaultResults', registry.Integer(1, """Default number of results to return on timelines."""))
conf.registerChannelValue(Tweety, 'maxResults', registry.Integer(10, """Maximum number of results to return on timelines."""))
conf.registerChannelValue(Tweety, 'outputColorTweets', registry.Boolean(False, """When outputting Tweets, display them with some color."""))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
