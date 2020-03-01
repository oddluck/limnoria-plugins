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
import json
from jinja2 import Template
from urllib.parse import urlencode

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
        apikey = self.registryValue('developerKey')
        safe_search = self.registryValue("safeSearch", dynamic.channel)
        sort_order = self.registryValue("sortOrder", dynamic.channel)
        video_id = None
        opts = {"q": query,
                "part": "snippet",
                "maxResults": "1",
                "order": sort_order,
                "key": apikey,
                "safeSearch": safe_search,
                "type": "video"}
        api_url = "https://www.googleapis.com/youtube/v3/search?{0}".format(urlencode(opts))
        try:
            log.debug("YouTube: requesting %s" % (api_url))
            request = requests.get(api_url, timeout=10)
            request = json.loads(request.content)
            video_id = request["items"][0]["id"]["videoId"]
        except Exception:
            log.error("YouTube: YouTube API HTTP %s: %s" % (request.status_code, request.content.decode()))
            pass
        return video_id

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
        channel = msg.channel
        yt_template = Template(self.registryValue("template", channel))
        response = None
        title = None
        video_id = self.dosearch(query)
        if video_id:
            log.debug("YouTube: got video id: %s" % video_id)
            opts = {
                "part": "snippet,statistics,contentDetails",
                "maxResults": 1,
                "key": apikey,
                "id": video_id}
            opts = urlencode(opts)
            api_url = "https://www.googleapis.com/youtube/v3/videos?%s" % (opts)
            log.debug("YouTube: requesting %s" % (api_url))
            request = requests.get(api_url, timeout=10)
            ok = request.status_code == requests.codes.ok
            if ok:
                response = json.loads(request.content)
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
                        log.error("YouTube: IndexError parsing Youtube API JSON response: %s" % (str(e)))
                else:
                    log.error("YouTube: Error parsing Youtube API JSON response")
            else:
                log.error("YouTube: YouTube API HTTP %s: %s" % (request.status_code, request.content.decode()))
        if title:
            use_bold = self.registryValue("useBold", channel)
            if use_bold:
                title = ircutils.bold(title)
            irc.reply(title, prefixNick=False)
    yt = wrap(yt, ['text'])

Class = YouTube

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
