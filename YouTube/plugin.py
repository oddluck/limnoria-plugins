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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import supybot.log as log
import requests
import pendulum
from jinja2 import Template
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qsl

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('YouTube')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class YouTube(callbacks.Plugin):
    """Queries OMDB database for information about YouTube titles"""
    threaded = True

    def dosearch(self, query):
        url = None
        k = 0
        while k < 3 and not url:
            try:
                searchurl = "https://www.google.com/search?&q={0} site:youtube.com".format(query)
                ua = UserAgent()
                header = {'User-Agent':str(ua.random)}
                data = requests.get(searchurl, headers=header, timeout=10)
                soup = BeautifulSoup(data.text)
                elements = soup.select('.r a')
                for i in range(len(elements)):
                    if 'watch?v=' in elements[i]['href']:
                        url = elements[i]['href']
                        break
                k += 1
            except Exception:
                continue
        return url

    def get_video_id_from_url(self, url):
        """
        Get YouTube video ID from URL
        """
        info = urlparse(url)
        try:
            path = info.path
            domain = info.netloc
            video_id = ""

            if domain == "youtu.be":
                video_id = path.split("/")[1]
            else:
                parsed = parse_qsl(info.query)
                params = dict(parsed)

                if "v" in params:
                    video_id = params["v"]

            if video_id:
                return video_id
            else:
                log.error("SpiffyTitles: error getting video id from %s" % (url))
                return None

        except IndexError as e:
            log.error("SpiffyTitles: error getting video id from %s (%s)" % (url, str(e)))

    def get_duration_from_seconds(self, duration_seconds):
        m, s = divmod(duration_seconds, 60)
        h, m = divmod(m, 60)

        duration = "%02d:%02d" % (m, s)

        """ Only include hour if the video is at least 1 hour long """
        if h > 0:
            duration = "%02d:%s" % (h, duration)

        return duration

    def get_total_seconds_from_duration(self, input):
        """
        Duration comes in a format like this: PT4M41S which translates to
        4 minutes and 41 seconds. This method returns the total seconds
        so that the duration can be parsed as usual.
        """
        duration = pendulum.parse(input)
        return duration.total_seconds()

    def get_published_date(self, date):
        date = pendulum.parse(date, strict=False)
        date = pendulum.datetime(date.year, date.month, date.day)
        date = date.to_date_string()
        return date

    def get_youtube_logo(self):
        use_bold = self.registryValue("useBold", dynamic.channel)
        if use_bold:
            yt_logo = "{0}\x0F\x02".format(self.registryValue("logo", dynamic.channel))
        else:
            yt_logo = "{0}\x0F".format(self.registryValue("logo", dynamic.channel))

        return yt_logo

    def yt(self, irc, msg, args, query):
        """<search term>
        Search for YouTube videos
        """
        apikey = self.registryValue('developerKey')
        url = self.dosearch(query)
        if url:
            video_id = self.get_video_id_from_url(url)
        else:
            video_id = None
            irc.reply("No results found for {0}".format(query))
            return

        channel = msg.args[0]
        result = None

        yt_template = Template(self.registryValue("template", dynamic.channel))
        title = ""

        if video_id:
            log.debug("YouTube: got video id: %s" % video_id)
            options = {
                "part": "snippet,statistics,contentDetails",
                "maxResults": 1,
                "key": apikey,
                "id": video_id
            }
            encoded_options = urlencode(options)
            api_url = "https://www.googleapis.com/youtube/v3/videos?%s" % (encoded_options)

            log.debug("YouTube: requesting %s" % (api_url))

            request = requests.get(api_url, timeout=10)
            ok = request.status_code == requests.codes.ok

            if ok:
                response = request.json()

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

                            published = snippet['publishedAt']
                            published = self.get_published_date(published)

                            yt_logo = self.get_youtube_logo()

                            link = "https://youtu.be/%s" % (video_id)

                            compiled_template = yt_template.render({
                                "title": title,
                                "duration": duration,
                                "views": view_count,
                                "likes": like_count,
                                "dislikes": dislike_count,
                                "comments": comment_count,
                                "favorites": favorite_count,
                                "uploader": channel_title,
                                "link": link,
                                "published": published,
                                "logo": yt_logo
                            })

                            title = compiled_template
                        else:
                            log.debug("YouTube: video appears to be private; no results!")

                    except IndexError as e:
                        log.error("YouTube: IndexError parsing Youtube API JSON response: %s" %
                                  (str(e)))
                else:
                    log.error("YouTube: Error parsing Youtube API JSON response")
            else:
                log.error("YouTube: YouTube API HTTP %s: %s" %
                          (request.status_code, request.text))
        if title:
            irc.reply(title, prefixNick=False)

    yt = wrap(yt, ['text'])

Class = YouTube


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
