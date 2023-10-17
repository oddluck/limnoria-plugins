###
# Copyright (c) 2015, butterscotchstallion
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
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
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.utils as utils
import supybot.ircdb as ircdb
import supybot.log as log
import supybot.conf as conf
import re, sys, random, time, json, unicodedata, datetime
from urllib.parse import urlparse, parse_qsl
from bs4 import BeautifulSoup
from jinja2 import Template
import requests

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

    def __init__(self, irc):
        self.__parent = super(SpiffyTitles, self)
        self.__parent.__init__(irc)
        self.link_cache = {}
        self.handlers = {}
        self.timeout = self.registryValue("timeout")
        self.add_handlers()
        self.proxies = {}
        self.proxies["http"] = None
        self.proxies["https"] = None
        proxy = str(conf.supybot.protocols.http.proxy)
        if proxy:
            match = re.match(r"https?:\/\/", proxy, re.IGNORECASE)
            if not match:
                proxy = "http://{0}".format(proxy)
            self.proxies["http"] = proxy
            self.proxies["https"] = proxy

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
        self.add_twitch_handlers()
        self.add_twitter_handlers()

    def add_twitter_handlers(self):
        self.handlers["twitter.com"] = self.handler_twitter
        self.handlers["www.twitter.com"] = self.handler_twitter
        self.handlers["x.com"] = self.handler_twitter
        self.handlers["www.x.com"] = self.handler_twitter

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

    def add_twitch_handlers(self):
        """
        Enables meta info about Twitch links through the Twitch API
        """
        self.handlers["twitch.tv"] = self.handler_twitch
        self.handlers["www.twitch.tv"] = self.handler_twitch
        self.handlers["go.twitch.tv"] = self.handler_twitch
        self.handlers["clips.twitch.tv"] = self.handler_twitch

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

    def add_imgur_handlers(self):
        # Images mostly
        self.handlers["i.imgur.com"] = self.handler_imgur_image
        # Albums, galleries, etc
        self.handlers["imgur.com"] = self.handler_imgur

    def doPrivmsg(self, irc, msg):
        """
        Observe each channel message and look for links
        """
        channel = msg.args[0]
        message = msg.args[1]
        title = None
        if not ircutils.isUserHostmask(msg.prefix):
            return
        if not irc.isChannel(channel):
            return
        if msg.nick.lower() == irc.nick.lower():
            return
        if callbacks.addressed(irc, msg) and self.registryValue(
            "ignoreAddressed", channel=channel
        ):
            return
        if ircdb.checkIgnored(msg.prefix, channel):
            return
        """
        Check if we require a capability to acknowledge this link
        """
        if self.registryValue("requireCapability", channel=channel):
            if not self.user_has_capability(msg):
                return
        """
        Configuration option determines whether we should
        ignore links that appear within an action
        """
        if self.registryValue("ignoreActionLinks", channel=channel) and (
            ircmsgs.isCtcp(msg) or ircmsgs.isAction(msg)
        ):
            return
        if self.message_matches_ignore_pattern(message, channel):
            log.debug(
                "SpiffyTitles: ignoring message due to ignoredMessagePattern match"
            )
            return
        if not self.is_channel_allowed(channel):
            log.debug(
                "SpiffyTitles: not responding to link in %s due to black/white "
                "list restrictions"
                % (channel)
            )
            return
        if self.registryValue("snarfMultipleUrls", channel=channel):
            urls = self.get_urls_from_message(message, channel)
        else:
            urls = self.get_urls_from_message(message, channel)[0:1]
        if not urls:
            return
        for url in urls:
            if url.strip():
                url = self.remove_control_characters(url)
                # Check if channel is allowed based on white/black list restrictions
                info = urlparse(url)
                domain = info.netloc
                is_ignored = self.is_ignored_domain(domain, channel)
                if is_ignored:
                    log.debug(
                        "SpiffyTitles: URL ignored due to domain blacklist match: %s"
                        % url
                    )
                    return
                is_whitelisted_domain = self.is_whitelisted_domain(domain, channel)
                whitelist_pattern = self.registryValue(
                    "whitelistDomainPattern", channel=channel
                )
                if whitelist_pattern and not is_whitelisted_domain:
                    log.debug(
                        "SpiffyTitles: URL ignored due to domain whitelist mismatch: %s"
                        % url
                    )
                    return
                title = self.get_title_by_url(url, channel, msg.nick)
                if title:
                    prefixed = self.registryValue("prefixNick", channel=channel)
                    ignore_match = self.title_matches_ignore_pattern(title, channel)
                    if ignore_match:
                        return
                    elif not is_ignored:
                        irc.reply(title, prefixNick=prefixed)
                else:
                    if self.registryValue("default.enabled", channel):
                        log.debug("SpiffyTitles: could not get a title for %s" % (url))
                    else:
                        log.debug(
                            "SpiffyTitles: could not get a title for %s but default    "
                            "                                handler is disabled"
                            % (url)
                        )

    def handler_default(self, url, channel):
        """
        Default handler for websites
        """
        if self.registryValue("default.enabled", channel):
            log.debug("SpiffyTitles: calling default handler for %s" % (url))
            default_template = Template(
                self.registryValue("default.template", channel=channel)
            )
            (title, is_redirect) = self.get_source_by_url(url, channel)
            if title:
                title_template = default_template.render(
                    title=title, redirect=is_redirect
                )
                return title_template
            else:
                return
        else:
            log.debug(
                "SpiffyTitles: default handler fired but doing nothing because disabled"
            )

    def get_title_by_url(self, url, channel, origin_nick=None):
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
        if self.registryValue("cacheGlobal"):
            channel = "global"
        cached_link = self.get_link_from_cache(url, channel)
        if cached_link:
            title = cached_link["title"]
        else:
            if domain in self.handlers:
                handler = self.handlers[domain]
                title = handler(url, info, channel)
            else:
                base_domain = self.get_base_domain("http://" + domain)
                if base_domain in self.handlers:
                    handler = self.handlers[base_domain]
                    title = handler(url, info, channel)
                else:
                    if self.registryValue("default.enabled", channel):
                        title = self.handler_default(url, channel)
        if title and not cached_link:
            title = self.get_formatted_title(title, channel)
            # Update link cache
            log.debug("SpiffyTitles: caching %s" % (url))
            now = datetime.datetime.now()
            if channel not in self.link_cache:
                self.link_cache[channel] = []
            self.link_cache[channel].append(
                {
                    "url": url,
                    "timestamp": now,
                    "title": title,
                    "from": origin_nick,
                    "channel": channel,
                }
            )
        elif title and cached_link:
            self.link_cache[channel].append(cached_link)
            log.debug("SpiffyTitles: serving link from cache: %s" % (url))
        return title

    def get_link_from_cache(self, url, channel):
        """
        Looks for a URL in the link cache and returns info about if it's not stale
        according to the configured cache lifetime, or None. If cacheLifetime is 0,
        then cache is disabled and we can immediately return
        """
        cache_lifetime_in_seconds = int(self.registryValue("cacheLifetime"))
        if cache_lifetime_in_seconds == 0:
            return
        # No cache yet
        if len(self.link_cache) == 0:
            return
        cached_link = None
        now = datetime.datetime.now()
        stale = False
        seconds = 0
        if channel in self.link_cache:
            for i in range(len(self.link_cache[channel])):
                if self.link_cache[channel][i]["url"] == url:
                    cached_link = self.link_cache[channel].pop(i)
                    break
        # Found link, check timestamp
        if cached_link:
            seconds = (now - cached_link["timestamp"]).total_seconds()
            if seconds >= cache_lifetime_in_seconds:
                stale = True
        if stale:
            log.debug("SpiffyTitles: %s was sent %s seconds ago" % (url, seconds))
        else:
            return cached_link

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
        # Most basic case: both white and blacklist are empty. Any channel is allowed.
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
                if pattern_search_result:
                    match = pattern_search_result.group()
                    return match
            except re.error:
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
                if pattern_search_result:
                    match = pattern_search_result.group()
                    return match
            except re.error:
                log.error("SpiffyTitles: invalid regular expression: %s" % (pattern))

    def get_formatted_title(self, title, channel):
        """
        Remove cruft from title and apply bold if applicable
        """
        use_bold = self.registryValue("useBold", channel=channel)
        # Replace anywhere in string
        title = re.sub(r"\s+", " ", title)
        if use_bold:
            title = ircutils.bold(title).strip()
        return title

    def get_title_from_html(self, html, channel):
        """
        Retrieves value of <title> tag from HTML
        """
        title = None
        soup = BeautifulSoup(html)
        if soup:
            try:
                title = soup.title.string.strip()
            except:
                title = self.registryValue("badLinkText", channel=channel)
        return title

    def get_source_by_url(self, url, channel, retries=1):
        """
        Get the HTML of a website based on a URL
        """
        max_retries = self.registryValue("maxRetries")
        if retries >= max_retries:
            log.debug("SpiffyTitles: hit maximum retries for %s" % url)
            return (None, False)
        log.debug("SpiffyTitles: attempt #%s for %s" % (retries, url))
        is_redirect = False
        try:
            headers = self.get_headers(channel)
            log.debug("SpiffyTitles: requesting %s" % (url))
            with requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
                proxies=self.proxies,
            ) as request:
                request.raise_for_status()
                if request.history:
                    # check the top two domain levels
                    link_domain = self.get_base_domain(request.history[0].url)
                    real_domain = self.get_base_domain(request.url)
                    if link_domain != real_domain:
                        is_redirect = True
                        for redir in request.history:
                            log.debug(
                                "SpiffyTitles: Redirect %s from %s"
                                % (redir.status_code, redir.url)
                            )
                        log.debug("SpiffyTitles: Final url %s" % (request.url))
                        info = urlparse(request.url)
                        domain = info.netloc
                        is_ignored = self.is_ignored_domain(domain, channel)
                        if is_ignored:
                            log.debug(
                                "SpiffyTitles: URL ignored due to domain blacklist"
                                " match: %s"
                                % url
                            )
                            return
                        whitelist_pattern = self.registryValue(
                            "whitelistDomainPattern", channel=channel
                        )
                        is_whitelisted_domain = self.is_whitelisted_domain(
                            domain, channel
                        )
                        if whitelist_pattern and not is_whitelisted_domain:
                            log.debug(
                                "SpiffyTitles: URL ignored due to domain whitelist"
                                " mismatch: %s"
                                % url
                            )
                            return
                        text = self.get_title_by_url(request.url, channel)
                        text = text.lstrip("\x02").lstrip("^").strip()
                        return (text, is_redirect)
                # Check the content type
                content_type = request.headers.get("content-type").split(";")[0].strip()
                acceptable_types = self.registryValue("default.mimeTypes")
                log.debug("SpiffyTitles: content type %s" % (content_type))
                if content_type in acceptable_types:
                    text = request.content
                    if text:
                        return (self.get_title_from_html(text, channel), is_redirect)
                    else:
                        log.debug("SpiffyTitles: empty content from %s" % (url))
                else:
                    log.debug(
                        "SpiffyTitles: unacceptable mime type %s for url %s"
                        % (content_type, url)
                    )
                    size = request.headers.get("content-length")
                    if size:
                        size = self.get_readable_file_size(int(size))
                    file_template = self.registryValue(
                        "default.fileTemplate", channel=channel
                    )
                    text = Template(file_template).render(
                        {"type": content_type, "size": size}
                    )
                    return (text, is_redirect)
        except requests.exceptions.MissingSchema as e:
            url_wschema = "http://%s" % (url)
            log.error("SpiffyTitles missing schema. Retrying with %s" % (url_wschema))
            info = urlparse(url_wschema)
            if self.is_ignored_domain(info.netloc, channel):
                return
            else:
                return self.get_source_by_url(url_wschema, channel)
        except requests.exceptions.Timeout as e:
            log.error("SpiffyTitles Timeout: %s" % (str(e)))
            self.get_source_by_url(url, channel, retries + 1)
        except requests.exceptions.ConnectionError as e:
            log.error("SpiffyTitles ConnectionError: %s" % (str(e)))
            self.get_source_by_url(url, channel, retries + 1)
        except requests.exceptions.HTTPError as e:
            log.error("SpiffyTitles HTTPError: %s" % (str(e)))
            text = self.registryValue("badLinkText", channel=channel)
            return (text, is_redirect)
        except requests.exceptions.InvalidURL as e:
            log.error("SpiffyTitles InvalidURL: %s" % (str(e)))
            text = self.registryValue("badLinkText", channel=channel)
            return (text, is_redirect)
        return (None, False)

    def get_base_domain(self, url):
        """
        Returns the FQDN comprising the top two domain levels
        """
        return ".".join(urlparse(url).netloc.rsplit(".", 2)[-2:])

    def get_headers(self, channel):
        agent = self.get_user_agent()
        language = self.registryValue("default.language", channel)
        headers = {
            "User-Agent": agent,
            "Accept-Language": "{0}".format(language),
        }
        return headers

    def get_user_agent(self):
        """
        Returns a random user agent from the ones available
        """
        agents = self.registryValue("default.userAgents")
        return random.choice(agents)

    def message_matches_ignore_pattern(self, input, channel):
        """
        Checks message against ignoredMessagePattern to determine
        whether the message should be ignored.
        """
        match = False
        pattern = self.registryValue("ignoredMessagePattern")
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
                log.debug(
                    "SpiffyTitles: title %s matches ignoredTitlePattern for %s"
                    % (input, channel)
                )
        return match

    def get_urls_from_message(self, input, channel):
        """
        Find the first string that looks like a URL from the message
        """
        url_re = self.registryValue("urlRegexp", channel)
        if not url_re:
            url_re = utils.web._httpUrlRe
        matches = re.findall(url_re, input)
        return matches

    def remove_control_characters(self, s):
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    def user_has_capability(self, msg):
        channel = msg.args[0]
        mask = msg.prefix
        required_capability = self.registryValue("requireCapability", channel=channel)
        cap = ircdb.makeChannelCapability(channel, required_capability)
        has_cap = ircdb.checkCapability(mask, cap, ignoreDefaultAllow=True)
        if has_cap:
            log.debug(
                "SpiffyTitles: %s has required capability '%s'"
                % (mask, required_capability)
            )
        else:
            log.debug(
                "SpiffyTitles: %s does NOT have required capability '%s'"
                % (mask, required_capability)
            )
        return has_cap

    def get_readable_file_size(self, num, suffix="B"):
        """
        Returns human readable file size
        """
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, "Yi", suffix)

    def get_template(self, handler_template, channel):
        """
        Returns the requested template object.
        """
        template = Template(self.registryValue(handler_template, channel=channel))
        return template

    def handler_dailymotion(self, url, info, channel):
        """
        Handles dailymotion links
        """
        dailymotion_handler_enabled = self.registryValue(
            "dailymotion.enabled", channel=channel
        )
        if not dailymotion_handler_enabled:
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: calling dailymotion handler for %s" % url)
        title = None
        video_id = None
        """ Get video ID """
        if "/video/" in info.path:
            video_id = info.path.lstrip("/video/").split("_")[0]
        elif "dai.ly" in url:
            video_id = url.split("/")[-1].split("?")[0]
        if not video_id:
            log.error(
                "SpiffyTitles: unable to get dailymotion video_id for URL: %s" % url
            )
            return self.handler_default(url, channel)
        fields = "id,title,owner.screenname,duration,views_total"
        api_url = "https://api.dailymotion.com/video/%s?fields=%s" % (video_id, fields,)
        log.debug("SpiffyTitles: looking up dailymotion info: %s", api_url)
        try:
            request = requests.get(api_url, timeout=self.timeout, proxies=self.proxies)
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: dailymotion error: {0}".format(e))
            return self.handler_default(url, channel)
        response = json.loads(request.content.decode())
        if response and "title" in response:
            video = response
            dailymotion_template = Template(
                self.registryValue("dailymotion.template", channel=channel)
            )
            video["views_total"] = "{:,}".format(int(video["views_total"]))
            video["duration"] = self.get_duration_from_seconds(video["duration"])
            video["ownerscreenname"] = video["owner.screenname"]
            title = dailymotion_template.render(video)
        else:
            log.debug(
                "SpiffyTitles: received unexpected payload from video: %s" % api_url
            )
        if not title:
            log.debug("SpiffyTitles: could not get dailymotion info for %s" % url)
            return self.handler_default(url, channel)
        else:
            return title

    def handler_vimeo(self, url, domain, channel):
        """
        Handles Vimeo links
        """
        vimeo_handler_enabled = self.registryValue("vimeo.enabled", channel=channel)
        if not vimeo_handler_enabled:
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: calling vimeo handler for %s" % url)
        title = None
        video_id = None
        """ Get video ID """
        result = re.search(r"^(http(s)://)?(www\.)?(vimeo\.com/)?(\d+)", url)
        if result:
            video_id = result.group(5)
        if not video_id:
            log.error("SpiffyTitles: Failef to get Vimeo video ID from URL: %s" % url)
            return self.handler_default(url, channel)
        api_url = "https://vimeo.com/api/v2/video/%s.json" % video_id
        log.debug("SpiffyTitles: looking up vimeo info: %s", api_url)
        try:
            request = requests.get(api_url, timeout=self.timeout, proxies=self.proxies)
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: vimeo error: {0}".format(e))
            return self.handler_default(url, channel)
        response = json.loads(request.content.decode())
        if response and "title" in response[0]:
            video = response[0]
            vimeo_template = Template(
                self.registryValue("vimeo.template", channel=channel)
            )
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
            log.debug(
                "SpiffyTitles: received unexpected payload from video: %s" % api_url
            )
        if not title:
            log.debug("SpiffyTitles: could not get vimeo info for %s" % url)
            return self.handler_default(url, channel)
        else:
            return title

    def handler_coub(self, url, domain, channel):
        """
        Handles coub.com links
        """
        coub_handler_enabled = self.registryValue("coub.enabled", channel=channel)
        if not coub_handler_enabled:
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: calling coub handler for %s" % url)
        title = None
        video_id = None
        """ Get video ID """
        if "/view/" in url:
            video_id = url.split("/view/")[1]
            """ Remove any query strings """
            if "?" in video_id:
                video_id = video_id.split("?")[0]
        if not video_id:
            log.error("SpiffyTitles: Failed to get Coub video ID for URL: %s" % url)
            return self.handler_default(url, channel)
        api_url = "http://coub.com/api/v2/coubs/%s" % video_id
        try:
            request = requests.get(api_url, timeout=self.timeout, proxies=self.proxies)
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: coub error: {0}".format(e))
            return self.handler_default(url, channel)
        response = json.loads(request.content.decode())
        if response:
            video = response
            coub_template = Template(self.registryValue("coub.template"))
            video["likes_count"] = "{:,}".format(int(video["likes_count"]))
            video["recoubs_count"] = "{:,}".format(int(video["recoubs_count"]))
            video["views_count"] = "{:,}".format(int(video["views_count"]))
            title = coub_template.render(video)
        if not title:
            log.debug("SpiffyTitles: Coub handler failed to get data for URL: %s" % url)
            return self.handler_default(url, channel)
        else:
            return title

    def get_video_id_from_url(self, url, info):
        """
        Get YouTube video ID from URL
        """
        try:
            path = info.path
            domain = info.netloc
            video_id = ""
            if domain == "youtu.be" or "/shorts/" in path:
                video_id = path.split("/")[-1]
            else:
                parsed = parse_qsl(info.query)
                params = dict(parsed)
                if "v" in params:
                    video_id = params["v"]
            if video_id:
                return video_id
            else:
                log.error("SpiffyTitles: error getting video id from %s" % (url))
        except IndexError as e:
            log.error(
                "SpiffyTitles: error getting video id from %s (%s)" % (url, str(e))
            )

    def handler_youtube(self, url, domain, channel):
        """
        Uses the Youtube API to provide additional meta data about
        Youtube Video links posted.
        """
        youtube_handler_enabled = self.registryValue("youtube.enabled", channel)
        if not youtube_handler_enabled:
            return self.handler_default(url, channel)
        developer_key = self.registryValue("youtube.developerKey")
        if not developer_key:
            log.info(
                "SpiffyTitles: no Youtube developer key set! Check the documentation "
                "for instructions."
            )
            return None
        log.debug("SpiffyTitles: calling Youtube handler for %s" % (url))
        video_id = self.get_video_id_from_url(url, domain)
        if not video_id:
            log.debug(
                "SpiffyTitles: Failed to get YouTube video ID for URL: {0}".format(url)
            )
            return self.handler_default(url, channel)
        yt_template = Template(self.registryValue("youtube.template", channel))
        title = ""
        options = {
            "part": "snippet,statistics,contentDetails",
            "maxResults": 1,
            "key": developer_key,
            "id": video_id,
        }
        api_url = "https://www.googleapis.com/youtube/v3/videos"
        log.debug("SpiffyTitles: requesting %s" % (api_url))
        try:
            request = requests.get(
                api_url, params=options, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitiles: YouTube Error: {0}".format(e))
            return self.handler_default(url, channel)
        response = json.loads(request.content.decode())
        if not response or not response.get("items"):
            log.error("SpiffyTitles: Failed to parse YouTube JSON response")
            return self.handler_default(url, channel)
        try:
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
            restricted = False
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
            if "ytRating" in video["contentDetails"]["contentRating"]:
                restricted = True
            published = snippet["publishedAt"].split("T")[0]
            timestamp = self.get_timestamp_from_youtube_url(url)
            yt_logo = self.get_youtube_logo(channel)
            compiled_template = yt_template.render(
                {
                    "title": title,
                    "duration": duration,
                    "timestamp": timestamp,
                    "view_count": view_count,
                    "like_count": like_count,
                    "dislike_count": dislike_count,
                    "comment_count": comment_count,
                    "favorite_count": favorite_count,
                    "channel_title": channel_title,
                    "published": published,
                    "restricted": restricted,
                    "yt_logo": yt_logo,
                }
            )
            title = compiled_template
        except IndexError as e:
            log.error(
                "SpiffyTitles: IndexError. Youtube API JSON response: %s" % (str(e))
            )
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

    def get_youtube_logo(self, channel):
        use_bold = self.registryValue("useBold", channel)
        if use_bold:
            yt_logo = "{0}\x0F\x02".format(self.registryValue("youtube.logo", channel))
        else:
            yt_logo = "{0}\x0F".format(self.registryValue("youtube.logo", channel))
        return yt_logo

    def get_total_seconds_from_duration(self, input):
        """
        Duration comes in a format like this: PT4M41S which translates to
        4 minutes and 41 seconds. This method returns the total seconds
        so that the duration can be parsed as usual.
        """
        regex = re.compile(
            r"""
                   (?P<sign>    -?) P
                (?:(?P<years>  \d+) Y)?
                (?:(?P<months> \d+) M)?
                (?:(?P<days>   \d+) D)?
            (?:                     T
                (?:(?P<hours>  \d+) H)?
                (?:(?P<minutes>\d+) M)?
                (?:(?P<seconds>\d+) S)?
            )?
            """,
            re.VERBOSE,
        )
        duration = regex.match(input).groupdict(0)
        delta = datetime.timedelta(
            hours=int(duration["hours"]),
            minutes=int(duration["minutes"]),
            seconds=int(duration["seconds"]),
        )
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

    def handler_twitch(self, url, domain, channel):
        """
        Queries twitch API for additional information about twitch links.
        This handler is for (www.)twitch.tv
        """
        twitch_handler_enabled = self.registryValue("twitch.enabled", channel=channel)
        if not twitch_handler_enabled:
            return self.handler_default(url, channel)
        twitch_client_id = self.registryValue("twitch.clientID")
        if not twitch_client_id:
            log.error("SpiffyTitles: Please set your Twitch client ID")
            return self.handler_default(url, channel)
        access_token = self.registryValue("twitch.accessToken")
        if not access_token:
            log.error("SpiffyTitles: Please set your Twitch Access Token")
            return self.handler_default(url, channel)
        url = url.split("?")[0]
        self.log.debug("SpiffyTitles: calling twitch handler for %s" % (url))
        patterns = {
            "video": {
                "pattern": r"^http(s)?:\/\/(www\.|go\.|player\.)?twitch\.tv\/"
                r"(videos/|\?video=v)(?P<video_id>[0-9]+)",
                "url": "https://api.twitch.tv/helix/videos?id={video_id}",
            },
            "clip": {
                "pattern": r"(http(s)?:\/\/clips\.twitch\.tv\/|http(s)?:\/\/"
                r"www\.twitch\.tv\/([^\/]+)\/clip\/)(?P<clip>.+)$",
                "url": "https://api.twitch.tv/helix/clips?id={clip}",
            },
            "channel": {
                "pattern": r"^http(s)?:\/\/(www\.|go\.)?twitch\.tv\/"
                r"(?P<channel_name>[^\/]+)",
                "url": "https://api.twitch.tv/helix/streams?user_login={channel_name}",
            },
        }
        for name in patterns:
            match = re.search(patterns[name]["pattern"], url)
            if match:
                link_type = name
                link_info = match.groupdict()
                data_url = patterns[name]["url"].format(**link_info)
                break
        if not match:
            self.log.debug("SpiffyTitles: twitch - no title found.")
            return self.handler_default(url, channel)
        bearer = "Bearer {}".format(access_token.strip())
        headers = {"Client-ID": twitch_client_id, "Authorization": bearer}
        self.log.debug("SpiffyTitles: twitch - requesting %s" % (data_url))
        try:
            request = requests.get(
                data_url, timeout=self.timeout, headers=headers, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffytTitles: Twitch Error: {0}".format(e))
            return self.handler_default(url, channel)
        data = {}
        try:
            response = json.loads(request.content.decode())
        except:
            response = None
        if not response:
            log.error("SpiffyTitles: Error parsing Twitch.TV JSON response")
            return self.handler_default(url, channel)
        self.log.debug("SpiffyTitles: twitch - got response:\n%s" % (response))
        if "error" in response:
            log.error("SpiffyTitles: Twitch Error: {0}".format(response["error"]))
            return self.handler_default(url, channel)
        if link_type == "channel":
            self.log.debug("SpiffyTitles: Twitch: link_type is channel")
            if "data" in response and response["data"]:
                self.log.debug("SpiffyTitles: Twitch: Got data[0]")
                data = response["data"][0]
                link_type = "stream"
            else:
                self.log.debug("SpiffyTitles: Twitch: No data[0]")
            data_url = "https://api.twitch.tv/helix/users?login={channel_name}".format(
                **link_info
            )
            try:
                request = requests.get(
                    data_url,
                    timeout=self.timeout,
                    headers=headers,
                    proxies=self.proxies,
                )
                request.raise_for_status()
            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
            ) as e:
                log.error("SpiffyTitles: Twitch Error: {0}".format(e))
                return self.handler_default(url, channel)
            user_data = {}
            try:
                response = json.loads(request.content.decode())
                user_data = response["data"][0]
                display_name = user_data["display_name"]
                description = user_data["description"]
                view_count = user_data["view_count"]
            except Exception as e:
                log.error(
                    "SpiffyTitles: KeyError parsing Twitch.TV JSON response: %s"
                    % (str(e))
                )
        elif link_type == "video":
            data = response
        elif link_type == "clip":
            data = response
        if not data and not user_data:
            log.error("SpiffyTitles: Twitch: Failed to get data from Twitch API")
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: twitch - Got data '%s'" % (data))
        twitch_template = self.get_template(
            "".join(["twitch.", link_type, "Template"]), channel
        )
        twitch_logo = self.get_twitch_logo(channel)
        if not twitch_template:
            self.log.debug("SpiffyTitles - twitch: bad template for %s" % (link_type))
            log.error("SpiffyTitles: Twitch: Got data, but template was bad")
            return self.handler_default(url, channel)
        if link_type == "stream":
            display_name = data["user_name"]
            game_id = data["game_id"]
            game_name = game_id
            title = data["title"]
            view_count = data["viewer_count"]
            created_at = self._time_created_at(data["started_at"])
            if game_id:
                get_game = requests.get(
                    "https://api.twitch.tv/helix/games?id={}".format(game_id),
                    timeout=self.timeout,
                    headers=headers,
                    proxies=self.proxies,
                )
                game_data = json.loads(get_game.content.decode())
                game_name = game_data["data"][0]["name"]
            template_vars = {
                "display_name": display_name,
                "game_name": game_name,
                "title": title,
                "view_count": view_count,
                "description": description,
                "created_at": created_at,
                "twitch_logo": twitch_logo,
            }
            reply = twitch_template.render(template_vars)
        elif link_type == "clip":
            data = response["data"][0]
            display_name = data["broadcaster_name"]
            data_url = "https://api.twitch.tv/helix/users?login={}".format(display_name)
            try:
                request = requests.get(
                    data_url,
                    timeout=self.timeout,
                    headers=headers,
                    proxies=self.proxies,
                )
                request.raise_for_status()
            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
            ) as e:
                log.error("SpiffyTitles: Twitch Error: {0}".format(e))
                return self.handler_default(url, channel)
            user_data = {}
            try:
                response = json.loads(request.content.decode())
                user_data = response["data"][0]
                description = user_data["description"]
                game_id = data["game_id"]
                game_name = game_id
                title = data["title"]
                view_count = data["view_count"]
                created_at = self._time_created_at(data["created_at"])
                if game_id:
                    get_game = requests.get(
                        "https://api.twitch.tv/helix/games?id={}".format(game_id),
                        timeout=self.timeout,
                        headers=headers,
                        proxies=self.proxies,
                    )
                    game_data = json.loads(get_game.content.decode())
                    game_name = game_data["data"][0]["name"]
                template_vars = {
                    "display_name": display_name,
                    "game_name": game_name,
                    "title": title,
                    "view_count": view_count,
                    "description": description,
                    "created_at": created_at,
                    "twitch_logo": twitch_logo,
                }
                reply = twitch_template.render(template_vars)
            except Exception as e:
                self.log.error(
                    "SpiffyTitles: Error parsing Twitch.TV JSON response: %s" % (str(e))
                )
        elif link_type == "video":
            data = response["data"][0]
            display_name = data["user_name"]
            data_url = "https://api.twitch.tv/helix/users?login={}".format(display_name)
            try:
                request = requests.get(
                    data_url,
                    timeout=self.timeout,
                    headers=headers,
                    proxies=self.proxies,
                )
            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
            ) as e:
                log.error("SpiffyTitles: Twitch Error: {0}".format(e))
                return self.handler_default(url, channel)
            user_data = {}
            try:
                response = json.loads(request.content.decode())
                user_data = response["data"][0]
                description = user_data["description"]
                title = data["title"]
                view_count = data["view_count"]
                created_at = self._time_created_at(data["created_at"])
                duration = data["duration"]
                template_vars = {
                    "display_name": display_name,
                    "title": title,
                    "view_count": view_count,
                    "created_at": created_at,
                    "description": description,
                    "duration": duration,
                    "twitch_logo": twitch_logo,
                }
                reply = twitch_template.render(template_vars)
            except Exception as e:
                self.log.error(
                    "SpiffyTitles: Error parsing Twitch.TV JSON response: %s" % (str(e))
                )
        else:
            try:
                template_vars = {
                    "display_name": display_name,
                    "description": description,
                    "view_count": view_count,
                    "twitch_logo": twitch_logo,
                }
                reply = twitch_template.render(template_vars)
            except Exception as e:
                self.log.error(
                    "SpiffyTitles: Error parsing Twitch.TV JSON response: %s" % (str(e))
                )
        return reply

    def _time_created_at(self, s):
        """
        Return relative time delta between now and s (dt string).
        """

        try:  # timeline's created_at Tue May 08 10:58:49 +0000 2012
            ddate = time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")[:-2]
        except ValueError:
            try:  # search's created_at Thu, 06 Oct 2011 19:41:12 +0000
                ddate = time.strptime(s, "%a, %d %b %Y %H:%M:%S +0000")[:-2]
            except ValueError:
                return s
        # do the math
        d = datetime.datetime.now() - datetime.datetime(*ddate, tzinfo=None)
        # now parse and return.
        if d.days:
            rel_time = "{:1d}d ago".format(abs(d.days))
        elif d.seconds > 3600:
            rel_time = "{:.1f}h ago".format(round((abs(d.seconds) / 3600), 1))
        elif 60 <= d.seconds < 3600:
            rel_time = "{:.1f}m ago".format(round((abs(d.seconds) / 60), 1))
        else:
            rel_time = "%ss ago" % (abs(d.seconds))
        return rel_time

    def get_twitch_logo(self, channel):
        use_bold = self.registryValue("useBold", channel)
        if use_bold:
            twitch_logo = "{0}\x0F\x02".format(
                self.registryValue("twitch.logo", channel)
            )
        else:
            twitch_logo = "{0}\x0F".format(self.registryValue("twitch.logo", channel))
        return twitch_logo

    def handler_imdb(self, url, info, channel):
        """
        Handles imdb.com links, querying the OMDB API for additional info
        Typical IMDB URL: http://www.imdb.com/title/tt2467372/
        """
        if not self.registryValue("imdb.enabled", channel=channel):
            log.debug(
                "SpiffyTitles: IMDB handler disabled. Falling back to default handler."
            )
            return self.handler_default(url, channel)
        apikey = self.registryValue("imdb.omdbAPI")
        result = None
        response = None
        imdb_id = None
        # Don't care about query strings
        if "?" in url:
            url = url.split("?")[0]
        # We can only accommodate a specific format of URL here
        match = re.match(r"https?:\/\/.*\.?imdb\.com\/title\/(tt[0-9]+)\/?.*", url)
        if match:
            imdb_id = match.group(1)
        if not imdb_id:
            log.error("SpiffyTitles: Invalid IMDB URL: %s" % url)
            return self.handler_default(url, channel)
        omdb_url = "http://www.omdbapi.com/"
        options = {"apikey": apikey, "i": imdb_id, "r": "json", "plot": "short"}
        try:
            request = requests.get(
                omdb_url, params=options, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles OMDB Error: %s" % (str(e)))
        try:
            response = json.loads(request.content.decode())
            imdb_template = Template(self.registryValue("imdb.template"))
            if "Error" in response or response["Response"] != "True":
                response = None
        except:
            log.error(
                "SpiffyTitles: JSON error opening OMDB response: %s"
                % (request.content.decode())
            )
            response = None
        if response:
            imdb_template = Template(self.registryValue("imdb.template"))
            meta = None
            tomato = None
            for rating in response["Ratings"]:
                if rating["Source"] == "Rotten Tomatoes":
                    tomato = rating["Value"]
                if rating["Source"] == "Metacritic":
                    meta = "{0}%".format(rating["Value"].split("/")[0])
            template_vars = {
                "title": response.get("Title"),
                "year": response.get("Year"),
                "country": response.get("Country"),
                "director": response.get("Director"),
                "plot": response.get("Plot"),
                "imdb_id": response.get("imdbID"),
                "imdb_rating": response.get("imdbRating"),
                "tomatoMeter": tomato,
                "metascore": meta,
                "released": response.get("Released"),
                "genre": response.get("Genre"),
                "awards": response.get("Awards"),
                "actors": response.get("Actors"),
                "rated": response.get("Rated"),
                "runtime": response.get("Runtime"),
                "writer": response.get("Writer"),
                "votes": response.get("imdbVotes"),
                "website": response.get("Website"),
                "language": response.get("Language"),
                "box_office": response.get("BoxOffice"),
                "production": response.get("Production"),
                "poster": response.get("Poster"),
                "imdb_logo": self.get_imdb_logo(channel),
            }
            result = imdb_template.render(template_vars)
        if result:
            return result
        else:
            log.debug("SpiffyTitles: IMDB handler failed. calling default handler")
            return self.handler_default(url, channel)

    def get_imdb_logo(self, channel):
        use_bold = self.registryValue("useBold", channel)
        if use_bold:
            imdb_logo = "{0}\x0F\x02".format(self.registryValue("imdb.logo", channel))
        else:
            imdb_logo = "{0}\x0F".format(self.registryValue("imdb.logo", channel))
        return imdb_logo

    def handler_wikipedia(self, url, domain, channel):
        """
        Queries wikipedia API for article extracts.
        """
        wikipedia_handler_enabled = self.registryValue(
            "wikipedia.enabled", channel=channel
        )
        if not wikipedia_handler_enabled:
            return self.handler_default(url, channel)
        self.log.debug("SpiffyTitles: calling Wikipedia handler for %s" % (url))
        pattern = r"/(?:w(?:iki))/(?P<page>[^/]+)$"
        info = urlparse(url)
        match = re.search(pattern, info.path)
        if not match:
            self.log.debug("SpiffyTitles: no title found.")
            return self.handler_default(url, channel)
        elif info.fragment and self.registryValue(
            "wikipedia.ignoreSectionLinks", channel=channel
        ):
            self.log.debug("SpiffyTitles: ignoring section link.")
            return self.handler_default(url, channel)
        else:
            page_title = match.groupdict()["page"]
        default_api_params = {
            "format": "json",
            "action": "query",
            "prop": "extracts",
            "exsentences": "2",
            "exlimit": "1",
            "exintro": "",
            "explaintext": "",
        }
        wiki_api_params = self.registryValue("wikipedia.apiParams", channel=channel)
        extra_params = dict(parse_qsl("&".join(wiki_api_params)))
        title_param = {
            self.registryValue("wikipedia.titleParam", channel=channel): page_title
        }
        # merge dicts
        api_params = default_api_params.copy()
        api_params.update(extra_params)
        api_params.update(title_param)
        api_url = "https://%s/w/api.php" % (info.netloc)
        extract = ""
        self.log.debug("SpiffyTitles: requesting %s" % (api_url))
        try:
            request = requests.get(
                api_url, params=api_params, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: Wikipedia Error: {0}".format(e))
            return self.handler_default(url, channel)
        response = json.loads(request.content.decode())
        if response:
            try:
                extract = list(response["query"]["pages"].values())[0]["extract"]
            except KeyError as e:
                self.log.error(
                    "SpiffyTitles: KeyError. Wikipedia API JSON response: %s" % (str(e))
                )
        else:
            self.log.error("SpiffyTitles: Error parsing Wikipedia API JSON response")
        if extract:
            if self.registryValue("wikipedia.removeParentheses"):
                extract = re.sub(r" ?\([^)]*\)", "", extract)
            max_chars = self.registryValue("wikipedia.maxChars", channel=channel)
            if len(extract) > max_chars:
                extract = (
                    extract[: max_chars - 3].rsplit(" ", 1)[0].rstrip(",.") + "..."
                )
            extract_template = self.registryValue(
                "wikipedia.extractTemplate", channel=channel
            )
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
                "pattern": r"^/r/(?P<subreddit>[^/]+)/comments/(?P<thread>[^/]+)"
                r"(?:/[^/]+/?)?$",
                "url": "https://www.reddit.com/r/{subreddit}/comments/{thread}.json",
            },
            "comment": {
                "pattern": r"^/r/(?P<subreddit>[^/]+)/comments/(?P<thread>[^/]+)/"
                r"[^/]+/(?P<comment>\w+/?)$",
                "url": (
                    "https://www.reddit.com/r/{subreddit}/comments/{thread}/x/"
                    "{comment}.json"
                ),
            },
            "user": {
                "pattern": r"^/u(?:ser)?/(?P<user>[^/]+)/?$",
                "url": "https://www.reddit.com/user/{user}/about.json",
            },
        }
        info = urlparse(url)
        for name in patterns:
            match = re.search(patterns[name]["pattern"], info.path)
            if match:
                link_type = name
                link_info = match.groupdict()
                data_url = patterns[name]["url"].format(**link_info)
                break
        if not match:
            self.log.debug("SpiffyTitles: no title found.")
            return self.handler_default(url, channel)
        self.log.debug("SpiffyTitles: requesting %s" % (data_url))
        headers = {"User-Agent": self.get_user_agent()}
        try:
            request = requests.get(
                data_url, headers=headers, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: Reddit Error: {0}".format(e))
            return self.handler_default(url, channel)
        data = {}
        extract = ""
        response = json.loads(request.content.decode())
        if response:
            try:
                if link_type == "thread":
                    data = response[0]["data"]["children"][0]["data"]
                if link_type == "comment":
                    data = response[1]["data"]["children"][0]["data"]
                    data["title"] = response[0]["data"]["children"][0]["data"]["title"]
                if link_type == "user":
                    data = response["data"]
            except KeyError as e:
                self.log.error(
                    "SpiffyTitles: KeyError parsing Reddit JSON response: %s" % (str(e))
                )
        else:
            self.log.error("SpiffyTitles: Error parsing Reddit JSON response")
        if data:
            today = datetime.datetime.now().date()
            created = datetime.datetime.fromtimestamp(data["created_utc"]).date()
            age_days = (today - created).days
            if age_days == 0:
                age = "today"
            elif age_days == 1:
                age = "yesterday"
            else:
                age = "{}d".format(age_days % 365)
                if age_days > 365:
                    age = "{}y, ".format(age_days // 365) + age
                age = age + " ago"
            if link_type == "thread":
                link_type = "linkThread"
                if data["is_self"]:
                    link_type = "textThread"
                    data["url"] = ""
                    extract = data.get("selftext", "")
            if link_type == "comment":
                extract = data.get("body", "")
            link_type_template = self.registryValue(
                "reddit." + link_type + "Template", channel=channel
            )
            reddit_template = Template(link_type_template)
            template_vars = {
                "id": data.get("id", ""),
                "user": data.get("name", ""),
                "gold": (data.get("is_gold", False) is True),
                "mod": (data.get("is_mod", False) is True),
                "author": data.get("author", ""),
                "subreddit": data.get("subreddit", ""),
                "url": data.get("url", ""),
                "title": data.get("title", ""),
                "domain": data.get("domain", ""),
                "score": data.get("score", 0),
                "percent": "{}%".format(int(data.get("upvote_ratio", 0) * 100)),
                "comments": "{:,}".format(data.get("num_comments", 0)),
                "created": created.strftime("%Y-%m-%d"),
                "age": age,
                "link_karma": "{:,}".format(data.get("link_karma", 0)),
                "comment_karma": "{:,}".format(data.get("comment_karma", 0)),
                "extract": "%%extract%%",
            }
            reply = reddit_template.render(template_vars)
            if extract:
                max_chars = self.registryValue("reddit.maxChars", channel=channel)
                max_extract_chars = max_chars + len("%%extract%%") - len(reply)
                if len(extract) > max_extract_chars:
                    extract = (
                        extract[: max_extract_chars - 3].rsplit(" ", 1)[0].rstrip(",.")
                        + "..."
                    )
            template_vars["extract"] = extract
            reply = reddit_template.render(template_vars)
            return reply
        else:
            self.log.debug("SpiffyTitles: falling back to default handler")
            return self.handler_default(url, channel)

    def is_valid_imgur_id(self, input):
        """
        Tests if input matches the typical imgur id, which seems to be alphanumeric.
        Images, galleries, and albums all share their format in their identifier.
        """
        match = re.match(r"[a-z0-9]+", input, re.IGNORECASE)
        if match:
            return match
        else:
            return

    def handler_imgur(self, url, info, channel):
        """
        Queries imgur API for additional information about imgur links.
        This handler is for any imgur.com domain.
        """
        is_album = info.path.startswith("/a/") or info.path.startswith("/gallery/")
        result = None
        if is_album:
            result = self.handler_imgur_album(url, info, channel)
        else:
            result = self.handler_imgur_image(url, info, channel)
        return result

    def handler_imgur_album(self, url, info, channel):
        """
        Handles retrieving information about albums from the imgur API.
        imgur provides the following information about albums:
        https://api.imgur.com/models/album
        """
        if not self.registryValue("imgur.enabled", channel=channel):
            return self.handler_default(url, channel)
        client_id = self.registryValue("imgur.clientID")
        if not client_id:
            log.error("SpiffyTitles: imgur client ID not set")
            return self.handler_default(url, channel)
        if info.path.startswith("/a/"):
            album_id = info.path.split("/a/")[1]
        elif info.path.startswith("/gallery/"):
            album_id = info.path.split("/gallery/")[1]
        """ If there is a query string appended, remove it """
        if "?" in album_id:
            album_id = album_id.split("?")[0]
        if not self.is_valid_imgur_id(album_id):
            log.error("SpiffyTitles: Invalid imgur ID")
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: found imgur album id %s" % (album_id))
        headers = {"Authorization": "Client-ID {0}".format(client_id)}
        api_url = "https://api.imgur.com/3/album/{0}".format(album_id)
        try:
            request = requests.get(
                api_url, headers=headers, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: Imgur Error: {0}".format(e))
            return self.handler_default(url, channel)
        album = None
        album = json.loads(request.content.decode())
        album = album.get("data")
        if album:
            album_template = self.registryValue("imgur.albumTemplate", channel=channel)
            imgur_album_template = Template(album_template)
            compiled_template = imgur_album_template.render(
                {
                    "title": album.get("title"),
                    "section": album.get("section"),
                    "view_count": "{:,}".format(album["views"]),
                    "image_count": "{:,}".format(album["images_count"]),
                    "nsfw": album.get("nsfw"),
                    "description": album.get("description"),
                }
            )
            return compiled_template
        else:
            log.error("SpiffyTitles: imgur album API returned unexpected results!")
            return self.handler_default(url, channel)

    def handler_imgur_image(self, url, info, channel):
        """
        Handles retrieving information about images from the imgur API.
        Used for both direct images and imgur.com/some_image_id_here type links, as
        they're both single images.
        """
        if not self.registryValue("imgur.enabled", channel=channel):
            return self.handler_default(url, channel)
        client_id = self.registryValue("imgur.clientID")
        if not client_id:
            log.error("SpiffyTitles: imgur client ID not set")
            return self.handler_default(url, channel)
        title = None
        """
        If there is a period in the path, it's a direct link to an image.
        If not, then it's an imgur.com/some_image_id_here type link
        """
        if "." in info.path:
            path = info.path.lstrip("/")
            image_id = path.split(".")[0]
        else:
            image_id = info.path.lstrip("/")
        if not self.is_valid_imgur_id(image_id):
            log.error("SpiffyTitles: Invalid imgur image ID")
            return self.handler_default(url, channel)
        log.debug("SpiffyTitles: found image id %s" % (image_id))
        headers = {"Authorization": "Client-ID {0}".format(client_id)}
        api_url = "https://api.imgur.com/3/image/{0}".format(image_id)
        try:
            request = requests.get(
                api_url, headers=headers, timeout=self.timeout, proxies=self.proxies
            )
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: Imgur Error: {0}".format(e))
            return self.handler_default(url, channel)
        image = None
        try:
            image = json.loads(request.content.decode())
            image = image.get("data")
        except:
            log.error("SpiffyTitles: Error reading imgur JSON response")
            image = None
        if image:
            channel_template = self.registryValue(
                "imgur.imageTemplate", channel=channel
            )
            imgur_template = Template(channel_template)
            readable_file_size = self.get_readable_file_size(image["size"])
            compiled_template = imgur_template.render(
                {
                    "title": image.get("title"),
                    "type": image.get("type"),
                    "nsfw": image.get("nsfw"),
                    "width": image.get("width"),
                    "height": image.get("height"),
                    "view_count": "{:,}".format(image["views"]),
                    "file_size": readable_file_size,
                    "section": image.get("section"),
                }
            )
            title = compiled_template
        else:
            log.error("SpiffyTitles: imgur API returned unexpected results!")
        if title:
            return title
        else:
            return self.handler_default(url, channel)

    def handler_twitter(self, url, info, channel):
        if not self.registryValue("twitter.enabled", channel):
            return self.handler_default(url, channel)
        api_url = "https://publish.twitter.com/oembed?url={0}&omit_script=True".format(
            url
        )
        try:
            request = requests.get(api_url, timeout=self.timeout, proxies=self.proxies)
            request.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            log.error("SpiffyTitles: Twitter Error: {0}".format(e))
            return self.handler_default(url, channel)
        response = None
        try:
            response = json.loads(request.content.decode())
        except:
            log.error("SpiffyTitles: Error reading Twitter JSON response")
            return self.handler_default(url, channel)
        results = {}
        soup = BeautifulSoup(response["html"])
        results["text"] = soup.get_text(" ").strip()
        match = re.match(r"(.*) — (.*) \((.*)\) (.*)", results["text"])
        if match:
            results["content"] = match.group(1)
            results["name"] = match.group(2)
            results["nick"] = match.group(3)
            results["date"] = match.group(4)
        template = Template(self.registryValue("twitter.template", channel))
        title = template.render(results).strip()
        if title:
            return title
        else:
            return self.handler_default(url, channel)

    def t(self, irc, msg, args, query):
        """
        Retrieves title for a URL on demand
        """
        channel = msg.args[0]
        title = None
        try:
            title = self.get_title_by_url(query, channel)
        except:
            pass
        if title:
            irc.reply(title)
        else:
            return

    t = wrap(t, ["text"])


Class = SpiffyTitles
