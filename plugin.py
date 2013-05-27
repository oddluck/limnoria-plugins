# -*- coding: utf-8 -*-
# Copyright (c) 2013, spline
###

# my libs
import urllib2
import json
# libraries for time_created_at
import time
from datetime import datetime
# for unescape
import re
import htmlentitydefs
# oauthtwitter
import oauth2 as oauth
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class OAuthApi:
    """OAuth class to work with Twitter v1.1 API."""

    def __init__(self, consumer_key, consumer_secret, token, token_secret):
        token = oauth.Token(token, token_secret)
        self._Consumer = oauth.Consumer(consumer_key, consumer_secret)
        self._signature_method = oauth.SignatureMethod_HMAC_SHA1()
        self._access_token = token

    def _FetchUrl(self,url, parameters=None):
        """Fetch a URL with oAuth. Returns a string containing the body of the response."""

        extra_params = {}
        if parameters:
            extra_params.update(parameters)

        req = self._makeOAuthRequest(url, params=extra_params)
        opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=0))
        url = req.to_url()
        url_data = opener.open(url)
        opener.close()
        return url_data

    def _makeOAuthRequest(self, url, token=None, params=None):
        """Make a OAuth request from url and parameters. Returns oAuth object."""

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
        request = oauth.Request(method="GET", url=url, parameters=params)
        request.sign_request(self._signature_method, self._Consumer, token)
        return request

    def ApiCall(self, call, parameters={}):
        """Calls the twitter API with 'call' and returns the twitter object (JSON)."""

        try:
            data = self._FetchUrl("https://api.twitter.com/1.1/" + call + ".json", parameters)
        except urllib2.HTTPError, e:  # http error code.
            return e.code
        except urllib2.URLError, e:  # http "reason"
            return e.reason
        else:  # return data if good.
            return data


class Tweety(callbacks.Plugin):
    """Public Twitter class for working with the API."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Tweety, self)
        self.__parent.__init__(irc)
        self.twitterApi = False
        if not self.twitterApi:
            self._checkAuthorization()

    def _checkAuthorization(self):
        """ Check if we have our keys and can auth."""

        if not self.twitterApi:  # if not set, try and auth.
            failTest = False  # first check that we have all 4 keys.
            for checkKey in ('consumerKey', 'consumerSecret', 'accessKey', 'accessSecret'):
                try:  # try to see if each key is set.
                    testKey = self.registryValue(checkKey)
                except:  # a key is not set, break and error.
                    self.log.debug("Failed checking keys. We're missing the config value for: {0}. Please set this and try again.".format(checkKey))
                    failTest = True
                    break
            # if any missing, throw an error and keep twitterApi=False
            if failTest:
                self.log.error('Failed getting keys. You must set all 4 keys in config variables and reload plugin.')
                return False
            # We have all 4 keys. Now lets see if they are valid by calling verify_credentials in the API.
            self.log.info("Got all 4 keys. Now trying to auth up with Twitter.")
            twitterApi = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
            data = twitterApi.ApiCall('account/verify_credentials')
            # check the response. if we can load json, it means we're authenticated. else, return response.
            try:  # if we pass, response is validated. set self.twitterApi w/object.
                json.loads(data.read())
                self.log.info("I have successfully authorized and logged in to Twitter using your credentials.")
                self.twitterApi = OAuthApi(self.registryValue('consumerKey'), self.registryValue('consumerSecret'), self.registryValue('accessKey'), self.registryValue('accessSecret'))
            except:  # response failed. Return what we got back.
                self.log.error("ERROR: I could not log in using your credentials. Message: {0}".format(data))
                return False
        else:  # if we're already validated, pass.
            pass

    ########################
    # COLOR AND FORMATTING #
    ########################

    def _red(self, string):
        """Returns a red string."""
        return ircutils.mircColor(string, 'red')

    def _blue(self, string):
        """Returns a blue string."""
        return ircutils.mircColor(string, 'blue')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))

    ######################
    # INTERNAL FUNCTIONS #
    ######################

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
        Return relative time delta between now and s (dt string).
        """

        try:  # timeline's created_at Tue May 08 10:58:49 +0000 2012
            ddate = time.strptime(s, "%a %b %d %H:%M:%S +0000 %Y")[:-2]
        except ValueError:
            try:  # search's created_at Thu, 06 Oct 2011 19:41:12 +0000
                ddate = time.strptime(s, "%a, %d %b %Y %H:%M:%S +0000")[:-2]
            except ValueError:
                return s
        # do the math
        d = datetime.utcnow() - datetime(*ddate, tzinfo=None)
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
        Constructs string to output for Tweet. Used for tsearch and twitter.
        """

        # build output string.
        if self.registryValue('outputColorTweets', msg.args[0]):
            ret = "@{0}".format(self._ul(self._blue(nick)))
        else:  # bold otherwise.
            ret = "@{0}".format(self._bu(nick))
        # show real name in tweet output?
        if not self.registryValue('hideRealName', msg.args[0]):
            ret += " ({0})".format(name)
        # add in the end with the text + tape.
        if self.registryValue('colorTweetURLs', msg.args[0]):  # color urls.
            text = re.sub(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', self._red(r'\1'), text)
            ret += ": {0} ({1})".format(text, self._bold(time))
        else:  # only bold time. no text color.
            ret += ": {0} ({1})".format(text, self._bold(time))
        # short url the link to the tweet?
        if self.registryValue('addShortUrl', msg.args[0]):
            url = self._createShortUrl(nick, tweetid)
            if url:  # if we got a url back.
                ret += " {0}".format(url)
        # now return.
        return ret

    def _createShortUrl(self, nick, tweetid):
        """Shortens a tweet into a short one."""

        try:
            longurl = "https://twitter.com/#!/%s/status/%s" % (nick, tweetid)
            posturi = "https://www.googleapis.com/urlshortener/v1/url"
            data = json.dumps({'longUrl': longurl})
            headers = {'Content-Type':'application/json'}
            request = utils.web.getUrl(posturi, data=data, headers=headers)
            return json.loads(request)['id']
        except Exception, err:
            self.log.error("ERROR: Failed shortening url: {0} :: {1}".format(longurl, err))
            return None

    def _woeid_lookup(self, lookup):
        """<location>
        Use Yahoo's API to look-up a WOEID.
        """

        query = "SELECT * FROM geo.places WHERE text='%s'" % lookup
        params = {"q": query,
                  "format":"json",
                  "diagnostics":"false",
                  "env":"store://datatables.org/alltableswithkeys" }
        # everything in try/except block incase it breaks.
        try:
            url = "http://query.yahooapis.com/v1/public/yql?"+utils.web.urlencode(params)
            response = utils.web.getUrl(url)
            data = json.loads(response)

            if data['query']['count'] > 1:  # return the "first" one.
                woeid = data['query']['results']['place'][0]['woeid']
            else:  # if one, return it.
                woeid = data['query']['results']['place']['woeid']
            return woeid
        except Exception, err:
            self.log.error("ERROR: Failed looking up WOEID for '{0}' :: {1}".format(lookup, err))
            return None

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def woeidlookup(self, irc, msg, args, lookup):
        """<location>
        Search Yahoo's WOEID DB for a location. Useful for the trends variable.
        Ex: London or Boston
        """

        woeid = self._woeid_lookup(lookup)
        if woeid:
            irc.reply("WOEID: {0} for '{1}'".format(self._bold(woeid), lookup))
        else:
            irc.reply("ERROR: Something broke trying to find a WOEID for '{0}'".format(lookup))

    woeidlookup = wrap(woeidlookup, ['text'])

    def ratelimits(self, irc, msg, args):
        """
        Display current rate limits for your twitter API account.
        """

        # before we do anything, make sure we have a twitterApi object.
        if not self.twitterApi:
            irc.reply("ERROR: Twitter is not authorized. Please check logs before running this command.")
            return
        # make API call.
        data = self.twitterApi.ApiCall('application/rate_limit_status', parameters={'resources':'trends,search,statuses,users'})
        try:
            data = json.loads(data.read())
        except:
            irc.reply("ERROR: Failed to lookup ratelimit data: {0}".format(data))
            return
        # parse data;
        data = data.get('resources')
        if not data:  # simple check if we have part of the json dict.
            irc.reply("ERROR: Failed to fetch application rate limit status. Something could be wrong with Twitter.")
            self.log.error("ERROR: fetching rate limit data. '{0}'".format(data))
            return
        # dict of resources we want and how to parse. key=human name, values are for the json dict.
        resources = {'trends':['trends', '/trends/place'],
                     'tsearch':['search', '/search/tweets'],
                     'twitter --id':['statuses', '/statuses/show/:id'],
                     'twitter --info':['users', '/users/show/:id'],
                     'twitter timeline':['statuses', '/statuses/user_timeline'] }
        # now iterate through dict above.
        for resource in resources:
            rdict = resources[resource]  # get value.
            endpoint = data.get(rdict[0]).get(rdict[1])  # value[0], value[1]
            minutes = "%sm%ss" % divmod(int(endpoint['reset'])-int(time.time()), 60)  # math.
            output = "Reset in: {0}  Remaining: {1}".format(minutes, endpoint['remaining'])
            irc.reply("{0} :: {1}".format(self._bold(resource), output))

    ratelimits = wrap(ratelimits)

    def trends(self, irc, msg, args, getopts, optwoeid):
        """[--exclude] [location]

        Returns the Top 10 Twitter trends for a specific location. Use optional argument location for trends.
        Defaults to worldwide and can be set via config variable.
        Use --exclude to not include #hashtags in trends data.
        Ex: Boston or --exclude London
        """

        # enforce +voice or above to use command?
        if self.registryValue('requireVoiceOrAbove', msg.args[0]):
            if irc.state.channels[msg.args[0]].isVoicePlus(msg.nick):  # are they voice or op?
                irc.error("ERROR: You have to be at least voiced to use the trends command in {0}.".format(msg.args[0]))
                return

        # before we do anything, make sure we have a twitterApi object.
        if not self.twitterApi:
            irc.reply("ERROR: Twitter is not authorized. Please check logs before running this command.")
            return

        # default arguments.
        args = {'id': self.registryValue('woeid', msg.args[0]),
                'exclude': self.registryValue('hideHashtagsTrends', msg.args[0])}
        # handle input.
        if getopts:
            for (key, value) in getopts:
                if key == 'exclude':  # remove hashtags from trends.
                    args['exclude'] = 'hashtags'
        # work with woeid. 1 is world, the default. can be set via input or via config.
        if optwoeid:  # if we have an input location, lookup the woeid.
            if optwoeid.lower().startswith('world'):  # looking for worldwide or some variation. (bypass)
                args['id'] = 1  # "World Wide" is worldwide (odd bug) = 1.
            else:  # looking for something else.
                woeid = self._woeid_lookup(optwoeid)  # yahoo search for woeid.
                if woeid:  # if we get a returned value, set it. otherwise default value.
                    args['id'] = woeid
                else:  # location not found.
                    irc.reply("ERROR: I could not lookup location: {0}. Try a different location.".format(optwoeid))
                    return
        # now build our API call
        data = self.twitterApi.ApiCall('trends/place', parameters=args)
        try:
            data = json.loads(data.read())
        except:
            irc.reply("ERROR: failed to lookup trends on Twitter: {0}".format(data))
            return
        # now, before processing, check for errors:
        if 'errors' in data:
            if data['errors'][0]['code'] == 34:  # 34 means location not found.
                irc.reply("ERROR: I do not have any trends for: {0}".format(optwoeid))
                return
            else:  # just return the message.
                errmsg = data['errors'][0]
                irc.reply("ERROR: Could not load trends. ({0} {1})".format(errmsg['code'], errmsg['message']))
                return
        # if no error here, we found trends. prepare string and output.
        location = data[0]['locations'][0]['name']
        ttrends = " | ".join([trend['name'].encode('utf-8') for trend in data[0]['trends']])
        irc.reply("Top 10 Twitter Trends in {0} :: {1}".format(self._bold(location), ttrends))

    trends = wrap(trends, [getopts({'exclude':''}), optional('text')])

    def tsearch(self, irc, msg, args, optlist, optterm):
        """[--num number] [--searchtype mixed,recent,popular] [--lang xx] <term>

        Searches Twitter for the <term> and returns the most recent results.
        --num is number of results. (1-10)
        --searchtype being recent, popular or mixed. Popular is the default.
        Ex: --num 3 breaking news
        """

        # enforce +voice or above to use command?
        if self.registryValue('requireVoiceOrAbove', msg.args[0]):
            if irc.state.channels[msg.args[0]].isVoicePlus(msg.nick):  # are they voice or op?
                irc.error("ERROR: You have to be at least voiced to use the tsearch command in {0}.".format(msg.args[0]))
                return

        # before we do anything, make sure we have a twitterApi object.
        if not self.twitterApi:
            irc.reply("ERROR: Twitter is not authorized. Please check logs before running this command.")
            return

        # default arguments.
        tsearchArgs = {'include_entities':'false',
                       'count': self.registryValue('defaultSearchResults', msg.args[0]),
                       'lang':'en',
                       'q':utils.web.urlquote(optterm)}
        # check input.
        if optlist:
            for (key, value) in optlist:
                if key == 'num':  # --num
                    maxresults = self.registryValue('maxSearchResults', msg.args[0])
                    if not (1 <= value <= maxresults):  # make sure it's between what we should output.
                        irc.reply("ERROR: '{0}' is not a valid number of tweets. Range is between 1 and {1}.".format(value, maxresults))
                        return
                    else:  # change number to output.
                        tsearchArgs['count'] = value
                if key == 'searchtype':  # getopts limits us here.
                    tsearchArgs['result_type'] = value  # limited by getopts to valid values.
                if key == 'lang':  # lang . Uses ISO-639 codes like 'en' http://en.wikipedia.org/wiki/ISO_639-1
                    tsearchArgs['lang'] = value
        # now build our API call.
        data = self.twitterApi.ApiCall('search/tweets', parameters=tsearchArgs)
        try:
            data = json.loads(data.read())
        except:
            irc.reply("ERROR: Something went wrong trying to search Twitter. ({0})".format(data))
            return
        # check the return data.
        results = data.get('statuses') # data returned as a dict.
        if not results or len(results) == 0:  # found nothing or length 0.
            irc.reply("ERROR: No Twitter Search results found for '{0}'".format(optterm))
            return
        else:  # we found something.
            for result in results:  # iterate over each.
                nick = result['user'].get('screen_name').encode('utf-8')
                name = result["user"].get('name').encode('utf-8')
                text = self._unescape(result.get('text')).encode('utf-8')
                date = self._time_created_at(result.get('created_at'))
                tweetid = result.get('id_str')
                # build output string and output.
                output = self._outputTweet(irc, msg, nick, name, text, date, tweetid)
                irc.reply(output)

    tsearch = wrap(tsearch, [getopts({'num':('int'),
                                      'searchtype':('literal', ('popular', 'mixed', 'recent')),
                                      'lang':('somethingWithoutSpaces')}),
                                     ('text')])

    def twitter(self, irc, msg, args, optlist, optnick):
        """[--noreply] [--nort] [--num number] <nick> | [--id id] | [--info nick]

        Returns last tweet or 'number' tweets (max 10). Shows all tweets, including rt and reply.
        To not display replies or RT's, use --noreply or --nort, respectively.
        Or returns specific tweet with --id 'tweet#'.
        Or returns information on user with --info 'name'.
        Ex: --info @cnn OR --id 337197009729622016 OR --number 3 @drudge
        """

        # enforce +voice or above to use command?
        if self.registryValue('requireVoiceOrAbove', msg.args[0]):
            if irc.state.channels[msg.args[0]].isVoicePlus(msg.nick):  # are they voice or op?
                irc.error("ERROR: You have to be at least voiced to use the twitter command in {0}.".format(msg.args[0]))
                return

        # before we do anything, make sure we have a twitterApi object.
        if not self.twitterApi:
            irc.reply("ERROR: Twitter is not authorized. Please check logs before running this command.")
            return

        # now begin
        optnick = optnick.replace('@','')  # strip @ from input if given.
        # default options.
        args = {'id': False,
                'nort': False,
                'noreply': False,
                'num': self.registryValue('defaultResults', msg.args[0]),
                'info': False}
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
                    maxresults = self.registryValue('maxResults', msg.args[0])
                    if not (1 <= value <= maxresults):  # make sure it's between what we should output.
                        irc.reply("ERROR: '{0}' is not a valid number of tweets. Range is between 1 and {1}.".format(value, maxresults))
                        return
                    else:  # number is valid so return this.
                        args['num'] = value
                if key == 'info':
                    args['info'] = True
        # handle the three different rest api endpoint urls + twitterArgs dict for options.
        if args['id']:  # -id #.
            apiUrl = 'statuses/show'
            twitterArgs = {'id': optnick, 'include_entities':'false'}
        elif args['info']:  # --info.
            apiUrl = 'users/show'
            twitterArgs = {'screen_name': optnick, 'include_entities':'false'}
        else:  # if not an --id or --info, we're printing from their timeline.
            apiUrl = 'statuses/user_timeline'
            twitterArgs = {'screen_name': optnick, 'count': args['num']}
            if args['nort']:  # show retweets?
                twitterArgs['include_rts'] = 'false'
            else:  # default is to show retweets.
                twitterArgs['include_rts'] = 'true'
            if args['noreply']:  # show replies?
                twitterArgs['exclude_replies'] = 'true'
            else:  # default is to NOT exclude replies.
                twitterArgs['exclude_replies'] = 'false'
        # call the Twitter API with our data.
        data = self.twitterApi.ApiCall(apiUrl, parameters=twitterArgs)
        try:
            data = json.loads(data.read())
        except:
            irc.reply("ERROR: Failed to lookup Twitter for '{0}' ({1}) ".format(optnick, data))
            return
        # before anything, check for errors. errmsg is conditional.
        if 'errors' in data:
            if data['errors'][0]['code'] == 34:  # not found.
                if args['id']:  # --id #. # is not found.
                    errmsg = "ERROR: Tweet ID '{0}' not found.".format(optnick)
                else:  # --info <user> or twitter <user> not found.
                    errmsg = "ERROR: Twitter user '{0}' not found.".format(optnick)
                irc.reply(errmsg)  # print the error and exit.
                return
            else:  # errmsg is not 34. just return it.
                errmsg = data['errors'][0]
                irc.reply("ERROR: {0} {1}".format(errmsg['code'], errmsg['message']))
                return
        # no errors, so we process data conditionally.
        if args['id']:  # If --id was given for a single tweet.
            text = self._unescape(data.get('text')).encode('utf-8')
            nick = data["user"].get('screen_name').encode('utf-8')
            name = data["user"].get('name').encode('utf-8')
            relativeTime = self._time_created_at(data.get('created_at'))
            tweetid = data.get('id')
            # prepare string to output and send to irc.
            output = self._outputTweet(irc, msg, nick, name, text, relativeTime, tweetid)
            irc.reply(output)
            return
        elif args['info']:  # --info to return info on a Twitter user.
            location = data.get('location')
            followers = data.get('followers_count')
            friends = data.get('friends_count')
            description = data.get('description')
            screen_name = data.get('screen_name')
            created_at = data.get('created_at')
            statuses_count = data.get('statuses_count')
            protected = data.get('protected')
            name = data.get('name')
            url = data.get('url')
            # build output string conditionally. build string conditionally.
            ret = self._bu("@{0}".format(screen_name.encode('utf-8')))
            ret += " ({0})".format(name.encode('utf-8'))
            if protected:  # is the account protected/locked?
                ret += " [{0}]:".format(self._bu('LOCKED'))
            else:  # open.
                ret += ":"
            if url:  # do they have a url?
                ret += " {0}".format(self._ul(url.encode('utf-8')))
            if description:  # a description?
                ret += " {0}".format(description.encode('utf-8'))
            ret += " [{0} friends,".format(self._bold(friends))
            ret += " {0} tweets,".format(self._bold(statuses_count))
            ret += " {0} followers,".format(self._bold(followers))
            ret += " signup: {0}".format(self._bold(self._time_created_at(created_at)))
            if location:  # do we have location?
                ret += " Location: {0}]".format(location.encode('utf-8'))
            else: # nope.
                ret += "]"
            # finally, output.
            irc.reply(ret)
            return
        else:  # this will display tweets/a user's timeline. can be n+1 tweets.
            if len(data) == 0:  # no tweets found.
                irc.reply("ERROR: '{0}' has not tweeted yet.".format(optnick))
                return
            for tweet in data:  # n+1 tweets found. iterate through each tweet.
                text = self._unescape(tweet.get('text')).encode('utf-8')
                nick = tweet["user"].get('screen_name').encode('utf-8')
                name = tweet["user"].get('name').encode('utf-8')
                tweetid = tweet.get('id')
                relativeTime = self._time_created_at(tweet.get('created_at'))
                # prepare string to output and send to irc.
                output = self._outputTweet(irc, msg, nick, name, text, relativeTime, tweetid)
                irc.reply(output)

    twitter = wrap(twitter, [getopts({'noreply':'',
                                      'nort':'',
                                      'info':'',
                                      'id':('int'),
                                      'num':('int')}), ('somethingWithoutSpaces')])

Class = Tweety


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=279:
