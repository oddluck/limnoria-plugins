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

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('SpiffyTitles')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class SpiffyTitles(callbacks.Plugin):
    """Displays link titles when posted in a channel"""
    threaded = True
    callBefore = ['Web']

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        is_channel = irc.isChannel(channel)
        is_ctcp = ircmsgs.isCtcp(msg)        
        message = msg.args[1]
        
        if is_channel and not is_ctcp:
            url = self.get_url_from_message(message)
            
            if url:
                domain = self.get_domain_from_url(url)
                
                if domain:
                    handlers = {
                        "youtube.com": self.handler_youtube,
                        "youtu.be": self.handler_youtube
                    }
                    
                    try:
                        handler = handlers[domain]                        
                        title = handler(url, irc)                            
                    except KeyError:
                        title = self.handler_default(url, irc)
                else:
                    self.log.error("SpiffyTitles: unable to determine domain from url %s" % (url))
                    title = self.handler_default(url, irc)
                
                if title is not None:
                    formatted_title = self.get_title(title)
                    
                    self.log.info("SpiffyTitles: title found: %s" % (formatted_title))
                    
                    irc.reply(formatted_title)

    def handler_youtube(self, url, irc):
        self.log.info("SpiffyTitles: calling youtube handler for %s" % (url))
    
    def handler_default(self, url, irc):
        self.log.info("SpiffyTitles: calling default handler for %s" % (url))
        
        html = self.get_html_by_url(url)
        
        if html:
            title = self.get_title_from_html(html)
            
            return title
        
    def get_title(self, title):
        template = self.registryValue("defaultTitleTemplate")
        useBold = self.registryValue("useBold")
        
        title = title.replace("\n", "")
        title = title.replace("\t", "")
        title = title.strip()
        
        title = template % (title)
        
        if useBold:
            title = ircutils.bold(title)
        
        return title
    
    def get_title_from_html(self, html):
        soup = BeautifulSoup(html)
        title = soup.find("head").find("title")
        
        if title:
            return title.get_text().strip()
    
    def get_html_by_url(self, url):
        try:
            agent = self.get_user_agent()
            headers = {
                "User-Agent": agent
            }
            request = requests.get(url, headers=headers)
            
            ok = request.status_code == requests.codes.ok
            
            if ok:
                text = request.text
                
                return text
            else:
                self.log.error("SpiffyTitles HTTP response code %s - %s" % (request.status_code, 
                                                                            request.text))
        
        except requests.exceptions.Timeout, e:
            self.log.error("SpiffyTitles Timeout: %s" % (str(e)))
        except requests.exceptions.ConnectionError, e:
            self.log.error("SpiffyTitles ConnectionError: %s" % (str(e)))
        except requests.exceptions.HTTPError, e:
            self.log.error("SpiffyTitles HTTPError: %s" % (str(e)))
        except requests.exceptions.InvalidURL, e:
            self.log.error("SpiffyTitles InvalidURL: %s" % (str(e)))
    
    def get_user_agent(self):
        agents = self.registryValue("userAgents")
        
        return random.choice(agents)
    
    def get_domain_from_url(self, url):
        try:        
            parsed = urlparse(url)
            
            if parsed:
                return parsed.netloc
        except:
            pass
    
    def get_url_from_message(self, input):
        url_re = self.registryValue("urlRegularExpression")
        match = re.search(url_re, input)
        
        if match:
            return match.group(0)
    
Class = SpiffyTitles


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
