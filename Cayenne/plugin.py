# -*- coding: utf-8 -*-
"""
Cayenne - Displays cat facts or cat gifs based on probability

Copyright (c) 2015, butterscotchstallion
All rights reserved.
"""
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import random
import datetime
import os

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("Cayenne")
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Cayenne(callbacks.Plugin):
    """Displays cat facts or cat gifs based on probability"""
    threaded = True
    last_message_timestamp = False
    cat_facts = []
    
    def __init__(self, irc):
        self.__parent = super(Cayenne, self)
        self.__parent.__init__(irc)
        
        self.read_cat_facts_file()
    
    def read_cat_facts_file(self):
        """
        Read the cat facts file into a list so we can retrieve at random later
        """
        try:
            dir = os.path.dirname(__file__)
            fact_file_path = os.path.join(dir, "./facts.txt")
            
            for line in open(fact_file_path):
                self.cat_facts.append(line.rstrip("\n"))
        
        except:
            self.log.error("Cayenne: error reading cat facts file: %s" % fact_file_path)
    
    def get_fact(self):
        """
        Get a random cat fact
        """        
        return random.choice(self.cat_facts)
    
    def message_contains_trigger_word(self, message):
        """
        Check prefined list of trigger words and return
        which one was found, if any
        """
        words = self.registryValue("triggerWords")
        
        if words:
            words = [word.strip() for word in words]
            
            if words:
                for word in words:
                    if word and word in message:
                        return word
            else:
                self.log.error("Cayenne: no trigger words set apparently")
        
        return False
        
    def get_link(self):
        """
        Query cat URL to get a random link
        """
        try:
            link_url = self.registryValue("linkURL")
            response = utils.web.getUrl(link_url).decode("utf8")
            
            # Expecting a link
            if "http" in response:
                return response
            else:
                self.log.error("Cayenne: received unexpected response from cat URL: %s" % (response))
            
        except:
            self.log.exception("Cayenne: error fetching cat URL")
    
    def doPrivmsg(self, irc, msg):
        """
        Checks each channel message to see if it contains a trigger word
        """
        channel = msg.args[0]
        is_channel = irc.isChannel(channel)
        is_ctcp = ircmsgs.isCtcp(msg)        
        message = msg.args[1]
        bot_nick = irc.nick
        
        # Check origin nick to make sure the trigger
        # didn"t come from the bot.
        origin_nick = msg.nick
        
        is_message_from_self = origin_nick.lower() == bot_nick.lower()
        
        # Only react to messages/actions in a channel and to messages that aren't from
        # the bot itself.
        if is_channel and not is_ctcp and not is_message_from_self and self.registryValue('enable', msg.args[0]):            
            if type(message) is str and len(message):
                fact_chance = int(self.registryValue("factChance"))
                link_chance = int(self.registryValue("linkChance"))            
                throttle_seconds = int(self.registryValue("throttleInSeconds"))
                triggered = self.message_contains_trigger_word(message)
                now = datetime.datetime.now()
                seconds = 0
                
                if self.last_message_timestamp:                
                    seconds = (now - self.last_message_timestamp).total_seconds()
                    throttled = seconds < throttle_seconds
                else:
                    throttled = False
                
                if triggered is not False:
                    self.log.debug("Cayenne triggered because message contained %s" % (triggered))
                    
                    fact_rand = random.randrange(0, 100) <= fact_chance
                    link_rand = random.randrange(0, 100) <= link_chance
                    
                    if fact_rand or link_rand:
                        if throttled:                    
                            self.log.info("Cayenne throttled. Not meowing: it has been %s seconds" % (round(seconds, 1)))
                        else:
                            self.last_message_timestamp = now
                            
                            if fact_rand:
                                output = self.get_fact()
                            
                            if link_rand:
                                output = self.get_link()
                            
                            if output:
                                irc.sendMsg(ircmsgs.privmsg(channel, output))
                            else:
                                self.log.error("Cayenne: error retrieving output")
    
Class = Cayenne


