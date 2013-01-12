# -*- coding: utf-8 -*-
###
# Copyright (c) 2011-2013, Terje Hoås, spline
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

# my libs
import urllib, urllib2
import json
import string
# libraries for time_created_at
import time
from datetime import tzinfo, datetime, timedelta
# for unescape
import re, htmlentitydefs
# reencode
import unicodedata
# oauthtwitter
import urlparse
import oauth2 as oauth

#supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

# Twitter error classes from the sixohsix/Twitter API.
class TwitterError(Exception):
    """Base Exception thrown by the Twitter object when there is a general error interacting with the API."""
    pass

class TwitterHTTPError(TwitterError):
    """Exception thrown by the Twitter object when there is an HTTP error interacting with twitter.com."""
    def __init__(self, e, uri, format, uriparts):
      self.e = e
      self.uri = uri
      self.format = format
      self.uriparts = uriparts

    def __str__(self):
        return (
            "Twitter sent status %i for URL: %s.%s using parameters: "
            "(%s)\ndetails: %s" %(
                self.e.code, self.uri, self.format, self.uriparts,
                self.e.fp.read()))

# OAuthApi class from https://github.com/jpittman/OAuth-Python-Twitter
# mainly kept intact but modified for Twitter API v1.1 and unncessary things removed. 
class OAuthApi:
    def __init__(self, consumer_key, consumer_secret, token=None, token_secret=None):
        if token and token_secret:
            token = oauth.Token(token, token_secret)
        else:
            token = None
        self._Consumer = oauth.Consumer(consumer_key, consumer_secret)
        self._signature_method = oauth.SignatureMethod_HMAC_SHA1()
        self._access_token = token 
        
    def _FetchUrl(self,url, http_method=None, parameters=None):
        extra_params = {}
        if parameters:
            extra_params.update(parameters)
        
        req = self._makeOAuthRequest(url, params=extra_params, http_method=http_method)      
        opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
        url = req.to_url()
        #callbacks.log.info(str(url))        
        url_data = opener.open(url).read()
        opener.close()
        return url_data
    
    def _makeOAuthRequest(self, url, token=None, params=None, http_method="GET"):       
        oauth_base_params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time())
            }
        
        if params:
            params.update(oauth_base_params)
        else:
            params = oauth_base_params
        
        if not token:
            token = self._access_token
        request = oauth.Request(method=http_method,url=url,parameters=params)
        request.sign_request(self._signature_method, self._Consumer, token)
        return request

    def ApiCall(self, call, type="GET", parameters={}):
        return_value = []
        try:
            data = self._FetchUrl("https://api.twitter.com/1.1/" + call + ".json", type, parameters)
        except urllib2.HTTPError, e:
            if (e.code == 304):
                return []
            else:
                raise TwitterHTTPError(e, uri, self.format, arg_data)
        except urllib2.URLError, e:
            return e
        else:
            return data

# now, begin our actual code.
# APIDOCS https://dev.twitter.com/docs/api/1.1
# TODO: centralize logging in. Add something to display error codes in the log while displaying error to irc.
# TODO: work on colorizing tweets better.
# TODO: maybe make an encode wrapper that can utilize strip_accents?
# TODO: langs in search to validate against: https://dev.twitter.com/docs/api/1.1/get/help/languages

class Tweety(callbacks.Plugin):
    """Simply use the commands available in this plugin. Allows fetching of the
    latest tween from a specified twitter handle, and listing of top ten
    trending tweets."""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Tweety, self)
        self.__parent.__init__(irc)
        self.twitter = False
        if not self.twitter:
            self._checkAuthorization()

    def _checkAuthorization(self):
        if not self.twitter:
            failTest = False
            for checkKey in ('consumerKey', 'consumerSecret', 'accessKey', 'accessSecret'):
                try:
                    testKey = self.registryValue(checkKey)
                except:
                    self.log.debug("Failed checking keys. We're missing the config value for: {0}. Please set this and try again.".format(checkKey))
                    failTest = True
                    break
        
            if failTest:
                self.log.error('Failed getting keys. You must set all 4 keys in config variables.')
                return False
        
            self.log.info("Got all 4 keys. Now trying to auth up with Twitter.")
            twitter = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
            data = twitter.ApiCall('account/verify_credentials')
            
            try:
                testjson = json.loads(data)
            except:
                self.log.debug("Failed logging in. Returned: %s" % data)
                return False
                
            if testjson:
                self.log.info("I have successfully authorized and logged in to Twitter using your credentials.")
                self.twitter = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
        else:
            pass

    def _strip_accents(string):
        import unicodedata
        return unicodedata.normalize('NFKD', unicode(string)).encode('ASCII', 'ignore')

    def _convert_to_utf8_str(arg):
        # written by Michael Norton (http://docondev.blogspot.com/)
        if isinstance(arg, unicode):
            arg = arg.encode('utf-8')
        elif not isinstance(arg, str):
            arg = str(arg)
        return arg

    def _unescape(self, text):
        """Created by Fredrik Lundh (http://effbot.org/zone/re-sub.htm#unescape-html)"""
        text = text.replace("\n", " ")
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except (ValueError, OverflowError):
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is
        return re.sub("&#?\w+;", fixup, text)


    def _time_created_at(self, s):
        """
        Takes a datetime string object that comes from twitter and twitter search timelines and returns a relative date.
        """
        # twitter search and timelines use different timeformats
        # timeline's created_at Tue May 08 10:58:49 +0000 2012
        # search's created_at Thu, 06 Oct 2011 19:41:12 +0000
        try:
            ddate = time.strptime(s, "%a %b %d %H:%M:%S +0000 %Y")[:-2]
        except ValueError:
            try:
                ddate = time.strptime(s, "%a, %d %b %Y %H:%M:%S +0000")[:-2]
            except ValueError:
                return "unknown"

        # do the math
        created_at = datetime(*ddate, tzinfo=None)
        d = datetime.utcnow() - created_at

        # now parse and return.
        if d.days:
            rel_time = "%sd ago" % d.days
        elif d.seconds > 3600: 
            rel_time = "%sh ago" % (d.seconds / 3600)
        elif 60 <= d.seconds < 3600:
            rel_time = "%sm ago" % (d.seconds / 60)
        else:
            rel_time = "%ss ago" % (d.seconds)
        return rel_time


    def _outputTweet(self, irc, msg, nick, name, text, time, tweetid):
        """
        Takes a group of strings and outputs a Tweet to IRC. Used for tsearch and twitter.
        """
        
        outputColorTweets = self.registryValue('outputColorTweets', msg.args[0])
        
        if outputColorTweets:
            ret = ircutils.underline(ircutils.mircColor(("@" + nick), 'blue'))
        else:
            ret = ircutils.underline(ircutils.bold("@" + nick))
            
        if not self.registryValue('hideRealName', msg.args[0]): # show realname in tweet output?
            ret += " ({0})".format(name)
            
        # add in the end with the text + tape
        if outputColorTweets:
            text = re.sub(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', ircutils.mircColor(r'\1', 'red'), text) # color urls.
            ret += ": {0} ({1})".format(text, ircutils.mircColor(time, 'yellow'))
        else:            
            ret += ": {0} ({1})".format(text, ircutils.bold(time))
        
        if self.registryValue('addShortUrl', msg.args[0]):
            if self._createShortUrl(nick, tweetid):
                ret += " {0}".format(url)
        
        irc.reply(ret)


    def _createShortUrl(self, nick, tweetid):
        """
        Takes a nick and tweetid and returns a shortened URL via is.gd service.
        """
        
        longurl = "https://twitter.com/#!/{0}/status/{1}".format(nick, tweetid)
        try:
            req = urllib2.Request("http://is.gd/api.php?longurl=" + urllib.quote(longurl))
            f = urllib2.urlopen(req)
            shorturl = f.read()
            return shorturl
        except:
            return False


    def _woeid_lookup(self, lookup):
        """
        Use Yahoo's API to look-up a WOEID.
        """

        query = "select * from geo.places where text='%s'" % lookup
        params = {
                "q": query,
                "format":"json",
                "diagnostics":"false",
                "env":"store://datatables.org/alltableswithkeys"}

        try:
            response = urllib2.urlopen("http://query.yahooapis.com/v1/public/yql",urllib.urlencode(params))
            data = json.loads(response.read())

            if data['query']['count'] > 1:
                woeid = data['query']['results']['place'][0]['woeid']
            else:
                woeid = data['query']['results']['place']['woeid']
            return woeid
        except Exception, err:
            self.log.error("Error looking up %s :: %s" % (lookup,err))
            return None
    
    ##########################
    ### PUBLIC FUNCTIONS #####
    ##########################

    def woeidlookup(self, irc, msg, args, lookup):
        """[location]
        Search Yahoo's WOEID DB for a location. Useful for the trends variable.
        """

        woeid = self._woeid_lookup(lookup)
        if woeid:
            irc.reply(("I found WOEID: %s while searching for: '%s'") % (ircutils.bold(woeid), lookup))
        else:
            irc.reply(("Something broke while looking up: '%s'") % (lookup))

    woeidlookup = wrap(woeidlookup, ['text'])
    

    # RATELIMITING
    # https://dev.twitter.com/docs/api/1.1/get/application/rate_limit_status
    # https://dev.twitter.com/docs/rate-limiting/1.1
    # https://dev.twitter.com/docs/rate-limiting/1.1/limits    
    def ratelimits(self, irc, msg, args):
        """
        Display current rate limits for your twitter API account.
        """
        
        data = self.twitter.ApiCall('application/rate_limit_status') #, parameters={'resources':optstatus})
        
        try:
            data = json.loads(data)
        except:
            irc.reply("Failed to lookup rate limit data. Something might have gone wrong. Data: %s" % data)
            return     
        
        data = data.get('resources', None)
              
        if not data: # simple check if we have part of the json dict.
            irc.reply("Failed to fetch application rate limit status. Something could be wrong with Twitter.")
            self.log.error(data)
            return

        # we only have resources needed in here. def below works with each entry properly.        
        resourcelist = ['trends/place', 'search/tweets', 'users/show/:id', 'statuses/show/:id', 'statuses/user_timeline/:id']
        
        for resource in resourcelist:
            family, endpoint = resource.split('/', 1) # need to split each entry on /, resource family is [0], append / to entry.
            resourcedict = data.get(family, None)
            endpoint = resourcedict.get("/"+resource, None)
            irc.reply("{0} :: {1}".format(resource, endpoint))
            # endpoint is {u'reset': 1351226072, u'limit': 15, u'remaining': 15}
        
    ratelimits = wrap(ratelimits)

    #< X-Rate-Limit-Limit: 15
    #< X-Rate-Limit-Remaining: 13
    #< X-Rate-Limit-Reset: 1357963140 / time.now()



    # https://dev.twitter.com/docs/api/1.1/get/trends/place
    def trends(self, irc, msg, args, getopts, optwoeid):
        """<location>
        Returns the Top 10 Twitter trends for a specific location. 
        Use optional argument location for trends. Ex: trends Boston
        Use --exclude to not include #hashtags in trends data.
        """
        
        args = {'id':self.registryValue('woeid', msg.args[0]),'exclude':self.registryValue('hideHashtagsTrends', msg.args[0])}
        if getopts:
            for (key,value) in getopts:
                if key=='exclude': # remove hashtags from trends.
                    args['exclude'] = 'hashtags'
                
        # work with woeid. 1 is world, the default. can be set via input or via config.
        if optwoeid:
            woeid = self._woeid_lookup(optwoeid)
            if woeid:
                args['id'] = woeid
                  
        data = self.twitter.ApiCall('trends/place', parameters=args)
        try:
            data = json.loads(data)
        except:
            irc.reply("Failed to lookup trends data. Something might have gone wrong. DATA: %s" % data)
            return
                    
        try:
            location = data[0]['locations'][0]['name']
        except:
            irc.reply("ERROR: Cannot load trends: {0}".format(data)) # error also throws 404.
            return
        
        ttrends = string.join([trend['name'].encode('utf-8') for trend in data[0]['trends']], " | ")
        
        irc.reply("Top 10 Twitter Trends in {0} :: {1}".format(ircutils.bold(location), ttrends))

    trends = wrap(trends, [getopts({'exclude':''}), optional('text')])
    

    # https://dev.twitter.com/docs/api/1.1/get/search/tweets
    def tsearch(self, irc, msg, args, optlist, optterm):
        """ [--num number] [--searchtype mixed,recent,popular] [--lang xx] <term>

        Searches Twitter for the <term> and returns the most recent results.
        Number is number of results. Must be a number higher than 0 and max 10.
        searchtype being recent, popular or mixed. Popular is the default.
        """
        
        tsearchArgs = {'include_entities':'false', 'count': self.registryValue('defaultSearchResults', msg.args[0]), 'lang':'en', 'q':urllib.quote(optterm)}

        if optlist:
            for (key, value) in optlist:
                if key == 'num':
                    max = self.registryValue('maxSearchResults', msg.args[0])
                    if value > max or value <= 0:
                        irc.reply("Error: '{0}' is not a valid number of tweets. Range is above 0 and max {1}.".format(value, max))
                        return
                    else:
                        tsearchArgs['count'] = value
                if key == 'searchtype':
                    tsearchArgs['result_type'] = value # limited by getopts to valid values.
                if key == 'lang': # lang . Uses ISO-639 codes like 'en' http://en.wikipedia.org/wiki/ISO_639-1
                    tsearchArgs['lang'] = value 

        try:
            twitter = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
        except:
            irc.reply("Failed to authorize with twitter.")
            return
        
        try:        
            data = twitter.ApiCall('search/tweets', parameters=tsearchArgs)
        except:
            irc.reply("Failed to get search results. Twitter broken?")
            return
            
        results = data.get('statuses', None) # data returned as a dict 

        if not results or len(results) == 0:
            irc.reply("Error: No Twitter Search results found for '{0}'".format(optterm))
            return
        else:
            for result in results:
                nick = result['user'].get('screen_name', None)
                name = result["user"].get('name', None)
                text = self._unescape(result.get('text', None)) # look also at the unicode strip here.
                date = self._time_created_at(result.get('created_at', None))
                tweetid = result.get('id_str', None)
                self._outputTweet(irc, msg, nick.encode('utf-8'), name.encode('utf-8'), text.encode('utf-8'), date, tweetid)

    tsearch = wrap(tsearch, [getopts({'num':('int'), 'searchtype':('literal', ('popular', 'mixed', 'recent')), 'lang':('somethingWithoutSpaces')}), ('text')])


    # INFO https://dev.twitter.com/docs/api/1.1/get/users/show
    # ID https://dev.twitter.com/docs/api/1.1/get/statuses/show/%3Aid
    # TIMELINE https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
    def twitter(self, irc, msg, args, optlist, optnick):
        """[--noreply] [--nort] [--num number] <nick> | <--id id> | [--info nick]

        Returns last tweet or 'number' tweets (max 10). Shows all tweets, including rt and reply.
        To not display replies or RT's, use --noreply or --nort, respectively. 
        Or returns tweet with id 'id'.
        Or returns information on user with --info. 
        """
            
        optnick = optnick.replace('@','') # strip @ from input if given.
        
        args = {'id': False, 'nort': False, 'noreply': False, 'num': self.registryValue('defaultResults', msg.args[0]), 'info': False}

        # handle input optlist. 
        if optlist: 
            for (key, value) in optlist:
                if key == 'id':
                    args['id'] = True
                if key == 'nort':
                    args['nort'] = True
                if key == 'noreply':
                    args['noreply'] = True
                if key == 'num':
                    if value > self.registryValue('maxResults', msg.args[0]) or value <= 0:
                        irc.reply("Error: '{0}' is not a valid number of tweets. Range is above 0 and max {1}.".format(value, max))
                        return                        
                    else:
                        args['num'] = value
                if key == 'info':
                    args['info'] = True

        # handle the three different rest api endpoint urls + twitterArgs dict for options.
        if args['id']:  
            apiUrl = 'statuses/show'
            twitterArgs = {'id': optnick, 'include_entities':'false'}
        elif args['info']:
            apiUrl = 'users/show'
            twitterArgs = {'screen_name': optnick, 'include_entities':'false'}
        else:
            apiUrl = 'statuses/user_timeline'
            twitterArgs = {'screen_name': optnick, 'count': args['num']}
            if args['nort']: # When set to false, the timeline will strip any native retweets
                twitterArgs['include_rts'] = 'false'
            else:
                twitterArgs['include_rts'] = 'true'
                
            if args['noreply']: # This parameter will prevent replies from appearing in the returned timeline.
                twitterArgs['exclude_replies'] = 'true'
            else:
                twitterArgs['exclude_replies'] = 'false'

        # now with and call the api.
        try:
            twitter = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
        except:
            irc.reply("Failed to authorize with twitter.")
            return
        
        try:        
            data = twitter.ApiCall(apiUrl, parameters=twitterArgs)
        except:
            irc.reply("Failed to get user's timeline. Twitter broken?")
            return
       
        # process the data. 
        if args['id']: # If --id was given for a single tweet.
            text = self._unescape(data.get('text', None))
            nick = data["user"].get('screen_name', None)
            name = data["user"].get('name', None)
            relativeTime = self._time_created_at(data.get('created_at', None))
            tweetid = data.get('id', None)
            self._outputTweet(irc, msg, nick.encode('utf-8'), name.encode('utf-8'), text.encode('utf-8'), relativeTime, tweetid)
            return

        
        elif args['info']: # Works with --info to return info on a Twitter user.
            location = data.get('location', None)
            followers = data.get('followers_count', None)
            friends = data.get('friends_count', None)
            description = data.get('description', None)
            screen_name = data.get('screen_name', None)
            name = data.get('name', None)
            url = data.get('url', None)

            # build ret, output string    
            ret = ircutils.underline(ircutils.bold("@" + optnick))
            ret += " ({0}):".format(name.encode('utf-8'))
            if url:
                ret += " {0}".format(ircutils.underline(url.encode('utf-8')))
            if description:
                ret += " {0}".format(description.encode('utf-8'))
            ret += " [{0} friends,".format(ircutils.bold(friends))
            ret += " {0} followers.".format(ircutils.bold(followers))
            if location: 
                ret += " Location: {0}]".format(location.encode('utf-8'))
            else:
                ret += "]"
            
            irc.reply(ret)
            return

        else: # Else, its the user's timeline. Count is handled above in the GET request. 
            if len(data) == 0:
                irc.reply("User: {0} has not tweeted yet.".format(optnick))
                return
            
            for tweet in data:
                text = self._unescape(tweet.get('text', None))
                nick = tweet["user"].get('screen_name', None)
                name = tweet["user"].get('name', None)
                tweetid = tweet.get('id', None)
                relativeTime = self._time_created_at(tweet.get('created_at', None))
                self._outputTweet(irc, msg, nick.encode('utf-8'), name.encode('utf-8'), text.encode('utf-8'), relativeTime, tweetid)

    twitter = wrap(twitter, [getopts({'noreply':'', 'nort': '', 'info': '', 'id': '', 'num': ('int')}), ('something')])

Class = Tweety


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=279:
