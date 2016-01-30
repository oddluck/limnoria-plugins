# -*- coding: utf-8 -*-
###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
###

from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import re
import requests
try:
    from urllib import urlencode
    from urlparse import urlparse, parse_qsl
except ImportError:
    from urllib.parse import urlencode, urlparse, parse_qsl
from bs4 import BeautifulSoup
import random
import json
import cgi
import datetime
from jinja2 import Template
from datetime import timedelta
import timeout_decorator
import unicodedata
import supybot.ircdb as ircdb
import supybot.log as log
import pytz

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("SpiffyTitles")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class SpiffyTitles(callbacks.Plugin):
    """Displays link titles when posted in a channel"""
    threaded = True
    callBefore = ["Web"]
    link_cache = []
    handlers = {}
    wall_clock_timeout = 8
    max_request_retries = 3
    imgur_client = None

    def __init__(self, irc):
        self.__parent = super(SpiffyTitles, self)
        self.__parent.__init__(irc)

        self.wall_clock_timeout = self.registryValue("wallClockTimeoutInSeconds")
        self.default_handler_enabled = self.registryValue("defaultHandlerEnabled")

        self.add_handlers()

    def add_handlers(self):
        """
        Adds all handlers
        """
        self.add_youtube_handlers()
        self.add_imdb_handlers()
        self.add_imgur_handlers()
        self.add_coub_handlers()
        self.add_vimeo_handlers()
        self.add_dailymotion_handlers()
        self.add_wikipedia_handlers()
        self.add_reddit_handlers()

    def add_dailymotion_handlers(self):
        self.handlers["www.dailymotion.com"] = self.handler_dailymotion
        self.handlers["dailymotion.com"] = self.handler_dailymotion
        self.handlers["dai.ly"] = self.handler_dailymotion

    def add_vimeo_handlers(self):
        self.handlers["vimeo.com"] = self.handler_vimeo

    def add_coub_handlers(self):
        self.handlers["coub.com"] = self.handler_coub

    def add_wikipedia_handlers(self):
        self.handlers["wikipedia.org"] = self.handler_wikipedia

    def add_reddit_handlers(self):
        self.handlers["reddit.com"] = self.handler_reddit
        self.handlers["www.reddit.com"] = self.handler_reddit

    def handler_dailymotion(self, url, info, channel):
        """
        Handles dailymotion links
        """
        dailymotion_handler_enabled = self.registryValue("dailymotionHandlerEnabled",
                                                         channel=channel)
        log.debug("SpiffyTitles: calling dailymotion handler for %s" % url)
        title = None
        video_id = None

        """ Get video ID """
        if dailymotion_handler_enabled:
            if "/video/" in info.path:
                video_id = info.path.lstrip("/video/").split("_")[0]

            if info.netloc == "dai.ly":
                video_id = info.path.lstrip("/")

            if video_id is not None:
                fields = "id,title,owner.screenname,duration,views_total"
                api_url = "https://api.dailymotion.com/video/%s?fields=%s" % (video_id, fields)
                log.debug("SpiffyTitles: looking up dailymotion info: %s", api_url)
                agent = self.get_user_agent()
                headers = {
                    "User-Agent": agent
                }

                request = requests.get(api_url, headers=headers)

                ok = request.status_code == requests.codes.ok

                if ok:
                    response = json.loads(request.text)

                    if response is not None and "title" in response:
                        video = response
                        dailymotion_template = \
                            Template(self.registryValue("dailymotionVideoTitleTemplate",
                                                        channel=channel))
                        video["views_total"] = "{:,}".format(int(video["views_total"]))
                        video["duration"] = self.get_duration_from_seconds(video["duration"])
                        video["ownerscreenname"] = video["owner.screenname"]

                        title = dailymotion_template.render(video)
                    else:
                        log.debug("SpiffyTitles: received unexpected payload from video: %s" %
                                  api_url)
                else:
                    log.error("SpiffyTitles: dailymotion handler returned %s: %s" %
                              (request.status_code, request.text[:200]))

        if title is None:
            log.debug("SpiffyTitles: could not get dailymotion info for %s" % url)

            return self.handler_default(url, channel)
        else:
            return title

    def handler_vimeo(self, url, domain, channel):
        """
        Handles Vimeo links
        """
        vimeo_handler_enabled = self.registryValue("vimeoHandlerEnabled", channel=channel)
        log.debug("SpiffyTitles: calling vimeo handler for %s" % url)
        title = None
        video_id = None

        """ Get video ID """
        if vimeo_handler_enabled:
            result = re.search(r'^(http(s)://)?(www\.)?(vimeo\.com/)?(\d+)', url)

            if result is not None:
                video_id = result.group(5)

            if video_id is not None:
                api_url = "https://vimeo.com/api/v2/video/%s.json" % video_id
                log.debug("SpiffyTitles: looking up vimeo info: %s", api_url)
                agent = self.get_user_agent()
                headers = {
                    "User-Agent": agent
                }

                request = requests.get(api_url, headers=headers)

                ok = request.status_code == requests.codes.ok

                if ok:
                    response = json.loads(request.text)

                    if response is not None and "title" in response[0]:
                        video = response[0]
                        vimeo_template = Template(self.registryValue("vimeoTitleTemplate",
                                                  channel=channel))

                        """
                        Some videos do not have this information available
                        """
                        if "stats_number_of_plays" in video:
                            int_plays = int(video["stats_number_of_plays"])
                            video["stats_number_of_plays"] = "{:,}".format(int_plays)
                        else:
                            video["stats_number_of_plays"] = 0

                        if "stats_number_of_comments" in video:
                            int_comments = int(video["stats_number_of_comments"])
                            video["stats_number_of_comments"] = "{:,}".format(int_comments)
                        else:
                            video["stats_number_of_comments"] = 0

                        video["duration"] = self.get_duration_from_seconds(video["duration"])

                        title = vimeo_template.render(video)
                    else:
                        log.debug("SpiffyTitles: received unexpected payload from video: %s" %
                                  api_url)
                else:
                    log.error("SpiffyTitles: vimeo handler returned %s: %s" % (request.status_code,
                                                                               request.text[:200]))

        if title is None:
            log.debug("SpiffyTitles: could not get vimeo info for %s" % url)

            return self.handler_default(url, channel)
        else:
            return title

    def handler_coub(self, url, domain, channel):
        """
        Handles coub.com links
        """
        coub_handler_enabled = self.registryValue("coubHandlerEnabled", channel=channel)
        log.debug("SpiffyTitles: calling coub handler for %s" % url)
        title = None

        """ Get video ID """
        if coub_handler_enabled and "/view/" in url:
            video_id = url.split("/view/")[1]

            """ Remove any query strings """
            if "?" in video_id:
                video_id = video_id.split("?")[0]

            api_url = "http://coub.com/api/v2/coubs/%s" % video_id
            agent = self.get_user_agent()
            headers = {
                "User-Agent": agent
            }

            request = requests.get(api_url, headers=headers)

            ok = request.status_code == requests.codes.ok

            if ok:
                response = json.loads(request.text)

                if response:
                    video = response
                    coub_template = Template(self.registryValue("coubTemplate"))

                    video["likes_count"] = "{:,}".format(int(video["likes_count"]))
                    video["recoubs_count"] = "{:,}".format(int(video["recoubs_count"]))
                    video["views_count"] = "{:,}".format(int(video["views_count"]))

                    title = coub_template.render(video)
            else:
                log.error("SpiffyTitles: coub handler returned %s: %s" %
                          (request.status_code, request.text[:200]))

        if title is None:
            if coub_handler_enabled:
                log.debug("SpiffyTitles: %s does not appear to be a video link!" % url)

            return self.handler_default(url, channel)
        else:
            return title

    def add_imgur_handlers(self):
        # Images mostly
        self.handlers["i.imgur.com"] = self.handler_imgur_image

        # Albums, galleries, etc
        self.handlers["imgur.com"] = self.handler_imgur

    def initialize_imgur_client(self, channel):
        """
        Check if imgur client id or secret are set, and if so initialize
        imgur API client
        """
        if self.imgur_client is None:
            imgur_client_id = self.registryValue("imgurClientID")
            imgur_client_secret = self.registryValue("imgurClientSecret")
            imgur_handler_enabled = self.registryValue("imgurHandlerEnabled", channel=channel)

            if imgur_handler_enabled and imgur_client_id and imgur_client_secret:
                log.debug("SpiffyTitles: enabling imgur handler")

                # Initialize API client
                try:
                    from imgurpython import ImgurClient
                    from imgurpython.helpers.error import ImgurClientError

                    try:
                        self.imgur_client = ImgurClient(imgur_client_id, imgur_client_secret)
                    except ImgurClientError as e:
                        log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))
                except ImportError as e:
                    log.error("SpiffyTitles ImportError: %s" % str(e))
            else:
                log.debug("SpiffyTitles: imgur handler disabled or empty client id/secret")

    def doPrivmsg(self, irc, msg):
        """
        Observe each channel message and look for links
        """
        channel = msg.args[0]
        ignore_actions = self.registryValue("ignoreActionLinks", channel=msg.args[0])
        is_channel = irc.isChannel(channel)
        is_ctcp = ircmsgs.isCtcp(msg)
        message = msg.args[1]
        title = None
        bot_nick = irc.nick
        origin_nick = msg.nick
        is_message_from_self = origin_nick.lower() == bot_nick.lower()
        requires_capability = len(str(self.registryValue("requireCapability",
                                                         channel=msg.args[0]))) > 0

        if is_message_from_self:
            return

        """
        Check if we require a capability to acknowledge this link
        """
        if requires_capability:
            user_has_capability = self.user_has_capability(msg)

            if not user_has_capability:
                return

        """
        Configuration option determines whether we should
        ignore links that appear within an action
        """
        if is_ctcp and ignore_actions:
            return

        if is_channel:
            channel_is_allowed = self.is_channel_allowed(channel)
            url = self.get_url_from_message(message)
            ignore_match = self.message_matches_ignore_pattern(message)

            if ignore_match:
                log.debug("SpiffyTitles: ignoring message due to linkMessagePattern match")
                return

            if url:
                # Check if channel is allowed based on white/black list restrictions
                if not channel_is_allowed:
                    log.debug("SpiffyTitles: not responding to link in %s due to black/white list \
                               restrictions" % (channel))
                    return

                info = urlparse(url)
                domain = info.netloc
                is_ignored = self.is_ignored_domain(domain, channel)

                if is_ignored:
                    log.debug("SpiffyTitles: URL ignored due to domain blacklist match: %s" % url)
                    return

                is_whitelisted_domain = self.is_whitelisted_domain(domain, channel)
                whitelist_pattern = self.registryValue("whitelistDomainPattern", channel=channel)
                if whitelist_pattern and not is_whitelisted_domain:
                    log.debug("SpiffyTitles: URL ignored due to domain whitelist mismatch: %s" %
                              url)
                    return

                title = self.get_title_by_url(url, channel)

                if title is not None and title:
                    ignore_match = self.title_matches_ignore_pattern(title, channel)

                    if ignore_match:
                        return
                    else:
                        irc.queueMsg(ircmsgs.privmsg(channel, title))
                else:
                    if self.default_handler_enabled:
                        log.debug("SpiffyTitles: could not get a title for %s" % (url))
                    else:
                        log.debug("SpiffyTitles: could not get a title for %s but default \
                                   handler is disabled" % (url))

    def get_title_by_url(self, url, channel):
        """
        Retrieves the title of a website based on the URL provided
        """
        info = urlparse(url)
        domain = info.netloc
        title = None

        """
        Check if we have this link cached according to the cache lifetime. If so, serve
        link from the cache instead of calling handlers.
        """
        cached_link = self.get_link_from_cache(url)

        if cached_link is not None:
            title = cached_link["title"]
        else:
            if domain in self.handlers:
                handler = self.handlers[domain]
                title = handler(url, info, channel)
            else:
                base_domain = self.get_base_domain('http://' + domain)
                if base_domain in self.handlers:
                    handler = self.handlers[base_domain]
                    title = handler(url, info, channel)
                else:
                    if self.default_handler_enabled:
                        title = self.handler_default(url, channel)

        if title is not None:
            title = self.get_formatted_title(title, channel)

            # Update link cache
            log.debug("SpiffyTitles: caching %s" % (url))
            now = datetime.datetime.now()
            self.link_cache.append({
                "url": url,
                "timestamp": now,
                "title": title
            })

        return title

    def t(self, irc, msg, args, query):
        """
        Retrieves title for a URL on demand
        """
        message = msg.args[1]
        channel = msg.args[0]
        url = self.get_url_from_message(message)
        title = None
        error_message = self.registryValue("onDemandTitleError", channel=channel)

        try:
            if url:
                title = self.get_title_by_url(query, channel)
        except:
            pass

        if title is not None and title:
            irc.queueMsg(ircmsgs.privmsg(channel, title))
        else:
            irc.queueMsg(ircmsgs.privmsg(channel, error_message))

    t = wrap(t, ['text'])

    def get_link_from_cache(self, url):
        """
        Looks for a URL in the link cache and returns info about if it's not stale
        according to the configured cache lifetime, or None.

        If linkCacheLifetimeInSeconds is 0, then cache is disabled and we can
        immediately return
        """
        cache_lifetime_in_seconds = int(self.registryValue("linkCacheLifetimeInSeconds"))

        if cache_lifetime_in_seconds == 0:
            return

        # No cache yet
        if len(self.link_cache) == 0:
            return

        cached_link = None
        now = datetime.datetime.now()
        stale = False
        seconds = 0

        for link in self.link_cache:
            if link["url"] == url:
                cached_link = link
                break

        # Found link, check timestamp
        if cached_link is not None:
            seconds = (now - cached_link["timestamp"]).total_seconds()
            stale = seconds >= cache_lifetime_in_seconds

        if stale:
            log.debug("SpiffyTitles: %s was sent %s seconds ago" % (url, seconds))
        else:
            log.debug("SpiffyTitles: serving link from cache: %s" % (url))
            return cached_link

    def add_imdb_handlers(self):
        """
        Enables meta info about IMDB links through the OMDB API
        """
        self.handlers["imdb.com"] = self.handler_imdb

    def add_youtube_handlers(self):
        """
        Adds handlers for Youtube videos. The handler is matched based on the
        domain used in the URL.
        """
        self.handlers["youtube.com"] = self.handler_youtube
        self.handlers["youtu.be"] = self.handler_youtube

    def is_channel_allowed(self, channel):
        """
        Checks channel whitelist and blacklist to determine if the current
        channel is allowed to display titles.
        """
        channel = channel.lower()
        is_allowed = False
        white_list = self.filter_empty(self.registryValue("channelWhitelist"))
        black_list = self.filter_empty(self.registryValue("channelBlacklist"))
        white_list_empty = len(white_list) == 0
        black_list_empty = len(black_list) == 0

        # Most basic case, which is that both white and blacklist are empty. Any channel is allowed.
        if white_list_empty and black_list_empty:
            is_allowed = True

        # If there is a white list, blacklist is ignored.
        if white_list:
            is_allowed = channel in white_list

        # Finally, check blacklist
        if not white_list and black_list:
            is_allowed = channel not in black_list

        return is_allowed

    def filter_empty(self, input):
        """
        Remove all empty strings from a list
        """
        return set([channel for channel in input if len(channel.strip())])

    def is_ignored_domain(self, domain, channel):
        """
        Checks domain against a regular expression
        """
        pattern = self.registryValue("ignoredDomainPattern", channel=channel)

        if pattern:
            log.debug("SpiffyTitles: matching %s against %s" % (domain, str(pattern)))

            try:
                pattern_search_result = re.search(pattern, domain)

                if pattern_search_result is not None:
                    match = pattern_search_result.group()

                    return match
            except re.Error:
                log.error("SpiffyTitles: invalid regular expression: %s" % (pattern))

    def is_whitelisted_domain(self, domain, channel):
        """
        Checks domain against a regular expression
        """
        pattern = self.registryValue("whitelistDomainPattern", channel=channel)

        if pattern:
            log.debug("SpiffyTitles: matching %s against %s" % (domain, str(pattern)))

            try:
                pattern_search_result = re.search(pattern, domain)

                if pattern_search_result is not None:
                    match = pattern_search_result.group()

                    return match
            except re.Error:
                log.error("SpiffyTitles: invalid regular expression: %s" % (pattern))

    def get_video_id_from_url(self, url, info):
        """
        Get YouTube video ID from URL
        """
        try:
            path = info.path
            domain = info.netloc
            video_id = ""

            if domain == "youtu.be":
                video_id = path.split("/")[1]
            else:
                parsed = cgi.parse_qsl(info.query)
                params = dict(parsed)

                if "v" in params:
                    video_id = params["v"]

            if video_id:
                return video_id
            else:
                log.error("SpiffyTitles: error getting video id from %s" % (url))

        except IndexError as e:
            log.error("SpiffyTitles: error getting video id from %s (%s)" % (url, str(e)))

    def handler_youtube(self, url, domain, channel):
        """
        Uses the Youtube API to provide additional meta data about
        Youtube Video links posted.
        """
        youtube_handler_enabled = self.registryValue("youtubeHandlerEnabled", channel=channel)
        developer_key = self.registryValue("youtubeDeveloperKey")

        if not youtube_handler_enabled:
            return None

        if not developer_key:
            log.info("SpiffyTitles: no Youtube developer key set! Check the documentation \
                      for instructions.")
            return None

        log.debug("SpiffyTitles: calling Youtube handler for %s" % (url))
        video_id = self.get_video_id_from_url(url, domain)
        yt_template = Template(self.registryValue("youtubeTitleTemplate", channel=channel))
        title = ""

        if video_id:
            options = {
                "part": "snippet,statistics,contentDetails",
                "maxResults": 1,
                "key": developer_key,
                "id": video_id
            }
            encoded_options = urlencode(options)
            api_url = "https://www.googleapis.com/youtube/v3/videos?%s" % (encoded_options)
            agent = self.get_user_agent()
            headers = {
                "User-Agent": agent
            }

            log.debug("SpiffyTitles: requesting %s" % (api_url))

            request = requests.get(api_url, headers=headers)
            ok = request.status_code == requests.codes.ok

            if ok:
                response = json.loads(request.text)

                if response:
                    try:
                        if response["pageInfo"]["totalResults"] > 0:
                            items = response["items"]
                            video = items[0]
                            snippet = video["snippet"]
                            title = snippet["title"]
                            statistics = video["statistics"]
                            view_count = 0
                            like_count = 0
                            dislike_count = 0
                            comment_count = 0
                            favorite_count = 0

                            if "viewCount" in statistics:
                                view_count = "{:,}".format(int(statistics["viewCount"]))

                            if "likeCount" in statistics:
                                like_count = "{:,}".format(int(statistics["likeCount"]))

                            if "dislikeCount" in statistics:
                                dislike_count = "{:,}".format(int(statistics["dislikeCount"]))

                            if "favoriteCount" in statistics:
                                favorite_count = "{:,}".format(int(statistics["favoriteCount"]))

                            if "commentCount" in statistics:
                                comment_count = "{:,}".format(int(statistics["commentCount"]))

                            channel_title = snippet["channelTitle"]
                            video_duration = video["contentDetails"]["duration"]
                            duration_seconds = self.get_total_seconds_from_duration(video_duration)

                            """
                            #23 - If duration is zero, then it"s a LIVE video
                            """
                            if duration_seconds > 0:
                                duration = self.get_duration_from_seconds(duration_seconds)
                            else:
                                duration = "LIVE"

                            timestamp = self.get_timestamp_from_youtube_url(url)
                            yt_logo = self.get_youtube_logo()

                            compiled_template = yt_template.render({
                                "title": title,
                                "duration": duration,
                                "timestamp": timestamp,
                                "view_count": view_count,
                                "like_count": like_count,
                                "dislike_count": dislike_count,
                                "comment_count": comment_count,
                                "favorite_count": favorite_count,
                                "channel_title": channel_title,
                                "yt_logo": yt_logo
                            })

                            title = compiled_template
                        else:
                            log.debug("SpiffyTitles: video appears to be private; no results!")

                    except IndexError as e:
                        log.error("SpiffyTitles: IndexError parsing Youtube API JSON response: %s" %
                                  (str(e)))
                else:
                    log.error("SpiffyTitles: Error parsing Youtube API JSON response")
            else:
                log.error("SpiffyTitles: Youtube API HTTP %s: %s" %
                          (request.status_code, request.text))

        # If we found a title, return that. otherwise, use default handler
        if title:
            return title
        else:
            log.debug("SpiffyTitles: falling back to default handler")

            return self.handler_default(url, channel)

    def get_duration_from_seconds(self, duration_seconds):
        m, s = divmod(duration_seconds, 60)
        h, m = divmod(m, 60)

        duration = "%02d:%02d" % (m, s)

        """ Only include hour if the video is at least 1 hour long """
        if h > 0:
            duration = "%02d:%s" % (h, duration)

        return duration

    def get_youtube_logo(self):
        colored_letters = [
            "%s" % ircutils.mircColor("You", fg="red", bg="white"),
            "%s" % ircutils.mircColor("Tube", fg="white", bg="red")
        ]

        yt_logo = "".join(colored_letters)

        return yt_logo

    def get_total_seconds_from_duration(self, input):
        """
        Duration comes in a format like this: PT4M41S which translates to
        4 minutes and 41 seconds. This method returns the total seconds
        so that the duration can be parsed as usual.
        """
        regex = re.compile("""
                   (?P<sign>    -?) P
                (?:(?P<years>  \d+) Y)?
                (?:(?P<months> \d+) M)?
                (?:(?P<days>   \d+) D)?
            (?:                     T
                (?:(?P<hours>  \d+) H)?
                (?:(?P<minutes>\d+) M)?
                (?:(?P<seconds>\d+) S)?
            )?
            """, re.VERBOSE)
        duration = regex.match(input).groupdict(0)

        delta = timedelta(hours=int(duration['hours']),
                          minutes=int(duration['minutes']),
                          seconds=int(duration['seconds']))

        return delta.total_seconds()

    def get_timestamp_from_youtube_url(self, url):
        """
        Get YouTube timestamp
        """
        pattern = r"[?&]t=([^&]+)"
        match = re.search(pattern, url)

        if match:
            timestamp = match.group(1).upper()
            try:
                seconds = float(timestamp)
            except ValueError:
                seconds = self.get_total_seconds_from_duration("PT" + timestamp)

            if seconds > 0:
                return self.get_duration_from_seconds(seconds)
        else:
            return ""

    def handler_default(self, url, channel):
        """
        Default handler for websites
        """
        default_handler_enabled = self.registryValue("defaultHandlerEnabled", channel=channel)

        if default_handler_enabled:
            log.debug("SpiffyTitles: calling default handler for %s" % (url))
            default_template = Template(self.registryValue("defaultTitleTemplate", channel=channel))
            (html, is_redirect) = self.get_source_by_url(url)

            if html is not None and html:
                title = self.get_title_from_html(html)

                if title is not None:
                    title_template = default_template.render(title=title, redirect=is_redirect)

                    return title_template
        else:
            log.debug("SpiffyTitles: default handler fired but doing nothing because disabled")

    def handler_imdb(self, url, info, channel):
        """
        Handles imdb.com links, querying the OMDB API for additional info

        Typical IMDB URL: http://www.imdb.com/title/tt2467372/
        """
        headers = self.get_headers()
        result = None

        if not self.registryValue("imdbHandlerEnabled", channel=channel):
            log.debug("SpiffyTitles: IMDB handler disabled. Falling back to default handler.")

            return self.handler_default(url, channel)

        # Don't care about query strings
        if "?" in url:
            url = url.split("?")[0]

        # We can only accommodate a specific format of URL here
        if "/title/" in url:
            imdb_id = url.split("/title/")[1].rstrip("/")
            omdb_url = "http://www.omdbapi.com/?i=%s&plot=short&r=json&tomatoes=true" % (imdb_id)

            try:
                request = requests.get(omdb_url, timeout=10, headers=headers)

                if request.status_code == requests.codes.ok:
                    response = json.loads(request.text)
                    result = None
                    imdb_template = Template(self.registryValue("imdbTemplate"))
                    not_found = "Error" in response
                    unknown_error = response["Response"] != "True"

                    if not_found or unknown_error:
                        log.debug("SpiffyTitles: OMDB error for %s" % (omdb_url))
                    else:
                        result = imdb_template.render(response)
                else:
                    log.error("SpiffyTitles OMDB API %s - %s" % (request.status_code, request.text))

            except requests.exceptions.Timeout as e:
                log.error("SpiffyTitles imdb Timeout: %s" % (str(e)))
            except requests.exceptions.ConnectionError as e:
                log.error("SpiffyTitles imdb ConnectionError: %s" % (str(e)))
            except requests.exceptions.HTTPError as e:
                log.error("SpiffyTitles imdb HTTPError: %s" % (str(e)))

        if result is not None:
            return result
        else:
            log.debug("SpiffyTitles: IMDB handler failed. calling default handler")

            return self.handler_default(url, channel)

    def handler_wikipedia(self, url, domain, channel):
        """
        Queries wikipedia API for article extracts.
        """
        wikipedia_handler_enabled = self.registryValue("wikipedia.enabled", channel=channel)

        if not wikipedia_handler_enabled:
            return self.handler_default(url, channel)

        self.log.debug("SpiffyTitles: calling Wikipedia handler for %s" % (url))

        pattern = r"/(?:w(?:iki))/(?P<page>[^/]+)$"
        info = urlparse(url)
        match = re.search(pattern, info.path)

        if not match:
            self.log.debug("SpiffyTitles: no title found.")
            return self.handler_default(url, channel)
        elif info.fragment and self.registryValue("wikipedia.ignoreSectionLinks", channel=channel):
            self.log.debug("SpiffyTitles: ignoring section link.")
            return self.handler_default(url, channel)
        else:
            page_title = match.groupdict()['page']

        default_api_params = {
            "format": "json",
            "action": "query",
            "prop": "extracts",
            "exsentences": "2",
            "exlimit": "1",
            "exintro": "",
            "explaintext": ""
        }

        wiki_api_params = self.registryValue("wikipedia.apiParams", channel=channel)
        extra_params = dict(parse_qsl('&'.join(wiki_api_params)))
        title_param = {
            self.registryValue("wikipedia.titleParam", channel=channel): page_title
        }

        # merge dicts
        api_params = default_api_params.copy()
        api_params.update(extra_params)
        api_params.update(title_param)
        param_string = "&".join("%s=%s" % (key, val) for (key, val) in api_params.iteritems())
        api_url = "https://%s/w/api.php?%s" % (info.netloc, param_string)

        agent = self.get_user_agent()
        headers = {
            "User-Agent": agent
        }
        extract = ""

        self.log.debug("SpiffyTitles: requesting %s" % (api_url))

        request = requests.get(api_url, headers=headers)
        ok = request.status_code == requests.codes.ok

        if ok:
            response = json.loads(request.text)

            if response:
                try:
                    extract = response['query']['pages'].values()[0]['extract']
                except KeyError as e:
                    self.log.error("SpiffyTitles: KeyError parsing Wikipedia API JSON response: \
                                    %s" % (str(e)))
            else:
                self.log.error("SpiffyTitles: Error parsing Wikipedia API JSON response")
        else:
            self.log.error("SpiffyTitles: Wikipedia API HTTP %s: %s" %
                           (request.status_code, request.text))

        if extract:
            if (self.registryValue("wikipedia.removeParentheses")):
                extract = re.sub(r' ?\([^)]*\)', '', extract)
            max_chars = self.registryValue("wikipedia.maxChars", channel=channel)
            if len(extract) > max_chars:
                extract = extract[:max_chars - 3].rsplit(' ', 1)[0].rstrip(',.') + '...'
            extract_template = self.registryValue("wikipedia.extractTemplate", channel=channel)
            wikipedia_template = Template(extract_template)
            return wikipedia_template.render({"extract": extract})
        else:
            self.log.debug("SpiffyTitles: falling back to default handler")

            return self.handler_default(url, channel)

    def handler_reddit(self, url, domain, channel):
        """
        Queries wikipedia API for article extracts.
        """
        reddit_handler_enabled = self.registryValue("reddit.enabled", channel=channel)
        if not reddit_handler_enabled:
            return self.handler_default(url, channel)

        self.log.debug("SpiffyTitles: calling reddit handler for %s" % (url))

        patterns = {
            "thread": {
                "pattern": r"^/r/(?P<subreddit>[^/]+)/comments/(?P<thread>[^/]+)(?:/[^/]+/?)?$",
                "url": "https://www.reddit.com/r/{subreddit}/comments/{thread}.json"
            },
            "comment": {
                "pattern":
                    r"^/r/(?P<subreddit>[^/]+)/comments/(?P<thread>[^/]+)/[^/]+/(?P<comment>\w+)$",
                "url": "https://www.reddit.com/r/{subreddit}/comments/{thread}/x/{comment}.json"
            },
            "user": {
                "pattern": r"^/u(?:ser)?/(?P<user>[^/]+)/?$",
                "url": "https://www.reddit.com/user/{user}/about.json"
            }
        }

        info = urlparse(url)
        for name in patterns:
            match = re.search(patterns[name]['pattern'], info.path)
            if match:
                link_type = name
                link_info = match.groupdict()
                data_url = patterns[name]['url'].format(**link_info)
                break

        if not match:
            self.log.debug("SpiffyTitles: no title found.")
            return self.handler_default(url, channel)

        agent = self.get_user_agent()
        headers = {
            "User-Agent": agent
        }

        self.log.debug("SpiffyTitles: requesting %s" % (data_url))

        request = requests.get(data_url, headers=headers)
        ok = request.status_code == requests.codes.ok
        data = {}
        extract = ''

        if ok:
            response = json.loads(request.text)

            if response:
                try:
                    if link_type == "thread":
                        data = response[0]['data']['children'][0]['data']

                    if link_type == "comment":
                        data = response[1]['data']['children'][0]['data']
                        data['title'] = response[0]['data']['children'][0]['data']['title']

                    if link_type == "user":
                        data = response['data']
                except KeyError as e:
                    self.log.error("SpiffyTitles: KeyError parsing Reddit JSON response: %s" %
                                   (str(e)))
            else:
                self.log.error("SpiffyTitles: Error parsing Reddit JSON response")
        else:
            self.log.error("SpiffyTitles: Reddit HTTP %s: %s" % (request.status_code, request.text))

        if data:
            today = datetime.datetime.now(pytz.UTC).date()
            created = datetime.datetime.fromtimestamp(data['created_utc'], pytz.UTC).date()
            age_days = (today - created).days
            if age_days == 0:
                age = "today"
            elif age_days == 1:
                age = "yesterday"
            else:
                age = '{}d'.format(age_days % 365)
                if age_days > 365:
                    age = '{}y, '.format(age_days / 365) + age
                age = age + " ago"
            if link_type == "thread":
                link_type = "linkThread"
                if data['is_self']:
                    link_type = "textThread"
                    data['url'] = ""
                    extract = data.get('selftext', '')
            if link_type == "comment":
                extract = data.get('body', '')
            link_type_template = self.registryValue("reddit." + link_type + "Template",
                                                    channel=channel)
            reddit_template = Template(link_type_template)
            template_vars = {
                "id": data.get('id', ''),
                "user": data.get('name', ''),
                "gold": (data.get('is_gold', False) is True),
                "mod": (data.get('is_mod', False) is True),
                "author": data.get('author', ''),
                "subreddit": data.get('subreddit', ''),
                "url": data.get('url', ''),
                "title": data.get('title', ''),
                "domain": data.get('domain', ''),
                "score": data.get('score', 0),
                "percent": '{}%'.format(int(data.get('upvote_ratio', 0) * 100)),
                "comments": '{:,}'.format(data.get('num_comments', 0)),
                "created": created.strftime('%Y-%m-%d'),
                "age": age,
                "link_karma": '{:,}'.format(data.get('link_karma', 0)),
                "comment_karma": '{:,}'.format(data.get('comment_karma', 0)),
                "extract": "%%extract%%"
            }
            reply = reddit_template.render(template_vars)
            if extract:
                max_chars = self.registryValue("reddit.maxChars", channel=channel)
                max_extract_chars = max_chars + len('%%extract%%') - len(reply)
                if len(extract) > max_extract_chars:
                    extract = extract[:max_extract_chars - 3].rsplit(' ', 1)[0].rstrip(',.') + '...'
            template_vars['extract'] = extract
            reply = reddit_template.render(template_vars)
            return reply
        else:
            self.log.debug("SpiffyTitles: falling back to default handler")
            return self.handler_default(url, channel)

    def is_valid_imgur_id(self, input):
        """
        Tests if input matches the typical imgur id, which seems to be alphanumeric. \
        Images, galleries, and albums all share their format in their identifier.
        """
        match = re.match(r"[a-z0-9]+", input, re.IGNORECASE)

        return match is not None

    def handler_imgur(self, url, info, channel):
        """
        Queries imgur API for additional information about imgur links.

        This handler is for any imgur.com domain.
        """
        self.initialize_imgur_client(channel)

        is_album = info.path.startswith("/a/")
        result = None

        if is_album:
            result = self.handler_imgur_album(url, info, channel)
        else:
            result = self.handler_default(url, channel)

        return result

    def handler_imgur_album(self, url, info, channel):
        """
        Handles retrieving information about albums from the imgur API.

        imgur provides the following information about albums: https://api.imgur.com/models/album
        """
        from imgurpython.helpers.error import ImgurClientRateLimitError
        from imgurpython.helpers.error import ImgurClientError
        self.initialize_imgur_client(channel)

        if self.imgur_client:
            album_id = info.path.split("/a/")[1]

            """ If there is a query string appended, remove it """
            if "?" in album_id:
                album_id = album_id.split("?")[0]

            if self.is_valid_imgur_id(album_id):
                log.debug("SpiffyTitles: found imgur album id %s" % (album_id))

                try:
                    album = self.imgur_client.get_album(album_id)

                    if album:
                        album_template = self.registryValue("imgurAlbumTemplate", channel=channel)
                        imgur_album_template = Template(album_template)
                        compiled_template = imgur_album_template.render({
                            "title": album.title,
                            "section": album.section,
                            "view_count": "{:,}".format(album.views),
                            "image_count": "{:,}".format(album.images_count),
                            "nsfw": album.nsfw
                        })

                        return compiled_template
                    else:
                        log.error("SpiffyTitles: imgur album API returned unexpected results!")

                except ImgurClientRateLimitError as e:
                    log.error("SpiffyTitles: imgur rate limit error: %s" % (e.error_message))
                except ImgurClientError as e:
                    log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))
            else:
                log.debug("SpiffyTitles: unable to determine album id for %s" % (url))
        else:
            return self.handler_default(url, channel)

    def handler_imgur_image(self, url, info, channel):
        """
        Handles retrieving information about images from the imgur API.

        Used for both direct images and imgur.com/some_image_id_here type links, as
        they're both single images.
        """
        self.initialize_imgur_client(channel)

        from imgurpython.helpers.error import ImgurClientRateLimitError
        from imgurpython.helpers.error import ImgurClientError
        title = None

        if self.imgur_client:
            """
            If there is a period in the path, it's a direct link to an image. If not, then
            it's a imgur.com/some_image_id_here type link
            """
            if "." in info.path:
                path = info.path.lstrip("/")
                image_id = path.split(".")[0]
            else:
                image_id = info.path.lstrip("/")

            if self.is_valid_imgur_id(image_id):
                log.debug("SpiffyTitles: found image id %s" % (image_id))

                try:
                    image = self.imgur_client.get_image(image_id)

                    if image:
                        channel_template = self.registryValue("imgurTemplate", channel=channel)
                        imgur_template = Template(channel_template)
                        readable_file_size = self.get_readable_file_size(image.size)
                        compiled_template = imgur_template.render({
                            "title": image.title,
                            "type": image.type,
                            "nsfw": image.nsfw,
                            "width": image.width,
                            "height": image.height,
                            "view_count": "{:,}".format(image.views),
                            "file_size": readable_file_size,
                            "section": image.section
                        })

                        title = compiled_template
                    else:
                        log.error("SpiffyTitles: imgur API returned unexpected results!")
                except ImgurClientRateLimitError as e:
                    log.error("SpiffyTitles: imgur rate limit error: %s" % (e.error_message))
                except ImgurClientError as e:
                    log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))
            else:
                log.error("SpiffyTitles: error retrieving image id for %s" % (url))

        if title is not None:
            return title
        else:
            return self.handler_default(url, channel)

    def get_readable_file_size(self, num, suffix="B"):
        """
        Returns human readable file size
        """
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, "Yi", suffix)

    def get_formatted_title(self, title, channel):
        """
        Remove cruft from title and apply bold if applicable
        """
        use_bold = self.registryValue("useBold", channel=channel)

        # Replace anywhere in string
        title = title.replace("\n", " ")
        title = title.replace("\t", " ")
        title = re.sub(" +", " ", title)

        if use_bold:
            title = ircutils.bold(title)

        title = title.strip()

        return title

    def get_title_from_html(self, html):
        """
        Retrieves value of <title> tag from HTML
        """
        soup = BeautifulSoup(html, "lxml")

        if soup is not None:
            """
            Some websites have more than one title tag, so get all of them
            and take the last value.
            """
            head = soup.find("head")
            titles = head.find_all("title")

            if titles is not None and len(titles):
                for t in titles[::-1]:
                    title = t.get_text().strip()
                    if len(title):
                        return title

    @timeout_decorator.timeout(wall_clock_timeout)
    def get_source_by_url(self, url, retries=1):
        """
        Get the HTML of a website based on a URL
        """
        max_retries = self.registryValue("maxRetries")

        if retries is None:
            retries = 1

        if retries >= max_retries:
            log.debug("SpiffyTitles: hit maximum retries for %s" % url)

            return (None, False)

        log.debug("SpiffyTitles: attempt #%s for %s" % (retries, url))

        try:
            headers = self.get_headers()

            log.debug("SpiffyTitles: requesting %s" % (url))

            request = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

            is_redirect = False
            if request.history:
                # check the top two domain levels
                link_domain = self.get_base_domain(request.history[0].url)
                real_domain = self.get_base_domain(request.url)
                if link_domain != real_domain:
                    is_redirect = True

                for redir in request.history:
                    log.debug("SpiffyTitles: Redirect %s from %s" % (redir.status_code, redir.url))
                log.debug("SpiffyTitles: Final url %s" % (request.url))

            if request.status_code == requests.codes.ok:
                # Check the content type which comes in the format: "text/html; charset=UTF-8"
                content_type = request.headers.get("content-type").split(";")[0].strip()
                acceptable_types = self.registryValue("mimeTypes")

                log.debug("SpiffyTitles: content type %s" % (content_type))

                if content_type in acceptable_types:
                    text = request.content

                    if text:
                        return (text, is_redirect)
                    else:
                        log.debug("SpiffyTitles: empty content from %s" % (url))

                else:
                    log.debug("SpiffyTitles: unacceptable mime type %s for url %s" %
                              (content_type, url))
            else:
                log.error("SpiffyTitles HTTP response code %s - %s" % (request.status_code,
                                                                       request.content))

        except timeout_decorator.TimeoutError:
            log.error("SpiffyTitles: wall timeout!")

            self.get_source_by_url(url, retries + 1)
        except requests.exceptions.MissingSchema as e:
            url_wschema = "http://%s" % (url)
            log.error("SpiffyTitles missing schema. Retrying with %s" % (url_wschema))
            return self.get_source_by_url(url_wschema)
        except requests.exceptions.Timeout as e:
            log.error("SpiffyTitles Timeout: %s" % (str(e)))

            self.get_source_by_url(url, retries + 1)
        except requests.exceptions.ConnectionError as e:
            log.error("SpiffyTitles ConnectionError: %s" % (str(e)))

            self.get_source_by_url(url, retries + 1)
        except requests.exceptions.HTTPError as e:
            log.error("SpiffyTitles HTTPError: %s" % (str(e)))
        except requests.exceptions.InvalidURL as e:
            log.error("SpiffyTitles InvalidURL: %s" % (str(e)))

        return (None, False)

    def get_base_domain(self, url):
        """
        Returns the FQDN comprising the top two domain levels
        """
        return '.'.join(urlparse(url).netloc.rsplit('.', 2)[-2:])

    def get_headers(self):
        agent = self.get_user_agent()
        self.accept_language = self.registryValue("language")

        headers = {
            "User-Agent": agent,
            "Accept-Language": ";".join((self.accept_language, "q=1.0"))
        }

        return headers

    def get_user_agent(self):
        """
        Returns a random user agent from the ones available
        """
        agents = self.registryValue("userAgents")

        return random.choice(agents)

    def message_matches_ignore_pattern(self, input):
        """
        Checks message against linkMessageIgnorePattern to determine
        whether the message should be ignored.
        """
        match = False
        pattern = self.registryValue("linkMessageIgnorePattern")

        if pattern:
            match = re.search(pattern, input)

        return match

    def title_matches_ignore_pattern(self, input, channel):
        """
        Checks message against ignoredTitlePattern to determine
        whether the title should be ignored.
        """
        match = False
        pattern = self.registryValue("ignoredTitlePattern", channel=channel)

        if pattern:
            match = re.search(pattern, input)

            if match:
                log.debug("SpiffyTitles: title %s matches ignoredTitlePattern for %s" %
                          (input, channel))

        return match

    def get_url_from_message(self, input):
        """
        Find the first string that looks like a URL from the message
        """
        url_re = self.registryValue("urlRegularExpression")
        match = re.search(url_re, input)

        if match:
            raw_url = match.group(0).strip()
            url = self.remove_control_characters(unicode(raw_url))

            return url

    def remove_control_characters(self, s):
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    def user_has_capability(self, msg):
        channel = msg.args[0]
        mask = msg.prefix
        required_capability = self.registryValue("requireCapability", channel=channel)
        cap = ircdb.makeChannelCapability(channel, required_capability)
        has_cap = ircdb.checkCapability(mask, cap, ignoreDefaultAllow=True)

        if has_cap:
            log.debug("SpiffyTitles: %s has required capability '%s'" % (mask, required_capability))
        else:
            log.debug("SpiffyTitles: %s does NOT have required capability '%s'" %
                      (mask, required_capability))

        return has_cap

Class = SpiffyTitles
