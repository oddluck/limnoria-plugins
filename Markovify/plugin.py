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
from itertools import chain
import os
import requests
import random
import re
import json
import markovify
import spacy
from ftfy import fix_text
from nltk.tokenize import sent_tokenize
import gc

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Markovify')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

nlp = spacy.load('en_core_web_sm')

CONTRACTION_MAP = {
"ain't": "is not",
"aren't": "are not",
"can't": "cannot",
"can't've": "cannot have",
"'cause": "because",
"could've": "could have",
"couldn't": "could not",
"couldn't've": "could not have",
"didn't": "did not",
"doesn't": "does not",
"don't": "do not",
"hadn't": "had not",
"hadn't've": "had not have",
"hasn't": "has not",
"haven't": "have not",
"he'd": "he would",
"he'd've": "he would have",
"he'll": "he will",
"he'll've": "he he will have",
"he's": "he is",
"how'd": "how did",
"how'd'y": "how do you",
"how'll": "how will",
"how's": "how is",
"I'd": "I would",
"I'd've": "I would have",
"I'll": "I will",
"I'll've": "I will have",
"I'm": "I am",
"I've": "I have",
"i'd": "i would",
"i'd've": "i would have",
"i'll": "i will",
"i'll've": "i will have",
"i'm": "i am",
"i've": "i have",
"isn't": "is not",
"it'd": "it would",
"it'd've": "it would have",
"it'll": "it will",
"it'll've": "it will have",
"it's": "it is",
"let's": "let us",
"ma'am": "madam",
"mayn't": "may not",
"might've": "might have",
"mightn't": "might not",
"mightn't've": "might not have",
"must've": "must have",
"mustn't": "must not",
"mustn't've": "must not have",
"needn't": "need not",
"needn't've": "need not have",
"o'clock": "of the clock",
"oughtn't": "ought not",
"oughtn't've": "ought not have",
"shan't": "shall not",
"sha'n't": "shall not",
"shan't've": "shall not have",
"she'd": "she would",
"she'd've": "she would have",
"she'll": "she will",
"she'll've": "she will have",
"she's": "she is",
"should've": "should have",
"shouldn't": "should not",
"shouldn't've": "should not have",
"so've": "so have",
"so's": "so as",
"that'd": "that would",
"that'd've": "that would have",
"that's": "that is",
"there'd": "there would",
"there'd've": "there would have",
"there's": "there is",
"they'd": "they would",
"they'd've": "they would have",
"they'll": "they will",
"they'll've": "they will have",
"they're": "they are",
"they've": "they have",
"to've": "to have",
"wasn't": "was not",
"we'd": "we would",
"we'd've": "we would have",
"we'll": "we will",
"we'll've": "we will have",
"we're": "we are",
"we've": "we have",
"weren't": "were not",
"what'll": "what will",
"what'll've": "what will have",
"what're": "what are",
"what's": "what is",
"what've": "what have",
"when's": "when is",
"when've": "when have",
"where'd": "where did",
"where's": "where is",
"where've": "where have",
"who'll": "who will",
"who'll've": "who will have",
"who's": "who is",
"who've": "who have",
"why's": "why is",
"why've": "why have",
"will've": "will have",
"won't": "will not",
"won't've": "will not have",
"would've": "would have",
"wouldn't": "would not",
"wouldn't've": "would not have",
"y'all": "you all",
"y'all'd": "you all would",
"y'all'd've": "you all would have",
"y'all're": "you all are",
"y'all've": "you all have",
"you'd": "you would",
"you'd've": "you would have",
"you'll": "you will",
"you'll've": "you will have",
"you're": "you are",
"you've": "you have"
}

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
        self.directory = conf.supybot.directories.data
        self.MATCH_MESSAGE_STRIPNICK = re.compile('^(<[^ ]+> )?(?P<message>.*)$')

    def save_corpus(self, channel):
        file = self.directory.dirize(channel + "/markov.json")
        os.makedirs(self.directory.dirize(channel), exist_ok=True)
        with open(file, 'w') as outfile:
            jsondata = self.model[channel].to_json()
            json.dump(jsondata, outfile)

    def add_text(self, channel, text):
        text = self.capsents(text)
        text = self.expand_contractions(text)
        if self.registryValue('stripURL', channel):
            new_text = re.sub(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', '', text)
            if new_text != text:
                log.debug("Markovify: url(s) stripped from text for %s. New text text: %s" % (channel, new_text))
                text = new_text
        text = re.sub("(^')|('$)|\s'|'\s|[\"(\(\)\[\])]", "", text)
        text = re.sub('<[^<]+?>', '', text)
        text = fix_text(text)
        try:
            self.model[channel] = markovify.combine(models=[self.model[channel], POSifiedText(text, retain_original=False)])
        except KeyError:
            file = self.directory.dirize(channel.lower() + "/markov.json")
            try:
                with open(file) as infile:
                    jsondata = json.load(infile)
                    self.model[channel] = POSifiedText.from_json(jsondata)
                    self.model[channel] = markovify.combine(models=[self.model[channel], POSifiedText(text)])
            except:
                self.model[channel] = POSifiedText(text, retain_original=False)

    def get_response(self, channel):
        try:
            response = self.model[channel].make_sentence()
        except KeyError:
            file = self.directory.dirize(channel.lower() + "/markov.json")
            try:
                with open(file) as infile:
                    jsondata = json.load(infile)
                    self.model[channel] = POSifiedText.from_json(jsondata)
            except:
                return
            response = self.model[channel].make_sentence()
        except:
            return
        if response and len(response) > 1 and not response.isspace():
            response = re.sub(' ([.!?,;:]) ', '\g<1> ', response)
            response = re.sub(' ([.!?,])$', '\g<1>', response)
            response = re.sub('([.?!,])(?=[^\s])', '\g<1> ', response)
            response = response.replace(' - ', '-')
            return response
        else:
            return None

    def capsents(self, user_sentences):
        sents = sent_tokenize(user_sentences)
        capitalized_sents = [sent.capitalize() for sent in sents]
        joined_ = ' '.join(capitalized_sents)
        return joined_

    def expand_contractions(self, text, contraction_mapping=CONTRACTION_MAP):
        contractions_pattern = re.compile('({})'.format('|'.join(contraction_mapping.keys())),
                                          flags=re.IGNORECASE|re.DOTALL)
        def expand_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            expanded_contraction = contraction_mapping.get(match)\
                                    if contraction_mapping.get(match)\
                                    else contraction_mapping.get(match.lower())
            expanded_contraction = first_char+expanded_contraction[1:]
            return expanded_contraction
        expanded_text = contractions_pattern.sub(expand_match, text)
        expanded_text = re.sub("'", "", expanded_text)
        return expanded_text

    def _subreddit(self, subreddit, latest_timestamp=None):
        """
        Downloads the subreddit comments, 500 at a time.
        """
        base_url = "https://api.pushshift.io/reddit/comment/search/"
        params = {"subreddit": subreddit, "sort": "desc",
                  "sort_type": "created_utc", "size": 500, "user_removed": False, "mod_removed": False}
        if latest_timestamp != None:
            params["before"] = latest_timestamp
        with requests.get(base_url, params=params) as response:
            data = response.json()
            self.count += len(data["data"])
            self.latest_timestamp = data['data'][-1]["created_utc"]
            data = [item['body'] for item in data["data"]]
            return data

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
            response = self.get_response(channel)
            if response and len(response) > 1 and not response.isspace():
                irc.reply(response, prefixNick=False)
                self.add_text(channel, response)
                self.add_text(channel, message)
        else:
            self.add_text(channel, message)
        self.save_corpus(channel)

    def processText(self, channel, text):
        match = False
        ignore = self.registryValue("ignorePattern", channel)
        strip = self.registryValue("stripPattern", channel)
        text = ircutils.stripFormatting(text)
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
        ends_with_punctuation = False
        if not text.strip() or text.isspace():
            return
        for char in [".", "?", "!"]:
            if text.endswith(char):
                ends_with_punctuation = True
                break
        if not ends_with_punctuation:
            text = text + "."
        if text and len(text) > 1 and not text.isspace():
            return text
        else:
            return None

    def subreddit(self, irc, msg, args, channel, optlist, subreddits):
        """[channel] [--num <###>] <subreddit_1> [subreddit_2] [subreddit_3] [...etc.]
        Load subreddit comments into channel corpus.
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        optlist = dict(optlist)
        if 'num' in optlist:
            max_comments = optlist.get('num')
        else:
            max_comments = 500
        for subreddit in subreddits.lower().strip().split(' '):
            self.latest_timestamp = None
            irc.reply("Attempting to retrieve last {0} comments from r/{1}".format(max_comments, subreddit))
            self.count = 0
            data = self._subreddit(subreddit, self.latest_timestamp)
            text = ""
            tries = 0
            self.count = 0
            data = []
            while self.count < max_comments:
                if tries > 20:
                    break
                data.extend(self._subreddit(subreddit, self.latest_timestamp))
                tries += 1
            if data:
                for line in data:
                    if not line.strip() or line.isspace():
                        continue
                    if '[removed]' in line:
                        continue
                    ends_with_punctuation = False
                    for char in [".", "?", "!"]:
                        if line.endswith(char):
                            ends_with_punctuation = True
                            break
                    if not ends_with_punctuation:
                        line = line + "."
                    text += " {}".format(line)
                self.add_text(channel, text)
            self.save_corpus(channel)
            irc.reply("Added {0} comments from r/{1}.".format(self.count, subreddit))
            del data, text
            gc.collect()
    subreddit = wrap(subreddit, [additional('channel'), getopts({'num':'int'}), 'text'])

    def text(self, irc, msg, args, channel, optlist, url):
        """[channel] <url>
        Load text file into channel corpus.
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        optlist = dict(optlist)
        if 'process' in optlist:
            process = True
        else:
            process = False
        r = requests.head(url)
        if "text/plain" in r.headers["content-type"]:
            file = requests.get(url)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        data = file.content.decode()
        lines = 0
        text = ""
        for line in data.split('\n'):
            if not line.strip() or line.isspace():
                continue
            if process:
                line = self.processText(channel, line)
            if not line or not line.strip() or line.isspace():
                continue
            text += " {}".format(line)
            lines += 1
        self.add_text(channel, text)
        irc.reply("{0} lines added to brain file for channel {1}.".format(lines, channel))
        self.save_corpus(channel)
        del data
        gc.collect()
    text = wrap(text, [additional('channel'), getopts({'process':''}), 'text'])

    def respond(self, irc, msg, args, channel):
        """[channel]
        Generate a response from channel corpus.
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        response = self.get_response(channel)
        if response:
            irc.reply(response, prefixNick=False)
            self.save_corpus(channel)
    respond = wrap(respond, [optional('channel')])

Class = Markovify
