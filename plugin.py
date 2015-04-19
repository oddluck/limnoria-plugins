# -*- coding: utf-8 -*-
###
# Copyright (c) 2015, PrgmrBill
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import re
import requests
from urlparse import urlparse
from bs4 import BeautifulSoup
import random
import json
import cgi
import datetime
from jinja2 import Template

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
    link_cache = {}
    handlers = {}
    
    def __init__(self, irc):
        self.__parent = super(SpiffyTitles, self)
        self.__parent.__init__(irc)
        
        self.link_throttle_in_seconds = self.registryValue("cooldownInSeconds")
        
        """
        Check if imgur client id or secret are set, and if so initialize
        imgur API client
        """
        imgur_client_id = self.registryValue("imgurClientID")
        imgur_client_secret = self.registryValue("imgurClientSecret")
        
        if imgur_client_id and imgur_client_secret:
            # Images mostly
            self.handlers["i.imgur.com"] = self.handler_imgur_image
            
            # Albums, galleries, etc
            self.handlers["imgur.com"] = self.handler_imgur
            
            # Initialize API client
            try:
                from imgurpython import ImgurClient
                
                try:
                    self.imgur_client = client = ImgurClient(imgur_client_id, imgur_client_secret)                    
                except ImgurClientError as e:
                    self.log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))                    
            except ImportError, e:
                self.log.error("SpiffyTitles ImportError: %s" % str(e))
        
        self.add_youtube_handlers()
    
    def doPrivmsg(self, irc, msg):
        """
        Observe each channel message and look for links
        """
        channel = msg.args[0].lower()
        is_channel = irc.isChannel(channel)
        is_ctcp = ircmsgs.isCtcp(msg)        
        message = msg.args[1]
        now = datetime.datetime.now()

        if is_channel and not is_ctcp:
            channel_is_allowed = self.is_channel_allowed(channel)            
            url = self.get_url_from_message(message)
            
            if url:
                # Check if channel is allowed based on white/black list restrictions
                if not channel_is_allowed:
                    self.log.info("SpiffyTitles: not responding to link in %s due to black/white list restrictions" % (channel))
                    return
                
                info = urlparse(url)
                
                domain = info.netloc
                is_ignored = self.is_ignored_domain(domain)
                
                if is_ignored:
                    self.log.info("SpiffyTitles: ignoring url due to pattern match: %s" % (url))
                    return
                
                # Check if we"ve seen this link lately
                if url in self.link_cache:
                    link_timestamp = self.link_cache[url]
                    
                    seconds = (now - link_timestamp).total_seconds()
                    throttled = seconds < self.link_throttle_in_seconds
                else:
                    throttled = False
                
                if throttled:
                    self.log.info("SpiffyTitles: %s ignored; throttle: it has been %s seconds since last post" % (url, seconds))
                    return
                
                # Update link cache now that we know it"s not an ignored link
                self.link_cache[url] = now
                
                if domain in self.handlers:
                    handler = self.handlers[domain]                        
                    title = handler(url, info)
                else:
                    title = self.handler_default(url, info)
                
                if title is not None and title:
                    self.log.info("SpiffyTitles: title found: %s" % (title))
                    
                    formatted_title = self.get_formatted_title(title)
                    
                    irc.reply(formatted_title)
                else:
                    self.log.error("SpiffyTitles: could not get a title for %s" % (url))
    
    def add_youtube_handlers(self):
        """
        Adds handlers for Youtube videos. The handler is matched based on the
        domain used in the URL.
        """
        self.handlers["youtube.com"] = self.handler_youtube
        self.handlers["www.youtube.com"] = self.handler_youtube
        self.handlers["youtu.be"] = self.handler_youtube
        self.handlers["m.youtube.com"] = self.handler_youtube
    
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
    
    def is_ignored_domain(self, domain):
        """
        Checks domain against a regular expression
        """
        pattern = self.registryValue("ignoredDomainPattern")
        
        if pattern:
            self.log.debug("SpiffyTitles: matching %s against %s" % (domain, str(pattern)))
            
            try:
                pattern_search_result = re.search(pattern, domain)
                
                if pattern_search_result is not None:
                    match = pattern_search_result.group()
                    
                    return match
            except re.Error:
                self.log.error("SpiffyTitles: invalid regular expression: %s" % (pattern))
    
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
                video_id = dict(parsed)["v"]
            
            if video_id:
                return video_id
            else:
                self.log.error("SpiffyTitles: error getting video id from %s" % (url))
        
        except IndexError, e:
            self.log.error("SpiffyTitles: error getting video id from %s (%s)" % (url, str(e)))

    def handler_youtube(self, url, domain):
        """
        Uses the Youtube API to provide additional meta data about
        Youtube Video links posted.
        """
        self.log.info("SpiffyTitles: calling Youtube handler for %s" % (url))
        video_id = self.get_video_id_from_url(url, domain)
        yt_template = Template(self.registryValue("youtubeTitleTemplate"))
        title = ""
        
        if video_id:
            api_url = "https://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc" % (video_id)
            agent = self.get_user_agent()
            headers = {
                "User-Agent": agent
            }
            
            self.log.info("SpiffyTitles: requesting %s" % (api_url))
            
            request = requests.get(api_url, headers=headers)            
            ok = request.status_code == requests.codes.ok
            
            if ok:
                response = json.loads(request.text)
                
                if response:
                    try:
                        data = response["data"]
                        title = data["title"]
                        rating = str(round(data["rating"], 2))
                        view_count = "{:,}".format(int(data["viewCount"]))
                        duration_seconds = int(data["duration"])
                        
                        """
                        #23 - If duration is zero, then it"s a LIVE video
                        """
                        if duration_seconds > 0:
                            m, s = divmod(duration_seconds, 60)
                            h, m = divmod(m, 60)
                            
                            duration = "%02d:%02d" % (m, s)
                            
                            # Only include hour if the video is at least 1 hour long
                            if h > 0:
                                duration = "%02d:%s" % (h, duration)
                        else:
                            duration = "LIVE"
                        
                        compiled_template = yt_template.render({
                            "title": title,
                            "rating": rating,
                            "duration": duration,
                            "view_count": view_count
                        })
                        
                        title = compiled_template
                    
                    except IndexError:
                        self.log.error("SpiffyTitles: IndexError parsing Youtube API JSON response")
                else:
                    self.log.error("SpiffyTitles: Error parsing Youtube API JSON response")
            else:
                self.log.error("SpiffyTitles: Youtube API HTTP %s: %s" % (request.status_code,
                                                                         request.text))
        
        # If we found a title, return that. otherwise, use default handler
        if title:
            return title
        else:
            self.log.info("SpiffyTitles: falling back to default handler")
            
            return self.handler_default(url, domain)
    
    def handler_default(self, url, domain):
        """
        Default handler for websites
        """
        self.log.info("SpiffyTitles: calling default handler for %s" % (url))
        default_template = Template(self.registryValue("defaultTitleTemplate"))
        html = self.get_source_by_url(url)
        
        if html:
            title = self.get_title_from_html(html)
            
            if title is not None:
                title_template = default_template.render(title=title)
                
                return title_template
    
    def handler_imgur(self, url, info):
        """
        Queries imgur API for additional information about imgur links.

        This handler is for any imgur.com domain.
        """
        is_album = info.path.startswith("/a/")
        is_gallery = info.path.startswith("/gallery/")
        result = None
        
        if is_album:
            result = self.handler_imgur_album(url, info)
        else:
            result = self.handler_default(url, info)
        
        return result
    
    def handler_imgur_album(self, url, info):
        """
        Handles retrieving information about albums from the imgur API.
        
        imgur provides the following information about albums: https://api.imgur.com/models/album
        """
        from imgurpython.helpers.error import ImgurClientRateLimitError
        from imgurpython.helpers.error import ImgurClientError
        
        album_id = info.path.split("/a/")[1]
        
        """ If there is a query string appended, remove it """
        if "?" in album_id:
            album_id = album_id.split("?")[0]
        
        if album_id:
            self.log.info("SpiffyTitles: found imgur album id %s" % (album_id))
            
            try:
                album = self.imgur_client.get_album(album_id)
                
                if album:
                    imgur_album_template = Template(self.registryValue("imgurAlbumTemplate"))
                    compiled_template = imgur_album_template.render({
                        "title": album.title,
                        "section": album.section,
                        "view_count": "{:,}".format(album.views),
                        "image_count": "{:,}".format(album.images_count),
                        "nsfw": album.nsfw
                    })
                    
                    return compiled_template
                else:
                    self.log.error("SpiffyTitles: imgur album API returned unexpected results!")

            except ImgurClientRateLimitError as e:
                self.log.error("SpiffyTitles: imgur rate limit error: %s" % (e.error_message))
            except ImgurClientError as e:
                self.log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))
        else:
            self.log.info("SpiffyTitles: unable to determine album id for %s" % (url))
    
    def handler_imgur_image(self, url, info):
        """
        Handles retrieving information about images from the imgur API.
        
        This handler is only run when the domain is i.imgur.com which is usually
        just images, except in the case of gifv - which is a HTML file which has
        a title. The latter case is why there are fallbacks here.
        
        The path comes in this form: /image_id.extension so strip off the left
        forward slash and then split by period to get the image id.
        """
        from imgurpython.helpers.error import ImgurClientRateLimitError
        from imgurpython.helpers.error import ImgurClientError
        
        path = info.path.lstrip("/")
        image_id = path.split(".")[0]
        title = None
        
        if image_id:
            try:
                image = self.imgur_client.get_image(image_id)
                
                if image:
                    imgur_template = Template(self.registryValue("imgurTemplate"))
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
                    self.log.error("SpiffyTitles: imgur API returned unexpected results!")
            except ImgurClientRateLimitError as e:
                self.log.error("SpiffyTitles: imgur rate limit error: %s" % (e.error_message))
            except ImgurClientError as e:
                self.log.error("SpiffyTitles: imgur client error: %s" % (e.error_message))
        else:
            self.log.error("SpiffyTitles: error retrieving image id for %s" % (url))
        
        if title is not None:
            return title
        else:
            return self.handler_default(url, info)
    
    def get_readable_file_size(self, num, suffix="B"):
        """
        Returns human readable file size
        """
        for unit in ["","Ki","Mi","Gi","Ti","Pi","Ei","Zi"]:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, "Yi", suffix)
    
    def get_formatted_title(self, title):
        """
        Remove cruft from title and apply bold if applicable
        """
        useBold = self.registryValue("useBold")
        
        # Replace anywhere in string
        title = title.replace("\n", "")
        title = title.replace("\t", "")
        title = re.sub(" +", " ", title)
        
        if useBold:
            title = ircutils.bold(title)
        
        # Strip whitespace on either side
        title = title.strip()
        
        return title
    
    def get_title_from_html(self, html):
        """
        Retrieves value of <title> tag from HTML
        """
        soup = BeautifulSoup(html)
        
        if soup is not None:
            head = soup.find("head")
            
            if head:
                # TODO: What should happen if there is more than one <title> tag?
                title = head.find("title")
                
                if title is not None:
                    title_text = title.get_text()
                    
                    if len(title_text):
                        stripped_title = title_text.strip()
                        
                        return stripped_title
    
    def get_source_by_url(self, url):
        """
        Get the HTML of a website based on a URL
        """
        try:
            agent = self.get_user_agent()
            headers = {
                "User-Agent": agent
            }
            request = requests.get(url, headers=headers)
            
            self.log.info("SpiffyTitles: requesting %s" % (url))
            
            if request.status_code == requests.codes.ok:
                # Check the content type which comes in the format: "text/html; charset=UTF-8"
                content_type = request.headers.get("content-type").split(";")[0].strip()
                acceptable_types = self.registryValue("mimeTypes")
                mime_type_acceptable = content_type in acceptable_types
                
                self.log.info("SpiffyTitles: content type %s" % (content_type))
                
                if mime_type_acceptable:
                    text = request.content
                    
                    if text:
                        return text
                    else:
                        self.log.info("SpiffyTitles: empty content from %s" % (url))                        

                else:
                    self.log.debug("SpiffyTitles: unacceptable mime type %s for url %s" % (content_type, url))
            else:
                self.log.error("SpiffyTitles HTTP response code %s - %s" % (request.status_code, 
                                                                            request.content))
        
        except requests.exceptions.Timeout, e:
            self.log.error("SpiffyTitles Timeout: %s" % (str(e)))
        except requests.exceptions.ConnectionError, e:
            self.log.error("SpiffyTitles ConnectionError: %s" % (str(e)))
        except requests.exceptions.HTTPError, e:
            self.log.error("SpiffyTitles HTTPError: %s" % (str(e)))
        except requests.exceptions.InvalidURL, e:
            self.log.error("SpiffyTitles InvalidURL: %s" % (str(e)))
    
    def get_user_agent(self):
        """
        Returns a random user agent from the ones available
        """
        agents = self.registryValue("userAgents")
        
        return random.choice(agents)
    
    def get_url_from_message(self, input):
        """
        Find the first string that looks like a URL from the message
        """
        url_re = self.registryValue("urlRegularExpression")
        match = re.search(url_re, input)
        
        if match:
            return match.group(0).strip()
    
Class = SpiffyTitles

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
