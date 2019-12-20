###
# Copyright (c) 2019 oddluck
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.log as log
import supybot.conf as conf
import os
import requests
import random
import re
import json
import markovify
import spacy
from ftfy import fix_text

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Markovify')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

nlp = spacy.load('en_core_web_sm')

class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

class Markovify(callbacks.Plugin):
    """Generates chat replies using subreddit comments"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Markovify, self)
        self.__parent.__init__(irc)
        self.model = {}
        self.MATCH_MESSAGE_STRIPNICK = re.compile('^(<[^ ]+> )?(?P<message>.*)$')

    def cleanText(self, user_sentences):
        fix_text(user_sentences)
        user_sentences = user_sentences.strip()                         # Strip whitespace from beginning and the end of the string.
        user_sentences = utils.str.normalizeWhitespace(user_sentences)  # Normalize the whitespace in the string.
        return text

    def _subreddit(self, subreddit, latest_timestamp=None):
        """
        Downloads the subreddit comments, 500 at a time.
        Parameters
        ----------
        subreddit : str
            The subreddit name.
        latest_timestamp : int
            The latest comment timestamp.
        """
        base_url = "https://api.pushshift.io/reddit/comment/search/"
        params = {"subreddit": subreddit, "sort": "desc",
                  "sort_type": "created_utc", "size": 500, "user_removed": False, "mod_removed": False}
        if latest_timestamp != None:
            params["before"] = latest_timestamp
        with requests.get(base_url, params=params) as response:
            data = response.json()
            self.count += len(data["data"])
            text = [self.cleanText(item['body']) for item in data["data"]]
            self.latest_timestamp = data['data'][-1]["created_utc"]
            text = POSifiedText(text)
            return text

    def doPrivmsg(self, irc, msg):
        (channel, message) = msg.args
        channel = channel.lower()
        if callbacks.addressed(irc.nick, msg) or ircmsgs.isCtcp(msg) or not irc.isChannel(channel) or not self.registryValue('enable', channel):
            return
        if msg.nick.lower() in self.registryValue('ignoreNicks', channel):
            log.debug("Markovify: nick %s in ignoreNicks for %s" % (msg.nick, channel))
            return
        if irc.nick.lower() in message.lower():
            message = re.sub(re.escape(irc.nick), '', message, re.IGNORECASE)
            probability = self.registryValue('probabilityWhenAddressed', channel)
        else:
            probability = self.registryValue('probability', channel)
        message = self.processText(channel, message)
        if not message and len(message) > 1 or message.isspace():
            return
        if random.random() < probability:
            try:
                new_comment = self.model[channel].make_sentence()
            except KeyError:
                directory = conf.supybot.directories.data
                directory = directory.dirize(channel.lower() + "/markov.json")
                with open(directory, 'r') as infile:
                    jsondata = json.load(infile)
                    self.model[channel] = POSifiedText.from_json(jsondata)
                new_comment = self.model[channel].make_sentence()
            except:
                self.model[channel] = POSifiedText("Hello!")
            if new_comment and len(new_comment) > 1 and not new_comment.isspace():
                self.model[channel] = markovify.combine(models=[self.model[channel], POSifiedText(message), POSifiedText(new_comment)])
                irc.reply(new_comment, prefixNick=False)
        else:
            self.model[channel] = markovify.combine(models=[self.model[channel], POSifiedText(message)])

    def processText(self, channel, text):
        match = False
        ignore = self.registryValue("ignorePattern", channel)
        strip = self.registryValue("stripPattern", channel)
        text = ircutils.stripFormatting(text)
        text = fix_text(text)
        if self.registryValue('stripRelayedNick', channel):
            text = self.MATCH_MESSAGE_STRIPNICK.match(text).group('message')
        if ignore:
            match = re.search(ignore, text)
            if match:
                log.debug("Markovify: %s matches ignorePattern for %s" % (text, channel))
                return
        if strip:
            match = re.findall(strip, text)
            if match:
                for x in match:
                    text = text.replace(x, '')
                    log.debug("Markovify: %s matches stripPattern for %s. New text text: %s" % (x, channel, text))
        if self.registryValue('stripURL', channel):
            new_text = re.sub(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', '', text)
            if new_text != text:
                log.debug("Markovify: url(s) stripped from text for %s. New text text: %s" % (channel, new_text))
                text = new_text
        text = text.strip()                         # Strip whitespace from beginning and the end of the string.
        text = utils.str.normalizeWhitespace(text)  # Normalize the whitespace in the string.
        text = self.capsents(text)
        if text and len(text) > 1 and not text.isspace():
            return text
        else:
            return None

    def subreddit(self, irc, msg, args, channel, subreddits):
        """[channel] <subreddit_1> [subreddit_2] [subreddit_3] [...etc.]
        Load subreddit comments into csv files
        """
        if not channel: # Did the user enter in a channel? If not, set the currect channel
            channel = msg.args[0]
        channel = msg.args[0].lower()
        for subreddit in subreddits.lower().strip().split(' '):
            self.latest_timestamp = None
            max_comments = 2000
            irc.reply("Downloading: {}".format(subreddit))
            tries = 0
            self.count = 0
            self.model[channel] = None
            while self.count <= max_comments:
                if tries >= 50:
                    break
                if self.model[channel]:
                    self.model[channel] = markovify.combine(models=[self.model[channel], self._subreddit(subreddit, self.latest_timestamp)])
                else:
                    self.model[channel] = self._subreddit(subreddit, self.latest_timestamp)
                tries += 1
            directory = conf.supybot.directories.data
            directory = directory.dirize(channel.lower() + "/markov.json")
            with open(directory, 'w') as outfile:
                jsondata = self.model[channel].to_json()
                json.dump(jsondata, outfile)
            irc.reply("Retrieved {0} comments from {1}".format(self.count, subreddit))
    subreddit = wrap(subreddit, [additional('channel'), 'text'])

    def respond(self, irc, msg, args, channel):
        """[channel] <text>
        Respomd to <text> using channel conversational model
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        try:
            new_comment = self.model[channel].make_sentence()
        except KeyError:
            directory = conf.supybot.directories.data
            directory = directory.dirize(channel.lower() + "/markov.json")
            with open(directory) as infile:
                jsondata = json.load(infile)
                self.model[channel] = POSifiedText.from_json(jsondata)
            new_comment = self.model[channel].make_sentence()
        except:
            return
        irc.reply(new_comment, prefixNick=False)
        self.model[channel] = markovify.combine(models=[self.model[channel], POSifiedText(new_comment)])
        directory = conf.supybot.directories.data
        directory = directory.dirize(channel.lower() + "/markov.json")
        with open(directory, 'w') as outfile:
            jsondata = self.model[channel].to_json()
            json.dump(jsondata, outfile)
    respond = wrap(respond, [optional('channel')])

Class = Markovify
